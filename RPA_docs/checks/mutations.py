#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the scorer, not the robot.

Added 2026-09-22 for G0.3 (`RPA_docs/PLAN.md`). The nine cases are
`RPA_docs/ORACLE.md` §4 verbatim: take a drawing that is known to be right, put
one known defect into it, and check the score moves in the right direction by
the right amount. A scorer that has never been tested this way can be wrong in
either direction and no run made with it means anything — which is the whole
reason `CLAUDE.md` of the parent repo carries "test the evaluator" as a rule.

Case 9 is the one that matters most: drawing *extra* shapes must not raise the
"found it" score. That is the cheapest way to fake recall, and a scorer that
falls for it rewards a broken robot for making a mess.

Run over every answer key in the benchmark, or a sample of them:

    python RPA_docs/checks/mutations.py               # 24 keys, 3 per band, seeded
    python RPA_docs/checks/mutations.py --all         # every key on disk
    python RPA_docs/checks/mutations.py --case easy_e01_v1_s5b0l0
"""
from __future__ import annotations

import argparse
import copy
import glob
import hashlib
import json
import random
import sys
from pathlib import Path

DOCUMENTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _console  # noqa: F401,E402  (switches this console to UTF-8)
import graph_score as gs  # noqa: E402

# The scorer rounds its output for legibility; compare below that, not at it.
TOL = 1e-5
# A "does not move" assertion has to allow the alignment to shift a hair when the
# point set changes; a tenth of a percent is far below any effect worth seeing.
DRIFT = 1e-3


def perfect_copy(ref: gs.Graph) -> gs.Graph:
    """The drawing you get if the robot were flawless."""
    g = gs.Graph()
    g.ids = ["d%d" % i for i in range(len(ref))]
    g.pos = list(ref.pos)
    g.types = [_draw_type(t) for t in ref.types]
    g.labels = list(ref.labels)
    g.edges = list(ref.edges)
    return g


def _draw_type(ref_type: str) -> str:
    """The style key draw.io would carry for a reference type word."""
    allowed = gs.TYPE_ALIASES.get(ref_type)
    if not allowed:
        return ref_type
    # deterministic pick: the alias that reads like draw.io's own name
    return sorted(allowed)[0]


# ------------------------------------------------------------------ mutations

def m1_identical(ref, rng):
    return perfect_copy(ref)


def m2_blank(ref, rng):
    return gs.Graph()


def m3_drop_edge(ref, rng):
    """Remove one edge *of the reference's n distinct edges*.

    Distinct matters: a key with the same pair listed twice would keep scoring
    that pair when only one copy is dropped, and the case would look broken when
    the scorer is right.
    """
    g = perfect_copy(ref)
    pairs = sorted({(a, b) for a, b, _ in g.edges})
    if not pairs:
        return None
    victim = pairs[rng.randrange(len(pairs))]
    g.edges = [e for e in g.edges if (e[0], e[1]) != victim]
    return g


def m4_swap_labels(ref, rng):
    g = perfect_copy(ref)
    idx = [i for i, l in enumerate(g.labels) if l]
    if len(idx) < 2:
        return None
    a, b = rng.sample(idx, 2)
    g.labels[a], g.labels[b] = g.labels[b], g.labels[a]
    return g


def m5_change_type(ref, rng):
    g = perfect_copy(ref)
    if not g.types:
        return None
    i = rng.randrange(len(g.types))
    others = [t for t in ("rectangle", "ellipse", "rhombus", "hexagon")
              if t != g.types[i]]
    g.types[i] = others[0]
    return g


def _shift(ref, rng, px):
    g = perfect_copy(ref)
    if not g.pos:
        return None
    # The keys are normalised to the image, so a pixel budget has to be turned
    # into the same units: the benchmark's PNGs are ~1060 units across (the
    # scenario files' own px_per_normalised_unit), which is what this divides by.
    i = rng.randrange(len(g.pos))
    x, y = g.pos[i]
    g.pos[i] = (x + px / 1062.5, y)
    return g


def m6_nudge_20px(ref, rng):
    return _shift(ref, rng, 20)


def m7_shove_300px(ref, rng):
    return _shift(ref, rng, 300)


def m8_reverse_edge(ref, rng):
    g = perfect_copy(ref)
    pool = [i for i, (a, b, _) in enumerate(g.edges) if a != b]
    if not pool:
        return None
    i = rng.choice(pool)
    a, b, lab = g.edges[i]
    g.edges[i] = (b, a, lab)
    return g


def m9_extra_node(ref, rng):
    g = perfect_copy(ref)
    if not g.pos:
        return None
    xs = [p[0] for p in g.pos]
    ys = [p[1] for p in g.pos]
    g.ids.append("extra")
    g.pos.append((max(xs) + 0.2, max(ys) + 0.2))
    g.types.append("rectangle")
    g.labels.append("")
    return g


MUTATIONS = [
    ("1 identical", m1_identical),
    ("2 blank canvas", m2_blank),
    ("3 drop one edge", m3_drop_edge),
    ("4 swap two labels", m4_swap_labels),
    ("5 change one type", m5_change_type),
    ("6 nudge a node 20px", m6_nudge_20px),
    ("7 shove a node 300px", m7_shove_300px),
    ("8 reverse one edge", m8_reverse_edge),
    ("9 add a spare node", m9_extra_node),
]


# ------------------------------------------------------------------- checking

def check(name, ref, base, mutated, scored) -> list:
    """Return a list of failure strings; empty means the case passed."""
    bad = []
    n = len(ref)
    ne = len({(a, b) for a, b, _ in ref.edges})

    def near(got, want, tol=TOL, what=""):
        if got is None:
            bad.append("%s is None" % what)
        elif abs(got - want) > tol:
            bad.append("%s = %.4f, expected %.4f" % (what, got, want))

    def unchanged(key, tol=DRIFT):
        a, b = base.get(key), scored.get(key)
        if a is None and b is None:
            return
        if a is None or b is None or abs(a - b) > tol:
            bad.append("%s moved %s -> %s" % (key, a, b))

    if name.startswith("1"):
        for k in ("node_f1", "shape_type_accuracy", "label_accuracy",
                  "edge_f1", "layout_score", "overall"):
            if scored.get(k) is not None:
                near(scored[k], 1.0, TOL, k)
    elif name.startswith("2"):
        for k in ("node_count_recall", "node_f1", "shape_type_accuracy",
                  "label_accuracy", "edge_recall", "layout_score", "overall"):
            if scored.get(k) is not None:
                near(scored[k], 0.0, 1e-9, k)
    elif name.startswith("3"):
        near(scored["edge_recall"], (ne - 1) / ne, TOL, "edge_recall")
        unchanged("node_f1")
        unchanged("shape_type_accuracy")
        unchanged("label_accuracy")
    elif name.startswith("4"):
        if base["label_accuracy"] is None:
            return bad
        if not scored["label_accuracy"] < base["label_accuracy"] - 1e-9:
            bad.append("label_accuracy did not drop (%s -> %s)"
                       % (base["label_accuracy"], scored["label_accuracy"]))
        unchanged("node_f1")
        unchanged("shape_type_accuracy")
    elif name.startswith("5"):
        near(scored["shape_type_accuracy"], base["shape_type_accuracy"] - 1.0 / n,
             TOL, "shape_type_accuracy")
        unchanged("node_f1")
        unchanged("label_accuracy")
        unchanged("edge_f1")
        unchanged("layout_score")
    elif name.startswith("6"):
        if not scored["layout_score"] < base["layout_score"] - 1e-9:
            bad.append("layout_score did not drop")
        unchanged("shape_type_accuracy")
        unchanged("label_accuracy")
        unchanged("node_count_recall")
    elif name.startswith("7"):
        if not scored["layout_score"] < base["layout_score"] - 1e-9:
            bad.append("layout_score did not drop")
    elif name.startswith("8"):
        if ne:
            if not scored["edge_recall"] < base["edge_recall"] - 1e-9:
                bad.append("edge_recall did not drop for a reversed edge")
    elif name.startswith("9"):
        if scored["node_count_recall"] > base["node_count_recall"] + 1e-9:
            bad.append("a spare node RAISED node_count_recall")
        if scored["node_placed_recall"] > base["node_placed_recall"] + 1e-9:
            bad.append("a spare node RAISED node_placed_recall")
        if not scored["node_precision"] < base["node_precision"] - 1e-9:
            bad.append("node_precision did not drop")
        near(scored["node_excess"], 1.0 / n, TOL, "node_excess")
    return bad


def keys_for(sample: int, seed: int, only: str | None, all_keys: bool):
    paths = sorted(glob.glob(str(DOCUMENTS.parent / "data" / "datasets" / "*"
                                 / "*.png.graph.json")))
    if only:
        return [p for p in paths if Path(p).name.startswith(only + ".")]
    if all_keys:
        return paths
    by_band = {}
    for p in paths:
        by_band.setdefault(Path(p).parent.name, []).append(p)
    out = []
    for band in sorted(by_band):
        rng = random.Random("%s:%d" % (band, seed))
        pool = sorted(by_band[band])
        out.extend(rng.sample(pool, min(sample, len(pool))))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", type=int, default=8, help="answer keys per band")
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--case", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    paths = keys_for(args.sample, args.seed, args.case, args.all)
    if not paths:
        print("no answer keys found")
        return 2

    totals = {name: {"ran": 0, "skipped": 0, "failed": 0} for name, _ in MUTATIONS}
    failures = []
    for path in paths:
        ref = gs.load_reference(path)
        if not len(ref):
            continue
        base = gs.score(ref, perfect_copy(ref))
        rng = random.Random(int(hashlib.sha256(Path(path).name.encode()).hexdigest()[:8], 16))
        for name, fn in MUTATIONS:
            mutated = fn(ref, rng)
            if mutated is None:
                totals[name]["skipped"] += 1
                continue
            scored = gs.score(ref, mutated)
            totals[name]["ran"] += 1
            bad = check(name, ref, base, mutated, scored)
            if bad:
                totals[name]["failed"] += 1
                failures.append((Path(path).stem, name, bad))

    width = max(len(n) for n, _ in MUTATIONS)
    print("mutation tests over %d answer keys\n" % len(paths))
    print("%-*s  %6s  %8s  %7s" % (width, "case", "ran", "skipped", "FAILED"))
    print("-" * (width + 27))
    all_ok = True
    for name, _ in MUTATIONS:
        t = totals[name]
        all_ok &= (t["failed"] == 0 and t["ran"] > 0)
        print("%-*s  %6d  %8d  %7d" % (width, name, t["ran"], t["skipped"], t["failed"]))
    print("-" * (width + 27))
    if failures and args.verbose:
        for case, name, bad in failures[:40]:
            print("  %s / %s: %s" % (case, name, "; ".join(bad)))
    print("\n%s" % ("ALL NINE CASES PASS" if all_ok else
                    "SCORER FAILED %d checks — do not use it until fixed" % len(failures)))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
