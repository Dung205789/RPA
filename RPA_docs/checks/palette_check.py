#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-check the shape matcher against the pinned build's palette.

Added 2026-09-22 for the G0 environment gate line *"Kiểm lại `palette_matcher`
trên bảng shape bản ghim"*, which exists because of the risk DECISIONS D9 names:
the icon templates in ``RPA_drawio/shape_icons`` were cut from
``app.diagrams.net`` as it looked in September 2026, and the runs now drive a
pinned ``jgraph/drawio:28.2.5`` container. If jgraph redrew an icon between the
two, the matcher silently picks a different palette entry and every scenario
using that shape draws the wrong thing while reporting success.

For each icon the check clicks the entry the matcher chooses, reads what
actually appeared out of the mxGraph model, and compares the drawn style against
the style that icon's name stands for. That is end to end: it does not ask the
matcher whether it is happy, it asks draw.io what got drawn.

    python RPA_docs/checks/palette_check.py --port 9405
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=9405)
    ap.add_argument("--out", default=str(DOCUMENTS / "RPA_docs" / "palette_check.json"))
    args = ap.parse_args(argv)

    os.chdir(RPA_DRAWIO)
    sys.path.insert(0, str(RPA_DRAWIO))
    os.environ["RPA_CHROME_DEBUG_PORT"] = str(args.port)

    import by_text
    import drawio_ops
    import mx_oracle
    import oracle_verdict
    import palette_matcher
    import rpa_env

    rpa_env.launch_chrome(port=args.port)
    if not rpa_env.wait_for_debug_port(args.port):
        print("Chrome debugging port never came up")
        return 2
    driver = by_text.setup_chrome_driver(use_existing=True)
    mx_oracle.install(driver)
    rpa_env.open_clean_drawio(driver, rpa_env.DRAWIO_URL, log=print)

    icons = sorted(p for p in (RPA_DRAWIO / "shape_icons").glob("*.png")
                   if not p.name.startswith("_"))
    rows = []
    try:
        for icon in icons:
            rpa_env.clear_canvas(driver)
            key = icon.stem.lower()
            expect = oracle_verdict.ICON_STYLE.get(key)
            match = palette_matcher.find_icon(driver, str(icon))
            row = {"icon": icon.name, "expected_style": sorted(expect) if expect else None}
            if not match.get("ok"):
                row.update({"ok": False, "reason": match.get("reason")})
                rows.append(row)
                continue
            best = match["ranked"][0]
            row.update({"score": round(best["score"], 3),
                        "palette_title": best.get("title") or best.get("text")})
            before = {c.id for c in mx_oracle.snapshot(driver).vertices}
            drawio_ops.click_palette_entry(driver, best["element"],
                                           view_origin=rpa_env.view_origin(driver))
            after = mx_oracle.snapshot(driver)
            new = [c for c in after.vertices if c.id not in before]
            if not new:
                row.update({"ok": False, "drawn": None, "reason": "nothing was inserted"})
            else:
                drawn = new[0].shape_key()
                row.update({"drawn": drawn, "style": new[0].style,
                            "size": [new[0].w, new[0].h],
                            "ok": bool(expect) and drawn in expect})
            rows.append(row)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        rpa_env.kill_chrome_on_port(args.port)

    Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print("\n%-18s %6s %-24s %-22s %s" % ("icon", "score", "palette says", "draw.io drew", ""))
    print("-" * 86)
    bad = 0
    for r in rows:
        ok = r.get("ok")
        bad += int(not ok)
        print("%-18s %6s %-24s %-22s %s"
              % (r["icon"], r.get("score", "—"), (r.get("palette_title") or "—")[:24],
                 r.get("drawn") or "—", "OK" if ok else "MISMATCH"))
    print("-" * 86)
    print("%d/%d icons draw what their name says on this build." % (len(rows) - bad, len(rows)))
    print("written to %s" % args.out)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
