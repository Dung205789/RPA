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


def search_shape(driver, query: str, log=print):
    """Type a name into draw.io's shape search and return the first result entry."""
    box = driver.find_element(By.CSS_SELECTOR, "#geOmniSearch")
    box.click()
    box.send_keys(Keys.CONTROL, "a")
    box.send_keys(query)
    box.send_keys(Keys.ENTER)
    deadline = time.time() + 15
    while time.time() < deadline:
        entries = driver.execute_script("""
        const sb = document.querySelector('.geSidebarContainer');
        const secs = Array.from(sb.querySelectorAll('.geSidebar'))
            .filter(s => s.offsetParent !== null && s.querySelector('a.geItem'));
        if (!secs.length) return [];
        return Array.from(secs[0].querySelectorAll('a.geItem')).slice(0, 6).map(a => {
          const r = a.getBoundingClientRect();
          return {x: r.x, y: r.y, w: r.width, h: r.height, title: a.getAttribute('title') || ''};
        });
        """)
        if entries:
            return entries
        time.sleep(0.4)
    return []


def crop_icon(driver, entry: dict) -> np.ndarray | None:
    shot = _screenshot(driver)
    css_w = driver.execute_script("return window.innerWidth;")
    scale = shot.shape[1] / float(css_w) if css_w else 1.0
    x0, y0 = int(entry["x"] * scale), int(entry["y"] * scale)
    x1, y1 = int((entry["x"] + entry["w"]) * scale), int((entry["y"] + entry["h"]) * scale)
    crop = shot[max(0, y0):y1, max(0, x0):x1]
    return crop if crop.size else None


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
    try:
        for name, query in SHAPE_QUERIES.items():
            entries = search_shape(driver, query)
            if not entries:
                print("  %-20s NO RESULT for %r" % (name, query))
                continue
            entry = entries[0]
            crop = crop_icon(driver, entry)
            if crop is None:
                print("  %-20s crop failed" % name)
                continue

            # Verify by using it: clicking the entry must put a cell on the canvas.
            rpa_env.clear_canvas(driver)
            rpa_env.reset_view(driver, origin)
            before = len(cell_tracker.cell_elements(driver))
            # Click the palette entry itself. Going through elementFromPoint at its
            # centre returned an inner <svg> for some shapes, and the click on that
            # child did nothing — ellipse, rhombus and hexagon all reported
            # "inserted=False" while their crops were perfectly good.
            el = driver.execute_script("""
            const sb = document.querySelector('.geSidebarContainer');
            const secs = Array.from(sb.querySelectorAll('.geSidebar'))
                .filter(s => s.offsetParent !== null && s.querySelector('a.geItem'));
            return secs.length ? secs[0].querySelector('a.geItem') : null;
            """)
            if el is None:
                print("  %-20s entry vanished before the click" % name)
                continue
            ActionChains(driver).move_to_element(el).click().perform()
            time.sleep(1.2)
            cells = cell_tracker.cell_info(driver)
            inserted = len(cells) > before
            kind = cells[-1]["kind"] if cells else None
            size = [cells[-1]["w"], cells[-1]["h"]] if cells else None

            path = ICON_DIR / ("%s.png" % name)
            cv2.imwrite(str(path), crop)
            manifest[name] = {"query": query, "file": path.name,
                              "inserted": inserted, "cell_kind": kind, "cell_size": size,
                              "icon_px": [crop.shape[1], crop.shape[0]]}
            print("  %-20s -> %-22s inserted=%s kind=%s size=%s"
                  % (name, path.name, inserted, kind, size))
            rpa_env.clear_canvas(driver)
            rpa_env.reset_view(driver, origin)
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
