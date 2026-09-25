#!/usr/bin/env python3
"""In hình học cuối cùng của một case, cạnh danh sách bước đã yêu cầu.

Sinh ra bằng chứng ở DIAGNOSIS.md §2: đặt toạ độ thật cạnh các lệnh Move mà
kịch bản phát ra, để thấy phần lệch nào KHÔNG do kịch bản gây ra.

    python RPA_docs/checks/cells_of.py result/new30_v2/easy_e06_v6_s4b0l0
"""
import json
import os
import sys

# Windows console mặc định cp1252 — ép UTF-8 để bảng tiếng Việt không vỡ.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass



def main(case_dir):
    with open(os.path.join(case_dir, "report.json"), encoding="utf-8") as fh:
        report = json.load(fh)

    moves = {"up": 0, "down": 0, "left": 0, "right": 0}
    for step in report.get("steps", []):
        if step.get("action") != "move":
            continue
        detail = step.get("detail") or {}
        dx, dy = detail.get("dx") or 0, detail.get("dy") or 0
        if abs(dx) > abs(dy):
            moves["right" if dx > 0 else "left"] += 1
        elif dy:
            moves["down" if dy > 0 else "up"] += 1

    print(f"=== {case_dir} ===")
    print("lệnh Move theo hướng :", {k: v for k, v in moves.items() if v})
    horizontal = moves["left"] + moves["right"]
    print(f"số lệnh dịch ngang   : {horizontal}")
    print()
    print("hình học cuối cùng:")
    header = f"  {'kind':<10} {'x':>6} {'y':>6} {'w':>5} {'h':>5}"
    print(header)
    xs = []
    for cell in report.get("cells", []):
        xs.append(cell.get("x"))
        print(f"  {str(cell.get('kind')):<10} {cell.get('x'):>6} {cell.get('y'):>6}"
              f" {cell.get('w'):>5} {cell.get('h'):>5}")
    if horizontal == 0 and len(set(xs)) > 1:
        spread = max(xs) - min(xs)
        print(f"\n  ⚠ kịch bản không có lệnh dịch ngang nào, nhưng x trải {spread}px"
              f"\n    → điểm chèn trôi (DIAGNOSIS.md L2)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
