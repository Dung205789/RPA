#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the same scenarios five times and measure how much the answer moves.

Added 2026-09-22 for G1.6 (`RPA_docs/PLAN.md`), against the thresholds in
`RPA_docs/ORACLE.md` §3.2:

| what                       | threshold                     |
|----------------------------|-------------------------------|
| final graph isomorphic     | ≥95% of run pairs             |
| position spread            | p95 ≤5 units                  |
| verdict stable             | ≥98% of steps                 |

Why it is a gate at all: `RESULTS.md` §9 already hit this — ``scenario_050``
scored 34/41 and then 41/41, and the difference was a leftover Chrome competing
for the CPU. That was handled by running it again, which is the one response
that guarantees the flakiness never gets measured. This measures it.

The sample is 20 cases drawn from the **tuning** split only, seeded, spread
across the three bands. Touching the held-out split five times would spend it
(`PLAN.md` §Bất biến 3).

    python RPA_docs/checks/repeatability.py --runs 5 --cases 20 --port 9222
    python RPA_docs/checks/repeatability.py --analyse-only result/g1_repeat
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCUMENTS = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DOCUMENTS / "RPA_drawio"))
import _console  # noqa: F401,E402
import mx_oracle  # noqa: E402

SEED = 20260922


def pick_cases(n: int, scenario_dir: Path, seed: int = SEED) -> list:
    """``n`` scenarios from the tuning split, spread evenly over the bands."""
    import random
    splits = json.loads((DOCUMENTS / "RPA_docs" / "splits.json").read_text(encoding="utf-8"))
    tuning = set()
    for band, sets in (splits.get("new_corpus") or {}).items():
        if isinstance(sets, dict):
            tuning.update(sets.get("tuning", []))
    by_band = defaultdict(list)
    for p in sorted(scenario_dir.glob("*.json")):
        if p.stem not in tuning:
            continue
        for band in ("easy", "medium", "hard"):
            if p.stem.startswith(band + "_"):
                by_band[band].append(p)
                break
    out = []
    bands = sorted(by_band)
    per = max(1, n // max(1, len(bands)))
    for band in bands:
        rng = random.Random("%s:%d" % (band, seed))
        out.extend(rng.sample(by_band[band], min(per, len(by_band[band]))))
    rest = [p for band in bands for p in by_band[band] if p not in out]
    random.Random(seed).shuffle(rest)
    return sorted(out + rest[: max(0, n - len(out))])


def canonical(model_path: Path):
    """What "the same drawing" means, reduced to something comparable.

    Vertices as a sorted multiset of (shape, label); edges as a sorted multiset
    of (source label+shape, target label+shape, edge label). Identity by label
    rather than by model id, because draw.io mints a fresh random id on every
    run and no two runs would ever match otherwise.
    """
    if not model_path.is_file():
        return None
    m = mx_oracle.parse(model_path.read_text(encoding="utf-8"))
    tag = {c.id: (c.shape_key(), c.value) for c in m.vertices}
    verts = sorted(tag.values())
    edges = sorted((tag.get(e.source, ("?", "?")), tag.get(e.target, ("?", "?")),
                    m.edge_label(e)) for e in m.edges)
    return (tuple(verts), tuple(edges))


def positions(model_path: Path) -> dict:
    if not model_path.is_file():
        return {}
    m = mx_oracle.parse(model_path.read_text(encoding="utf-8"))
    out = {}
    for c in m.vertices:
        if c.cx is None:
            continue
        key = (c.shape_key(), c.value)
        out.setdefault(key, []).append((c.cx, c.cy))
    return out


def verdicts(case_dir: Path) -> dict:
    f = case_dir / "verdicts.json"
    if not f.is_file():
        return {}
    data = json.loads(f.read_text(encoding="utf-8"))
    return {v["n"]: v["verdict"] for v in data.get("steps", [])}


def analyse(root: Path, runs: list) -> dict:
    ids = sorted({d.name for r in runs for d in (root / r).iterdir() if d.is_dir()})
    iso_pairs = iso_same = 0
    deltas = []
    step_total = step_stable = 0
    per_case = {}
    for cid in ids:
        forms, poss, vs = [], [], []
        for r in runs:
            case = root / r / cid
            forms.append(canonical(case / "model.xml"))
            poss.append(positions(case / "model.xml"))
            vs.append(verdicts(case))
        pairs = same = 0
        for i in range(len(runs)):
            for j in range(i + 1, len(runs)):
                if forms[i] is None or forms[j] is None:
                    continue
                pairs += 1
                same += int(forms[i] == forms[j])
        iso_pairs += pairs
        iso_same += same

        base = poss[0]
        for other in poss[1:]:
            for key, pts in base.items():
                got = other.get(key)
                if not got or len(got) != len(pts):
                    continue
                for (x1, y1), (x2, y2) in zip(sorted(pts), sorted(got)):
                    deltas.append(math.hypot(x2 - x1, y2 - y1))

        steps = sorted({n for v in vs for n in v})
        stable = 0
        for n in steps:
            calls = [v.get(n) for v in vs if v.get(n) is not None]
            if not calls:
                continue
            step_total += 1
            top = Counter(calls).most_common(1)[0][1]
            if top == len(calls):
                stable += 1
                step_stable += 1
        per_case[cid] = {"iso_pairs": pairs, "iso_same": same,
                         "steps": len(steps), "stable_steps": stable}

    deltas.sort()
    def pct(p):
        if not deltas:
            return None
        k = max(0, min(len(deltas) - 1, int(round(p / 100.0 * len(deltas))) - 1))
        return round(deltas[k], 2)

    return {
        "runs": len(runs),
        "n_cases": len(ids),
        "isomorphic_rate": round(iso_same / iso_pairs, 4) if iso_pairs else None,
        "isomorphic_pairs": iso_pairs,
        "position_median": pct(50),
        "position_p95": pct(95),
        "position_max": round(deltas[-1], 2) if deltas else None,
        "verdict_stability": round(step_stable / step_total, 4) if step_total else None,
        "n_step_observations": step_total,
        "per_case": per_case,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--cases", type=int, default=20)
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--out", default="result/g1_repeat")
    ap.add_argument("--scenarios", default="RPA_Datasets_new30_v2")
    ap.add_argument("--analyse-only", default=None)
    args = ap.parse_args(argv)

    root = Path(args.analyse_only or args.out)
    if not root.is_absolute():
        root = DOCUMENTS / root

    if not args.analyse_only:
        scen_dir = Path(args.scenarios)
        if not scen_dir.is_absolute():
            scen_dir = DOCUMENTS / scen_dir
        cases = pick_cases(args.cases, scen_dir)
        if not cases:
            print("no tuning-split scenarios found under %s" % scen_dir)
            return 2
        print("%d case:\n  %s" % (len(cases), "\n  ".join(c.stem for c in cases)))
        root.mkdir(parents=True, exist_ok=True)
        (root / "cases.json").write_text(
            json.dumps([c.stem for c in cases], indent=2), encoding="utf-8")
        for r in range(1, args.runs + 1):
            out = root / ("run%d" % r)
            if (out / "summary.json").is_file():
                print("run %d already done, skipping" % r)
                continue
            print("\n=== lần chạy %d/%d ===" % (r, args.runs))
            for case in cases:
                subprocess.run(
                    [sys.executable, str(DOCUMENTS / "run_drawio_v2.py"),
                     "--scenarios", str(case), "--out", str(out),
                     "--port", str(args.port)],
                    cwd=str(DOCUMENTS), check=False)
            # summary.json is written per invocation; the last one wins, which is
            # fine — the analysis reads the per-case folders, not the summary.
            (out / "summary.json").write_text(
                json.dumps({"runs_of": [c.stem for c in cases]}, indent=2),
                encoding="utf-8")

    runs = sorted(d.name for d in root.iterdir() if d.is_dir() and d.name.startswith("run"))
    if len(runs) < 2:
        print("need at least two runs to compare; found %d" % len(runs))
        return 1
    result = analyse(root, runs)
    (root / "repeatability.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n-- Ổn định (ORACLE §3.2) --")
    print("  %d case x %d lần chạy" % (result["n_cases"], result["runs"]))
    print("  đồ thị cuối đẳng cấu : %s  (ngưỡng ≥0,95, trên %d cặp)"
          % (result["isomorphic_rate"], result["isomorphic_pairs"]))
    print("  vị trí p95           : %s đơn vị  (ngưỡng ≤5)" % result["position_p95"])
    print("  phán định ổn định    : %s  (ngưỡng ≥0,98, trên %d bước)"
          % (result["verdict_stability"], result["n_step_observations"]))
    ok = ((result["isomorphic_rate"] or 0) >= 0.95
          and (result["position_p95"] if result["position_p95"] is not None else 99) <= 5
          and (result["verdict_stability"] or 0) >= 0.98)
    print("\n%s" % ("ĐẠT cả ba ngưỡng." if ok else "CHƯA ĐẠT — xem bảng trên."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
