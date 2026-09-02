#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find which shape-palette entry an icon image refers to.

Added 2026-09-03, as the draw.io replacement for by_image.process_url_with_image.

The old path screenshotted the whole page and slid the template across it at five
scales, then handed the winning pixel to ``document.elementFromPoint``. On the
draw.io palette that failed on both counts (logged 2026-09-03): the primary pass
found *zero* candidates over threshold, SIFT found zero good matches, and the
scroll-and-retry fallback settled for a 0.632 correlation whose coordinates
landed in the middle of the empty canvas — so "Click on [rectangle.png]" clicked
the canvas, not a rectangle. It also cost ~10 seconds per step.

The search space is not the page: it is the ~45 palette entries, each of which is
a DOM element with a known box. So crop those boxes out of one screenshot and
compare the icon against each. Same job, same inputs, no hard-coded shape names —
the icon file still decides which entry wins.
"""
from __future__ import annotations

import base64
import io
import os
import time

import cv2
import numpy as np

_ENTRIES_JS = r"""
const out = [];
document.querySelectorAll('.geSidebarContainer a.geItem').forEach((a, i) => {
  if (a.offsetParent === null) return;
  const r = a.getBoundingClientRect();
  if (r.width < 4 || r.height < 4) return;
  out.push({i: i, x: r.x, y: r.y, w: r.width, h: r.height,
            title: a.getAttribute('title') || ''});
});
return out;
"""


# Not every bracketed image in the corpus is a shape. Checking what the old
# 100-case corpus actually references: object2.png is the toolbar's "100% v" zoom
# control, help.png is a menu item, 65.png/o61.png… are ribbon icons. Restricting
# the search to the shape palette therefore mis-resolves those steps — measured on
# scenario_050, where "Click on [object2.png]" was forced onto palette entry 32 and
# inserted a random shape instead of opening the zoom menu.
#
# So the candidate set is every small visible leaf-ish control on the page, with
# the palette entries always included. One screenshot still covers all of them.
_UI_CANDIDATES_JS = r"""
const out = [];
const seen = new Set();
const push = (el, isPalette) => {
  if (seen.has(el)) return;
  seen.add(el);
  if (el.offsetParent === null) return;
  const r = el.getBoundingClientRect();
  if (r.width < 8 || r.height < 8 || r.width > 260 || r.height > 140) return;
  if (r.x < 0 || r.y < 0) return;
  out.push({x: r.x, y: r.y, w: r.width, h: r.height,
            tag: el.tagName.toLowerCase(),
            title: el.getAttribute('title') || '',
            text: (el.textContent || '').trim().slice(0, 30),
            palette: !!isPalette, idx: out.length});
};
document.querySelectorAll('.geSidebarContainer a.geItem').forEach(e => push(e, true));
document.querySelectorAll('a, button, img, span, div, input, li, td').forEach(el => {
  // leaf-ish only: a control, not the panel that contains it
  if (el.querySelectorAll('*').length > 3) return;
  push(el, false);
});
return out;
"""


def palette_entries(driver) -> list:
    """Boxes of the visible palette entries, in sidebar order."""
    return driver.execute_script(_ENTRIES_JS) or []


def ui_candidates(driver) -> list:
    """Every small visible control on the page, palette entries first."""
    return driver.execute_script(_UI_CANDIDATES_JS) or []


def _page_screenshot(driver) -> np.ndarray:
    png = base64.b64decode(driver.get_screenshot_as_base64())
    arr = np.frombuffer(png, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _ink_mask(bgr: np.ndarray, size: int = 40) -> np.ndarray:
    """Reduce an icon to the strokes that define its outline.

    Palette icons and the corpus's template files are line art: a dark outline on
    a light ground, drawn at different sizes and line weights. Comparing raw
    pixels punishes those differences; comparing where the ink is does not.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # Otsu picks the ink/paper split per image, so a faint template and a crisp
    # palette entry still binarise the same way.
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ys, xs = np.nonzero(binary)
    if len(xs) == 0:
        return np.zeros((size, size), dtype=np.uint8)
    # Crop to the ink before resizing: the template files carry different amounts
    # of white margin than the palette cells do.
    binary = binary[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    # Letterbox rather than stretch. Squashing the ink box into a square throws
    # away the one feature that separates half the flowchart vocabulary: a wide
    # oval and a circle, or a wide rectangle and a square, become the same
    # picture. Measured before this change, rectangle.png scored an identical
    # 0.806 against the rectangle, the rounded rectangle and the square.
    h, w = binary.shape
    scale = float(size) / max(h, w)
    new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = cv2.resize(binary, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((size, size), dtype=np.uint8)
    y0 = (size - new_h) // 2
    x0 = (size - new_w) // 2
    canvas[y0:y0 + new_h, x0:x0 + new_w] = (resized > 96).astype(np.uint8)
    return canvas


def _similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Intersection-over-union of two ink masks, softened by a small dilation.

    The dilation is what lets a 1px outline and a 2px outline of the same shape
    score highly: without it two rectangles drawn at different weights barely
    overlap at all.
    """
    kernel = np.ones((3, 3), np.uint8)
    a_d = cv2.dilate(a, kernel)
    b_d = cv2.dilate(b, kernel)
    inter = np.logical_and(a_d, b_d).sum()
    union = np.logical_or(a_d, b_d).sum()
    return float(inter) / float(union) if union else 0.0


def find_palette_entry(driver, template_path: str, top_k: int = 3,
                       log=None) -> dict:
    """Best palette entry for ``template_path``.

    Returns ``{"ok", "index", "score", "element", "ranked"}``. ``ranked`` carries
    the runners-up so a caller can retry with the next best when a click does not
    produce a shape — the same fallback idea the original executor had, but over
    real candidates instead of over one rescanned screenshot.
    """
    if log is None:
        def log(*a, **k):
            pass

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return {"ok": False, "reason": "cannot read template %s" % template_path}
    t_mask = _ink_mask(template)

    entries = palette_entries(driver)
    if not entries:
        return {"ok": False, "reason": "no palette entries visible"}

    shot = _page_screenshot(driver)
    # The screenshot may be at device-pixel scale while getBoundingClientRect is
    # in CSS pixels; derive the factor instead of assuming 1.0.
    css_width = driver.execute_script("return window.innerWidth;")
    scale = shot.shape[1] / float(css_width) if css_width else 1.0

    scored = []
    for e in entries:
        x0 = int(e["x"] * scale)
        y0 = int(e["y"] * scale)
        x1 = int((e["x"] + e["w"]) * scale)
        y1 = int((e["y"] + e["h"]) * scale)
        crop = shot[max(0, y0):y1, max(0, x0):x1]
        if crop.size == 0:
            continue
        scored.append((_similarity(t_mask, _ink_mask(crop)), e))

    if not scored:
        return {"ok": False, "reason": "no usable palette crops"}

    scored.sort(key=lambda p: p[0], reverse=True)
    els = driver.find_elements("css selector", ".geSidebarContainer a.geItem")
    ranked = []
    for score, e in scored[:top_k]:
        if e["i"] < len(els):
            ranked.append({"score": round(score, 4), "index": e["i"],
                           "title": e["title"], "element": els[e["i"]]})
    log("[palette] %s -> %s" % (os.path.basename(template_path),
                                [(r["index"], r["score"]) for r in ranked]))
    if not ranked:
        return {"ok": False, "reason": "top candidates out of range"}
    best = ranked[0]
    return {"ok": True, "index": best["index"], "score": best["score"],
            "element": best["element"], "ranked": ranked}


def find_icon(driver, template_path: str, top_k: int = 4, log=None) -> dict:
    """Best-matching control anywhere on the page for ``template_path``.

    Same comparison as :func:`find_palette_entry`, over a wider candidate set, so
    one call resolves both "click this shape in the palette" and "click this
    toolbar button" without the caller having to know which kind of icon it holds.
    """
    if log is None:
        def log(*a, **k):
            pass

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return {"ok": False, "reason": "cannot read template %s" % template_path}
    t_mask = _ink_mask(template)

    cands = ui_candidates(driver)
    if not cands:
        return {"ok": False, "reason": "no candidate controls visible"}

    shot = _page_screenshot(driver)
    css_width = driver.execute_script("return window.innerWidth;")
    scale = shot.shape[1] / float(css_width) if css_width else 1.0

    scored = []
    for c in cands:
        x0, y0 = int(c["x"] * scale), int(c["y"] * scale)
        x1, y1 = int((c["x"] + c["w"]) * scale), int((c["y"] + c["h"]) * scale)
        crop = shot[max(0, y0):y1, max(0, x0):x1]
        if crop.size == 0:
            continue
        # An icon and its control should be a similar shape; a 200x20 menu strip is
        # not a 47x33 button however its ink lands.
        ar_t = template.shape[1] / float(template.shape[0])
        ar_c = c["w"] / float(c["h"]) if c["h"] else 99.0
        if max(ar_t, ar_c) / max(1e-6, min(ar_t, ar_c)) > 3.0:
            continue
        scored.append((_similarity(t_mask, _ink_mask(crop)), c))

    if not scored:
        return {"ok": False, "reason": "no usable crops"}
    scored.sort(key=lambda p: p[0], reverse=True)

    ranked = []
    for score, c in scored[:top_k]:
        el = _element_at(driver, c)
        if el is not None:
            ranked.append({"score": round(score, 4), "element": el,
                           "tag": c["tag"], "title": c["title"],
                           "text": c["text"], "palette": c["palette"],
                           "box": [round(c["x"]), round(c["y"]),
                                   round(c["w"]), round(c["h"])]})
    log("[icon] %s -> %s" % (os.path.basename(template_path),
                             [(r["score"], r["tag"], r["title"] or r["text"]) for r in ranked]))
    if not ranked:
        return {"ok": False, "reason": "candidates could not be re-acquired"}
    return {"ok": True, "score": ranked[0]["score"],
            "element": ranked[0]["element"], "ranked": ranked}


def _element_at(driver, cand: dict):
    """Re-acquire a candidate as a WebElement from its centre point.

    Matching works on a screenshot, so the winner is known by geometry; going back
    through ``elementFromPoint`` is what turns that back into something clickable.
    """
    cx = cand["x"] + cand["w"] / 2.0
    cy = cand["y"] + cand["h"] / 2.0
    return driver.execute_script(
        "return document.elementFromPoint(arguments[0], arguments[1]);", cx, cy)
