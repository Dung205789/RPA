#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grep for the one shortcut that would make every number meaningless.

`PLAN.md` §Bất biến 2: no ``if case_id == ...``, no lookup table keyed by a
case's file name, no list of special shapes. The G1 gate asks for this to be
checked by grep and the result written down, so this is that grep, with the
result printed rather than remembered.

What counts as a breach:

* a scenario or case id anywhere in the execution path — ``scenario_051``,
  ``easy_e06_v6_s4b0l0``;
* a branch on a case identifier;
* a table keyed by a *case's* file name.

What does not, and why:

* ``oracle_verdict.ICON_STYLE`` maps the nine shape-icon names to the style
  strings draw.io writes for them. It is keyed by the shape vocabulary, not by a
  case, and it is a statement about how draw.io names its own shapes — exactly
  the form `KNOWN_LIMITS.md` requires a fix to take. Every scenario clicking
  those icons uses the same table.
* ``graph_score.TYPE_ALIASES`` is the same table on the judging side.
* Counting ``.png`` files in a folder to decide whether it is a shape palette
  (D12) is a rule about folders and holds for any corpus.

Those three are listed as reviewed exceptions below; anything else is a finding.

    python RPA_docs/checks/no_case_hardcoding.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCUMENTS = HERE.parents[1]
RPA_DRAWIO = DOCUMENTS / "RPA_drawio"
sys.path.insert(0, str(HERE))
import _console  # noqa: F401,E402
from test_no_leakage import EXECUTION_PATH, _prose_lines  # noqa: E402

PATTERNS = [
    ("mã kịch bản bộ cũ", re.compile(r"scenario_\d{2,}")),
    ("mã case bộ mới", re.compile(r"\b(?:easy|medium|hard)_[a-z]\d{2}_v\d")),
    ("rẽ nhánh theo id case", re.compile(r"case_id\s*[=!]=|\bsid\s*==")),
    ("tra theo tên file ảnh của corpus", re.compile(r"\bobject\d+\.png|\bhelp\.png")),
]

REVIEWED = {
    "oracle_verdict.py:ICON_STYLE": "bảng từ vựng hình của draw.io, không theo case",
    "graph_score.py:TYPE_ALIASES": "cùng bảng đó, phía chấm điểm",
    "oracle_steps.py:_is_shape_vocabulary": "luật về thư mục (D12), áp cho mọi corpus",
}


def main():
    findings = []
    for path in EXECUTION_PATH + [HERE / "graph_score.py", RPA_DRAWIO / "mx_control.py",
                                  RPA_DRAWIO / "leak_guard.py"]:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        prose = _prose_lines(text)
        for i, line in enumerate(text.splitlines(), 1):
            if i in prose:
                continue
            # Comments inside an embedded JS block are still prose, and Python's
            # tokenizer sees the whole block as one string literal. The modules
            # here explain their evidence in those comments — "which is what took
            # scenario_050 down" is a citation, not a branch.
            if line.lstrip().startswith(("//", "#", "*")):
                continue
            for label, rx in PATTERNS:
                if rx.search(line):
                    findings.append((path.name, i, label, line.strip()[:100]))

    print("Rà hard-code theo case — %d file trên đường thực thi\n" % len(EXECUTION_PATH))
    if findings:
        for name, i, label, line in findings:
            print("  PHÁT HIỆN %s:%d  [%s]\n      %s" % (name, i, label, line))
    else:
        print("  Không có nhánh nào rẽ theo id case, không có bảng tra theo tên file case.")
    print("\nNgoại lệ đã rà và chấp nhận:")
    for k, v in REVIEWED.items():
        print("  %-42s %s" % (k, v))
    print("\nLệnh tái sinh: python RPA_docs/checks/no_case_hardcoding.py")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
