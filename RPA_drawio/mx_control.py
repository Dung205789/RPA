#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The executor's own look at the model — for steering, not for scoring.

Added 2026-09-22 for G1.1 (`RPA_docs/PLAN.md`).

`RPA_docs/ORACLE.md` §2 draws the line this module sits on: *"Executor được
phép tự đo để biết khi nào cần bấm bù (vòng kín), nhưng con số báo cáo phải lấy
từ oracle độc lập."* A closed loop has to see what it just did, or it cannot
correct it. What it may not do is grade itself, and it does not: every verdict
comes from ``oracle_verdict``, which reads the model again through its own code
and never asks this module anything.

Kept in its own file rather than added to ``mx_oracle`` so the boundary stays
visible in the import graph: the executor imports ``mx_control``, the judge
imports ``mx_oracle``, and neither imports the other's decisions.

Why the model and not the SVG: ``cell_tracker`` recovers a model-ish coordinate
by dividing the canvas transform out of ``getBoundingClientRect``, and that is
the measurement `DIAGNOSIS.md` L1 shows reading a 150px nudge as 22, 78 or 950
depending on what draw.io had done to the canvas. ``mxGeometry`` is the number
draw.io itself acts on, so a loop closed on it converges on the number the step
asked for.
"""
from __future__ import annotations

import time

_PRELUDE = """
var g = null;
var gs = window.__RPA_GRAPHS__ || [];
for (var i = 0; i < gs.length; i++) {
  var c = gs[i].container;
  if (c && String(c.className).indexOf('geDiagramContainer') >= 0) { g = gs[i]; break; }
}
if (!g) return null;
"""

_GRAPH_READY_JS = _PRELUDE + "return true;"

# The model id of the cell an SVG node belongs to. mxGraph keeps the mapping in
# its view states, so this asks the view rather than guessing from coordinates —
# two shapes stacked at the same insertion point would make a geometric guess
# pick the wrong one, which is exactly the situation the corpus creates.
_ID_FOR_NODE_JS = _PRELUDE + """
var node = arguments[0];
var model = g.getModel();
for (var id in model.cells) {
  var cell = model.cells[id];
  var st = g.view.getState(cell);
  if (!st || !st.shape || !st.shape.node) continue;
  var n = st.shape.node;
  if (n === node || n.contains(node) || node.contains(n)) return id;
}
return null;
"""

_GEOMETRY_JS = _PRELUDE + """
var cell = g.getModel().getCell(arguments[0]);
if (!cell) return null;
var geo = cell.getGeometry();
if (!geo) return null;
return {x: geo.x, y: geo.y, w: geo.width, h: geo.height};
"""

_ALL_GEOMETRY_JS = _PRELUDE + """
var out = {};
var model = g.getModel();
for (var id in model.cells) {
  var cell = model.cells[id];
  if (!cell.vertex && !cell.edge) continue;
  var geo = cell.getGeometry();
  out[id] = geo ? {x: geo.x, y: geo.y, w: geo.width, h: geo.height,
                   vertex: !!cell.vertex} : null;
}
return out;
"""


def graph_ready(driver) -> bool:
    try:
        return bool(driver.execute_script(_GRAPH_READY_JS))
    except Exception:
        return False


_LABEL_JS = _PRELUDE + """
var model = g.getModel();
var cell = model.getCell(arguments[0]);
if (!cell) return null;
var v = cell.getValue();
if (v && v.nodeType === 1) v = v.getAttribute('label');
if (v === null || v === undefined || v === '') {
  // An edge label draw.io had to position lives on a child cell instead.
  for (var i = 0; i < model.getChildCount(cell); i++) {
    var kid = model.getChildAt(cell, i);
    var kv = kid.getValue();
    if (kv && kv.nodeType === 1) kv = kv.getAttribute('label');
    if (kv) return String(kv);
  }
}
return v === null || v === undefined ? '' : String(v);
"""


def label_of(driver, cell_id):
    """The cell's label as draw.io holds it, HTML and all. ``None`` on failure."""
    if not cell_id:
        return None
    try:
        return driver.execute_script(_LABEL_JS, cell_id)
    except Exception:
        return None


def all_geometry(driver) -> dict:
    """Every cell's geometry in one round trip, for a before/after comparison."""
    try:
        return driver.execute_script(_ALL_GEOMETRY_JS) or {}
    except Exception:
        return {}


def cell_id_for(driver, element):
    """Which model cell is this SVG node? ``None`` if the node is not a cell."""
    try:
        return driver.execute_script(_ID_FOR_NODE_JS, element)
    except Exception:
        return None


def geometry_of(driver, cell_id):
    """``{x, y, w, h}`` in model units, or ``None``."""
    if not cell_id:
        return None
    try:
        return driver.execute_script(_GEOMETRY_JS, cell_id)
    except Exception:
        return None
