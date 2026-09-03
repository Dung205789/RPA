#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Browser environment setup for the draw.io RPA runs.

Added 2026-09-03. This file contains NO task logic — it only makes the browser a
sane place for the existing executor to work in. It exists because three
environment defects, none of them in the RPA algorithms, were destroying every
run:

1. **Chrome reported the page as hidden.** Windows Chrome has native window
   occlusion tracking: a window fully covered by other windows is treated like a
   background tab (``document.visibilityState === 'hidden'``). draw.io builds its
   shape palette lazily and never does that work while hidden, so ``a.geItem``
   stayed at 6 instead of ~45 — the shape icons the image matcher is supposed to
   find were literally not drawn. Measured 2026-09-03: the pre-existing Chrome on
   port 9222 reported ``hidden`` with 6 palette entries after 40s of waiting; the
   same page in a Chrome started with the flags below reported ``visible``.

2. **A modal blocked the app.** draw.io keeps unsaved drafts in localStorage.
   After the first run the profile always had drafts, so every later run opened
   onto the "Choose a draft to continue editing" dialog with the canvas
   unreachable behind it — visible in result/new30_run/*/after.png.

3. **The UI was in Vietnamese.** The scenario corpus addresses menus in English
   ("Click on File", "Click on Extras"), which cannot match "Tập tin"/"Bổ sung".

Nothing here special-cases a scenario or a shape: it starts a browser, waits for
the editor to actually be ready, and clears state between cases.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

DRAWIO_URL = "https://app.diagrams.net/?lang=en&splash=0"


def _find_chrome() -> str:
    override = os.environ.get("RPA_CHROME_BINARY")
    if override:
        return override
    for path in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ):
        if os.path.exists(path):
            return path
    return "chrome"


# The flags that matter, and why:
#   CalculateNativeWinOcclusion / backgrounding-occluded-windows
#       stop Chrome marking a covered window hidden (defect 1)
#   renderer-backgrounding / background-timer-throttling
#       keep timers at full rate so draw.io's deferred rendering happens
#   no-first-run / no-default-browser-check / search-engine-choice-screen
#       a fresh profile must open straight onto the page, not onto onboarding
_FLAGS = [
    "--disable-features=CalculateNativeWinOcclusion",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-search-engine-choice-screen",
    "--disable-notifications",
    "--force-device-scale-factor=1",
]


def kill_chrome_on_port(port: int) -> int:
    """Stop any Chrome already holding this debugging port.

    Without this, a relaunch silently attaches to the previous instance (Chrome
    refuses the port, Selenium connects to the survivor) and the "fresh profile"
    guarantee quietly does not hold. Only processes whose command line names this
    exact port are touched, so the user's own browser is never affected.
    """
    killed = 0
    try:
        out = subprocess.run(
            ["wmic", "process", "where", "name='chrome.exe'", "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, timeout=20).stdout
    except Exception:
        out = ""
    needle = "--remote-debugging-port=%d" % port
    for line in out.splitlines():
        if needle not in line:
            continue
        pid = line.strip().rsplit(None, 1)[-1]
        if pid.isdigit():
            subprocess.run(["taskkill", "/F", "/PID", pid],
                           capture_output=True, timeout=20)
            killed += 1
    if killed:
        time.sleep(2.0)
    return killed


def launch_chrome(port: int = 9222, profile_dir: str | Path | None = None,
                  width: int = 1600, height: int = 1000,
                  position: tuple = (0, 0), fresh_profile: bool = True,
                  url: str = DRAWIO_URL):
    """Start a Chrome the harness owns, on its own debugging port and profile.

    A dedicated profile per port is what makes parallel workers possible later:
    two Chrome instances cannot share one user-data-dir.
    """
    kill_chrome_on_port(port)
    if profile_dir is None:
        profile_dir = Path.home() / ".rpa_chrome_profiles" / f"port{port}"
    profile_dir = Path(profile_dir)
    if fresh_profile and profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        _find_chrome(),
        "--remote-debugging-port=%d" % port,
        "--user-data-dir=%s" % profile_dir,
        "--window-size=%d,%d" % (width, height),
        "--window-position=%d,%d" % (position[0], position[1]),
        *_FLAGS,
        url,
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for_debug_port(port: int, timeout: float = 40.0) -> bool:
    """Wait until DevTools answers, so attaching cannot race the launch."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=1):
                return True
        except Exception:
            time.sleep(0.4)
    return False


def editor_state(driver) -> dict:
    """One round-trip that answers 'is the editor usable right now?'."""
    return driver.execute_script("""
    const dialogs = Array.from(document.querySelectorAll('.geDialog, .geTransDialog'))
        .filter(e => e.offsetParent !== null);
    return {
      visibility: document.visibilityState,
      paletteItems: document.querySelectorAll('.geSidebarContainer a.geItem').length,
      canvas: !!document.querySelector('.geDiagramContainer svg'),
      dialogs: dialogs.map(e => e.textContent.trim().slice(0, 60))
    };
    """)


def dismiss_dialogs(driver) -> int:
    """Close any modal standing in front of the canvas (draft recovery, notices).

    Clicks the dialog's own dismissal control rather than removing the node, so
    draw.io's internal state stays consistent. Returns how many were closed.
    """
    return driver.execute_script("""
    let closed = 0;
    document.querySelectorAll('.geDialog, .geTransDialog').forEach(dlg => {
      if (dlg.offsetParent === null) return;
      const btns = Array.from(dlg.querySelectorAll('button'));
      const cancel = btns.find(b => /cancel|close|discard|no thanks|hủy|loại bỏ/i.test(b.textContent.trim()));
      const target = cancel || btns[btns.length - 1];
      if (target) { target.click(); closed++; }
    });
    return closed;
    """)


def clear_drawio_storage(driver) -> None:
    """Remove saved drafts so the next load opens on a blank, unnamed diagram."""
    driver.execute_script("""
    try { localStorage.clear(); } catch (e) {}
    try { sessionStorage.clear(); } catch (e) {}
    """)


def wait_ready(driver, min_palette_items: int = 20, timeout: float = 90.0,
               log=None) -> dict:
    """Block until draw.io has a canvas and a rendered shape palette.

    Replaces the fixed ``time.sleep(3)`` the executor used. The palette is what
    the image matcher searches, and how long it takes to appear varies with
    network and machine load, so waiting on the thing itself is the only reliable
    gate.
    """
    if log is None:
        def log(*a, **k):
            pass
    deadline = time.time() + timeout
    state = {}
    while time.time() < deadline:
        try:
            state = editor_state(driver)
        except Exception as exc:
            log("[env] editor_state failed: %s" % exc)
            time.sleep(0.5)
            continue
        if state["dialogs"]:
            log("[env] dismissing dialog(s): %s" % state["dialogs"])
            dismiss_dialogs(driver)
            time.sleep(1.0)
            continue
        if state["canvas"] and state["paletteItems"] >= min_palette_items:
            return state
        time.sleep(0.5)
    log("[env] NOT READY after %ss: %s" % (timeout, state))
    return state


def clear_canvas(driver, log=None) -> int:
    """Empty the canvas through the UI (Select All, then Delete).

    Clearing localStorage is not enough on its own: draw.io also keeps the working
    file in IndexedDB, so a reload can bring the previous scenario's shapes back —
    observed 2026-09-03, where a "clean" reload still showed five leftover cells.
    Doing it as an editing action is deterministic and needs no storage surgery.
    Returns the number of cells still present afterwards (0 when clean).
    """
    if log is None:
        def log(*a, **k):
            pass
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    import cell_tracker

    for attempt in range(3):
        remaining = len(cell_tracker.cell_elements(driver))
        if remaining == 0:
            return 0
        body = driver.find_element("tag name", "body")
        ActionChains(driver).move_to_element(body).click().perform()
        time.sleep(0.2)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
        time.sleep(0.4)
        ActionChains(driver).send_keys(Keys.DELETE).perform()
        time.sleep(0.8)
        log("[env] clear_canvas attempt %d: %d cells before" % (attempt + 1, remaining))
    return len(cell_tracker.cell_elements(driver))


def set_page_view(driver, on: bool = False) -> str:
    """Turn draw.io's paged canvas on or off.

    Off, for the runs. With Page View on, the canvas is divided into 850x1100
    sheets, and moving a shape past the top of a sheet makes draw.io re-anchor the
    page grid — the shape's position jumps by a full page height. Measured
    2026-09-03: a lone shape nudged up 150px four times went 968, 818, 1768, 1618
    with Page View on, and 1445, 1295, 1145, 995 with it off. That +1100 is exactly
    what put the first shape of easy_e01_v1_s5b0l0 at the bottom of a chain it
    should have led.

    It also makes the result look more like what it is judged against: the
    benchmark's reference images are diagrams, not sheets of paper.
    """
    return driver.execute_script("""
    const want = arguments[0];
    // The format panel exists more than once in the DOM and both copies report as
    // visible, so clicking only the first match flipped a stale copy and left the
    // live one untouched — Page View stayed on and the page-boundary jump kept
    // happening. Every matching control is set, and the page element itself is
    // then used as the proof.
    const boxes = [];
    Array.from(document.querySelectorAll('span, div, label'))
        .filter(e => (e.textContent || '').trim() === 'Page View')
        .forEach(lab => {
          let box = lab.previousElementSibling;
          if (!box || box.type !== 'checkbox') {
            box = (lab.parentElement || lab).querySelector('input[type=checkbox]');
          }
          if (box && boxes.indexOf(box) === -1) boxes.push(box);
        });
    let clicked = 0;
    boxes.forEach(b => { if (b.checked !== want) { b.click(); clicked++; } });
    const page = document.querySelector('.geBackgroundPage');
    const pageShown = !!(page && page.offsetParent !== null);
    return {boxes: boxes.length, clicked: clicked, pageShown: pageShown,
            ok: pageShown === want};
    """, on)


def view_origin(driver) -> dict:
    """Where the canvas is currently scrolled to."""
    return driver.execute_script("""
    const c = document.querySelector('.geDiagramContainer');
    return c ? {x: c.scrollLeft, y: c.scrollTop} : {x: 0, y: 0};
    """)


def reset_view(driver, origin: dict) -> None:
    """Put the canvas back to a known scroll position.

    draw.io inserts a click-added shape at the centre of the *current view*, and
    Selenium pans that view every time it scrolls an element into range to click
    it. Left alone, consecutive inserts therefore land at different model
    coordinates — measured 2026-09-03, two identical palette clicks dropped
    shapes 350px apart — which makes every subsequent "Move" step place things
    somewhere unintended. Restoring the scroll before each insert is what makes
    placement reproducible.
    """
    driver.execute_script("""
    const c = document.querySelector('.geDiagramContainer');
    if (c) { c.scrollLeft = arguments[0]; c.scrollTop = arguments[1]; }
    """, origin.get("x", 0), origin.get("y", 0))
    time.sleep(0.25)


def deselect_all(driver) -> None:
    """Drop the current selection.

    This matters before any drag that starts on a shape's perimeter: while a shape
    is selected its eight resize handles sit exactly on that perimeter and swallow
    the gesture. Measured 2026-09-03 — the same drag resized the shape when it was
    selected and drew a proper connector when it was not.
    """
    from selenium.webdriver.common.action_chains import ActionChains
    container = driver.find_element("css selector", ".geDiagramContainer")
    size = container.size
    # a corner of the canvas, far from where shapes get inserted (the centre)
    dx = -int(size["width"] * 0.42)
    dy = -int(size["height"] * 0.40)
    ActionChains(driver).move_to_element_with_offset(container, dx, dy).click().perform()
    time.sleep(0.3)


def settle_for_screenshot(driver) -> None:
    """Leave the editor in a state fit to be judged from a picture.

    Whatever is still selected draws grips over the diagram, and draw.io floats a
    style toolbar next to the selection that covers neighbouring shapes — in
    scenario_050 it sat squarely on top of the "Take bus" box. Since the run is
    scored by looking at the screenshot, clearing that is part of finishing, not
    cosmetics.
    """
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.3)
        deselect_all(driver)
        # park the pointer off the canvas so nothing is hovered
        header = driver.find_element("css selector", ".geDiagramContainer")
        ActionChains(driver).move_to_element_with_offset(
            header, -int(header.size["width"] * 0.45),
            -int(header.size["height"] * 0.45)).perform()
        time.sleep(0.6)
    except Exception:
        pass


def _content_box(driver):
    """Bounding box of everything drawn, and the viewport it has to fit into."""
    import cell_tracker
    els = cell_tracker.cell_elements(driver)
    if not els:
        return None
    infos = cell_tracker.cell_info(driver, els)
    x0 = min(i["x"] for i in infos)
    y0 = min(i["y"] for i in infos)
    x1 = max(i["x"] + i["w"] for i in infos)
    y1 = max(i["y"] + i["h"] for i in infos)
    cont = driver.execute_script("""
    const c = document.querySelector('.geDiagramContainer');
    const r = c.getBoundingClientRect();
    return {w: r.width, h: r.height};
    """)
    return {"w": x1 - x0, "h": y1 - y0, "view_w": cont["w"], "view_h": cont["h"]}


def fit_page(driver, max_steps: int = 8) -> dict:
    """Zoom out until the whole diagram is in frame, then centre it.

    The screenshot is what the run gets judged on, so a picture showing part of
    the drawing is a lost case regardless of what was drawn. Ctrl+Shift+H looked
    like the right tool and is not: on medium_m21_v4_s7b1l0 it left the canvas
    zoomed so far in that a single diamond filled the frame, while the run had in
    fact drawn all seven shapes and seven arrows.

    Zooming out one step at a time and measuring after each is unglamorous but it
    is checkable, which the shortcut was not.
    """
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    import cell_tracker

    steps = 0
    try:
        for _ in range(max_steps):
            box = _content_box(driver)
            if box is None:
                return {"fitted": False, "reason": "nothing drawn"}
            if box["w"] <= box["view_w"] * 0.92 and box["h"] <= box["view_h"] * 0.92:
                break
            (ActionChains(driver).key_down(Keys.CONTROL).send_keys(Keys.SUBTRACT)
             .key_up(Keys.CONTROL).perform())
            steps += 1
            time.sleep(0.6)
        # centre what is now visible
        els = cell_tracker.cell_elements(driver)
        if els:
            import drawio_ops
            drawio_ops.ensure_visible(driver, *els)
        box = _content_box(driver)
        return {"fitted": bool(box and box["w"] <= box["view_w"]
                               and box["h"] <= box["view_h"]),
                "zoom_out_steps": steps, "box": box}
    except Exception as exc:
        return {"fitted": False, "reason": "%s: %s" % (type(exc).__name__, exc)}


def open_clean_drawio(driver, url: str = DRAWIO_URL, log=None) -> dict:
    """Put the editor into a known-empty state: no drafts, English UI, palette up.

    Two loads are needed: localStorage can only be cleared once a page from that
    origin is open, and whether the draft dialog appears is decided at load time.
    """
    if log is None:
        def log(*a, **k):
            pass
    driver.get(url)
    time.sleep(1.0)
    clear_drawio_storage(driver)
    driver.get(url)
    state = wait_ready(driver, log=log)
    left = clear_canvas(driver, log=log)
    deselect_all(driver)
    state["cellsLeftOver"] = left
    state["pageView"] = set_page_view(driver, False)
    time.sleep(0.5)
    log("[env] ready: visibility=%s palette=%s cellsLeftOver=%s pageView=%s"
        % (state.get("visibility"), state.get("paletteItems"), left, state["pageView"]))
    return state
