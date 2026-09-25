#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Put each drawing next to the picture it was meant to reproduce.

Added 2026-09-22 for the last line of `RPA_docs/ORACLE.md` §6 — *"Đã nhìn bằng
mắt: ≥10 case, mỗi case một dòng mô tả sai ở đâu"* — and its note that the line
is not decoration: a run can score well and still be nonsense, which is how the
previous run got through.

Looking at thirty pairs of files one at a time is how that step gets skipped, so
this pastes reference and result side by side, a few cases per sheet, with the
case id and its deterministic score written under each pair.

    python RPA_docs/checks/contact_sheet.py result/g1_after
    python RPA_docs/checks/contact_sheet.py result/g1_after --worst 10
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCUMENTS = HERE.parents[1]
sys.path.insert(0, str(HERE))
import _console  # noqa: F401,E402
import graph_score as gs  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

CELL_W, CELL_H = 460, 340
PAD = 12
LABEL_H = 34


def reference_png(case_id: str):
    hits = glob.glob(str(DOCUMENTS.parent / "data" / "datasets" / "*" / (case_id + ".png")))
    return hits[0] if hits else None


def _fit(path, box=(CELL_W, CELL_H)):
    img = Image.new("RGB", box, "white")
    if not path or not Path(path).is_file():
        ImageDraw.Draw(img).text((10, 10), "missing", fill="red")
        return img
    src = Image.open(path).convert("RGB")
    src.thumbnail(box, Image.LANCZOS)
    img.paste(src, ((box[0] - src.width) // 2, (box[1] - src.height) // 2))
    return img


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--per-sheet", type=int, default=4)
    ap.add_argument("--worst", type=int, default=None,
                    help="only the N lowest-scoring cases")
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = DOCUMENTS / run_dir
    cases = sorted(p for p in run_dir.iterdir() if p.is_dir())
    rows = []
    for case in cases:
        score = gs.score_case(case)
        rows.append((case, score))
    if args.worst:
        rows.sort(key=lambda r: (r[1] or {}).get("overall", 1.0))
        rows = rows[: args.worst]

    out_dir = run_dir / "sheets"
    out_dir.mkdir(exist_ok=True)
    made = []
    for i in range(0, len(rows), args.per_sheet):
        chunk = rows[i: i + args.per_sheet]
        w = 2 * CELL_W + 3 * PAD
        h = len(chunk) * (CELL_H + LABEL_H + PAD) + PAD
        sheet = Image.new("RGB", (w, h), "#f4f4f4")
        draw = ImageDraw.Draw(sheet)
        for j, (case, score) in enumerate(chunk):
            top = PAD + j * (CELL_H + LABEL_H + PAD)
            sheet.paste(_fit(reference_png(case.name)), (PAD, top))
            sheet.paste(_fit(case / "canvas.png"), (2 * PAD + CELL_W, top))
            s = score or {}
            line = ("%s   overall %s  layout %s  nodeF1 %s  edgeF1 %s  type %s"
                    % (case.name, _f(s.get("overall")), _f(s.get("layout_score")),
                       _f(s.get("node_f1")), _f(s.get("edge_f1")),
                       _f(s.get("shape_type_accuracy"))))
            draw.text((PAD, top + CELL_H + 8), line, fill="black")
            draw.text((PAD, top + CELL_H + 20), "trái: bản tham chiếu   phải: bản vẽ",
                      fill="#666666")
        path = out_dir / ("sheet%02d.png" % (i // args.per_sheet + 1))
        sheet.save(path)
        made.append(path)
    for p in made:
        print(p)
    print("\n%d sheet, %d case." % (len(made), len(rows)))
    return 0


def _f(v):
    return "  -  " if v is None else "%.3f" % v


if __name__ == "__main__":
    raise SystemExit(main())
