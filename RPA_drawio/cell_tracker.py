#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Track the diagram cells draw.io has on its canvas, and which step created each.

Added 2026-09-03, replacing the DOM-diff in detect_new_g for the draw.io runs.
The old approach could not work, for reasons that are all visible in a live DOM
dump (scratchpad probes, 2026-09-03):

* It identified a cell by a positional CSS path (``:nth-child(k)`` chains) taken
  once and reused later. mxGraph re-creates a cell's SVG node on every redraw, so
  those paths go stale as soon as anything moves.
* It kept every ``<g>`` carrying ``visibility: visible`` and no text. That set
  also contains the selection preview (``cursor: move; visibility: visible``),
  so a shape being selected counted as a newly created element and shifted the
  whole step->element mapping by one.
* It diffed against the snapshot taken at step 1 only, and that snapshot was
  taken *before* the ``open`` action navigated, so on draw.io it captured the
  previous page and failed outright ("Không thể tạo selector cho container").
  After that failure the executor silently never tracked anything, which is why
  every "element created in step N" resolved to ``//not-found``.

What this module does instead: ask the DOM, every time, for the cells in the
content layers only, and hand back live element handles plus geometry. Identity
is the cell's position in document order, which mxGraph keeps equal to model
insertion order — verified by inserting, moving and connecting shapes and
watching the order hold.
"""
from __future__ import annotations

# A "cell" is a shape or an edge that belongs to the diagram. Three things have to
# be excluded, and each exclusion is here because it was observed polluting the set:
#   - the handler layer (selection preview + the eight resize handles + rotate),
#   - label groups (they carry the text; the shape's own group has none),
#   - decoration groups with no geometry primitive of their own.
_CELLS_JS = r"""
const svg = document.querySelector('.geDiagramContainer svg');
if (!svg) return [];
const root = svg.querySelector('g');
if (!root) return [];
const layers = Array.from(root.children).filter(c => c.tagName.toLowerCase() === 'g');

// The handler layer is the one that owns resize/rotate affordances. Identifying it
// by what it contains, rather than by a fixed index, survives draw.io reshuffling
// its layers between builds.
const isHandlerLayer = (l) =>
  Array.from(l.querySelectorAll('*')).some(e => {
    const st = e.getAttribute('style') || '';
    return st.includes('resize') || st.includes('crosshair');
  });

const GEO = new Set(['rect','ellipse','path','polygon','polyline','line','image']);
const out = [];
layers.filter(l => !isHandlerLayer(l)).forEach(layer => {
  Array.from(layer.children).forEach(g => {
    if (g.tagName.toLowerCase() !== 'g') return;
    if (g.textContent.trim().length > 0) return;      // a label group, not a cell
    if (g.querySelector('foreignObject')) return;
    const geo = Array.from(g.children)
        .filter(c => GEO.has(c.tagName.toLowerCase()));
    if (geo.length === 0) return;
    out.push(g);
  });
});
return out;
"""

# Positions come back twice over: in viewport coordinates (what ActionChains needs)
# and with the canvas scroll added back in (what stays comparable across steps).
# The distinction is not cosmetic: Selenium scrolls an element into view before
# clicking it, which pans the canvas container, so a shape that never moved can
# appear to have jumped 70px. Measuring displacement in viewport coordinates made
# a 150px nudge read as 78px.
_INFO_JS = r"""
const GEO = new Set(['rect','ellipse','path','polygon','polyline','line','image']);
const cont = document.querySelector('.geDiagramContainer');
const sx = cont ? cont.scrollLeft : 0;
const sy = cont ? cont.scrollTop : 0;
return arguments[0].map((g, i) => {
  const r = g.getBoundingClientRect();
  const geo = Array.from(g.children).filter(c => GEO.has(c.tagName.toLowerCase()));
  const tags = geo.map(c => c.tagName.toLowerCase());
  // An mxGraph edge renders as several <path> elements (wide invisible hit area,
  // the visible stroke, the arrow marker); a vertex owns exactly one primitive.
  const isEdge = tags.length > 1 && tags.every(t => t === 'path');
  return {
    index: i,
    kind: isEdge ? 'edge' : (tags[0] || 'unknown'),
    tags: tags.join(','),
    x: Math.round(r.x), y: Math.round(r.y),
    w: Math.round(r.width), h: Math.round(r.height),
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
    mx: Math.round(r.x + r.width / 2 + sx), my: Math.round(r.y + r.height / 2 + sy)
  };
});
"""

# Text that draw.io has painted on the canvas, with the box it sits in. Used to
# check that a Fill actually landed on the intended shape.
_LABELS_JS = r"""
const svg = document.querySelector('.geDiagramContainer svg');
if (!svg) return [];
const out = [];
svg.querySelectorAll('g').forEach(g => {
  const t = g.textContent.trim();
  if (!t) return;
  if (Array.from(g.children).some(c => c.tagName.toLowerCase() === 'g')) return; // keep the innermost
  const r = g.getBoundingClientRect();
  out.push({text: t, x: Math.round(r.x), y: Math.round(r.y),
            cx: Math.round(r.x + r.width/2), cy: Math.round(r.y + r.height/2)});
});
return out;
"""


def cell_elements(driver) -> list:
    """Live WebElement handles for the diagram's cells, in insertion order."""
    return driver.execute_script(_CELLS_JS) or []


def cell_info(driver, elements=None) -> list:
    """Geometry and kind for each cell, in the same order as :func:`cell_elements`."""
    if elements is None:
        elements = cell_elements(driver)
    if not elements:
        return []
    return driver.execute_script(_INFO_JS, elements)


def canvas_labels(driver) -> list:
    """Every piece of text currently painted on the canvas, with its position."""
    return driver.execute_script(_LABELS_JS) or []


class CellTracker:
    """Remembers which step produced which cell, and re-resolves it on demand.

    The scenario language refers to shapes as "the element created in step N" and
    to edges as ``connector_from_stepA_to_stepB``. This class is the only place
    that mapping lives.

    Identity is the DOM node itself, held as a Selenium element handle. Position
    in document order looked like the obvious key and is wrong: mxGraph paints
    edges beneath vertices, so the first connector a scenario draws is inserted at
    index 0 and shifts every previously recorded index by one (observed
    2026-09-03 — a two-shape diagram became ``[edge, rect, rect]``). Node handles
    do not move when the list is reordered, and mxGraph updates a cell's group in
    place rather than recreating it, so a handle survives moves, labelling and
    redraws. Geometry is kept alongside purely as a recovery path for the case
    where a handle does go stale.
    """

    def __init__(self, driver, log=None):
        self.driver = driver
        self.log = log or (lambda *a, **k: None)
        self.step_to_cell: dict = {}        # step number -> {"el":…, "info":…}
        self.connector_to_cell: dict = {}   # (from_step, to_step) -> {"el":…, "info":…}

    # ---- observation -------------------------------------------------------
    def snapshot(self) -> list:
        """The current cells as (element, info) pairs."""
        els = cell_elements(self.driver)
        return list(zip(els, cell_info(self.driver, els))) if els else []

    def count(self) -> int:
        return len(cell_elements(self.driver))

    def _new_cell_since(self, known: list):
        """The cell present now whose handle was not in ``known``."""
        for el, info in self.snapshot():
            if el not in known:
                return el, info
        return None, None

    # ---- recording ---------------------------------------------------------
    def record_created(self, step_num: int, known_before: list) -> bool:
        """Bind ``step_num`` to whichever cell appeared since ``known_before``.

        Returns False when the action produced nothing, which is the signal that
        the step failed — reported rather than papered over, because the previous
        executor's habit of continuing regardless is what let scenarios finish
        with an empty canvas and still be counted "ok".
        """
        el, info = self._new_cell_since(known_before)
        if el is None:
            self.log("[track] step %d created no cell (count still %d)"
                     % (step_num, len(known_before)))
            return False
        self.step_to_cell[step_num] = {"el": el, "info": info}
        self.log("[track] step %d -> %s cell at (%d,%d)"
                 % (step_num, info["kind"], info["mx"], info["my"]))
        return True

    def record_connector(self, from_step: int, to_step: int, known_before: list) -> bool:
        el, info = self._new_cell_since(known_before)
        if el is None:
            self.log("[track] connect %d->%d created no edge" % (from_step, to_step))
            return False
        self.connector_to_cell[(from_step, to_step)] = {"el": el, "info": info}
        self.log("[track] connector %d->%d -> %s cell" % (from_step, to_step, info["kind"]))
        return True

    # ---- resolution --------------------------------------------------------
    def element_for_step(self, step_num: int):
        return self._resolve(self.step_to_cell.get(step_num))

    def element_for_connector(self, from_step: int, to_step: int):
        return self._resolve(self.connector_to_cell.get((from_step, to_step)))

    def _resolve(self, entry):
        """Refresh a remembered cell's geometry, falling back to nearest-match."""
        if entry is None:
            return None, None
        els = cell_elements(self.driver)
        if not els:
            return None, None
        infos = cell_info(self.driver, els)
        for el, info in zip(els, infos):
            if el == entry["el"]:
                entry["info"] = info          # keep the recovery hint current
                return el, info
        # Handle went stale (draw.io rebuilt the node). Fall back to the nearest
        # cell of the same kind to the last known position.
        last = entry["info"]
        same = [(el, i) for el, i in zip(els, infos) if i["kind"] == last["kind"]]
        if not same:
            self.log("[track] lost a %s cell entirely" % last["kind"])
            return None, None
        el, info = min(same, key=lambda p: (p[1]["mx"] - last["mx"]) ** 2
                                           + (p[1]["my"] - last["my"]) ** 2)
        self.log("[track] handle went stale, recovered %s cell by position" % last["kind"])
        entry["el"], entry["info"] = el, info
        return el, info
