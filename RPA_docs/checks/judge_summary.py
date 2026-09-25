#!/usr/bin/env python3
"""In bảng điểm mức hình của một hay nhiều lượt chạy đã chấm.

Sinh ra bảng ở DIAGNOSIS.md §6.

    python RPA_docs/checks/judge_summary.py result/old100_v2 result/new30_v2
"""
import json
import os
import sys

# Windows console mặc định cp1252 — ép UTF-8 để bảng tiếng Việt không vỡ.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


FIELDS = [
    ("mean_overall", "Điểm tổng"),
    ("mean_layout_similarity", "Giống bố cục"),
    ("shape_recall", "Tìm đúng hình"),
    ("shape_type_accuracy", "Đúng loại hình"),
    ("label_accuracy", "Đúng nhãn"),
    ("arrow_recall", "Tìm đúng cạnh"),
    ("arrow_label_accuracy", "Đúng nhãn cạnh"),
]


def main(run_dirs):
    loaded = []
    for run_dir in run_dirs:
        path = os.path.join(run_dir, "judge.json")
        if not os.path.exists(path):
            print(f"{run_dir}: chưa chấm (không có judge.json)")
            continue
        with open(path, encoding="utf-8") as fh:
            loaded.append((os.path.basename(run_dir), json.load(fh)))
    if not loaded:
        return

    width = max(len(label) for _, label in FIELDS) + 2
    print(" " * width + "".join(f"{name:>18}" for name, _ in loaded))
    for key, label in FIELDS:
        row = "".join(
            f"{(f'{data[key]:.4f}' if data.get(key) is not None else '-'):>18}"
            for _, data in loaded
        )
        print(f"{label:<{width}}{row}")
    print()
    for name, data in loaded:
        print(f"{name}: n_cases={data.get('n_cases')} n_judged={data.get('n_judged')}"
              f" totals={data.get('totals')}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["result/old100_v2", "result/new30_v2"])
