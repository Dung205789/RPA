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


_CENTER_ON_JS = r"""
const cont = document.querySelector('.geDiagramContainer');
if (!cont) return null;
const cr = cont.getBoundingClientRect();
let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
for (const g of arguments[0]) {
  if (!g) continue;
  const r = g.getBoundingClientRect();
  minX = Math.min(minX, r.x); minY = Math.min(minY, r.y);
  maxX = Math.max(maxX, r.x + r.width); maxY = Math.max(maxY, r.y + r.height);
}
if (!isFinite(minX)) return null;
const wantX = (minX + maxX) / 2, wantY = (minY + maxY) / 2;
cont.scrollLeft += wantX - (cr.x + cr.width / 2);
cont.scrollTop  += wantY - (cr.y + cr.height / 2);
return {scrollLeft: cont.scrollLeft, scrollTop: cont.scrollTop};
"""


def ensure_visible(driver, *elements) -> None:
    """Scroll the canvas so the given cells sit in the middle of the viewport.

    Cells that have been nudged a few hundred pixels leave the visible area, and
    once they do, point-based clicks fall outside the container and Selenium's own
    scroll-into-view is not reliable enough to recover: in scenario_050 the four
    shapes that had been moved up or down never received their labels, while the
    two that only moved sideways did. Centring them first removes the whole class
    of failure.
    """
    driver.execute_script(_CENTER_ON_JS, [e for e in elements if e is not None])
    time.sleep(0.3)


def select_cell(driver, element) -> None:
    """Click a cell so keyboard nudges apply to it."""
    ensure_visible(driver, element)
    pt = point_on_cell(driver, element)
    if not _act_at_point(driver, pt["x"], pt["y"]):
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


def move_cell(driver, element, direction: str, distance_px: int = MOVE_STEP_PX,
              measure: bool = True) -> dict:
    """Nudge one cell.

    With ``measure=True`` the displacement is read here, comparing the element's
    own geometry before and after. Callers that own a tracker should pass
    ``measure=False`` and compare through it instead: draw.io occasionally rebuilds
    a cell's DOM node when it scrolls back into view, and a raw handle comparison
    then reports the shape as gone when it is plainly still on the canvas.

    Displacement is read in scroll-corrected coordinates either way, because
    clicking a cell makes Selenium scroll it into view and that pans the canvas.
    """
    key = _ARROW.get((direction or "").lower())
    if key is None:
        return {"ok": False, "reason": "unknown direction %r" % direction}

    before = _info_of(driver, element) if measure else None
    if measure and before is None:
        return {"ok": False, "reason": "cell not on canvas"}
    select_cell(driver, element)
    _press_arrow(driver, key, max(1, round(distance_px / PX_PER_ARROW_PRESS)))
    time.sleep(0.5)
    if not measure:
        return {"ok": True, "measured": False}
    after = _info_of(driver, element)
    if after is None:
        return {"ok": False, "reason": "cell disappeared during move"}
    dx, dy = after["mx"] - before["mx"], after["my"] - before["my"]
    return {"ok": (abs(dx) + abs(dy)) >= distance_px // 2, "dx": dx, "dy": dy,
            "wanted": distance_px}


_POINT_ON_CELL_JS = r"""
const g = arguments[0];
const paths = Array.from(g.querySelectorAll('path'));
// Only an edge gets the on-the-path treatment. A vertex drawn as a single <path>
// (diamond, parallelogram, hexagon…) has its path midpoint on the *outline*, and
// double-clicking the outline does not open the label editor — measured: the
// diamond's point landed on its bottom vertex, the parallelogram's on its right
// edge, and neither took a label, while rectangles did.
const isEdge = paths.length > 1 && g.children.length === paths.length;
if (isEdge) {
  // Pick the longest path (the drawn stroke, not the arrow marker) and take its
  // midpoint. An edge's bounding-box centre is not on the edge at all once the
  // route turns a corner, so double-clicking there lands on empty canvas.
  let best = null, bestLen = -1;
  for (const p of paths) {
    let len = 0;
    try { len = p.getTotalLength(); } catch (e) { continue; }
    if (len > bestLen) { bestLen = len; best = p; }
  }
  if (best && bestLen > 0) {
    const frac = (typeof arguments[1] === 'number') ? arguments[1] : 0.5;
    const pt = best.getPointAtLength(bestLen * frac);
    const m = best.getScreenCTM();
    if (m) {
      return {x: pt.x * m.a + pt.y * m.c + m.e, y: pt.x * m.b + pt.y * m.d + m.f, on: 'path'};
    }
  }
}
const r = g.getBoundingClientRect();
return {x: r.x + r.width / 2, y: r.y + r.height / 2, on: 'box'};
"""


def point_on_cell(driver, element, frac: float = 0.5) -> dict:
    """A viewport point that really lies on the cell.

    ``frac`` picks how far along an edge's path to sample, so a caller can try a
    different spot when the first one turns out to select the wrong cell.
    """
    return driver.execute_script(_POINT_ON_CELL_JS, element, frac)


def _act_at_point(driver, x: float, y: float, double: bool = False) -> bool:
    """Click (or double-click) an absolute viewport point.

    Offsets are taken from the canvas container's centre because Selenium 4
    measures ``move_to_element_with_offset`` from an element's centre, and using
    ``body`` as the anchor put the target out of bounds.
    """
    container = driver.find_element("css selector", ".geDiagramContainer")
    rect = driver.execute_script("""
    const r = arguments[0].getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height};
    """, container)
    dx = int(round(x - (rect["x"] + rect["w"] / 2.0)))
    dy = int(round(y - (rect["y"] + rect["h"] / 2.0)))
    if abs(dx) > rect["w"] / 2 or abs(dy) > rect["h"] / 2:
        return False
    chain = ActionChains(driver).move_to_element_with_offset(container, dx, dy).pause(0.2)
    (chain.double_click() if double else chain.click()).perform()
    time.sleep(0.6)
    return True


def label_cell(driver, element, text: str) -> dict:
    """Put text into a shape: double-click to open the inline editor, type, commit.

    The commit is what the old executor left out — it typed the label and moved
    straight on, so the editor was still open when the next click arrived and the
    text was frequently lost. Escape closes the editor keeping the text, which is
    draw.io's own behaviour. Select-all first so a re-label replaces rather than
    appends.
    """
    open_editor_on(driver, element)
    ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
    time.sleep(0.15)
    ActionChains(driver).send_keys(text).perform()
    time.sleep(0.4)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.8)
    return _label_result(driver, text, near=_info_of(driver, element))


def open_editor_on(driver, element) -> dict:
    """Double-click a cell to start editing its label, leaving the editor open.

    The corpus splits labelling into two steps ("Double click on X" then
    "Fill ..."), so the two halves have to be callable separately. The click goes
    to a point on the cell rather than to its bounding-box centre, which for a
    routed connector is usually empty canvas — that is how "NO"/"YES" ended up on
    the wrong edge of scenario_050.
    """
    ensure_visible(driver, element)
    # Select, then F2, then *check the editor opened on the cell we meant*.
    #
    # A precise double-click is what the corpus's wording describes, but on a
    # connector it has to land inside a 5px-tall line at whatever zoom the
    # scenario left behind, and a near-miss silently edits the neighbouring shape
    # instead: scenario_050 typed the edge label "YES" over the "Take subway" box
    # and lost that box's own label, while every step still reported success.
    # Comparing the editor's position against the target's is what turns that into
    # something the run can notice and retry.
    target = _info_of(driver, element)
    want_kind = "edge" if (target and target["kind"] == "edge") else "vertex"
    for attempt, frac in enumerate((0.5, 0.35, 0.65, 0.2, 0.8)):
        pt = point_on_cell(driver, element, frac)
        if not _act_at_point(driver, pt["x"], pt["y"]):
            ActionChains(driver).move_to_element(element).click().perform()
            time.sleep(0.3)
        if selected_kind(driver) != want_kind:
            continue          # the click landed on the neighbour; try another spot
        ActionChains(driver).send_keys(Keys.F2).perform()
        time.sleep(0.8)
        box = editor_box(driver)
        if box and _editor_matches(box, target):
            return {"via": "select+F2", "attempt": attempt, "editor": True}
        if box:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.4)
    # last resort: the plain gesture the corpus names
    pt = point_on_cell(driver, element)
    if not _act_at_point(driver, pt["x"], pt["y"], double=True):
        ActionChains(driver).move_to_element(element).double_click().perform()
    time.sleep(0.9)
    return {"via": "double-click-fallback", "editor": editor_is_open(driver)}


def selected_kind(driver):
    """Whether draw.io currently has a vertex, an edge, or nothing selected.

    Read from the affordances it draws: a selected vertex gets eight corner/side
    resize grips (``nw-resize`` and friends) plus a rotate grip; a selected edge
    gets endpoint grips instead (``col-resize``/``pointer``). This is the check
    that separates "clicked the connector" from "clicked the box next to it" —
    comparing positions was not enough, because a short connector's midpoint sits
    within tolerance of its target shape's centre, and the edge label "YES"
    overwrote the "Take subway" box's own label while every check passed.
    """
    return driver.execute_script("""
    const svg = document.querySelector('.geDiagramContainer svg');
    if (!svg) return null;
    const styles = Array.from(svg.querySelectorAll('g'))
        .map(g => g.getAttribute('style') || '');
    if (styles.some(s => s.includes('nw-resize'))) return 'vertex';
    if (styles.some(s => s.includes('col-resize') || s.includes('row-resize'))) return 'edge';
    return null;
    """)


def editor_is_open(driver) -> bool:
    return bool(driver.execute_script(
        "return !!document.querySelector('[contenteditable=\"true\"]');"))


def editor_box(driver):
    return driver.execute_script("""
    const e = document.querySelector('[contenteditable="true"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height,
            cx: r.x + r.width / 2, cy: r.y + r.height / 2};
    """)


def _editor_matches(box, target) -> bool:
    """Is the open editor sitting on the cell we aimed at?"""
    if target is None:
        return True
    tol = max(40, target["w"] / 2 + 20, target["h"] / 2 + 20)
    return (abs(box["cx"] - (target["x"] + target["w"] / 2)) <= tol
            and abs(box["cy"] - (target["y"] + target["h"] / 2)) <= tol)


def type_into_open_editor(driver, text: str, near: dict | None = None) -> dict:
    """Type into the label editor a previous step opened, then commit."""
    ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
    time.sleep(0.15)
    ActionChains(driver).send_keys(text).perform()
    time.sleep(0.4)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.8)
    return _label_result(driver, text, near=near)


def _label_result(driver, text: str, near: dict | None = None) -> dict:
    """Did the text land, and did it land on the intended cell?

    Checking only that the string appears somewhere on the canvas is too weak: in
    scenario_050 the edge labels "NO" and "YES" were both typed onto the wrong
    connector and the step still reported success. When the caller knows which
    cell it aimed at, the label has to sit inside that cell's box.
    """
    labels = cell_tracker.canvas_labels(driver)
    want = " ".join(text.split())
    hits = [l for l in labels if want in " ".join(l["text"].split())]
    if not hits:
        return {"ok": False, "labels": [l["text"] for l in labels]}
    if near is None:
        return {"ok": True, "placement": "unchecked"}
    pad = 12
    x0, x1 = near["x"] - pad, near["x"] + near["w"] + pad
    y0, y1 = near["y"] - pad, near["y"] + near["h"] + pad
    on_target = any(x0 <= h["cx"] <= x1 and y0 <= h["cy"] <= y1 for h in hits)
    return {"ok": on_target, "placement": "on-target" if on_target else "elsewhere",
            "label_at": [(h["cx"], h["cy"]) for h in hits],
            "target_box": [near["x"], near["y"], near["w"], near["h"]]}


def _cardinal_toward(info: dict, toward: dict) -> tuple:
    """Which of the four sides of ``info`` faces ``toward``, as a unit vector."""
    dx = toward["mx"] - info["mx"]
    dy = toward["my"] - info["my"]
    if abs(dy) >= abs(dx):
        return (0, 1 if dy > 0 else -1)
    return (1 if dx > 0 else -1, 0)


_EDGE_POINT_JS = r"""
const g = arguments[0], dirx = arguments[1], diry = arguments[2];
const geo = g.querySelector('rect,ellipse,path,polygon');
const r = g.getBoundingClientRect();
const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
const bx = cx + dirx * (r.width / 2), by = cy + diry * (r.height / 2);
// rect/ellipse are convex and axis-aligned, so the bounding-box edge midpoint
// really is on the outline. A path-based shape (diamond, parallelogram, hexagon,
// trapezoid...) is not: a parallelogram's slanted right edge at vertical centre
// sits inboard of the bounding box by half its slant, so that same point falls
// in the shape's cut corner, outside the fill. draw.io does not show a
// connection affordance there, and the drag starts a selection instead of an
// edge — measured on a parallelogram, where this cost the connector outright.
//
// Rather than a per-shape slant constant, walk the segment from the bbox edge
// toward the centre and ask the path itself, via isPointInFill, where its fill
// actually starts. This is shape-agnostic: the same probe handles diamond,
// hexagon and trapezoid without knowing any of their geometry in advance.
if (!geo || geo.tagName.toLowerCase() !== 'path' || !geo.isPointInFill) {
  return {x: bx, y: by};
}
const inv = geo.getScreenCTM().inverse();
const inside = (px, py) => geo.isPointInFill(new DOMPoint(px, py).matrixTransform(inv));
for (let t = 0; t <= 1.0; t += 0.02) {
  const px = bx + (cx - bx) * t, py = by + (cy - by) * t;
  if (inside(px, py)) return {x: px, y: py};
}
return {x: cx, y: cy};
"""


def _edge_point(driver, el, dirx: int, diry: int) -> dict:
    return driver.execute_script(_EDGE_POINT_JS, el, dirx, diry)


def connect_cells(driver, src_el, dst_el) -> dict:
    """Draw a connector from one shape to another.

    Order of operations, all four of which were needed to make it work:
      1. clear the selection — a selected shape's resize handles sit on the
         perimeter and turn the drag into a resize (observed: the shape stretched
         into a tall rectangle instead of an edge appearing),
      2. hover the source so draw.io materialises its connection points,
      3. find a point that is actually on the shape's outline (see
         ``_edge_point`` — the bounding box is not the outline for a slanted
         shape),
      4. start the drag there, step off it, then land on the target's centre,
         which makes a floating connection to that shape.
    """
    before = known_cells(driver)
    ensure_visible(driver, src_el, dst_el)
    rpa_env.deselect_all(driver)
    ensure_visible(driver, src_el, dst_el)
    src_info = _info_of(driver, src_el)
    dst_info = _info_of(driver, dst_el)
    if src_info is None or dst_info is None:
        return {"ok": False, "reason": "source or target not on canvas"}

    ActionChains(driver).move_to_element(src_el).perform()
    time.sleep(0.7)
    dirx, diry = _cardinal_toward(src_info, dst_info)
    edge = _edge_point(driver, src_el, dirx, diry)
    lead_x, lead_y = (18 * dirx, 18 * diry) if dirx else (0, 18 * diry)
    if diry == 0 and dirx == 0:
        lead_x = lead_y = 0

    container = driver.find_element("css selector", ".geDiagramContainer")
    crect = driver.execute_script("""
    const r = arguments[0].getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height};
    """, container)
    ox = int(round(edge["x"] - (crect["x"] + crect["w"] / 2.0)))
    oy = int(round(edge["y"] - (crect["y"] + crect["h"] / 2.0)))

    (ActionChains(driver)
     .move_to_element_with_offset(container, ox, oy)
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
