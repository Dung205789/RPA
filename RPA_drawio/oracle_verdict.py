#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decide whether a step's postcondition actually holds.

Added 2026-09-22 for G0.1 / G0.1b (`RPA_docs/PLAN.md`). This is the back half of
the independent oracle; the front half is ``oracle_steps`` (what was asked for)
and the reader is ``mx_oracle`` (what the editor now holds).

The rule this exists to enforce is `RPA_docs/ORACLE.md` §1: no number may be
reported below **N3**, and `Move`, `Connect`, `Delete` must also clear **N4**.
Before this module, ``drawio_ops.move_cell`` both performed the nudge and
certified it, with the certificate reading ``(|dx| + |dy|) >= distance // 2`` —
75px out of a demanded 150px passed. That single line is what
`RPA_docs/DIAGNOSIS.md` L1 measures the damage of.

Everything here reads the mxGraph model. Nothing reads the SVG geometry that
``cell_tracker`` and ``drawio_ops`` measure, and nothing consults the executor's
own opinion of the step it just ran. The executor's opinion *is* recorded next to
the verdict — that is how the false-pass rate is computed (`ORACLE.md` §3.1) —
but it never influences it.

Which step owns which cell is worked out here too, from model diffs alone: a
shape click that adds exactly one vertex binds that vertex to that step. The
executor keeps its own DOM-handle tracker for driving; the two are never
compared, so a mistake in one cannot excuse a mistake in the other.
"""
from __future__ import annotations

import os
import time

import mx_oracle
import oracle_steps

# ``Move`` is graded against the same constant the executor nudges by; they are
# two uses of one number, not a measurement of itself. ±2 model units is the
# tolerance `ORACLE.md` §1 sets.
MOVE_TOLERANCE = 2.0
RESIZE_TOLERANCE = 2.0

# draw.io's style vocabulary for the nine shapes in ``RPA_drawio/shape_icons``.
# A statement about how draw.io names its own shapes, not about any case: the
# same table serves every scenario that clicks any of those icons.
ICON_STYLE = {
    # Strictly "rectangle": the palette also offers a rounded rectangle, whose
    # icon is 97% identical at thumbnail size (`DIAGNOSIS.md` L6), so allowing
    # both here would hide exactly the mis-match that matters. DECISIONS D5
    # substitutes a rectangle for a rounded rectangle in the *scenario*; once the
    # step says "click rectangle.png", a rounded rectangle is the wrong shape.
    "rectangle": {"rectangle"},
    "ellipse": {"ellipse"},
    "diamond": {"rhombus"},
    "hexagon": {"hexagon"},
    "parallelogram": {"parallelogram"},
    "trapezoid": {"trapezoid"},
    "cylinder": {"cylinder", "cylinder3", "datastore"},
    "document": {"document"},
}

_UI_STATE_JS = r"""
const vis = (e) => e.offsetParent !== null;
const dialogs = Array.from(document.querySelectorAll('.geDialog, .geTransDialog')).filter(vis);
const menus = Array.from(document.querySelectorAll('.mxPopupMenu, .geMenu')).filter(vis);
const gs = window.__RPA_GRAPHS__ || [];
let editing = null, g = null;
for (let i = 0; i < gs.length; i++) {
  const c = gs[i].container;
  if (c && String(c.className).indexOf('geDiagramContainer') >= 0) { g = gs[i]; break; }
}
if (g && g.cellEditor && g.cellEditor.editingCell) editing = g.cellEditor.editingCell.id;
const ae = document.activeElement;
return {
  url: location.href,
  palette: document.querySelectorAll('.geSidebarContainer a.geItem').length,
  dialogs: dialogs.map(e => (e.textContent || '').trim().slice(0, 60)),
  menus: menus.length,
  menuText: menus.map(e => (e.textContent || '').trim().slice(0, 120)).join('|'),
  editingCell: editing,
  activeTag: ae ? ae.tagName.toLowerCase() : null,
  activeEditable: ae ? (ae.tagName.toLowerCase() === 'input'
                        || ae.tagName.toLowerCase() === 'textarea'
                        || !!ae.isContentEditable) : false,
  canvas: !!document.querySelector('.geDiagramContainer svg')
};
"""

_TEXT_VISIBLE_JS = r"""
const want = arguments[0].trim().toLowerCase().replace(/\s+/g, ' ');
let found = 0;
document.querySelectorAll('*').forEach(e => {
  if (e.children.length > 0) return;
  const t = (e.textContent || '').trim().toLowerCase().replace(/\s+/g, ' ');
  if (t !== want) return;
  if (e.offsetParent === null) return;
  const r = e.getBoundingClientRect();
  if (r.width > 0 && r.height > 0) found++;
});
return found;
"""


class State:
    """Everything the oracle needs about one instant, read in one visit."""

    __slots__ = ("model", "ui", "t")

    def __init__(self, model, ui):
        self.model = model
        self.ui = ui or {}
        self.t = time.time()


def read_state(driver) -> State:
    return State(mx_oracle.snapshot(driver), driver.execute_script(_UI_STATE_JS))


def _icon_key(path: str) -> str:
    return os.path.splitext(os.path.basename(path or ""))[0].lower()


class Verdict(dict):
    """One row of the judgement log. ``verdict`` is the only field a rate uses."""

    def __init__(self, step, level, verdict, reason="", **extra):
        super().__init__(n=step.n, action=step.action,
                         oracle_row=oracle_steps.ORACLE_ROW.get(step.action),
                         level=level, verdict=verdict, reason=reason, **extra)

    @property
    def ok(self):
        return self["verdict"] == "pass"


class Oracle:
    """Judges a scenario's steps, keeping its own step -> cell bindings.

    Usage per step::

        before = oracle.before(n)
        ...executor runs the step...
        verdict = oracle.after(n, before)

    ``before``/``after`` read the model; they never write to it and never touch
    the selection, so interposing them cannot change what the executor sees.
    """

    def __init__(self, driver, steps: list, log=None):
        self.driver = driver
        self.steps = {s.n: s for s in steps}
        self.log = log or (lambda *a, **k: None)
        self.bind = {}            # ('created', n) / ('connector', a, b) -> cell id
        self.verdicts = {}
        self.unavailable = 0
        # What the most recent `Double click on ...` step *named*. A bare
        # `Fill "X"` types into whatever that step left open, so this is the cell
        # the scenario intends the text to land on — which is not the same thing
        # as the cell the editor actually opened on. Judging the fill against the
        # open editor would pass the text wherever a mis-aimed double click had
        # put it, which is precisely the silent wrong-element failure
        # `ORACLE.md` §3.1 exists to catch.
        self.last_double_click = None

    # ------------------------------------------------------------- snapshots
    def before(self, n: int):
        try:
            return read_state(self.driver)
        except Exception as exc:
            self.log("[oracle] pre-state unreadable at step %d: %s" % (n, exc))
            return None

    def after(self, n: int, before: State | None, executor_status: str = "",
              executor_detail: dict | None = None) -> Verdict:
        step = self.steps.get(n) or oracle_steps.OracleStep(n=n, text="")
        try:
            now = read_state(self.driver)
        except Exception as exc:
            self.unavailable += 1
            v = Verdict(step, "none", "no-verdict",
                        "oracle could not read the model: %s" % exc)
            v["executor_status"] = executor_status
            self.verdicts[n] = v
            return v
        if before is None:
            # `Open` is the one step with legitimately nothing before it: the
            # model cannot be read until the page it loads exists. Every other
            # action needs its pre-state, and must not be graded without one.
            if step.action == "open":
                before = State(mx_oracle.Model(), {})
            else:
                v = Verdict(step, "none", "no-verdict", "no pre-state for this step")
                v["executor_status"] = executor_status
                self.verdicts[n] = v
                return v
        v = self._judge(step, before, now)
        v["executor_status"] = executor_status
        # `ok` from the executor while the oracle says otherwise is the false pass
        # `ORACLE.md` §3.1 calls the project's most serious defect. Flagged on the
        # row so no later summary has to re-derive it.
        v["false_pass"] = bool(executor_status == "ok" and v["verdict"] == "fail")
        v["false_fail"] = bool(executor_status in ("failed", "error")
                               and v["verdict"] == "pass")
        self.verdicts[n] = v
        return v

    # ---------------------------------------------------------------- lookup
    def resolve(self, ref):
        if ref is None:
            return None
        return self.bind.get(ref.key())

    # --------------------------------------------------------------- judging
    def _judge(self, step, b: State, a: State) -> Verdict:
        d = mx_oracle.diff(b.model, a.model)
        fn = getattr(self, "_j_" + step.action, None)
        if fn is None:
            return Verdict(step, "none", "no-verdict",
                           "no postcondition defined for %r" % step.action,
                           diff=d.as_dict())
        return fn(step, b, a, d)

    # -- 1. open ------------------------------------------------------------
    def _j_open(self, step, b, a, d):
        """The editor is up, its palette is drawn, nothing is in front of it.

        The corpus writes ``Open "https://app.diagrams.net/"`` because that is
        where it was authored. DECISIONS D9 pins the runs to a local
        ``jgraph/drawio:28.2.5`` instead, so the host in the step is not the host
        that should load — deliberately. The postcondition is therefore "the
        draw.io this environment is configured to drive came up", with the
        substitution recorded on the row rather than scored as a failure. The
        *readiness* half of the check is unchanged and is the part that can fail.
        """
        import rpa_env
        want = (step.value or "").rstrip("/")
        configured = (rpa_env.DRAWIO_URL or "").rstrip("/")
        got = (a.ui.get("url") or "").rstrip("/")

        def _host(u):
            return u.split("//")[-1].split("/")[0]

        substituted = bool(got) and _host(got) == _host(configured) != _host(want)
        loaded = bool(got) and (_host(got) in (_host(want), _host(configured)))
        palette = a.ui.get("palette") or 0
        blocked = bool(a.ui.get("dialogs"))
        empty = not a.model.vertices and not a.model.edges
        ok3 = loaded and palette >= 20 and not blocked
        reason = []
        if not loaded:
            reason.append("url is %r, wanted %r or the configured %r"
                          % (got, want, configured))
        if palette < 20:
            reason.append("palette rendered %d entries (<20)" % palette)
        if blocked:
            reason.append("modal in front: %s" % a.ui["dialogs"][:1])
        if not empty:
            reason.append("canvas not empty: %d vertices, %d edges"
                          % (len(a.model.vertices), len(a.model.edges)))
        return Verdict(step, "N3+N4", "pass" if (ok3 and empty) else "fail",
                       "; ".join(reason), n3=ok3, n4=empty,
                       measured={"palette": palette, "url": got,
                                 "url_in_step": want,
                                 "host_substituted_per_D9": substituted})

    # -- 2. click on a shape icon -------------------------------------------
    def _j_click_shape(self, step, b, a, d):
        new_v = [cid for cid in d.added if a.model.cells[cid].kind == "vertex"]
        new_e = [cid for cid in d.added if a.model.cells[cid].kind == "edge"]
        if len(new_v) != 1:
            return Verdict(step, "N3+N4", "fail",
                           "%d vertices appeared, wanted exactly 1" % len(new_v),
                           n3=False, n4=None, diff=d.as_dict())
        cid = new_v[0]
        cell = a.model.cells[cid]
        want = ICON_STYLE.get(_icon_key(step.target.text))
        drawn = cell.shape_key()
        type_ok = None if want is None else (drawn in want)
        # N4: an insert must not disturb what was already there.
        others = (set(d.moved) | set(d.resized) | set(d.relabelled)
                  | set(d.restyled) | set(d.reanchored) | d.removed) - {cid}
        n4 = not others and not new_e
        self.bind[("created", step.n)] = cid
        ok = (type_ok is not False) and n4
        reason = []
        if type_ok is False:
            reason.append("icon %r drew %r" % (_icon_key(step.target.text), drawn))
        if others:
            reason.append("also changed: %s" % sorted(others))
        if new_e:
            reason.append("an edge appeared as well: %s" % new_e)
        return Verdict(step, "N3+N4", "pass" if ok else "fail", "; ".join(reason),
                       n3=(type_ok is not False), n4=n4,
                       measured={"cell": cid, "shape": drawn,
                                 "type_checked": type_ok is not None},
                       diff=d.as_dict())

    # -- 2b. click on a bracketed icon that is not a shape -------------------
    def _j_click_control(self, step, b, a, d):
        """A bracketed image from a mixed icon dump.

        `ORACLE.md` §1 row 2 assumes a bracketed icon inserts a shape. In the old
        100-case corpus most do not: ``object2.png`` is the zoom control,
        ``help.png`` a menu entry. Whether such a click "worked" is not decidable
        from the model, so this is reported at **N2 + N4** — the target was
        activated in the sense that the UI responded, and the diagram was not
        disturbed — and counted separately. See DECISIONS D10.
        """
        changed = (a.ui.get("menuText") != b.ui.get("menuText")
                   or a.ui.get("dialogs") != b.ui.get("dialogs")
                   or a.ui.get("menus") != b.ui.get("menus")
                   or a.ui.get("url") != b.ui.get("url"))
        made = sorted(d.added)
        n4 = not (d.removed or d.moved or d.resized or d.relabelled or d.reanchored)
        # It may legitimately be a shape after all (the folder rule is coarse);
        # record that rather than calling it a side effect.
        if made:
            for cid in made:
                if a.model.cells[cid].kind == "vertex":
                    self.bind[("created", step.n)] = cid
                    break
        ok = bool(changed or made)
        return Verdict(step, "N2+N4", "pass" if (ok and n4) else "fail",
                       "" if ok else "no UI response and nothing created",
                       n3=None, n4=n4, measured={"created": made, "ui_changed": changed},
                       diff=d.as_dict())

    # -- 3. click on a text control -----------------------------------------
    def _j_click_text(self, step, b, a, d):
        want = step.target.text
        try:
            visible = self.driver.execute_script(_TEXT_VISIBLE_JS, want)
        except Exception:
            visible = None
        responded = (a.ui.get("menuText") != b.ui.get("menuText")
                     or a.ui.get("dialogs") != b.ui.get("dialogs")
                     or a.ui.get("menus") != b.ui.get("menus")
                     or a.ui.get("url") != b.ui.get("url")
                     or a.ui.get("activeTag") != b.ui.get("activeTag"))
        model_changed = bool(d.touched())
        ok = bool(responded or model_changed)
        reason = "" if ok else "clicking %r changed nothing observable" % want
        return Verdict(step, "N3", "pass" if ok else "fail", reason,
                       n3=ok, n4=None,
                       measured={"text_still_visible": visible, "responded": responded},
                       diff=d.as_dict())

    def _j_click_cell(self, step, b, a, d):
        """`Click on the element created in step N` — a selection, not an edit."""
        cid = self.resolve(step.target)
        untouched = not d.touched()
        ok = cid is not None and untouched
        return Verdict(step, "N2+N4", "pass" if ok else "fail",
                       "" if cid else "step %s created nothing to click" % step.target.step,
                       n3=None, n4=untouched, measured={"cell": cid}, diff=d.as_dict())

    # -- 4. double click ----------------------------------------------------
    def _j_double_click(self, step, b, a, d):
        if step.target.kind == "text":
            return self._j_click_text(step, b, a, d)
        # Remembered whatever the verdict turns out to be: a bare Fill after a
        # failed double click still *intended* this cell.
        self.last_double_click = step.target
        cid = self.resolve(step.target)
        editing = a.ui.get("editingCell")
        if cid is None:
            return Verdict(step, "N3+N4", "fail",
                           "nothing bound to %r" % (step.target.key(),),
                           n3=False, n4=None, diff=d.as_dict())
        n3 = (editing == cid)
        n4 = not d.touched()
        reason = ""
        if not n3:
            reason = ("label editor is on %r, wanted %r" % (editing, cid)
                      if editing else "no label editor open")
        return Verdict(step, "N3+N4", "pass" if (n3 and n4) else "fail", reason,
                       n3=n3, n4=n4, measured={"cell": cid, "editing": editing},
                       diff=d.as_dict())

    # -- 5. fill / enter ----------------------------------------------------
    def _j_fill(self, step, b, a, d):
        want = " ".join((step.value or "").split())
        cid = self.resolve(step.target) if step.target.kind != "none" else None
        aimed_at_editor = False
        if cid is None and step.target.kind == "none":
            # A bare Fill goes into whatever the previous step left open. The
            # cell it *should* land on is the one that step named, not the one
            # the editor happens to be sitting on — see `last_double_click`.
            cid = self.resolve(self.last_double_click)
            if cid is None:
                cid = b.ui.get("editingCell")
                aimed_at_editor = cid is not None
        if cid is None:
            # Nothing on the canvas was being edited: the text went into a dialog
            # or a search box. Judge it there — it is still a postcondition.
            typed = bool(a.ui.get("activeEditable"))
            return Verdict(step, "N2", "pass" if typed else "fail",
                           "" if typed else "no editable target for the text",
                           n3=None, n4=not d.touched(),
                           measured={"target": "off-canvas"}, diff=d.as_dict())
        cell = a.model.cells.get(cid)
        if cell is None:
            got = None
        elif cell.kind == "edge":
            # An edge label is on the edge's own `value` when it sits at the
            # midpoint, and on a child cell once draw.io has to position it. All
            # 70 bare `Fill` steps in this corpus are edge labels, so reading
            # only `value` would fail the positioned ones for the wrong reason.
            got = a.model.edge_label(cell)
        else:
            got = cell.value
        n3 = (got == want)
        still_editing = a.ui.get("editingCell") == cid
        # A label stored as a child of the target edge is that edge's label, not
        # a stray cell, so it is not a side effect.
        label_children = {c for c in d.added
                          if (a.model.cells[c].parent == cid
                              and a.model.cells[c].kind == "vertex")}
        others = {k: v for k, v in d.relabelled.items() if k != cid}
        stray = (d.added - label_children) | d.removed
        n4 = not others and not stray
        reason = []
        if not n3:
            reason.append("cell %s reads %r, wanted %r" % (cid, got, want))
        if still_editing:
            reason.append("editor still open (not committed)")
        if others:
            reason.append("other labels changed: %s" % sorted(others))
        if stray:
            reason.append("cells appeared or vanished: %s" % sorted(stray))
        return Verdict(step, "N3+N4" if not aimed_at_editor else "N2+N4",
                       "pass" if (n3 and n4 and not still_editing) else "fail",
                       "; ".join(reason), n3=n3, n4=n4,
                       measured={"cell": cid, "value": got, "wanted": want,
                                 "target_from": ("open editor" if aimed_at_editor
                                                 else "the step that named it")},
                       diff=d.as_dict())

    # -- 6. move ------------------------------------------------------------
    _VEC = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}

    def _j_move(self, step, b, a, d, want_px=None):
        import drawio_ops
        want = drawio_ops.MOVE_STEP_PX if want_px is None else want_px
        cid = self.resolve(step.target)
        if cid is None:
            return Verdict(step, "N3+N4", "fail",
                           "nothing bound to step %s" % step.target.step,
                           n3=False, n4=None, diff=d.as_dict())
        vec = self._VEC.get(step.direction)
        if vec is None:
            return Verdict(step, "N3+N4", "fail", "unreadable direction %r" % step.direction,
                           n3=False, n4=None, diff=d.as_dict())
        bc, ac = b.model.cells.get(cid), a.model.cells.get(cid)
        if bc is None or ac is None or None in (bc.x, ac.x):
            return Verdict(step, "N3+N4", "fail", "cell %s has no geometry" % cid,
                           n3=False, n4=None, diff=d.as_dict())
        dx, dy = ac.x - bc.x, ac.y - bc.y
        ex, ey = vec[0] * want, vec[1] * want
        err = max(abs(dx - ex), abs(dy - ey))
        n3 = err <= MOVE_TOLERANCE
        # N4: nothing else may move. An edge anchored to the moved cell has no
        # x/y of its own, so it never appears here.
        others = {k: v for k, v in d.moved.items() if k != cid}
        n4 = (not others and not d.added and not d.removed and not d.resized
              and not d.relabelled and not d.reanchored)
        reason = []
        if not n3:
            reason.append("moved (%+.0f, %+.0f), wanted (%+.0f, %+.0f)" % (dx, dy, ex, ey))
        if not n4:
            reason.append("side effects: %s" % d.as_dict())
        return Verdict(step, "N3+N4", "pass" if (n3 and n4) else "fail", "; ".join(reason),
                       n3=n3, n4=n4,
                       measured={"cell": cid, "dx": round(dx, 1), "dy": round(dy, 1),
                                 "wanted": want, "error_px": round(err, 1)},
                       diff=d.as_dict())

    # -- 7. connect ---------------------------------------------------------
    def _j_connect(self, step, b, a, d):
        src = self.resolve(step.target)
        dst = self.resolve(step.related)
        new_e = [cid for cid in d.added if a.model.cells[cid].kind == "edge"]
        if src is None or dst is None:
            return Verdict(step, "N3+N4", "fail", "endpoint not bound (%s -> %s)" % (src, dst),
                           n3=False, n4=None, diff=d.as_dict())
        if len(new_e) != 1:
            return Verdict(step, "N3+N4", "fail",
                           "%d edges appeared, wanted exactly 1" % len(new_e),
                           n3=False, n4=None,
                           measured={"src": src, "dst": dst}, diff=d.as_dict())
        e = a.model.cells[new_e[0]]
        n3 = (e.source == src and e.target == dst)
        n4 = not d.reanchored and not d.removed
        reason = ""
        if not n3:
            reason = "edge anchored %s->%s, wanted %s->%s" % (e.source, e.target, src, dst)
        if n3:
            key = step.target.step, (step.related.step if step.related else None)
            self.bind[("connector", key[0], key[1])] = e.id
        return Verdict(step, "N3+N4", "pass" if (n3 and n4) else "fail", reason,
                       n3=n3, n4=n4,
                       measured={"edge": e.id, "source": e.source, "target": e.target,
                                 "want_source": src, "want_target": dst},
                       diff=d.as_dict())

    # -- 8/9. extend / shrink -----------------------------------------------
    _EDGE_AXIS = {"right": ("w", 1), "left": ("w", -1), "top": ("h", -1),
                  "up": ("h", -1), "bottom": ("h", 1), "down": ("h", 1)}

    def _j_resize(self, step, b, a, d, grow: bool):
        """N3: the named edge moved by the amount asked for, ±2 units.

        N4 here is *the opposite edge held*, not "the centre held" as
        `ORACLE.md` §1 rows 8–9 originally put it. Measured 2026-09-22
        (`RPA_docs/probe_editor.json` section B): Ctrl+Right grows the width and
        leaves ``x`` alone, so the centre necessarily moves by half the growth.
        A centre-held predicate would fail every correct extension. The centre's
        movement is still reported on the row. See DECISIONS D11.
        """
        import drawio_ops
        want = drawio_ops.RESIZE_STEP_PX
        cid = self.resolve(step.target)
        if cid is None:
            return Verdict(step, "N3+N4", "fail", "nothing bound to step %s" % step.target.step,
                           n3=False, n4=None, diff=d.as_dict())
        axis = self._EDGE_AXIS.get((step.edge or step.direction or "").lower())
        if axis is None:
            return Verdict(step, "N3+N4", "fail", "unreadable edge %r" % step.edge,
                           n3=False, n4=None, diff=d.as_dict())
        bc, ac = b.model.cells.get(cid), a.model.cells.get(cid)
        if bc is None or ac is None or None in (bc.w, ac.w):
            return Verdict(step, "N3+N4", "fail", "cell %s has no geometry" % cid,
                           n3=False, n4=None, diff=d.as_dict())
        dim = "w" if axis[0] == "w" else "h"
        before_v = getattr(bc, dim)
        after_v = getattr(ac, dim)
        delta = after_v - before_v
        expect = want if grow else -want
        n3 = abs(delta - expect) <= RESIZE_TOLERANCE
        other_dim = "h" if dim == "w" else "w"
        other_changed = abs(getattr(ac, other_dim) - getattr(bc, other_dim)) > RESIZE_TOLERANCE
        centre_held = (abs((ac.cx or 0) - (bc.cx or 0)) <= RESIZE_TOLERANCE
                       and abs((ac.cy or 0) - (bc.cy or 0)) <= RESIZE_TOLERANCE)
        # Which edge the step named, and therefore which one must not have moved.
        named = (step.edge or step.direction or "").lower()
        anchor_attr = "x" if dim == "w" else "y"
        anchor_moved = getattr(ac, anchor_attr) - getattr(bc, anchor_attr)
        if named in ("right", "bottom", "down"):
            opposite_held = abs(anchor_moved) <= RESIZE_TOLERANCE
        else:                                   # left / top: that edge moves instead
            opposite_held = abs(anchor_moved + delta) <= RESIZE_TOLERANCE
        others = (set(d.moved) | set(d.resized) | d.added | d.removed) - {cid}
        n4 = not others and opposite_held
        reason = []
        if not n3:
            reason.append("%s changed %+.0f, wanted %+.0f" % (dim, delta, expect))
        if other_changed:
            reason.append("the other dimension changed too")
        if not opposite_held:
            reason.append("the opposite edge moved %+.0f" % anchor_moved)
        if others:
            reason.append("also changed: %s" % sorted(others))
        return Verdict(step, "N3+N4", "pass" if (n3 and n4 and not other_changed) else "fail",
                       "; ".join(reason), n3=n3, n4=n4,
                       measured={"cell": cid, "d" + dim: round(delta, 1),
                                 "wanted": expect, "edge": named,
                                 "opposite_edge_held": opposite_held,
                                 "centre_held": centre_held,
                                 "centre_moved": [round((ac.cx or 0) - (bc.cx or 0), 1),
                                                  round((ac.cy or 0) - (bc.cy or 0), 1)]},
                       diff=d.as_dict())

    def _j_extend(self, step, b, a, d):
        return self._j_resize(step, b, a, d, grow=True)

    def _j_shrink(self, step, b, a, d):
        return self._j_resize(step, b, a, d, grow=False)

    # -- 10. delete ---------------------------------------------------------
    def _j_delete(self, step, b, a, d):
        cid = self.resolve(step.target)
        if cid is None:
            return Verdict(step, "N3+N4", "fail", "nothing bound to step %s" % step.target.step,
                           n3=False, n4=None, diff=d.as_dict())
        n3 = cid in d.removed
        # Removing a vertex takes its own edges with it — that is draw.io's
        # semantics for the gesture, not a side effect of a mis-aimed one.
        incident = {e.id for e in b.model.edges if cid in (e.source, e.target)}
        unexpected = d.removed - {cid} - incident
        n4 = not unexpected and not d.added and not d.moved and not d.resized
        reason = []
        if not n3:
            reason.append("cell %s is still on the canvas" % cid)
        if unexpected:
            reason.append("also removed: %s" % sorted(unexpected))
        return Verdict(step, "N3+N4", "pass" if (n3 and n4) else "fail", "; ".join(reason),
                       n3=n3, n4=n4,
                       measured={"cell": cid, "collateral_edges": sorted(incident & d.removed)},
                       diff=d.as_dict())

    # -- 11. press ----------------------------------------------------------
    def _j_press(self, step, b, a, d):
        """Declared at N2, per `ORACLE.md` §1's own note on this action.

        Enter in the shape-search box and Enter on the canvas have nothing in
        common to assert, so there is no general N3 postcondition to write. What
        is checkable is that the key reached a focused element and that the
        diagram was not altered behind the gesture's back.
        """
        focused = b.ui.get("activeTag") is not None
        n4 = not d.touched()
        return Verdict(step, "N2", "pass" if (focused and n4) else "fail",
                       "" if focused else "nothing had focus to receive the key",
                       n3=None, n4=n4,
                       measured={"focus_before": b.ui.get("activeTag"),
                                 "focus_after": a.ui.get("activeTag")},
                       diff=d.as_dict())


def summarise(verdicts: dict, steps: list) -> dict:
    """Step-level totals in the shape `ORACLE.md` §6 asks a report to print."""
    passed = {n: (v["verdict"] == "pass") if v["verdict"] != "no-verdict" else None
              for n, v in verdicts.items()}
    kinds = oracle_steps.classify(steps, passed)
    n_total = len(steps)
    counts = {"pass": 0, "root": 0, "cascade": 0, "no-verdict": 0}
    for n in range(1, n_total + 1):
        counts[kinds.get(n, "no-verdict")] = counts.get(kinds.get(n, "no-verdict"), 0) + 1
    graded = [v for v in verdicts.values() if v["verdict"] != "no-verdict"]
    return {
        "n_steps": n_total,
        "n_graded": len(graded),
        "pass": counts["pass"],
        "root_failure": counts["root"],
        "cascade_failure": counts["cascade"],
        "no_verdict": counts["no-verdict"],
        "false_pass": sum(1 for v in verdicts.values() if v.get("false_pass")),
        "false_fail": sum(1 for v in verdicts.values() if v.get("false_fail")),
        "by_action": _by_action(verdicts),
        "kinds": kinds,
    }


def _by_action(verdicts: dict) -> dict:
    out = {}
    for v in verdicts.values():
        row = out.setdefault(v["action"], {"n": 0, "pass": 0, "fail": 0, "no-verdict": 0,
                                           "false_pass": 0, "level": v["level"]})
        row["n"] += 1
        row[v["verdict"]] = row.get(v["verdict"], 0) + 1
        if v.get("false_pass"):
            row["false_pass"] += 1
    return out
