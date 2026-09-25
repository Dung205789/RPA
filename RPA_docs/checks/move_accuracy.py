#!/usr/bin/env python3
"""Đo độ chính xác của bước Move trong một hoặc nhiều lượt chạy.

Sinh ra các con số ở DIAGNOSIS.md §1. Chỉ đọc report.json của lượt chạy —
không mở answer key, không mở ảnh.

    python RPA_docs/checks/move_accuracy.py result/old100_v2 result/new30_v2
"""
import collections
import glob
import json
import os
import statistics
import sys

# Windows console mặc định cp1252 — ép UTF-8 để bảng tiếng Việt không vỡ.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass



def measure(run_dir):
    total = exact = ok_but_wrong = 0
    distances = []
    by_distance = collections.Counter()
    for path in sorted(glob.glob(os.path.join(run_dir, "*", "report.json"))):
        with open(path, encoding="utf-8") as fh:
            report = json.load(fh)
        for step in report.get("steps", []):
            if step.get("action") != "move":
                continue
            detail = step.get("detail") or {}
            if "dx" not in detail:
                continue
            moved = max(abs(detail.get("dx") or 0), abs(detail.get("dy") or 0))
            wanted = detail.get("wanted") or 150
            total += 1
            distances.append(moved)
            by_distance[moved] += 1
            if moved == wanted:
                exact += 1
            elif step.get("status") == "ok":
                ok_but_wrong += 1
    return total, exact, ok_but_wrong, distances, by_distance


def main(run_dirs):
    for run_dir in run_dirs:
        total, exact, ok_but_wrong, distances, by_distance = measure(run_dir)
        print(f"=== {run_dir} ===")
        if not total:
            print("  không có bước Move nào đo được\n")
            continue
        print(f"  số bước Move          : {total}")
        print(f"  dịch đúng khoảng cách : {exact} ({exact / total:.1%})")
        print(f"  ok nhưng sai k/c      : {ok_but_wrong} ({ok_but_wrong / total:.1%})")
        print(f"  trung vị              : {statistics.median(distances):g}px")
        print(f"  trung bình            : {statistics.mean(distances):.0f}px")
        top = ", ".join(f"{d:g}px×{n}" for d, n in by_distance.most_common(8))
        print(f"  hay gặp nhất          : {top}\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ["result/new30_v2"])
