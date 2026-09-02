#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The canvas gestures a draw.io flowchart scenario is made of.

Added 2026-09-03. Each function here is the *measured* way to perform one verb of
the scenario language against the live editor. They were established empirically
(scratchpad probes, 2026-09-03) rather than assumed, because the executor's
existing versions each failed for a concrete reason recorded below.

Everything is geometry- and gesture-based; nothing calls draw.io's JavaScript API
to create cells, so the runs still measure what a UI robot can do.
"""
from __future__ import annotations

import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import cell_tracker
import rpa_env

# One Shift+Arrow press moves the selection by exactly 10px at 100% zoom.
# Measured 2026-09-03: 1, 5 and 15 presses moved a shape 10, 50 and 150px.
PX_PER_ARROW_PRESS = 10

# What one "Move <direction>" step in the scenario language is worth. The original
# executor hard-coded 15 presses in one place and 12 in another, and the dataset
# converter independently assumed 100px. Defining it once, here, is what keeps the
# corpus and the executor talking about the same distance.
MOVE_STEP_PX = 150

_ARROW = {
    "left": Keys.ARROW_LEFT, "right": Keys.ARROW_RIGHT,
    "up": Keys.ARROW_UP, "top": Keys.ARROW_UP,
    "down": Keys.ARROW_DOWN, "bottom": Keys.ARROW_DOWN,
}


def _press_arrow(driver, key, times: int) -> None:
    """Send the nudges one at a time.

    Batching all of them into a single ActionChains perform() loses presses:
    15 batched Shift+ArrowDown moved a shape by well under 150px, while the same
    count sent individually lands exactly.
    """
    for _ in range(times):
        ActionChains(driver).key_down(Keys.SHIFT).send_keys(key).key_up(Keys.SHIFT).perform()
        time.sleep(0.02)


def known_cells(driver) -> list:
    """Handles of the cells on the canvas right now — the 'before' set an
    insert/connect is judged against."""
    return cell_tracker.cell_elements(driver)


def select_cell(driver, element) -> None:
    """Click a cell so keyboard nudges apply to it."""
    ActionChains(driver).move_to_element(element).click().perform()
    time.sleep(0.3)


def _info_of(driver, element):
    els = cell_tracker.cell_elements(driver)
    if not els:
        return None
    infos = cell_tracker.cell_info(driver, els)
    for el, info in zip(els, infos):
        if el == element:
            return info
    return None


def move_cell(driver, element, direction: str, distance_px: int = MOVE_STEP_PX) -> dict:
    """Nudge one cell, and report the displacement actually observed.

    Verification matters: the old executor issued the key presses and assumed they
    landed. If the click missed the shape the presses went to the canvas and the
    step silently did nothing, which is invisible in a screenshot taken at the end.

    Displacement is read in scroll-corrected coordinates, because clicking a cell
    makes Selenium scroll it into view and that pans the whole canvas.
    """
    key = _ARROW.get((direction or "").lower())
    if key is None:
        return {"ok": False, "reason": "unknown direction %r" % direction}

    before = _info_of(driver, element)
    if before is None:
        return {"ok": False, "reason": "cell not on canvas"}
    select_cell(driver, element)
    _press_arrow(driver, key, max(1, round(distance_px / PX_PER_ARROW_PRESS)))
    time.sleep(0.5)
    after = _info_of(driver, element)
    if after is None:
        return {"ok": False, "reason": "cell disappeared during move"}
    dx, dy = after["mx"] - before["mx"], after["my"] - before["my"]
    return {"ok": (abs(dx) + abs(dy)) >= distance_px // 2, "dx": dx, "dy": dy,
            "wanted": distance_px}


def label_cell(driver, element, text: str) -> dict:
    """Put text into a shape: double-click to open the inline editor, type, commit.

    The commit is what the old executor left out — it typed the label and moved
    straight on, so the editor was still open when the next click arrived and the
    text was frequently lost. Escape closes the editor keeping the text, which is
    draw.io's own behaviour. Select-all first so a re-label replaces rather than
    appends.
    """
    ActionChains(driver).move_to_element(element).double_click().perform()
    time.sleep(0.9)
    ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
    time.sleep(0.15)
    ActionChains(driver).send_keys(text).perform()
    time.sleep(0.4)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.8)
    return _label_result(driver, text)


def open_editor_on(driver, element) -> None:
    """Double-click a cell to start editing its label, leaving the editor open.

    The corpus splits labelling into two steps ("Double click on X" then
    "Fill ..."), so the two halves have to be callable separately.
    """
    ActionChains(driver).move_to_element(element).double_click().perform()
    time.sleep(0.9)


def type_into_open_editor(driver, text: str) -> dict:
    """Type into the label editor a previous step opened, then commit."""
    ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
    time.sleep(0.15)
    ActionChains(driver).send_keys(text).perform()
    time.sleep(0.4)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.8)
    return _label_result(driver, text)


def _label_result(driver, text: str) -> dict:
    labels = [l["text"] for l in cell_tracker.canvas_labels(driver)]
    want = " ".join(text.split())
    return {"ok": any(want in " ".join(l.split()) for l in labels), "labels": labels}


def _border_point(info: dict, toward: dict) -> tuple:
    """Offset from a cell's centre to the middle of the border facing ``toward``.

    Starting the drag on the border is what makes draw.io treat the gesture as
    "draw a connector" rather than "move the shape".
    """
    dx = toward["mx"] - info["mx"]
    dy = toward["my"] - info["my"]
    if abs(dy) >= abs(dx):
        return (0, info["h"] // 2 if dy > 0 else -info["h"] // 2)
    return (info["w"] // 2 if dx > 0 else -info["w"] // 2, 0)


def connect_cells(driver, src_el, dst_el) -> dict:
    """Draw a connector from one shape to another.

    Order of operations, all three of which were needed to make it work:
      1. clear the selection — a selected shape's resize handles sit on the
         perimeter and turn the drag into a resize (observed: the shape stretched
         into a tall rectangle instead of an edge appearing),
      2. hover the source so draw.io materialises its connection points,
      3. start the drag on the border facing the target, step off it, then land on
         the target's centre, which makes a floating connection to that shape.
    """
    before = known_cells(driver)
    rpa_env.deselect_all(driver)
    src_info = _info_of(driver, src_el)
    dst_info = _info_of(driver, dst_el)
    if src_info is None or dst_info is None:
        return {"ok": False, "reason": "source or target not on canvas"}

    ActionChains(driver).move_to_element(src_el).perform()
    time.sleep(0.7)
    ox, oy = _border_point(src_info, dst_info)
    lead_x = 0 if ox == 0 else (18 if ox > 0 else -18)
    lead_y = 0 if oy == 0 else (18 if oy > 0 else -18)
    (ActionChains(driver)
     .move_to_element_with_offset(src_el, ox, oy)
     .pause(0.4)
     .click_and_hold()
     .pause(0.3)
     .move_by_offset(lead_x, lead_y)
     .pause(0.3)
     .move_to_element(dst_el)
     .pause(0.7)
     .release()
     .perform())
    time.sleep(1.2)
    after = known_cells(driver)
    return {"ok": len(after) > len(before), "before": len(before), "after": len(after)}


def click_palette_entry(driver, element, view_origin=None) -> dict:
    """Insert a shape by clicking its palette icon.

    draw.io drops a click-inserted shape at the centre of the current view, so
    every shape lands on the same spot and they stack until moved — which is why
    the scenario language always follows an insert with Move steps, and why a
    converter must compute each shape's moves from that one insertion point
    rather than from the previous shape's position.

    ``view_origin`` restores the canvas scroll first. Without it the insertion
    point drifts with whatever Selenium last scrolled into view, and "the same
    spot" stops being true.
    """
    if view_origin is not None:
        rpa_env.deselect_all(driver)
        rpa_env.reset_view(driver, view_origin)
    before = known_cells(driver)
    ActionChains(driver).move_to_element(element).click().perform()
    time.sleep(1.3)
    after = known_cells(driver)
    return {"ok": len(after) > len(before), "before": len(before), "after": len(after)}
