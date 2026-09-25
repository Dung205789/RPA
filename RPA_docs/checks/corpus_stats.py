#!/usr/bin/env python3
"""Đếm kịch bản và thao tác của từng site, đối chiếu bảng tab:thong_ke_2.

Sinh ra bảng ở DIAGNOSIS.md §7 và §8.

    python RPA_docs/checks/corpus_stats.py
"""
import sys
import glob
import json
import os

# Windows console mặc định cp1252 — ép UTF-8 để bảng tiếng Việt không vỡ.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# Số trong main.tex, bảng tab:thong_ke_2 — để đối chiếu, KHÔNG phải để khớp vào.
PAPER = {
    "drawio": ((15, 36), (89, 429)),
    "lucid_chart": ((20, 46), (80, 1010)),
    "visual_paradigm": ((24, 80), (76, 756)),
}

NEW_CORPORA = {
    "drawio": "../data/datasets",
    "visual_paradigm": "../data/datasetsVP",
    "lucid_chart": "../data/datasetsLucid",
}


def count_old(site):
    text = image = text_steps = image_steps = 0
    for path in sorted(glob.glob(os.path.join("RPA_Datasets/data", site, "*.json"))):
        with open(path, encoding="utf-8") as fh:
            case = json.load(fh)
        n = len(case.get("descriptions", []))
        if case.get("assets"):
            image += 1
            image_steps += n
        else:
            text += 1
            text_steps += n
    return (text, text_steps), (image, image_steps)


def main():
    print("=== RPA_Datasets (bộ cũ) so với main.tex tab:thong_ke_2 ===")
    print(f"{'site':<18}{'text đo':>12}{'text paper':>13}"
          f"{'ảnh đo':>12}{'ảnh paper':>13}")
    for site, (paper_text, paper_image) in PAPER.items():
        measured_text, measured_image = count_old(site)
        mark = "" if measured_text == paper_text else "  <- lệch"
        print(f"{site:<18}"
              f"{f'{measured_text[0]}/{measured_text[1]}':>12}"
              f"{f'{paper_text[0]}/{paper_text[1]}':>13}"
              f"{f'{measured_image[0]}/{measured_image[1]}':>12}"
              f"{f'{paper_image[0]}/{paper_image[1]}':>13}{mark}")

    print("\n=== Benchmark mới (ảnh) ===")
    for site, root in NEW_CORPORA.items():
        if not os.path.isdir(root):
            print(f"{site:<18} không thấy {root}")
            continue
        bands = {}
        for band in ("easy", "medium", "hard"):
            bands[band] = len(glob.glob(os.path.join(root, band, "*.png")))
        print(f"{site:<18} tổng {sum(bands.values()):>4}   " +
              "  ".join(f"{b}={n}" for b, n in bands.items()))


if __name__ == "__main__":
    main()
