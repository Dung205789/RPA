#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prove the oracle is not taking the executor's word for anything.

`RPA_docs/ORACLE.md` §2 states the requirement and the way to check it: make the
executor lie, and see whether the oracle still catches the error. This script
does exactly that, against the live editor.

Two sabotages are applied, both to the *execution* path only:

* every keyboard nudge sends half the presses it was asked for, so each ``Move``
  lands 75px short of the 150px the step demands — the precise defect
  `RPA_docs/DIAGNOSIS.md` L1 shows the old ruler accepting;
* every handler reports ``ok`` regardless of what happened.

A passing result is: the executor reports 100% ok, and the oracle still fails the
sabotaged steps and flags them as false passes. If the oracle agreed with the
executor here, every number the project produces would be worthless.

    python RPA_docs/checks/oracle_independence.py [--case <scenario.json>] [--port 9402]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DOCUMENTS = Path(__file__).resolve().parents[2]
RPA_DRAWIO = DOCUMENTS / "RPA_drawio"
DEFAULT_CASE = DOCUMENTS / "RPA_Datasets_new30_v2" / "easy_e06_v6_s4b0l0.json"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", default=str(DEFAULT_CASE))
    ap.add_argument("--port", type=int, default=9402)
    ap.add_argument("--out", default=str(DOCUMENTS / "result" / "_independence"))
    args = ap.parse_args(argv)

    os.chdir(RPA_DRAWIO)
    sys.path.insert(0, str(RPA_DRAWIO))
    sys.path.insert(0, str(DOCUMENTS))
    os.environ["RPA_CHROME_DEBUG_PORT"] = str(args.port)

    import drawio_ops
    import drawio_executor

    # --- sabotage 1: half the presses, and no chance to correct --------------
    # Halving alone is no longer enough to break anything: G1.1's closed loop
    # measures the shortfall and presses again, which is the point of it. So the
    # loop is also capped at a single round, reproducing exactly the pre-G1
    # defect `DIAGNOSIS.md` L1 describes — 75 units delivered against 150 asked.
    real_press = drawio_ops._press_arrow

    def half_press(driver, key, times):
        return real_press(driver, key, max(1, times // 2))

    drawio_ops._press_arrow = half_press
    drawio_ops.MOVE_MAX_ROUNDS = 1

    # --- sabotage 2: every handler claims success ---------------------------
    for name, fn in list(drawio_executor.DrawioExecutor._HANDLERS.items()):
        def liar(self, step, n, _fn=fn):
            try:
                _fn(self, step, n)
            except Exception as exc:                # noqa: BLE001 - the point is to hide it
                return "ok", {"sabotage": "swallowed %s" % type(exc).__name__}
            return "ok", {"sabotage": "forced ok"}
        drawio_executor.DrawioExecutor._HANDLERS[name] = liar

    import run_drawio_v2 as harness
    rc = harness.main(["--scenarios", args.case, "--out", args.out,
                       "--port", str(args.port)])
    if rc != 0:
        print("harness failed with %s" % rc)
        return rc

    summary = json.loads((Path(args.out) / "summary.json").read_text(encoding="utf-8"))
    n0 = summary["step_success_rate_N0"]
    n3 = summary["step_pass_rate_N3"]
    fp = summary["false_pass"]
    print("\n--- independence check ---")
    print("executor (N0) says      : %.4f of steps ok" % n0)
    print("oracle   (N3) says      : %.4f of steps pass" % n3)
    print("false passes caught     : %d" % fp)
    ok = (n0 > n3) and fp > 0
    print("VERDICT: %s" % ("INDEPENDENT — the oracle caught the lie" if ok
                           else "NOT INDEPENDENT — the oracle believed the executor"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
