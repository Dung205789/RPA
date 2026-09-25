#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every check that does not need a browser, in one command.

Added 2026-09-22. The G0 gate is a list of conditions, and a list that takes
eight commands to evaluate gets evaluated from memory instead. This runs the
offline half and prints one line per condition.

The browser half — `probe_editor.py`, `palette_check.py`,
`oracle_independence.py`, and the runs themselves — is listed at the end with
the command for each, because those cost minutes and must not be hidden inside
something that looks quick.

    python RPA_docs/checks/run_all_checks.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCUMENTS = HERE.parents[1]
sys.path.insert(0, str(HERE))
import _console  # noqa: F401,E402

OFFLINE = [
    ("bộ chấm qua 9 ca đột biến (toàn bộ 506 answer key)",
     [sys.executable, str(HERE / "mutations.py"), "--all"]),
    ("chốt chặn leakage",
     [sys.executable, str(HERE / "test_no_leakage.py")]),
    ("splits.json tất định, tái sinh được, chia đều theo band",
     [sys.executable, str(HERE / "verify_splits.py")]),
    ("ba baseline tầm thường chạy được",
     [sys.executable, str(HERE / "baselines.py")]),
    ("không có nhánh nào rẽ theo id case",
     [sys.executable, str(HERE / "no_case_hardcoding.py")]),
]

BROWSER = [
    ("oracle độc lập với executor (ép executor nói dối)",
     "python RPA_docs/checks/oracle_independence.py --port 9402"),
    ("cơ chế điểm chèn / resize / nudge của draw.io",
     "python RPA_docs/checks/probe_editor.py --port 9403"),
    ("palette_matcher trên bảng shape của bản ghim",
     "python RPA_docs/checks/palette_check.py --port 9405"),
    ("độ lặp lại 20 case x 5 lần",
     "python RPA_docs/checks/repeatability.py --runs 5 --cases 20"),
]


def main():
    width = max(len(name) for name, _ in OFFLINE + BROWSER)
    failed = 0
    print("KIỂM TRA NGOẠI TUYẾN\n")
    for name, cmd in OFFLINE:
        # The children print Vietnamese; decoding their output with the console's
        # cp1252 default throws before the result is ever read.
        proc = subprocess.run(cmd, cwd=str(DOCUMENTS), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        ok = proc.returncode == 0
        failed += int(not ok)
        print("  %-*s  %s" % (width, name, "ĐẠT" if ok else "HỎNG"))
        if not ok:
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-6:]
            for line in tail:
                print("      %s" % line)
    print("\nKIỂM TRA CẦN TRÌNH DUYỆT — chạy tay, mỗi lệnh vài phút\n")
    for name, cmd in BROWSER:
        print("  %-*s  %s" % (width, name, cmd))
    print("\n%s" % ("Toàn bộ kiểm tra ngoại tuyến ĐẠT." if not failed
                    else "%d kiểm tra HỎNG — xem ở trên." % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
