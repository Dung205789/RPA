#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read draw.io's own cell model, by a path the executor never touches.

Added 2026-09-22 for G0 (`RPA_docs/PLAN.md`), to satisfy the rule in
`RPA_docs/ORACLE.md` §2: the component that performs an action must not be the
component that certifies it.

Why a second reader at all
--------------------------
``cell_tracker`` measures the *rendered SVG*: it walks ``.geDiagramContainer
svg``, filters ``<g>`` panes, reads ``getBoundingClientRect()`` and divides out
the canvas transform to recover something model-like. Every gesture in
``drawio_ops`` is judged with that same ruler, so a mistake in the ruler — the
wrong pane picked, a stale transform, a rebuilt node — shows up identically in
the action and in the verdict on the action, and the run cannot notice.

This module asks mxGraph for its model instead: the logical cells, their
``mxGeometry`` in model units, their style strings, and, for an edge, the ids of
the two cells it is actually anchored to. Nothing here measures pixels, reads a
bounding box, or knows the SVG panes exist. The two paths share only the browser.

How the model is reached
------------------------
draw.io keeps no global handle on its ``EditorUi`` (probed 2026-09-22: ``App``,
``EditorUi``, ``Graph``, ``mxCodec`` are all defined, no instance is exported,
and no ``window`` key holds one). So a small observer is injected with
``Page.addScriptToEvaluateOnNewDocument`` *before* the page's own scripts run: it
waits for ``mxGraph`` to exist and wraps ``mxGraph.prototype.init`` so every
graph that gets built records itself. The editor's graph is then the instance
whose container is ``.geDiagramContainer`` — draw.io builds two (the outline has
its own), which is why the container is checked rather than taking the first.

The observer only observes. It creates no cells, moves nothing, and is never
consulted by the execution path.

One edge case worth naming: the hook must be installed *before* the page loads.
``ensure()`` reloads once if it finds the page already up without it.
"""
from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

# Injected at document start. It polls because app.min.js defines mxGraph some
# way into its own execution; 2000 ticks at 5ms is 10s, far longer than observed
# (mxGraph appears within ~200ms locally) but harmless if draw.io never loads.
HOOK_JS = r"""
(function () {
  if (window.__RPA_ORACLE_HOOK__) return;
  window.__RPA_ORACLE_HOOK__ = true;
  window.__RPA_GRAPHS__ = [];
  var tries = 0;
  var iv = setInterval(function () {
    if (++tries > 2000) { clearInterval(iv); return; }
    if (typeof window.mxGraph !== 'function') return;
    clearInterval(iv);
    var orig = mxGraph.prototype.init;
    mxGraph.prototype.init = function (container) {
      try { window.__RPA_GRAPHS__.push(this); } catch (e) {}
      return orig.apply(this, arguments);
    };
  }, 5);
})();
"""

_FIND_GRAPH_JS = r"""
var gs = window.__RPA_GRAPHS__ || [];
for (var i = 0; i < gs.length; i++) {
  var c = gs[i].container;
  if (c && String(c.className).indexOf('geDiagramContainer') >= 0) return true;
}
return false;
"""

_MODEL_XML_JS = r"""
var gs = window.__RPA_GRAPHS__ || [];
var g = null;
for (var i = 0; i < gs.length; i++) {
  var c = gs[i].container;
  if (c && String(c.className).indexOf('geDiagramContainer') >= 0) { g = gs[i]; break; }
}
if (!g) return null;
var enc = new mxCodec();
return mxUtils.getXml(enc.encode(g.getModel()));
"""


class OracleUnavailable(RuntimeError):
    """The model could not be read. Never downgrade this to 'the step passed'."""


def install(driver) -> None:
    """Arm the observer for every page this driver loads from now on.

    Idempotent per driver: Chrome keeps every script handed to
    ``addScriptToEvaluateOnNewDocument`` and runs them all, so calling this once
    per scenario would accumulate hundreds of copies over a batch.
    """
    if getattr(driver, "_rpa_oracle_installed", False):
        return
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": HOOK_JS})
    driver._rpa_oracle_installed = True


def is_armed(driver) -> bool:
    try:
        return bool(driver.execute_script(_FIND_GRAPH_JS))
    except Exception:
        return False


def ensure(driver, reload_if_missing: bool = True, timeout: float = 30.0) -> bool:
    """Make sure the current page is observable; reload once if it is not."""
    install(driver)
    if is_armed(driver):
        return True
    if not reload_if_missing:
        return False
    driver.refresh()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_armed(driver):
            return True
        time.sleep(0.5)
    return False


def model_xml(driver) -> str:
    xml = driver.execute_script(_MODEL_XML_JS)
    if not xml:
        raise OracleUnavailable(
            "mxGraph model not reachable — was mx_oracle.install() called before the page loaded?")
    return xml


# --------------------------------------------------------------------- parsing

@dataclass
class Cell:
    """One cell of the model. Geometry is in model units, never pixels on screen."""
    id: str
    parent: str | None = None
    value: str = ""
    style: str = ""
    kind: str = "other"          # 'vertex' | 'edge' | 'other'
    x: float | None = None
    y: float | None = None
    w: float | None = None
    h: float | None = None
    source: str | None = None
    target: str | None = None

    @property
    def cx(self):
        return None if self.x is None or self.w is None else self.x + self.w / 2.0

    @property
    def cy(self):
        return None if self.y is None or self.h is None else self.y + self.h / 2.0

    def shape_key(self) -> str:
        """The style reduced to what names the shape, for type comparison."""
        return style_shape(self.style)

    def box(self):
        return (self.x, self.y, self.w, self.h)


@dataclass
class Model:
    cells: dict = field(default_factory=dict)
    xml: str = ""

    def _label_children(self) -> dict:
        """Edge labels draw.io stored as child cells rather than on the edge."""
        out = {}
        for c in self.cells.values():
            par = self.cells.get(c.parent or "")
            if par is not None and par.kind == "edge" and c.kind == "vertex" and c.value:
                out.setdefault(par.id, []).append(c.value)
        return out

    @property
    def vertices(self) -> list:
        """Diagram shapes. Edge-label children are not shapes and are excluded."""
        out = []
        for c in self.cells.values():
            if c.kind != "vertex":
                continue
            par = self.cells.get(c.parent or "")
            if par is not None and par.kind == "edge":
                continue
            out.append(c)
        return sorted(out, key=_id_sort_key)

    @property
    def edges(self) -> list:
        return sorted((c for c in self.cells.values() if c.kind == "edge"), key=_id_sort_key)

    def edge_label(self, edge: Cell) -> str:
        if edge.value:
            return edge.value
        kids = self._label_children().get(edge.id) or []
        return kids[0] if kids else ""

    def get(self, cid):
        return self.cells.get(cid)

    def ids(self) -> set:
        return set(self.cells)


def _id_sort_key(cell: Cell):
    """Numeric ids sort numerically; draw.io's hash ids fall back to text."""
    m = re.fullmatch(r"\d+", cell.id or "")
    return (0, int(cell.id), "") if m else (1, 0, cell.id or "")


def _text_of(value: str) -> str:
    """Strip the HTML draw.io wraps a typed label in, keeping the visible text."""
    if not value:
        return ""
    s = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
          .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    return " ".join(s.split())


_NON_SHAPE_TOKENS = {"html", "whiteSpace", "sketch", "rounded", "dashed",
                     "comic", "labelBackgroundColor"}


def style_shape(style: str) -> str:
    """Name the shape a style string draws, ignoring colour and decoration.

    draw.io writes a vertex style as a semicolon list. The shape is named either
    by a bare leading word (``ellipse``, ``rhombus``, ``triangle``), by
    ``shape=<name>``, or not at all — a plain rectangle has no shape token, and
    ``rounded=1`` is what separates a rounded rectangle from a square one. Those
    three cases are exactly what the corpus's shape vocabulary needs, so they are
    what this normalises to.
    """
    if style is None:
        return "unknown"
    parts = [p.strip() for p in str(style).split(";") if p.strip()]
    shape = None
    rounded = False
    for p in parts:
        if "=" not in p:
            if p not in _NON_SHAPE_TOKENS:
                shape = shape or p
            continue
        k, _, v = p.partition("=")
        k = k.strip()
        if k == "shape":
            shape = v.strip()
        elif k == "rounded":
            rounded = v.strip() in ("1", "true")
        elif k == "ellipse":
            shape = shape or "ellipse"
    if shape:
        return shape.lower()
    return "rounded rectangle" if rounded else "rectangle"


def _read_geometry(src, cell: "Cell") -> None:
    geo = src.find("mxGeometry")
    if geo is None:
        return
    for attr, name in (("x", "x"), ("y", "y"), ("width", "w"), ("height", "h")):
        raw = geo.get(attr)
        if raw is None:
            continue
        try:
            setattr(cell, name, float(raw))
        except ValueError:
            pass


def parse(xml: str) -> Model:
    """Turn an encoded mxGraphModel into cells. Pure function, no browser."""
    root = ET.fromstring(xml)
    node = root if root.tag == "root" else root.find("root")
    model = Model(xml=xml)
    if node is None:
        return model

    # <object>/<UserObject> wraps an <mxCell> and carries the label itself. Walk
    # the wrappers first and remember their inner cells, so the plain-mxCell pass
    # below does not also record the same shape under the inner element.
    wrapped = set()
    for el in node.iter():
        if el.tag not in ("object", "UserObject"):
            continue
        inner = el.find("mxCell")
        if inner is None:
            continue
        wrapped.add(id(inner))
        cid = el.get("id") or inner.get("id") or ""
        if not cid:
            continue
        cell = _cell_from(cid, inner, el.get("label") or "")
        model.cells[cid] = cell

    for el in node.iter("mxCell"):
        if id(el) in wrapped:
            continue
        cid = el.get("id") or ""
        if not cid or cid in model.cells:
            continue
        model.cells[cid] = _cell_from(cid, el, el.get("value") or "")
    return model


def _cell_from(cid: str, src, value: str) -> Cell:
    kind = ("edge" if src.get("edge") in ("1", "true")
            else "vertex" if src.get("vertex") in ("1", "true") else "other")
    cell = Cell(id=cid, parent=src.get("parent"), value=_text_of(value),
                style=src.get("style") or "", kind=kind,
                source=src.get("source"), target=src.get("target"))
    _read_geometry(src, cell)
    return cell


def snapshot(driver) -> Model:
    """The model as it stands right now."""
    return parse(model_xml(driver))


# ----------------------------------------------------------------------- diffs

@dataclass
class Diff:
    added: set = field(default_factory=set)
    removed: set = field(default_factory=set)
    moved: dict = field(default_factory=dict)       # id -> (dx, dy)
    resized: dict = field(default_factory=dict)     # id -> (dw, dh)
    relabelled: dict = field(default_factory=dict)  # id -> (before, after)
    restyled: dict = field(default_factory=dict)    # id -> (before, after)
    reanchored: dict = field(default_factory=dict)  # id -> ((s,t) before, after)

    def touched(self) -> set:
        return (self.added | self.removed | set(self.moved) | set(self.resized)
                | set(self.relabelled) | set(self.restyled) | set(self.reanchored))

    def as_dict(self) -> dict:
        return {"added": sorted(self.added), "removed": sorted(self.removed),
                "moved": {k: [round(v[0], 2), round(v[1], 2)] for k, v in self.moved.items()},
                "resized": {k: [round(v[0], 2), round(v[1], 2)] for k, v in self.resized.items()},
                "relabelled": self.relabelled, "restyled": self.restyled,
                "reanchored": {k: [list(a), list(b)] for k, (a, b) in self.reanchored.items()}}


def diff(before: Model, after: Model, eps: float = 0.51) -> Diff:
    """What changed between two model snapshots.

    ``eps`` is a hair over half a model unit: mxGeometry is floating point and
    draw.io snaps a dragged cell to its grid, so an unmoved cell can differ in
    the last bits. Anything at or above half a unit is a real change.
    """
    d = Diff()
    d.added = after.ids() - before.ids()
    d.removed = before.ids() - after.ids()
    for cid in before.ids() & after.ids():
        b, a = before.cells[cid], after.cells[cid]
        if None not in (b.x, b.y, a.x, a.y):
            dx, dy = a.x - b.x, a.y - b.y
            if abs(dx) >= eps or abs(dy) >= eps:
                d.moved[cid] = (dx, dy)
        if None not in (b.w, b.h, a.w, a.h):
            dw, dh = a.w - b.w, a.h - b.h
            if abs(dw) >= eps or abs(dh) >= eps:
                d.resized[cid] = (dw, dh)
        if b.value != a.value:
            d.relabelled[cid] = (b.value, a.value)
        if b.style != a.style:
            d.restyled[cid] = (b.style, a.style)
        if (b.source, b.target) != (a.source, a.target):
            d.reanchored[cid] = ((b.source, b.target), (a.source, a.target))
    return d
