#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read a scenario's step language without asking the executor what it thinks.

Added 2026-09-22 for G0.3b and as the front half of the independent oracle
(`RPA_docs/ORACLE.md` §2, `RPA_docs/PLAN.md` G0).

The executor understands a step through ``step_parser.StepParser`` — stanza plus
a sentence-transformer action matcher. That is the right tool for *driving* the
editor, and it is deliberately not reused here: if the same reader both decides
what a step asked for and decides whether that was delivered, a misreading
passes unnoticed in both halves at once.

The corpus does not need NLP to be judged. Counted 2026-09-22 over the two
draw.io corpora on disk, the step language collapses to 75 distinct templates in
``RPA_Datasets/data/drawio`` (100 scenarios) and 72 in ``RPA_Datasets_new30_v2``
(30 scenarios), and the drawing verbs among them are a closed, fully templated
set. So this module reads them with an explicit grammar. Anything the grammar
does not recognise comes back as ``action='unknown'`` and is *reported*, never
guessed at — an unparsed step must not silently become a passing one.

It also builds the dependency graph G0.3b asks for: which later steps cannot
possibly succeed once an earlier one has failed. That is what separates a root
failure from a cascade, and stops the two being averaged into one number.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------- the grammar

_CREATED = r"the element created in step\s+(\d+)"
_CONNECTOR = r"connector_from_step(\d+)_to_step(\d+)"

# "up", "down", "left", "right", and the corpus's "to the left" / "to the up".
_DIR = r"(?:to\s+the\s+)?(up|down|left|right|top|bottom)"

_DIR_CANON = {"up": "up", "top": "up", "down": "down", "bottom": "down",
              "left": "left", "right": "right"}

_RULES = [
    ("open", re.compile(r'^\s*open\s+"([^"]*)"\s*$', re.I)),
    ("connect", re.compile(
        r'^\s*connect\s+' + _CREATED + r'\s+to\s+' + _CREATED + r'\s*$', re.I)),
    ("move", re.compile(r'^\s*move\s+' + _CREATED + r'\s+' + _DIR + r'\s*$', re.I)),
    ("fill_into", re.compile(
        r'^\s*fill\s+"([^"]*)"\s+into\s+' + _CREATED + r'\s*$', re.I)),
    ("fill", re.compile(r'^\s*fill\s+"([^"]*)"\s*$', re.I)),
    ("dclick_created", re.compile(r'^\s*double\s+click\s+on\s+' + _CREATED + r'\s*$', re.I)),
    ("dclick_conn", re.compile(r'^\s*double\s+click\s+on\s+' + _CONNECTOR + r'\s*$', re.I)),
    ("click_created", re.compile(r'^\s*click\s+(?:on\s+)?' + _CREATED + r'\s*$', re.I)),
    ("click_conn", re.compile(r'^\s*click\s+(?:on\s+)?' + _CONNECTOR + r'\s*$', re.I)),
    ("click_image", re.compile(r'^\s*click\s+(?:on\s+)?\[(.+?)\]\s*$', re.I)),
    ("press", re.compile(r'^\s*press\s+(.+?)\s*$', re.I)),
    ("extend", re.compile(
        r'^\s*extend\s+the\s+(\w+)\s+edge\s+of\s+' + _CREATED + r'\s*$', re.I)),
    ("shrink", re.compile(
        r'^\s*shrink\s+the\s+(\w+)\s+edge\s+of\s+' + _CREATED + r'\s*$', re.I)),
    ("scale_up", re.compile(r'^\s*scale\s+up\s+' + _CREATED + r'\s+' + _DIR + r'\s*$', re.I)),
    ("scale_down", re.compile(r'^\s*scale\s+down\s+' + _CREATED + r'\s+' + _DIR + r'\s*$', re.I)),
    ("delete", re.compile(r'^\s*(?:delete|remove)\s+' + _CREATED + r'\s*$', re.I)),
    ("click_text", re.compile(r'^\s*click\s+(?:on\s+)?(.+?)\s*$', re.I)),
    ("dclick_text", re.compile(r'^\s*double\s+click\s+(?:on\s+)?(.+?)\s*$', re.I)),
]

# Which ORACLE §1 row each action is judged by.
ORACLE_ROW = {
    "open": 1, "click_shape": 2, "click_control": 2, "click_text": 3,
    "click_cell": 3, "double_click": 4, "fill": 5, "move": 6, "connect": 7,
    "extend": 8, "shrink": 9, "delete": 10, "press": 11,
}


@dataclass
class Ref:
    """What a step points at, expressed the way the scenario expresses it."""
    kind: str                # 'created' | 'connector' | 'image' | 'text' | 'none'
    step: int | None = None
    from_step: int | None = None
    to_step: int | None = None
    text: str = ""

    def key(self):
        if self.kind == "created":
            return ("created", self.step)
        if self.kind == "connector":
            return ("connector", self.from_step, self.to_step)
        return (self.kind, self.text)

    def creation_steps(self) -> list:
        if self.kind == "created":
            return [self.step]
        if self.kind == "connector":
            return [self.from_step, self.to_step]
        return []


@dataclass
class OracleStep:
    n: int                        # 1-based index into descriptions
    text: str
    action: str = "unknown"
    target: Ref = field(default_factory=lambda: Ref("none"))
    related: Ref | None = None    # connect's second endpoint
    value: str = ""               # the typed string, the URL, the key name
    direction: str = ""           # for move / scale
    edge: str = ""                # for extend / shrink
    note: str = ""

    def is_drawing(self) -> bool:
        return self.action in ("click_shape", "move", "connect", "fill",
                               "double_click", "extend", "shrink", "delete")


def _is_shape_vocabulary(icon_path: str) -> bool:
    """Does this icon come from a folder that is a shape palette, not an icon dump?

    The same rule the executor uses to decide whether identifying a drawn shape
    is meaningful, restated here because the judgement must not be taken on the
    executor's word. It is a rule about a *folder*, not about a case, so it does
    not violate the no-hard-coding invariant: ``RPA_drawio/shape_icons`` holds
    nine shape templates and nothing else, while ``RPA_Datasets/images/drawio``
    holds 64 files that are mostly toolbar and menu glyphs.
    """
    import os
    d = os.path.dirname(icon_path) or "."
    try:
        pngs = [f for f in os.listdir(d)
                if f.lower().endswith(".png") and not f.startswith("_")]
    except OSError:
        return False
    return 0 < len(pngs) <= 15


def parse_step(n: int, text: str) -> OracleStep:
    """One description line -> what it asks for. No NLP, no executor."""
    s = OracleStep(n=n, text=text)
    # A trailing comma on an otherwise well-formed line is a typo in the corpus,
    # not a different instruction: one line of the old drawio corpus reads
    # `Open "https://app.diagrams.net/",`. Strip it rather than report the step
    # unreadable, which would hand it a free "no verdict".
    raw = (text or "").strip().rstrip(",")
    for name, rx in _RULES:
        m = rx.match(raw)
        if not m:
            continue
        if name == "open":
            s.action, s.value = "open", m.group(1)
        elif name == "connect":
            s.action = "connect"
            s.target = Ref("created", step=int(m.group(1)))
            s.related = Ref("created", step=int(m.group(2)))
        elif name == "move":
            s.action = "move"
            s.target = Ref("created", step=int(m.group(1)))
            s.direction = _DIR_CANON[m.group(2).lower()]
        elif name == "fill_into":
            s.action = "fill"
            s.value = m.group(1)
            s.target = Ref("created", step=int(m.group(2)))
        elif name == "fill":
            s.action, s.value = "fill", m.group(1)
            s.target = Ref("none")
        elif name == "dclick_created":
            s.action = "double_click"
            s.target = Ref("created", step=int(m.group(1)))
        elif name == "dclick_conn":
            s.action = "double_click"
            s.target = Ref("connector", from_step=int(m.group(1)), to_step=int(m.group(2)))
        elif name == "click_created":
            s.action = "click_cell"
            s.target = Ref("created", step=int(m.group(1)))
        elif name == "click_conn":
            s.action = "click_cell"
            s.target = Ref("connector", from_step=int(m.group(1)), to_step=int(m.group(2)))
        elif name == "click_image":
            path = m.group(1)
            s.action = "click_shape" if _is_shape_vocabulary(path) else "click_control"
            s.target = Ref("image", text=path)
        elif name == "press":
            s.action, s.value = "press", m.group(1)
        elif name in ("extend", "shrink"):
            s.action = name
            s.edge = m.group(1).lower()
            s.target = Ref("created", step=int(m.group(2)))
        elif name in ("scale_up", "scale_down"):
            s.action = "extend" if name == "scale_up" else "shrink"
            s.target = Ref("created", step=int(m.group(1)))
            s.direction = _DIR_CANON[m.group(2).lower()]
            s.edge = s.direction
        elif name == "delete":
            s.action = "delete"
            s.target = Ref("created", step=int(m.group(1)))
        elif name == "click_text":
            s.action, s.target = "click_text", Ref("text", text=m.group(1))
        elif name == "dclick_text":
            s.action, s.target = "double_click", Ref("text", text=m.group(1))
        return s
    return s


def parse_scenario(descriptions: list) -> list:
    """Every line, 1-based, including the ones the grammar cannot read."""
    return [parse_step(i + 1, d) for i, d in enumerate(descriptions)]


# --------------------------------------------------------- dependency graph

def dependencies(steps: list) -> dict:
    """step number -> the steps that must have succeeded for it to be possible.

    Only *preconditions* count. Two kinds exist in this language:

    * **existence** — "the element created in step K" cannot be acted on if step
      K created nothing. A connector reference needs the connect step that made
      it, and that connect step's own two endpoints.
    * **editor state** — a bare ``Fill "X"`` with no target types into whatever
      the previous step left focused, so it depends on that step.

    Deliberately *not* counted: a later step whose geometry would be wrong
    because an earlier ``Move`` fell short. That step can still meet its own
    postcondition, so calling it a cascade would move failures out of the
    "root" column and flatter the tool. `ORACLE.md` §3.3 records that positions
    are relative and that the damage is real — it is charged at the figure
    level, where it belongs, not hidden at step level.
    """
    by_n = {s.n: s for s in steps}
    # Every step that connects a given pair, in order. A scenario may connect the
    # same two shapes twice — ``medium_m08_v3_s5b2l0`` does, to hang a second
    # label on the pair — so a single "who made this connector" entry would point
    # a reference at whichever connect came *last*, including ones that had not
    # run yet. The maker of a reference at step N is the latest connect before N.
    conn_steps = {}
    for s in steps:
        if s.action == "connect":
            a = s.target.step
            b = s.related.step if s.related is not None else None
            if a is not None and b is not None:
                conn_steps.setdefault((a, b), []).append(s.n)

    deps = {}
    for s in steps:
        need = set()
        refs = [s.target, s.related]
        for r in refs:
            if r is None:
                continue
            if r.kind == "created" and r.step is not None:
                need.add(r.step)
            elif r.kind == "connector":
                need.update(x for x in (r.from_step, r.to_step) if x is not None)
                earlier = [n for n in conn_steps.get((r.from_step, r.to_step), [])
                           if n < s.n]
                if earlier:
                    need.add(earlier[-1])
        if s.action == "fill" and s.target.kind == "none" and s.n > 1:
            prev = by_n.get(s.n - 1)
            if prev is not None and prev.action in ("double_click", "click_text",
                                                    "click_control", "click_shape"):
                need.add(prev.n)
        need.discard(s.n)
        deps[s.n] = sorted(need)
    return deps


def dependents(steps: list) -> dict:
    """The transpose: step -> every later step that hard-depends on it."""
    deps = dependencies(steps)
    out = {s.n: [] for s in steps}
    for n, ds in deps.items():
        for d in ds:
            out.setdefault(d, []).append(n)
    return {k: sorted(v) for k, v in out.items()}


def classify(steps: list, passed: dict) -> dict:
    """Split every step into pass / root failure / cascade failure.

    ``passed`` maps step number -> bool (None for steps with no verdict).
    A failing step is a *cascade* only when something it hard-depends on, at any
    depth, also failed; otherwise it is the root of its own failure.
    """
    deps = dependencies(steps)
    order = sorted(deps)
    broken = set()
    out = {}
    for n in order:
        ok = passed.get(n)
        if ok is None:
            out[n] = "no-verdict"
            continue
        if ok:
            out[n] = "pass"
            continue
        chain = [d for d in deps.get(n, []) if d in broken]
        out[n] = "cascade" if chain else "root"
        broken.add(n)
    return out
