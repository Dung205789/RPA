#!/usr/bin/env python3
"""Dựng RPA_docs/splits.json — tập chỉnh / tập giữ kín, tất định.

Chính sách đã khoá ở PLAN.md §Bất biến luật 3 và DECISIONS.md:
    sha256(case_id) -> 20% vào tập giữ kín, chia TRONG TỪNG BAND
    (easy/medium/hard) để giữ nguyên tỉ lệ band ở cả hai tập.

Áp dụng cho:
  * ../data/datasets      (benchmark ảnh, có band trong tên file)
  * RPA_Datasets/data/drawio, lucid_chart, visual_paradigm (bộ cũ, không có
    band -- coi mỗi site là một "band" của chính nó)

Chạy lại luôn ra đúng cùng một kết quả -- không có RNG, không có seed cần nhớ.

    python RPA_docs/checks/build_splits.py [--write]

Không có --write thì chỉ in ra để xem trước, không ghi đè splits.json.
"""
import argparse
import glob
import hashlib
import json
import os
import sys

# Windows console mặc định cp1252 -- ép UTF-8 để bảng tiếng Việt không vỡ.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.dirname(HERE)          # RPA_docs/
ROOT = os.path.dirname(DOCS_DIR)          # documents/
HOLDOUT_PCT = 20
HASH_VERSION = "sha256-mod100-v1"


def is_holdout(case_id: str) -> bool:
    """Tất định: sha256(id) -> số nguyên -> % 100 < HOLDOUT_PCT."""
    h = hashlib.sha256(case_id.encode("utf-8")).hexdigest()
    return (int(h[:8], 16) % 100) < HOLDOUT_PCT


def band_of_new_corpus(path: str) -> str:
    name = os.path.basename(path)
    for band in ("easy", "medium", "hard"):
        if name.startswith(band + "_"):
            return band
    return "unknown"


def collect_new_corpus(root: str) -> dict:
    """../data/datasets -- id lấy từ tên file .png, band từ tiền tố."""
    bands: dict = {}
    for png in sorted(glob.glob(os.path.join(root, "*", "*.png"))):
        case_id = os.path.splitext(os.path.basename(png))[0]
        band = band_of_new_corpus(png)
        bands.setdefault(band, []).append(case_id)
    return bands


def collect_old_corpus(root: str) -> dict:
    """RPA_Datasets/data/<site> -- không có band, coi mỗi site một band."""
    sites: dict = {}
    for site in ("drawio", "lucid_chart", "visual_paradigm"):
        site_dir = os.path.join(root, site)
        ids = sorted(
            os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(site_dir, "*.json"))
        )
        if ids:
            sites[site] = ids
    return sites


def split_bands(bands: dict) -> dict:
    out = {}
    for band, ids in bands.items():
        ids = sorted(ids)
        chỉnh = [i for i in ids if not is_holdout(i)]
        giữ_kín = [i for i in ids if is_holdout(i)]
        out[band] = {
            "n_total": len(ids),
            "n_tuning": len(chỉnh),
            "n_holdout": len(giữ_kín),
            "holdout_pct_actual": round(100 * len(giữ_kín) / len(ids), 1) if ids else 0.0,
            "tuning": chỉnh,
            "holdout": giữ_kín,
        }
    return out


def build() -> dict:
    """Cả hai corpus, đã chia. Tách khỏi main() từ 2026-09-22 để
    RPA_docs/checks/verify_splits.py dựng lại được trong bộ nhớ và so với file
    trên đĩa -- đó là cách chứng minh "tái sinh được", không phải lời hứa."""
    new_corpus_root = os.path.join(ROOT, "..", "data", "datasets")
    old_corpus_root = os.path.join(ROOT, "RPA_Datasets", "data")
    return {
        "_policy": "sha256(case_id) mod 100 < %d%% => tập giữ kín, chia trong từng band"
                   % HOLDOUT_PCT,
        "_hash_version": HASH_VERSION,
        "_holdout_pct_target": HOLDOUT_PCT,
        "_lệnh_tái_sinh": "python RPA_docs/checks/build_splits.py --write",
        "new_corpus": split_bands(collect_new_corpus(new_corpus_root)),
        "old_corpus": split_bands(collect_old_corpus(old_corpus_root)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                     help="ghi đè RPA_docs/splits.json (mặc định chỉ in ra)")
    args = ap.parse_args(argv)

    result = build()

    summary_lines = []
    for corpus_name, bands in (("new_corpus", result["new_corpus"]),
                                ("old_corpus", result["old_corpus"])):
        for band, info in bands.items():
            summary_lines.append(
                "%-12s %-16s tổng=%-4d chỉnh=%-4d giữ_kín=%-4d (%.1f%%)"
                % (corpus_name, band, info["n_total"], info["n_tuning"],
                   info["n_holdout"], info["holdout_pct_actual"])
            )
    print("\n".join(summary_lines))

    if args.write:
        out_path = os.path.join(DOCS_DIR, "splits.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print("\nghi:", out_path)
    else:
        print("\n(chỉ xem trước -- chạy lại với --write để ghi RPA_docs/splits.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
