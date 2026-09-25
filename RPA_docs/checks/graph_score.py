#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score a drawing against its answer key, deterministically.

Added 2026-09-22 for G0.2 (`RPA_docs/PLAN.md`). The judge in use until now is
``judge_drawings.py``, a VLM looking at two pictures; `RPA_docs/DECISIONS.md` D1
keeps it, and `RPA_docs/KNOWN_LIMITS.md` C1 records its cost — ±0,05–0,08
between two scorings of the *same* run. A number that moves that much cannot
settle whether a patch helped. So this runs alongside it: same drawings, no
model call, same answer every time.

What it reads
-------------
* the drawing, from ``model.xml`` — draw.io's own encoded ``mxGraphModel``, saved
  by the harness through ``mx_oracle``;
* the answer key, from ``<case>.png.graph.json``.

Answer keys are opened **here only**. Nothing on the execution path may touch
them (`RPA_docs/PLAN.md` §Bất biến 1); ``RPA_docs/checks/test_no_leakage.py``
enforces that.

How shapes are matched
----------------------
By position, and by position alone. Both point sets are put into their own
canonical frame (centroid at the origin, RMS radius 1) and paired with a
Hungarian assignment. Labels and shape types are deliberately kept out of the
matching: `ORACLE.md` §4 case 4 swaps two labels and requires shape recall not to
move, and case 5 changes one type and requires everything else not to move.
Matching on either of those would couple the metrics and both cases would fail.

The alignment is a **similarity transform without rotation** — translation and
one uniform scale. Classical Procrustes also fits a rotation, which here would
score a diagram drawn on its side as perfect; in a flowchart, up means "earlier".
See DECISIONS D10.

Denominators
------------
Always the reference's counts, never the matched counts (`ORACLE.md` §4, closing
rule). Every "found it" number is printed next to the matching "drew too much"
number, which is what stops recall being bought by drawing extra shapes.

    python RPA_docs/checks/graph_score.py <run-dir> [--refs "../data/datasets/*/{id}.png.graph.json"]
    python RPA_docs/checks/graph_score.py --case result/g0_baseline/easy_e01_v1_s5b0l0
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

DOCUMENTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DOCUMENTS / "RPA_drawio"))

import mx_oracle  # noqa: E402  (path set above)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: F401,E402  (switches this console to UTF-8)

# A pair counts as "the same shape in the same place" when it lands within this
# fraction of the reference's bounding-box diagonal after alignment.
MATCH_TOLERANCE = 0.15
# Where the layout score reaches zero, as a fraction of that diagonal.
LAYOUT_TAU = 0.25

# The corpus's type words against draw.io's style vocabulary. A statement about
# how draw.io names its own shapes; no case appears in it.
TYPE_ALIASES = {
    "rectangle": {"rectangle"},
    "rounded rectangle": {"rounded rectangle"},
    "ellipse": {"ellipse", "circle"},
    "diamond": {"rhombus", "diamond"},
    "parallelogram": {"parallelogram"},
    "trapezoid": {"trapezoid"},
    "hexagon": {"hexagon"},
    "document": {"document", "note"},
    "cylinder": {"cylinder", "cylinder3", "datastore", "cylinder2"},
}


def _norm_label(s) -> str:
    return " ".join((s or "").split()).strip().lower()


@dataclass
class Graph:
    """A diagram reduced to what can be compared: who, where, what, joined how."""
    ids: list = field(default_factory=list)
    pos: list = field(default_factory=list)      # (x, y) in any consistent frame
    types: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    edges: list = field(default_factory=list)    # (src_index, dst_index, label)

    def __len__(self):
        return len(self.ids)


def load_reference(path) -> Graph:
    """The answer key. Opened by the judge, never by the execution path."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    g = Graph()
    index = {}
    for n in d.get("nodes", []):
        index[n["id"]] = len(g.ids)
        g.ids.append(n["id"])
        g.pos.append((float(n["x"]), float(n["y"])))
        g.types.append((n.get("type") or "").strip().lower())
        g.labels.append(_norm_label(n.get("label")))
    for e in d.get("edges", []):
        a, b = index.get(e.get("from")), index.get(e.get("to"))
        if a is None or b is None:
            continue
        g.edges.append((a, b, _norm_label(e.get("label"))))
    return g


def load_drawing(path) -> Graph:
    """The drawing, straight out of draw.io's own model."""
    model = mx_oracle.parse(Path(path).read_text(encoding="utf-8"))
    g = Graph()
    index = {}
    for c in model.vertices:
        if c.cx is None or c.cy is None:
            continue
        index[c.id] = len(g.ids)
        g.ids.append(c.id)
        g.pos.append((c.cx, c.cy))
        g.types.append(c.shape_key())
        g.labels.append(_norm_label(c.value))
    for e in model.edges:
        a, b = index.get(e.source), index.get(e.target)
        if a is None or b is None:
            # A dangling edge is drawn but joins nothing; it cannot be credited,
            # and it is counted as excess below.
            g.edges.append((None, None, _norm_label(model.edge_label(e))))
            continue
        g.edges.append((a, b, _norm_label(model.edge_label(e))))
    return g


def _canonical(points: np.ndarray):
    """Centre at the origin, scale so the RMS radius is 1."""
    if len(points) == 0:
        return points, np.zeros(2), 1.0
    centre = points.mean(axis=0)
    centred = points - centre
    rms = math.sqrt((centred ** 2).sum(axis=1).mean()) or 1.0
    return centred / rms, centre, rms


def _fit_similarity(src: np.ndarray, dst: np.ndarray):
    """Translation + one uniform scale taking ``src`` onto ``dst``, least squares.

    No rotation, on purpose — see the module docstring and DECISIONS D10.
    """
    if len(src) == 0:
        return 1.0, np.zeros(2)
    sc, sm = src - src.mean(axis=0), src.mean(axis=0)
    dc, dm = dst - dst.mean(axis=0), dst.mean(axis=0)
    denom = float((sc ** 2).sum())
    scale = float((sc * dc).sum() / denom) if denom > 1e-12 else 1.0
    return scale, dm - scale * sm


def _bbox_diagonal(points: np.ndarray) -> float:
    if len(points) == 0:
        return 1.0
    span = points.max(axis=0) - points.min(axis=0)
    d = float(math.hypot(span[0], span[1]))
    return d if d > 1e-9 else 1.0


def match(ref: Graph, drawn: Graph):
    """Pair drawn shapes with reference shapes, by position only.

    Returns ``(pairs, residuals, diagonal)`` where ``pairs`` is a list of
    ``(ref_index, drawn_index)`` and ``residuals`` are distances in the
    reference's own units, one per pair.
    """
    if not len(ref) or not len(drawn):
        return [], [], _bbox_diagonal(np.array(ref.pos or [[0, 0]], dtype=float))
    R = np.array(ref.pos, dtype=float)
    D = np.array(drawn.pos, dtype=float)
    Rc, _, _ = _canonical(R)
    Dc, _, _ = _canonical(D)
    cost = np.linalg.norm(Rc[:, None, :] - Dc[None, :, :], axis=2)
    ri, di = linear_sum_assignment(cost)
    pairs = list(zip(ri.tolist(), di.tolist()))
    # Now fit the transform on the pairing and measure in the reference's frame.
    scale, shift = _fit_similarity(D[[d for _, d in pairs]], R[[r for r, _ in pairs]])
    moved = D * scale + shift
    residuals = [float(np.linalg.norm(R[r] - moved[d])) for r, d in pairs]
    return pairs, residuals, _bbox_diagonal(R)


def _types_equal(ref_type: str, drawn_type: str) -> bool:
    allowed = TYPE_ALIASES.get(ref_type)
    if allowed is None:
        return ref_type == drawn_type
    return drawn_type in allowed


def score(ref: Graph, drawn: Graph) -> dict:
    """Every metric, with the reference's counts as every denominator."""
    n_ref, n_drawn = len(ref), len(drawn)
    pairs, residuals, diag = match(ref, drawn)

    rel = [r / diag for r in residuals]
    within = [i for i, r in enumerate(rel) if r <= MATCH_TOLERANCE]

    node_count_recall = (min(n_ref, n_drawn) / n_ref) if n_ref else 0.0
    node_placed_recall = (len(within) / n_ref) if n_ref else 0.0
    node_precision = (len(pairs) / n_drawn) if n_drawn else 0.0
    node_excess = (max(0, n_drawn - n_ref) / n_ref) if n_ref else 0.0
    node_f1 = _f1(node_count_recall, node_precision)

    label_hits = sum(1 for r, d in pairs if ref.labels[r] and ref.labels[r] == drawn.labels[d])
    n_labelled = sum(1 for l in ref.labels if l)
    label_accuracy = (label_hits / n_labelled) if n_labelled else None

    type_hits = sum(1 for r, d in pairs if _types_equal(ref.types[r], drawn.types[d]))
    type_accuracy = (type_hits / n_ref) if n_ref else 0.0

    # Edges, mapped through the node pairing. Directed: a reversed edge is wrong.
    d2r = {d: r for r, d in pairs}
    ref_edges = {(a, b) for a, b, _ in ref.edges}
    drawn_mapped = []
    for a, b, lab in drawn.edges:
        if a is None or b is None:
            drawn_mapped.append((None, None, lab))
            continue
        drawn_mapped.append((d2r.get(a), d2r.get(b), lab))
    correct = set()
    for a, b, _ in drawn_mapped:
        if a is not None and b is not None and (a, b) in ref_edges:
            correct.add((a, b))
    n_ref_edges = len(ref_edges)
    edge_recall = (len(correct) / n_ref_edges) if n_ref_edges else None
    edge_precision = (len(correct) / len(drawn.edges)) if drawn.edges else 0.0
    edge_excess = (max(0, len(drawn.edges) - len(correct)) / n_ref_edges) if n_ref_edges else None
    edge_f1 = _f1(edge_recall, edge_precision) if edge_recall is not None else None

    ref_edge_label = {(a, b): lab for a, b, lab in ref.edges if lab}
    drawn_edge_label = {(a, b): lab for a, b, lab in drawn_mapped if a is not None}
    lab_hits = sum(1 for k, v in ref_edge_label.items() if drawn_edge_label.get(k) == v)
    edge_label_accuracy = (lab_hits / len(ref_edge_label)) if ref_edge_label else None

    layout = (sum(max(0.0, 1.0 - r / LAYOUT_TAU) for r in rel) / n_ref) if n_ref else 0.0

    parts = [node_f1, type_accuracy, layout]
    if label_accuracy is not None:
        parts.append(label_accuracy)
    if edge_f1 is not None:
        parts.append(edge_f1)
    overall = sum(parts) / len(parts)

    return {
        "n_ref_nodes": n_ref, "n_drawn_nodes": n_drawn,
        "n_ref_edges": n_ref_edges, "n_drawn_edges": len(drawn.edges),
        "node_count_recall": _r(node_count_recall),
        "node_placed_recall": _r(node_placed_recall),
        "node_precision": _r(node_precision),
        "node_excess": _r(node_excess),
        "node_f1": _r(node_f1),
        "shape_type_accuracy": _r(type_accuracy),
        "label_accuracy": _r(label_accuracy),
        "edge_recall": _r(edge_recall),
        "edge_precision": _r(edge_precision),
        "edge_excess": _r(edge_excess),
        "edge_f1": _r(edge_f1),
        "edge_label_accuracy": _r(edge_label_accuracy),
        "layout_score": _r(layout),
        "position_error_median": _r(_median(rel)),
        "position_error_p95": _r(_pct(rel, 95)),
        "overall": _r(overall),
    }


def _f1(recall, precision):
    if not recall or not precision:
        return 0.0
    return 2 * recall * precision / (recall + precision)


def _r(x, nd=6):
    return None if x is None else round(float(x), nd)


def _median(xs):
    if not xs:
        return None
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _pct(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    k = min(len(s) - 1, int(math.ceil(p / 100.0 * len(s))) - 1)
    return s[max(0, k)]


# ------------------------------------------------------------------ CLI glue

def find_reference(case_id: str, pattern: str | None = None):
    pattern = pattern or str(DOCUMENTS.parent / "data" / "datasets" / "*" / "{id}.png.graph.json")
    hits = glob.glob(pattern.replace("{id}", case_id))
    return hits[0] if hits else None


def score_case(case_dir: Path, ref_pattern=None) -> dict | None:
    model = case_dir / "model.xml"
    if not model.is_file():
        return None
    ref_path = find_reference(case_dir.name, ref_pattern)
    if not ref_path:
        return None
    ref = load_reference(ref_path)
    drawn = load_drawing(model)
    row = score(ref, drawn)
    row["id"] = case_dir.name
    row["reference"] = os.path.relpath(ref_path, DOCUMENTS)
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?", help="a result/ directory of finished cases")
    ap.add_argument("--case", help="score a single case directory")
    ap.add_argument("--refs", default=None,
                    help="glob for answer keys, with {id} where the case id goes")
    ap.add_argument("--json", action="store_true", help="print rows as JSON")
    args = ap.parse_args(argv)

    dirs = []
    if args.case:
        dirs = [Path(args.case)]
    elif args.run_dir:
        dirs = sorted(p for p in Path(args.run_dir).iterdir() if p.is_dir())
    else:
        ap.error("give a run directory or --case")

    rows = [r for r in (score_case(d, args.refs) for d in dirs) if r]
    if not rows:
        print("no case in that directory has both a model.xml and an answer key")
        return 1
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    print(format_table(rows))
    return 0


_COLS = [("id", 26, "s"), ("overall", 8, "f"), ("layout_score", 8, "f"),
         ("node_f1", 8, "f"), ("node_excess", 8, "f"), ("shape_type_accuracy", 8, "f"),
         ("label_accuracy", 8, "f"), ("edge_f1", 8, "f"), ("edge_excess", 8, "f"),
         ("position_error_median", 9, "f")]

_HEAD = {"overall": "overall", "layout_score": "layout", "node_f1": "nodeF1",
         "node_excess": "n_extra", "shape_type_accuracy": "type",
         "label_accuracy": "label", "edge_f1": "edgeF1", "edge_excess": "e_extra",
         "position_error_median": "pos~med"}


def format_table(rows: list) -> str:
    out = ["  ".join(("%-*s" % (w, _HEAD.get(k, k))) for k, w, _ in _COLS)]
    out.append("-" * len(out[0]))
    for r in rows:
        cells = []
        for k, w, kind in _COLS:
            v = r.get(k)
            cells.append("%-*s" % (w, v if kind == "s" else
                                   ("  -  " if v is None else "%.3f" % v)))
        out.append("  ".join(cells))
    out.append("-" * len(out[0]))
    agg = {}
    for k, w, kind in _COLS:
        if kind != "f":
            continue
        vals = [r[k] for r in rows if r.get(k) is not None]
        agg[k] = sum(vals) / len(vals) if vals else None
    cells = ["%-*s" % (_COLS[0][1], "MEAN n=%d" % len(rows))]
    for k, w, kind in _COLS[1:]:
        v = agg.get(k)
        cells.append("%-*s" % (w, "  -  " if v is None else "%.3f" % v))
    out.append("  ".join(cells))
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
