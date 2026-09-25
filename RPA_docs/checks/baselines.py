#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The three trivial baselines, so a score has a floor to stand on.

Added 2026-09-22 for G0.3c (`RPA_docs/PLAN.md`), from `RPA_docs/ORACLE.md` §5.

Without these, "overall 0,64" says nothing: it could be a competent robot on a
hard corpus or a useless one on an easy corpus. Each baseline isolates one
source of free points.

| baseline            | what it draws                                     | what it exposes |
|---------------------|---------------------------------------------------|-----------------|
| blank canvas        | nothing at all                                     | whether the scorer hands out points for turning up |
| all rectangles      | every node, in the right place, all rectangles, no labels, no edges | how much of the score is layout alone |
| nodes without edges | every node, right place, right type, right label, no edges | how much of the score is the edges |

They are built from each answer key rather than driven through the editor. The
question these answer is what the *scorer* gives away, and the editor cannot
make a blank canvas any blanker. The robot's own numbers come from a real run
and are printed above these three in the report.

    python RPA_docs/checks/baselines.py                 # whole benchmark
    python RPA_docs/checks/baselines.py --band easy
    python RPA_docs/checks/baselines.py --run result/g0_baseline   # add the real run
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

DOCUMENTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _console  # noqa: F401,E402  (switches this console to UTF-8)
import graph_score as gs  # noqa: E402


def b_blank(ref: gs.Graph) -> gs.Graph:
    return gs.Graph()


def b_all_rectangles(ref: gs.Graph) -> gs.Graph:
    g = gs.Graph()
    g.ids = ["r%d" % i for i in range(len(ref))]
    g.pos = list(ref.pos)
    g.types = ["rectangle"] * len(ref)
    g.labels = [""] * len(ref)
    g.edges = []
    return g


def b_nodes_no_edges(ref: gs.Graph) -> gs.Graph:
    g = gs.Graph()
    g.ids = ["n%d" % i for i in range(len(ref))]
    g.pos = list(ref.pos)
    g.types = [sorted(gs.TYPE_ALIASES.get(t, {t}))[0] for t in ref.types]
    g.labels = list(ref.labels)
    g.edges = []
    return g


BASELINES = [
    ("canvas trắng", b_blank),
    ("toàn chữ nhật", b_all_rectangles),
    ("node không cạnh", b_nodes_no_edges),
]

REPORT_KEYS = ["overall", "layout_score", "node_f1", "node_excess",
               "shape_type_accuracy", "label_accuracy", "edge_f1", "edge_excess"]


def keys_for(band: str | None):
    pattern = str(DOCUMENTS.parent / "data" / "datasets" / (band or "*") / "*.png.graph.json")
    return sorted(glob.glob(pattern))


def mean_scores(paths, build) -> dict:
    rows = []
    for p in paths:
        ref = gs.load_reference(p)
        if not len(ref):
            continue
        rows.append(gs.score(ref, build(ref)))
    out = {"n": len(rows)}
    for k in REPORT_KEYS:
        vals = [r[k] for r in rows if r.get(k) is not None]
        out[k] = round(sum(vals) / len(vals), 4) if vals else None
    return out


def run_scores(run_dir: Path) -> dict | None:
    rows = [r for r in (gs.score_case(d) for d in sorted(run_dir.iterdir()) if d.is_dir()) if r]
    if not rows:
        return None
    out = {"n": len(rows)}
    for k in REPORT_KEYS:
        vals = [r[k] for r in rows if r.get(k) is not None]
        out[k] = round(sum(vals) / len(vals), 4) if vals else None
    return out


def format_rows(rows: list) -> str:
    head = "%-22s %5s  " % ("", "n") + "  ".join("%-9s" % k[:9] for k in REPORT_KEYS)
    out = [head, "-" * len(head)]
    for name, r in rows:
        cells = []
        for k in REPORT_KEYS:
            v = r.get(k)
            cells.append("%-9s" % ("   -   " if v is None else "%.4f" % v))
        out.append("%-22s %5d  " % (name, r["n"]) + "  ".join(cells))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--band", default=None, choices=["easy", "medium", "hard"])
    ap.add_argument("--run", default=None, help="a finished run to print above the floor")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    paths = keys_for(args.band)
    if not paths:
        print("no answer keys found")
        return 2

    rows = []
    if args.run:
        run_dir = Path(args.run)
        if not run_dir.is_absolute():
            run_dir = DOCUMENTS / run_dir
        real = run_scores(run_dir)
        if real:
            # The floor must be computed over the same cases the run covered,
            # or the comparison is between different corpora.
            ids = {d.name for d in run_dir.iterdir() if d.is_dir()}
            paths = [p for p in paths if Path(p).name.split(".png")[0] in ids]
            rows.append(("LƯỢT CHẠY %s" % run_dir.name, real))

    for name, build in BASELINES:
        rows.append(("  sàn: " + name, mean_scores(paths, build)))

    if args.json:
        print(json.dumps({n: r for n, r in rows}, ensure_ascii=False, indent=2))
        return 0
    print("Sàn điểm — %s, n=%d answer keys\n" % (args.band or "toàn benchmark", len(paths)))
    print(format_rows(rows))
    print("\nĐọc: mọi cột đều lấy mẫu số là số đếm của bản tham chiếu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
