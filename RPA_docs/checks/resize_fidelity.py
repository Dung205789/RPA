#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Can the executor put a shape at a size it was asked for?

Added 2026-09-22 for the G1 gate line *"Kích thước hình đạt tỉ lệ khung mục tiêu
trong ±10%"*.

That line cannot be tested from a corpus run, and the reason is worth stating
rather than working around: the scenarios in `RPA_Datasets_new30_v2` contain no
``Extend`` or ``Shrink`` step at all (counted 2026-09-22: 0 of 1617). Teaching
the converter to emit them is G2.1/G2.2, and G1 says in as many words not to
touch ``image_to_scenario.py`` yet. So what G1 can honestly claim is the
*capability*: when a size is demanded, the executor delivers it.

This drives the executor's own resize primitive against a set of target aspect
ratios taken from the benchmark's real shapes, and checks the achieved box
against the target. Nothing about any particular case enters: the targets are
ratios, applied to whatever draw.io's default insert size happens to be.

    python RPA_docs/checks/resize_fidelity.py --port 9406
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DOCUMENTS = Path(__file__).resolve().parents[2]
RPA_DRAWIO = DOCUMENTS / "RPA_drawio"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _console  # noqa: F401,E402

# Box shapes a flowchart actually needs: a wide process box, a near-square
# decision, a tall container, and the editor's own default as a control.
TARGETS = [(410, 110), (160, 160), (120, 240), (120, 60)]
TOLERANCE = 0.10


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=9406)
    ap.add_argument("--out", default=str(DOCUMENTS / "RPA_docs" / "resize_fidelity.json"))
    args = ap.parse_args(argv)

    os.chdir(RPA_DRAWIO)
    sys.path.insert(0, str(RPA_DRAWIO))
    os.environ["RPA_CHROME_DEBUG_PORT"] = str(args.port)

    import by_text
    import drawio_ops
    import mx_control
    import mx_oracle
    import palette_matcher
    import rpa_env

    rpa_env.launch_chrome(port=args.port)
    if not rpa_env.wait_for_debug_port(args.port):
        print("Chrome debugging port never came up")
        return 2
    driver = by_text.setup_chrome_driver(use_existing=True)
    mx_oracle.install(driver)
    rpa_env.open_clean_drawio(driver, rpa_env.DRAWIO_URL, log=print)

    rows = []
    try:
        icon = str(RPA_DRAWIO / "shape_icons" / "rectangle.png")
        for want_w, want_h in TARGETS:
            rpa_env.clear_canvas(driver)
            match = palette_matcher.find_icon(driver, icon)
            if not match.get("ok"):
                rows.append({"target": [want_w, want_h], "error": match.get("reason")})
                continue
            drawio_ops.click_palette_entry(driver, match["ranked"][0]["element"],
                                           view_origin=rpa_env.view_origin(driver))
            el = drawio_ops.known_cells(driver)[-1]
            cid = mx_control.cell_id_for(driver, el)
            start = mx_control.geometry_of(driver, cid)
            steps = []
            for edge, dim, want in (("right", "w", want_w), ("bottom", "h", want_h)):
                delta = int(round(want - start[dim]))
                if abs(delta) < drawio_ops.PX_PER_RESIZE_PRESS:
                    continue
                steps.append(drawio_ops.resize_cell_exact(driver, el, edge, delta,
                                                          cell_id=cid, log=print))
            end = mx_control.geometry_of(driver, cid)
            got_ratio = end["w"] / end["h"] if end["h"] else None
            want_ratio = want_w / want_h
            rows.append({
                "target": [want_w, want_h],
                "achieved": [end["w"], end["h"]],
                "target_ratio": round(want_ratio, 4),
                "achieved_ratio": round(got_ratio, 4) if got_ratio else None,
                "ratio_error": round(abs(got_ratio - want_ratio) / want_ratio, 4)
                if got_ratio else None,
                "size_error": [round(abs(end["w"] - want_w) / want_w, 4),
                               round(abs(end["h"] - want_h) / want_h, 4)],
                "opposite_edge_held": all(s.get("opposite_edge_held") for s in steps)
                if steps else True,
                "rounds": [len(s.get("rounds") or []) for s in steps],
            })
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        rpa_env.kill_chrome_on_port(args.port)

    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print("\n%-14s %-14s %-12s %-12s %-10s %s"
          % ("mục tiêu", "đạt được", "tỉ lệ đích", "tỉ lệ đạt", "sai số", "cạnh đối giữ"))
    print("-" * 82)
    bad = 0
    for r in rows:
        if "error" in r:
            print("%-14s %s" % (r["target"], r["error"]))
            bad += 1
            continue
        ok = (r["ratio_error"] is not None and r["ratio_error"] <= TOLERANCE
              and r["opposite_edge_held"])
        bad += int(not ok)
        print("%-14s %-14s %-12s %-12s %-10s %s"
              % (r["target"], r["achieved"], r["target_ratio"], r["achieved_ratio"],
                 "%.1f%%" % (100 * r["ratio_error"]), r["opposite_edge_held"]))
    print("-" * 82)
    print("%d/%d mục tiêu đạt trong ±%d%% tỉ lệ khung." % (len(rows) - bad, len(rows),
                                                           int(100 * TOLERANCE)))
    print("written to %s" % args.out)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
