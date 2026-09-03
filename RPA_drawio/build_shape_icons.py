#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the shape-icon templates the scenario language needs, from draw.io itself.

Added 2026-09-03.

RPA_Datasets/images/drawio ships icons for four shapes: rectangle, ellipse,
diamond, parallelogram. The image benchmark uses nine — counted over its 506
answer keys: rounded rectangle (949 nodes), diamond (856), parallelogram (555),
ellipse (494), rectangle (399), trapezoid (93), hexagon (92), document (60),
cylinder (18). Mapping the five missing types onto the four available ones, which
is what the first conversion did, throws away the single most common shape in the
corpus before a run even starts.

Rather than hand-draw icons, this asks draw.io for them: type the shape's name
into the editor's own shape search, take the first result, and crop its thumbnail
out of a screenshot. The corpus's original icons are palette crops too, so the
new ones are the same kind of artefact, produced the same way — and because the
name is resolved through the editor's search rather than a memorised palette
position, nothing here breaks when draw.io reorders its palette.

Run once:
    python build_shape_icons.py            # writes RPA_drawio/shape_icons/*.png
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import cell_tracker
import palette_matcher
import rpa_env

ICON_DIR = Path(__file__).resolve().parent / "shape_icons"

# The vocabulary the image benchmark actually uses, with the search term that
# brings each one up in draw.io's shape search.
SHAPE_QUERIES = {
    "rectangle": "rectangle",
    "rounded_rectangle": "rounded rectangle",
    "ellipse": "ellipse",
    "diamond": "rhombus",
    "parallelogram": "parallelogram",
    "hexagon": "hexagon",
    "trapezoid": "trapezoid",
    "document": "document",
    "cylinder": "cylinder",
}


def _screenshot(driver) -> np.ndarray:
    png = base64.b64decode(driver.get_screenshot_as_base64())
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)


def _result_entries(driver):
    return driver.execute_script("""
    const sb = document.querySelector('.geSidebarContainer');
    const secs = Array.from(sb.querySelectorAll('.geSidebar'))
        .filter(s => s.offsetParent !== null && s.querySelector('a.geItem'));
    if (!secs.length) return [];
    return Array.from(secs[0].querySelectorAll('a.geItem')).slice(0, 6).map(a => {
      const r = a.getBoundingClientRect();
      return {x: r.x, y: r.y, w: r.width, h: r.height, title: a.getAttribute('title') || ''};
    });
    """) or []


def search_shape(driver, query: str, log=print):
    """Type a name into draw.io's shape search and return the result entries.

    The box is cleared and the previous results are waited out first. Without
    that, the entries read back can still be the *previous* query's — which is how
    the parallelogram and hexagon icons were captured as rectangles even after the
    blank-crop bug was fixed.
    """
    box = driver.find_element(By.CSS_SELECTOR, "#geOmniSearch")
    box.click()
    box.send_keys(Keys.CONTROL, "a")
    box.send_keys(Keys.DELETE)
    box.send_keys(Keys.ENTER)
    deadline = time.time() + 6
    while time.time() < deadline and _result_entries(driver):
        time.sleep(0.3)

    box.click()
    box.send_keys(query)
    box.send_keys(Keys.ENTER)
    deadline = time.time() + 15
    while time.time() < deadline:
        entries = _result_entries(driver)
        if entries:
            time.sleep(0.8)          # let the thumbnails paint
            return _result_entries(driver)
        time.sleep(0.4)
    return []


def cell_crop(driver, entry_info: dict):
    """Crop the shape a click just put on the canvas, for comparison with the icon."""
    shot = _screenshot(driver)
    css_w = driver.execute_script("return window.innerWidth;")
    scale = shot.shape[1] / float(css_w) if css_w else 1.0
    pad = 6
    x0 = int((entry_info["x"] - pad) * scale)
    y0 = int((entry_info["y"] - pad) * scale)
    x1 = int((entry_info["x"] + entry_info["w"] + pad) * scale)
    y1 = int((entry_info["y"] + entry_info["h"] + pad) * scale)
    crop = shot[max(0, y0):y1, max(0, x0):x1]
    return crop if crop.size else None


def crop_icon(driver, entry: dict, attempts: int = 8):
    """Crop a palette entry, waiting until it has actually been drawn.

    Search results appear in the DOM before their thumbnails are painted, so a
    crop taken immediately can be a flat swatch of the panel background. That
    happened silently to hexagon.png and parallelogram.png — both files were a
    uniform #f3f3f3 — and since a blank template has no ink to compare, every
    later match against them scored 0.00 and the executor inserted whatever the
    ranking happened to put first. The crop is only accepted once it contains
    more than one grey level.
    """
    for _ in range(attempts):
        shot = _screenshot(driver)
        css_w = driver.execute_script("return window.innerWidth;")
        scale = shot.shape[1] / float(css_w) if css_w else 1.0
        x0, y0 = int(entry["x"] * scale), int(entry["y"] * scale)
        x1, y1 = int((entry["x"] + entry["w"]) * scale), int((entry["y"] + entry["h"]) * scale)
        crop = shot[max(0, y0):y1, max(0, x0):x1]
        if crop.size:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            if int(gray.max()) - int(gray.min()) > 30:
                return crop
        time.sleep(0.5)
    return None


def main(argv=None):
    port = int(os.environ.get("RPA_CHROME_DEBUG_PORT", "9226"))
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    import by_text
    rpa_env.launch_chrome(port=port)
    rpa_env.wait_for_debug_port(port)
    driver = by_text.setup_chrome_driver(use_existing=True)
    rpa_env.open_clean_drawio(driver, log=print)
    origin = rpa_env.view_origin(driver)

    manifest = {}
    taken = {}          # icon name -> ink mask, to keep the set mutually distinct
    try:
        for name, query in SHAPE_QUERIES.items():
            entries = search_shape(driver, query)
            if not entries:
                print("  %-20s NO RESULT for %r" % (name, query))
                continue

            accepted = None
            # Take the icon from the shape draw.io actually draws, not from the
            # palette thumbnail. The thumbnail is a 32px pictogram whose ink barely
            # overlaps the same shape rendered at node size, so verifying one
            # against the other kept scoring the correct entry at 0.02-0.37 and
            # accepting clipart from another library instead. The drawn shape is
            # the shape, at the size the matcher will meet it, with no label on it.
            for rank in range(min(3, len(entries))):
                rpa_env.clear_canvas(driver)
                rpa_env.reset_view(driver, origin)
                before = len(cell_tracker.cell_elements(driver))
                el = driver.execute_script("""
                const sb = document.querySelector('.geSidebarContainer');
                const secs = Array.from(sb.querySelectorAll('.geSidebar'))
                    .filter(s => s.offsetParent !== null && s.querySelector('a.geItem'));
                if (!secs.length) return null;
                return secs[0].querySelectorAll('a.geItem')[arguments[0]] || null;
                """, rank)
                if el is None:
                    continue
                ActionChains(driver).move_to_element(el).click().perform()
                time.sleep(1.3)
                if len(cell_tracker.cell_elements(driver)) <= before:
                    continue
                rpa_env.deselect_all(driver)
                time.sleep(0.5)
                cells = cell_tracker.cell_info(driver)
                if not cells:
                    continue
                drawn = cells[-1]
                # A flowchart node is roughly node-sized. This rejects the clipart
                # and mockup libraries the search also returns — a 576x512 "hexagon"
                # graphic and a 48x48 parallelogram button both look right and are
                # useless as flowchart shapes.
                if not (40 <= drawn["w"] <= 220 and 30 <= drawn["h"] <= 220):
                    print("     %-18s rank %d -> %sx%s, not a node-sized shape"
                          % (name, rank, drawn["w"], drawn["h"]))
                    continue
                crop = cell_crop(driver, drawn)
                if crop is None:
                    continue
                # Refuse an icon that is indistinguishable from one already taken.
                # draw.io's search returns the same first entry for "rectangle" and
                # for "rounded rectangle", so both files ended up being the same
                # picture — identical corner profiles, IoU 0.97 — and no matcher
                # downstream could ever tell the corpus's rounded rectangles from
                # its square ones.
                mask = palette_matcher._ink_mask(crop)
                clash = next((prev for prev, prev_mask in taken.items()
                              if palette_matcher._similarity(mask, prev_mask)[0] > 0.95), None)
                if clash:
                    print("     %-18s rank %d -> same picture as %s, trying next"
                          % (name, rank, clash))
                    continue
                accepted = (crop, drawn, rank, mask)
                break

            rpa_env.clear_canvas(driver)
            rpa_env.reset_view(driver, origin)
            if accepted is None:
                print("  %-20s no result drew a matching shape" % name)
                continue
            crop, drawn, rank, mask = accepted
            taken[name] = mask
            path = ICON_DIR / ("%s.png" % name)
            cv2.imwrite(str(path), crop)
            manifest[name] = {"query": query, "file": path.name, "result_rank": rank,
                              "cell_kind": drawn["kind"],
                              "cell_size": [drawn["w"], drawn["h"]],
                              "icon_px": [crop.shape[1], crop.shape[0]]}
            print("  %-20s -> %-22s kind=%s size=%s"
                  % (name, path.name, drawn["kind"], [drawn["w"], drawn["h"]]))
    finally:
        (ICON_DIR / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            driver.quit()
        except Exception:
            pass
        rpa_env.kill_chrome_on_port(port)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if len(manifest) == len(SHAPE_QUERIES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
