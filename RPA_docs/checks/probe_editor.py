#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure how draw.io behaves, instead of assuming it.

Added 2026-09-22 for G1.2 (`RPA_docs/PLAN.md`), which says in as many words:
write a probe, run it in a real browser, and find out what decides where a
click-inserted shape lands — do not guess. `PLAN.md`'s G1 gate then requires the
answer to be written into `DIAGNOSIS.md` rather than patched around blind.

Three questions, three probes, all read from the mxGraph model:

A. **Insertion point.** Click the same palette entry ten times, moving nothing.
   Where does each shape land, and does the landing point drift? `DIAGNOSIS.md`
   L2 measured x spreading 268px across four inserts in a scenario with no
   horizontal move at all; this isolates the same effect with nothing else
   happening.

B. **Resize.** What does Ctrl+Arrow actually do to ``mxGeometry`` — which edge
   moves, by how much, and does the centre hold? `ORACLE.md` §1 rows 8–9 assume
   the centre stays put; the executor assumes one press is 10px. Both are
   claims, neither was measured.

C. **Nudge.** Is Shift+Arrow exactly 10 model units, and how many presses go
   missing in a burst? That drop rate is the thing G1.1's closed loop exists to
   absorb.

    python RPA_docs/checks/probe_editor.py --port 9403
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

DOCUMENTS = Path(__file__).resolve().parents[2]
RPA_DRAWIO = DOCUMENTS / "RPA_drawio"


def setup(port: int):
    os.chdir(RPA_DRAWIO)
    sys.path.insert(0, str(RPA_DRAWIO))
    os.environ["RPA_CHROME_DEBUG_PORT"] = str(port)
    import by_text
    import mx_oracle
    import rpa_env
    rpa_env.launch_chrome(port=port)
    if not rpa_env.wait_for_debug_port(port):
        raise RuntimeError("Chrome debugging port %d never came up" % port)
    driver = by_text.setup_chrome_driver(use_existing=True)
    mx_oracle.install(driver)
    rpa_env.open_clean_drawio(driver, rpa_env.DRAWIO_URL, log=print)
    return driver


def _palette_entry(driver, icon: str):
    import palette_matcher
    match = palette_matcher.find_icon(driver, str(RPA_DRAWIO / "shape_icons" / icon))
    if not match.get("ok"):
        raise RuntimeError("cannot find %s in the palette: %s" % (icon, match.get("reason")))
    return match["ranked"][0]["element"]


def _view(driver):
    return driver.execute_script("""
    const cont = document.querySelector('.geDiagramContainer');
    const svg = cont ? cont.querySelector('svg') : null;
    const root = svg ? svg.querySelector('g') : null;
    const tr = root ? (root.getAttribute('transform') || '') : '';
    return {scrollLeft: cont ? cont.scrollLeft : null,
            scrollTop: cont ? cont.scrollTop : null,
            transform: tr};
    """)


def probe_insert(driver, n: int = 10) -> dict:
    import drawio_ops
    import mx_oracle
    import rpa_env
    entry = _palette_entry(driver, "rectangle.png")
    origin = rpa_env.view_origin(driver)
    rows = []
    seen = set()
    for i in range(n):
        before = mx_oracle.snapshot(driver)
        drawio_ops.click_palette_entry(driver, entry, view_origin=origin)
        after = mx_oracle.snapshot(driver)
        new = [c for c in after.vertices if c.id not in {v.id for v in before.vertices}]
        v = _view(driver)
        if not new:
            rows.append({"i": i, "landed": None, "view": v})
            continue
        c = new[0]
        rows.append({"i": i, "x": c.x, "y": c.y, "w": c.w, "h": c.h, "view": v})
        seen.add(c.id)
    xs = [r["x"] for r in rows if r.get("x") is not None]
    ys = [r["y"] for r in rows if r.get("y") is not None]
    return {"rows": rows,
            "n_inserted": len(xs),
            "x_spread": (max(xs) - min(xs)) if xs else None,
            "y_spread": (max(ys) - min(ys)) if ys else None,
            "x_values": xs, "y_values": ys,
            "size": (rows[0].get("w"), rows[0].get("h")) if rows else None}


def probe_resize(driver) -> dict:
    """One shape, one Ctrl+Arrow per direction, geometry read each time."""
    import drawio_ops
    import mx_control
    import mx_oracle
    import rpa_env
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys

    rpa_env.clear_canvas(driver)
    entry = _palette_entry(driver, "rectangle.png")
    drawio_ops.click_palette_entry(driver, entry, view_origin=rpa_env.view_origin(driver))
    cells = drawio_ops.known_cells(driver)
    if not cells:
        return {"error": "nothing was inserted"}
    el = cells[-1]
    cid = mx_control.cell_id_for(driver, el)
    out = {"cell": cid, "presses": {}}
    for name, key in (("right", Keys.ARROW_RIGHT), ("left", Keys.ARROW_LEFT),
                      ("down", Keys.ARROW_DOWN), ("up", Keys.ARROW_UP)):
        drawio_ops.select_cell(driver, el)
        before = mx_control.geometry_of(driver, cid)
        for _ in range(3):
            (ActionChains(driver).key_down(Keys.CONTROL).send_keys(key)
             .key_up(Keys.CONTROL).perform())
            time.sleep(0.05)
        time.sleep(0.4)
        after = mx_control.geometry_of(driver, cid)
        if not before or not after:
            out["presses"][name] = {"error": "no geometry"}
            continue
        out["presses"][name] = {
            "per_press": {k: round((after[k] - before[k]) / 3.0, 3)
                          for k in ("x", "y", "w", "h")},
            "before": before, "after": after,
            "centre_moved": [round((after["x"] + after["w"] / 2)
                                   - (before["x"] + before["w"] / 2), 2),
                             round((after["y"] + after["h"] / 2)
                                   - (before["y"] + before["h"] / 2), 2)],
        }
    return out


def probe_nudge(driver, bursts=(1, 5, 15, 15, 15)) -> dict:
    """How far one Shift+Arrow really goes, and how many presses vanish."""
    import drawio_ops
    import mx_control
    import rpa_env
    rpa_env.clear_canvas(driver)
    entry = _palette_entry(driver, "rectangle.png")
    drawio_ops.click_palette_entry(driver, entry, view_origin=rpa_env.view_origin(driver))
    cells = drawio_ops.known_cells(driver)
    if not cells:
        return {"error": "nothing was inserted"}
    el = cells[-1]
    cid = mx_control.cell_id_for(driver, el)
    rows = []
    drawio_ops.select_cell(driver, el)
    for count in bursts:
        before = mx_control.geometry_of(driver, cid)
        drawio_ops._press_arrow(driver, drawio_ops._ARROW["down"], count)
        time.sleep(0.4)
        after = mx_control.geometry_of(driver, cid)
        moved = (after["y"] - before["y"]) if (before and after) else None
        rows.append({"presses": count, "moved": moved,
                     "per_press": round(moved / count, 3) if moved is not None else None,
                     "lost_presses": (count - moved / drawio_ops.PX_PER_ARROW_PRESS)
                     if moved is not None else None})
    return {"rows": rows}


def probe_insert_after_moves(driver, n: int = 6, reset_view: bool = True) -> dict:
    """The pattern the corpus actually uses: insert, nudge it away, insert again.

    Probe A inserts ten shapes and touches nothing else, and the landing point
    does not move at all. That is not what `DIAGNOSIS.md` L2 saw, and the
    difference is the moves in between — every scenario nudges each shape a few
    hundred units right after inserting it, which scrolls the canvas. This
    repeats the real pattern and watches the landing point, with the view reset
    before each insert or not, so the reset's contribution is separable.
    """
    import drawio_ops
    import mx_oracle
    import rpa_env
    rpa_env.clear_canvas(driver)
    entry = _palette_entry(driver, "rectangle.png")
    origin = rpa_env.view_origin(driver)
    landings = []
    for i in range(n):
        before = {c.id for c in mx_oracle.snapshot(driver).vertices}
        drawio_ops.click_palette_entry(driver, entry,
                                       view_origin=origin if reset_view else None)
        after = mx_oracle.snapshot(driver)
        new = [c for c in after.vertices if c.id not in before]
        if not new:
            landings.append({"i": i, "landed": None})
            continue
        cell = new[0]
        landings.append({"i": i, "x": cell.x, "y": cell.y, "view": _view(driver)})
        # push it out of the way, the way a scenario would
        els = drawio_ops.known_cells(driver)
        drawio_ops.move_cell_exact(driver, els[-1], "down",
                                   drawio_ops.MOVE_STEP_PX * (i + 1))
    xs = [r["x"] for r in landings if r.get("x") is not None]
    ys = [r["y"] for r in landings if r.get("y") is not None]
    return {"reset_view": reset_view, "landings": landings,
            "x_values": xs, "y_values": ys,
            "x_spread": (max(xs) - min(xs)) if xs else None,
            "y_spread": (max(ys) - min(ys)) if ys else None}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=9403)
    ap.add_argument("--inserts", type=int, default=10)
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-browser", action="store_true")
    args = ap.parse_args(argv)

    driver = setup(args.port)
    result = {}
    try:
        result["A_insert_point"] = probe_insert(driver, args.inserts)
        result["B_resize"] = probe_resize(driver)
        result["C_nudge"] = probe_nudge(driver)
        result["D_insert_after_moves_reset"] = probe_insert_after_moves(driver, reset_view=True)
        result["D_insert_after_moves_noreset"] = probe_insert_after_moves(driver, reset_view=False)
    finally:
        if not args.keep_browser:
            try:
                driver.quit()
            except Exception:
                pass
            import rpa_env
            rpa_env.kill_chrome_on_port(args.port)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    out = Path(args.out) if args.out else (DOCUMENTS / "RPA_docs" / "probe_editor.json")
    out.write_text(text, encoding="utf-8")

    a = result["A_insert_point"]
    print("\nA. insertion point over %d clicks" % a["n_inserted"])
    print("   x values : %s" % a["x_values"])
    print("   y values : %s" % a["y_values"])
    print("   spread   : x %s, y %s" % (a["x_spread"], a["y_spread"]))
    print("   inserted size: %s" % (a["size"],))
    print("\nB. Ctrl+Arrow, per press")
    for k, v in (result["B_resize"].get("presses") or {}).items():
        print("   %-6s %s  centre moved %s" % (k, v.get("per_press"), v.get("centre_moved")))
    print("\nC. Shift+Arrow bursts")
    for r in result["C_nudge"].get("rows", []):
        print("   %2d presses -> %s units (%s/press, %s lost)"
              % (r["presses"], r["moved"], r["per_press"], r["lost_presses"]))
    print("\nD. insert -> move -> insert (the corpus's own pattern)")
    for key in ("D_insert_after_moves_reset", "D_insert_after_moves_noreset"):
        d = result[key]
        print("   view reset=%-5s  x %s (spread %s)  y %s (spread %s)"
              % (d["reset_view"], d["x_values"], d["x_spread"],
                 d["y_values"], d["y_spread"]))
    print("\nwritten to %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
