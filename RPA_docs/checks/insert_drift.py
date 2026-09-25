#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""How far the insertion point wanders during a real run.

Added 2026-09-22 for the G1 gate line *"Điểm chèn trôi <5px qua 10 lần chèn liên
tiếp"*. `RPA_docs/probe_editor.py` answers the same question in a laboratory —
nothing on the canvas but the probe. This answers it in the field, over whatever
the scenarios actually do, which is where `DIAGNOSIS.md` L2 saw 268px of spread.

Two numbers per run:

* **drift before correction** — where each insert landed relative to the
  scenario's first insert. This is the defect's size, and it is visible whether
  or not the anchoring in G1.3 is switched on, because the executor records the
  drift it measured before acting on it.
* **residual after correction** — how far off the insertion point a shape was
  left once the anchoring had run. With anchoring off there is no correction and
  the two are the same number.

    python RPA_docs/checks/insert_drift.py result/g1_after
    python RPA_docs/checks/insert_drift.py result/g0_baseline result/g1_after
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCUMENTS = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DOCUMENTS / "RPA_drawio"))
import _console  # noqa: F401,E402
import stats  # noqa: E402


def drifts_of(run_dir: Path):
    """(drift, residual) magnitudes for every insert after a scenario's first."""
    before, after = [], []
    for case in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        f = case / "report.json"
        if not f.is_file():
            continue
        try:
            steps = json.loads(f.read_text(encoding="utf-8")).get("steps", [])
        except Exception:
            continue
        for s in steps:
            detail = s.get("detail") or {}
            corr = detail.get("insert_correction")
            if not isinstance(corr, dict):
                continue
            d = corr.get("drift")
            if isinstance(d, list) and len(d) == 2:
                before.append(math.hypot(d[0], d[1]))
            r = corr.get("residual")
            if isinstance(r, list) and len(r) == 2:
                after.append(math.hypot(r[0], r[1]))
            elif corr.get("corrected") is False and isinstance(d, list):
                # below the nudge grid, so nothing was done and the drift stands
                after.append(math.hypot(d[0], d[1]))
            elif isinstance(corr.get("dx"), (int, float)):
                # the pre-G1 estimator reports the correction it applied, not a
                # residual; it cannot say where the shape ended up.
                pass
    return before, after


def describe(name, values):
    if not values:
        return "  %-26s chưa có số liệu" % name
    values = sorted(values)
    med = values[len(values) // 2]
    p95 = values[max(0, min(len(values) - 1,
                            int(round(0.95 * len(values))) - 1))]
    within = sum(1 for v in values if v < 5)
    return ("  %-26s n=%-4d trung vị %6.1f  p95 %7.1f  max %7.1f  <5px: %s"
            % (name, len(values), med, p95, values[-1],
               stats.fmt_rate(within, len(values))))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+")
    args = ap.parse_args(argv)
    for rd in args.run_dirs:
        p = Path(rd)
        if not p.is_absolute():
            p = DOCUMENTS / p
        if not p.is_dir():
            print("%s: không có" % rd)
            continue
        b, a = drifts_of(p)
        print("\n%s" % p.name)
        print(describe("trôi trước khi sửa", b))
        print(describe("còn lại sau khi sửa", a))
    print("\nNgưỡng cổng G1: điểm chèn trôi <5px. Lệnh tái sinh nằm trong docstring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
