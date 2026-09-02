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

# A "cell" is a shape or an edge that belongs to the diagram.
#
# mxGraph lays the canvas out as a root <g> holding four sibling panes, in this
# order (dumped from a live editor, 2026-09-03):
#
#   layer 0  empty
#   layer 1  CONTENT  - <g style="visibility: visible; opacity: 1; cursor: move">
#                        wrapping one <rect>/<ellipse>/<path> per vertex, plus
#                        <g style="visibility: visible"> with three <path>s per edge,
#                        plus a text-bearing <g> per label
#   layer 2  HANDLERS - the selection preview and the eight resize handles and the
#                        rotate grip, each <g style="cursor: *"> wrapping an <image>
#   layer 3  empty
#
# Two earlier rules for telling content from handlers both failed:
#   * "reject any <g> whose style names a cursor" — real vertices carry
#     `cursor: move` too, so this deleted the whole diagram once a shape had been
#     hovered;
#   * "reject any layer containing a resize/crosshair style" — a transient during
#     the connect drag flagged the content layer as well, and cell detection
#     collapsed from 6 cells to 0 mid-scenario, which took three connect steps
#     down with it.
#
# What is stable is the *ordering*: the handler pane always follows the content
# pane, and handlers only exist while something in the content pane is selected.
# So the content pane is simply the first pane that yields any cell at all.
_CELLS_JS = r"""
const svg = document.querySelector('.geDiagramContainer svg');
if (!svg) return [];
const root = svg.querySelector('g');
if (!root) return [];
const GEO = new Set(['rect','ellipse','path','polygon','polyline','line','image']);

const cellsOf = (layer) => Array.from(layer.children).filter(g => {
  if (g.tagName.toLowerCase() !== 'g') return false;
  const st = g.getAttribute('style') || '';
  if (!st.includes('visibility: visible')) return false;
  if (g.textContent.trim().length > 0) return false;   // a label group, not a cell
  if (g.querySelector('foreignObject')) return false;
  if (!Array.from(g.children).some(c => GEO.has(c.tagName.toLowerCase()))) return false;
  // Selection grips are <g style="cursor: *-resize|crosshair|pointer"><image/></g>.
  // They qualify on every other test, and with a connector selected there were
  // more of them in the handler pane than there were real cells in the content
  // pane, so the "most cells" rule handed back three 18x18 grips and one edge and
  // lost both rectangles. A clipart shape is also an <image>, but carries
  // `cursor: move`, so keying on the grip cursors leaves it alone.
  if (g.querySelector('image') && /resize|crosshair|pointer/.test(st)) return false;
  // Degenerate boxes are page rules and alignment guides, never diagram cells.
  const r = g.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
});

// Pick the pane holding the most cells rather than the first one holding any.
// A single alignment guide appearing in an earlier pane was enough to make the
// first-match rule return one bogus 850x0 "edge" and drop the whole diagram —
// which is what took scenario_050 from step 16 onwards down.
const layers = Array.from(root.children).filter(c => c.tagName.toLowerCase() === 'g');
let best = [];
for (const layer of layers) {
  const found = cellsOf(layer);
  if (found.length > best.length) best = found;
}
return best;
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
// mxGraph writes the current zoom into the canvas root's transform. Reading it
// there is exact, and it has to be divided out of every displacement: after a
// "Fit Page" step the editor sat at ~65%, so a 150-unit nudge measured 97 screen
// pixels and every move looked like it had fallen short.
const root = document.querySelector('.geDiagramContainer svg > g');
let zoom = 1;
if (root) {
  const m = /scale\(\s*([0-9.]+)/.exec(root.getAttribute('transform') || '');
  if (m) zoom = parseFloat(m[1]) || 1;
}
return arguments[0].map((g, i) => {
  const r = g.getBoundingClientRect();
  const geo = Array.from(g.children).filter(c => GEO.has(c.tagName.toLowerCase()));
  const tags = geo.map(c => c.tagName.toLowerCase());
  // An mxGraph edge renders as several <path> elements (wide invisible hit area,
  // the visible stroke, the arrow marker); a vertex owns exactly one primitive.
  // An edge is several <path>s whose longest one is an OPEN polyline; a vertex
  // built from several paths (cylinder, document) has a closed outline as its
  // longest path. Counting paths alone classified every cylinder as a connector.
  let longest = null, longestLen = -1;
  for (const p of geo) {
    if (p.tagName.toLowerCase() !== 'path') continue;
    let L = 0;
    try { L = p.getTotalLength(); } catch (e) { continue; }
    if (L > longestLen) { longestLen = L; longest = p; }
  }
  const longestClosed = longest ? /[Zz]/.test(longest.getAttribute('d') || '') : false;
  const isEdge = tags.length > 1 && tags.every(t => t === 'path') && !longestClosed;
  // For an edge, where the line actually starts and ends. That is what says which
  // two shapes it joins, and it survives draw.io rebuilding the node.
  let p1 = null, p2 = null;
  if (isEdge) {
    let best = null, bestLen = -1;
    for (const p of geo) {
      let L = 0;
      try { L = p.getTotalLength(); } catch (e) { continue; }
      if (L > bestLen) { bestLen = L; best = p; }
    }
    if (best && bestLen > 0) {
      const m = best.getScreenCTM();
      const a = best.getPointAtLength(0), b = best.getPointAtLength(bestLen);
      if (m) {
        p1 = [Math.round(a.x*m.a + a.y*m.c + m.e), Math.round(a.x*m.b + a.y*m.d + m.f)];
        p2 = [Math.round(b.x*m.a + b.y*m.c + m.e), Math.round(b.x*m.b + b.y*m.d + m.f)];
      }
    }
  }
  return {
    p1: p1, p2: p2,
    index: i,
    kind: isEdge ? 'edge' : (tags[0] || 'unknown'),
    tags: tags.join(','),
    x: Math.round(r.x), y: Math.round(r.y),
    w: Math.round(r.width), h: Math.round(r.height),
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
    // model coordinates: scroll added back, zoom divided out
    mx: Math.round((r.x + r.width / 2 + sx) / zoom),
    my: Math.round((r.y + r.height / 2 + sy) / zoom),
    zoom: zoom
  };
});
"""

# Text draw.io has painted on the canvas, with where it sits. Used to check that a
# Fill landed, and landed on the cell it was aimed at.
#
# The box has to come from the element that actually renders the glyphs. Reading
# it off the wrapping <g> gives the whole canvas: label groups carry the canvas
# transform, so every label reported the same nonsensical position (-723, -235).
# draw.io draws labels either as an HTML <div> inside a <foreignObject>, or as a
# plain SVG <text>, so both are collected.
_LABELS_JS = r"""
const cont = document.querySelector('.geDiagramContainer');
if (!cont) return [];
const out = [];
const seen = new Set();
const add = (el) => {
  if (seen.has(el)) return;
  const t = (el.textContent || '').trim();
  if (!t) return;
  if (el.isContentEditable) return;           // the open editor is not a label yet
  // Keep the deepest element that still holds the whole string. "No element
  // children" is too strict: draw.io's innermost label div contains empty spans,
  // so that test rejected every level of the chain and reported no labels at all
  // for a shape that visibly had one.
  const nested = Array.from(el.querySelectorAll('*'))
      .some(c => (c.textContent || '').trim() === t);
  if (nested) return;
  const r = el.getBoundingClientRect();
  if (r.width === 0 && r.height === 0) return;
  seen.add(el);
  out.push({text: t, x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height),
            cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2)});
};
// mxGraph draws vertex/edge labels as HTML, positioned over the canvas, and only
// sometimes inside the SVG as a <foreignObject> or <text>. Searching the SVG
// alone missed every label on an ellipse, diamond or parallelogram — the text was
// plainly on screen while canvas_labels() reported none, which made four
// correctly-labelled shapes in scenario_050 look like failures.
cont.querySelectorAll('div, span, text').forEach(add);
return out;
"""


def _d2(p, q) -> float:
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


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
        """Resolve a connector by the two shapes it joins, not by its DOM node.

        Node handles are enough for shapes but not for edges: labelling one edge
        makes mxGraph re-render the others, and once a handle goes stale the
        nearest-position fallback picks whichever edge happens to be closest —
        which is how scenario_050's "YES" ended up on the first edge of the chart
        instead of on the decision's right-hand branch. An edge's endpoints say
        unambiguously which pair it belongs to.
        """
        entry = self.connector_to_cell.get((from_step, to_step))
        src = self.step_to_cell.get(from_step)
        dst = self.step_to_cell.get(to_step)
        if src is None or dst is None:
            return self._resolve(entry)

        _, src_info = self._resolve(src)
        _, dst_info = self._resolve(dst)
        if src_info is None or dst_info is None:
            return self._resolve(entry)

        els = cell_elements(self.driver)
        if not els:
            return None, None
        infos = cell_info(self.driver, els)

        def cost(info):
            if info["kind"] != "edge" or not info.get("p1") or not info.get("p2"):
                return None
            a, b = info["p1"], info["p2"]
            sc = (src_info["cx"], src_info["cy"])
            dc = (dst_info["cx"], dst_info["cy"])
            fwd = _d2(a, sc) + _d2(b, dc)
            rev = _d2(a, dc) + _d2(b, sc)   # draw.io may report the path reversed
            return min(fwd, rev)

        best = None
        for el, info in zip(els, infos):
            c = cost(info)
            if c is None:
                continue
            if best is None or c < best[0]:
                best = (c, el, info)
        if best is None:
            return self._resolve(entry)
        if entry is not None:
            entry["el"], entry["info"] = best[1], best[2]
        return best[1], best[2]

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
