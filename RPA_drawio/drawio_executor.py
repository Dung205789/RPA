#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run an RPA_Datasets scenario against the live draw.io editor.

Added 2026-09-03. This is the draw.io execution path; ``generator.py`` and the
other sites' code are left alone.

What it keeps from the original executor:
  * ``step_parser.StepParser`` — the NLP that turns an English sentence into
    (action, object, related object, value). It parses the whole corpus
    correctly and there was no reason to touch it.
  * ``by_text`` — locating a menu item by its label, which is how the older
    100-case corpus drives File/Extras/View menus.
  * the Java script as an output artefact.

What it replaces, and why (all four measured 2026-09-03, see the module docs of
rpa_env / cell_tracker / drawio_ops / palette_matcher):
  * created-element tracking, which never produced a single mapping;
  * the palette icon lookup, which clicked the empty canvas;
  * the canvas gestures, which silently no-opped or did the wrong thing;
  * step accounting: the old loop logged failures and carried on, so a scenario
    whose every drawing step failed still ended up recorded as "ok".

Two details of the scenario language that the previous harness got wrong and are
honoured here:

  * **Step numbers are indices into ``descriptions``, 1-based, including any
    description the parser could not read.** The old harness appended only the
    steps it managed to parse, so a single unparsed line shifted every later
    "element created in step N" reference onto the wrong shape.
  * **A "Move" step names its subject.** "Move the element created in step 5
    down" moves the shape from step 5 — the step number does not advance to the
    Move step itself.
"""
from __future__ import annotations

import os
import re
import time
import traceback

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import by_text
import cell_tracker
import drawio_ops
import palette_matcher
import rpa_env

CREATED_RE = re.compile(r"element created in step\s+(\d+)", re.IGNORECASE)
CONNECTOR_RE = re.compile(r"connector_from_step(\d+)_to_step(\d+)", re.IGNORECASE)
IMAGE_RE = re.compile(r"\.(png|jpe?g|bmp|gif)$", re.IGNORECASE)


def _is_shape_vocabulary(icon_dir: str) -> bool:
    """Is this folder a small set of shape templates, or a mixed icon dump?"""
    try:
        pngs = [f for f in os.listdir(icon_dir)
                if f.lower().endswith(".png") and not f.startswith("_")]
    except OSError:
        return False
    return 0 < len(pngs) <= 15


class StepResult(dict):
    """One row of the per-step report."""

    def __init__(self, n, description, action="", status="skipped", detail=None):
        super().__init__(n=n, description=description, action=action,
                         status=status, detail=detail)


class DrawioExecutor:
    def __init__(self, driver, log=None, url: str = rpa_env.DRAWIO_URL):
        self.driver = driver
        self.log = log or (lambda *a, **k: None)
        self.url = url
        self.tracker = cell_tracker.CellTracker(driver, log=self.log)
        self.origin = None
        self.editor_open_on = None      # which step's cell has its label editor open
        self.java_lines = []
        # How far each shape has been nudged from the point it was inserted at,
        # accumulated from the displacements actually observed. This is what makes
        # the insertion point recoverable — see _insert_origin.
        self.displacement: dict = {}

    # ------------------------------------------------------- frame-safe geometry
    def _positions(self) -> dict:
        """Where every tracked shape is, all read in one frame.

        Positions are only ever compared *within* one of these snapshots. draw.io
        grows its canvas when content approaches the edge and re-anchors the view
        when it does, which shifts every reported coordinate at once; differences
        taken inside a single snapshot are immune to that, absolute values are not.
        """
        els = cell_tracker.cell_elements(self.driver)
        if not els:
            return {}
        infos = cell_tracker.cell_info(self.driver, els)
        by_el = dict(zip(els, infos))
        out = {}
        for step, entry in self.tracker.step_to_cell.items():
            info = by_el.get(entry["el"])
            if info is not None:
                out[step] = info
        return out

    def _insert_origin(self, snapshot: dict):
        """Where a freshly clicked shape *should* land, in the current frame.

        draw.io drops every click-inserted shape at the centre of the view, so the
        scenario language treats that as one fixed point and expresses all
        placement as moves away from it. Restoring the container's scroll offset is
        not enough to hold it: once the canvas grows, the same scroll number names a
        different model point. Measured — after three upward nudges the insertion
        point had slid a full page height, and the first shape of
        easy_e01_v1_s5b0l0 ended up at the bottom of a chain it should have headed.

        Each tracked shape knows how far it has been nudged, so each one implies
        where the insertion point is now. The median of those estimates is robust
        to any single shape having been mis-tracked.
        """
        estimates = []
        for step, info in snapshot.items():
            dx, dy = self.displacement.get(step, (0, 0))
            estimates.append((info["mx"] - dx, info["my"] - dy))
        if not estimates:
            return None
        xs = sorted(e[0] for e in estimates)
        ys = sorted(e[1] for e in estimates)
        mid = len(estimates) // 2
        return xs[mid], ys[mid]

    def _nudge(self, element, dx: int, dy: int) -> None:
        """Move a cell by an exact model offset, using the arrow-key grid."""
        if abs(dx) >= drawio_ops.PX_PER_ARROW_PRESS:
            drawio_ops.move_cell(self.driver, element,
                                 "right" if dx > 0 else "left", abs(dx), measure=False)
        if abs(dy) >= drawio_ops.PX_PER_ARROW_PRESS:
            drawio_ops.move_cell(self.driver, element,
                                 "down" if dy > 0 else "up", abs(dy), measure=False)

    # ------------------------------------------------------------------ setup
    def prepare(self):
        state = rpa_env.open_clean_drawio(self.driver, self.url, log=self.log)
        self.origin = rpa_env.view_origin(self.driver)
        return state

    # ------------------------------------------------------------- resolution
    def _resolve_object(self, text: str):
        """Turn an object phrase into (element, info, kind_of_reference)."""
        if not text:
            return None, None, "none"
        m = CONNECTOR_RE.search(text)
        if m:
            el, info = self.tracker.element_for_connector(int(m.group(1)), int(m.group(2)))
            return el, info, "connector"
        m = CREATED_RE.search(text)
        if m:
            el, info = self.tracker.element_for_step(int(m.group(1)))
            return el, info, "created"
        if IMAGE_RE.search(text.strip()):
            return None, None, "image"
        return None, None, "text"

    def _click_by_text(self, text: str) -> dict:
        """Click a menu entry / labelled control found by its text.

        Tries the candidate xpaths in order, the same fallback idea the original
        executor had; the difference is that a failure is reported instead of
        being retried against an unchanged page five times.
        """
        xpaths = by_text.process_url_with_text(self.url, text, driver=self.driver,
                                               return_all=True) or []
        for xp in xpaths[:6]:
            if xp == "//not-found":
                continue
            try:
                el = self.driver.find_element(By.XPATH, xp)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.2)
                ActionChains(self.driver).move_to_element(el).click().perform()
                time.sleep(0.8)
                return {"ok": True, "xpath": xp}
            except Exception as exc:
                self.log("[click-text] %s failed on %s: %s" % (text, xp, type(exc).__name__))
        return {"ok": False, "reason": "no candidate clickable for %r" % text,
                "tried": xpaths[:6]}

    # ---------------------------------------------------------------- actions
    def _do_open(self, step, n):
        self.prepare()
        self.java_lines.append('driver.get("%s");' % self.url)
        return "ok", {"url": self.url}

    def _do_click(self, step, n):
        obj = (step.object or "").strip()
        _, _, kind = self._resolve_object(obj)

        if kind == "image":
            # The corpus's bracketed images are not all shapes — object2.png is the
            # toolbar zoom control, help.png a menu item — so the search covers every
            # small control on the page, and whether a shape appeared afterwards is
            # what decides if this click created a cell.
            match = palette_matcher.find_icon(self.driver, obj, log=self.log)
            if not match.get("ok"):
                return "failed", {"reason": match.get("reason")}
            candidates = match["ranked"][:3]
            for ci, cand in enumerate(candidates):
                known = drawio_ops.known_cells(self.driver)
                before_positions = self._positions()
                if cand["palette"]:
                    res = drawio_ops.click_palette_entry(self.driver, cand["element"],
                                                         view_origin=self.origin)
                else:
                    try:
                        ActionChains(self.driver).move_to_element(cand["element"]).click().perform()
                        time.sleep(1.0)
                        res = {"ok": True}
                    except Exception as exc:
                        res = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc)}
                created = len(drawio_ops.known_cells(self.driver)) > len(known)
                if not created:
                    if not res.get("ok"):
                        self.log("[click] candidate %s failed, trying next" % cand["tag"])
                        continue
                    # a UI click (menu, toolbar) — nothing should have appeared
                    self.java_lines.append("// click %s (%s, score %.2f)"
                                           % (obj, cand["tag"], cand["score"]))
                    return "ok", {"score": cand["score"], "palette": cand["palette"],
                                  "title": cand["title"] or cand["text"],
                                  "created_cell": False}

                self.tracker.record_created(n, known)
                self.displacement[n] = (0, 0)
                el, info = self.tracker.element_for_step(n)
                # Which shape did that actually draw? Reported, not enforced.
                #
                # Enforcing it was a mistake worth recording. The check ranks the
                # drawn shape against every icon in the same folder, which works
                # for RPA_drawio/shape_icons (nine shapes, nothing else) but not
                # for RPA_Datasets/images/drawio, where 64 files are mostly
                # toolbar and menu icons. A correctly drawn diamond resembled some
                # ribbon glyph more than it resembled diamond.png, so the shape
                # was deleted and retried — and since every later step refers back
                # to it, one rejected insert took about ten steps down with it.
                # scenario_050 fell from 41/41 to 30/41 that way.
                identification = None
                icon_dir = os.path.dirname(obj) or "."
                # Only meaningful over a folder that *is* a shape vocabulary; over
                # the old corpus's 64 mixed icons it would also be 64 comparisons
                # per insert for an answer that means nothing.
                if info is not None and _is_shape_vocabulary(icon_dir):
                    ranking = palette_matcher.identify_drawn_shape(
                        self.driver, info, icon_dir, log=self.log)
                    wanted = os.path.basename(obj)
                    identification = {
                        "wanted": wanted,
                        "identified_as": ranking[0]["icon"] if ranking else None,
                        "drawn_match": next((r["score"] for r in ranking
                                             if r["icon"] == wanted), 0.0),
                    }
                correction = self._align_to_origin(n, before_positions)
                self.java_lines.append("// click %s (%s, score %.2f)"
                                       % (obj, cand["tag"], cand["score"]))
                detail = {"score": cand["score"], "palette": cand["palette"],
                          "title": cand["title"] or cand["text"], "created_cell": True}
                if identification:
                    detail.update(identification)
                if correction:
                    detail["insert_correction"] = correction
                return "ok", detail

            return "failed", {"reason": "no candidate could be clicked",
                              "ranked": [(c["score"], c["tag"]) for c in match["ranked"]]}

        if kind in ("created", "connector"):
            el, _, _ = self._resolve_object(obj)
            if el is None:
                return "failed", {"reason": "unknown reference %r" % obj}
            drawio_ops.select_cell(self.driver, el)
            return "ok", {"selected": obj}

        res = self._click_by_text(obj)
        if res["ok"]:
            self.java_lines.append('driver.findElement(By.xpath("%s")).click();' % res["xpath"])
            return "ok", res
        return "failed", res

    _COMMANDED = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "top": (0, -1),
                  "down": (0, 1), "bottom": (0, 1)}

    def _displacement(self, moved_step, before: dict, after: dict,
                      direction: str = "") -> dict:
        """How far one shape moved, relative to the shapes that did not move.

        With other shapes on the canvas this is a difference of differences, which
        cancels any view shift draw.io performs while the move happens.

        With the moved shape alone on the canvas there is nothing to be relative
        to, and the measurement is not just noisy but meaningless: a lone shape's
        absolute position on an unbounded canvas is defined only up to whatever
        origin the editor currently happens to use, and growing the canvas moves
        that origin. Measured, the third consecutive nudge of a lone shape read as
        +250 or +950 depending on how far the canvas had grown. The keyboard nudge
        itself is exact — verified at 10px per press against a fixed anchor shape —
        so the commanded displacement is used and the row is flagged `assumed`.
        """
        want = drawio_ops.MOVE_STEP_PX
        if moved_step is None or moved_step not in before or moved_step not in after:
            return {"ok": False, "reason": "cell not measurable after move"}
        others = [s for s in before if s != moved_step and s in after]
        if not others:
            vec = self._COMMANDED.get((direction or "").lower())
            if vec is None:
                return {"ok": False, "reason": "unknown direction %r" % direction}
            return {"ok": True, "dx": vec[0] * want, "dy": vec[1] * want,
                    "wanted": want, "relative_to": 0, "assumed": True}
        dx = after[moved_step]["mx"] - before[moved_step]["mx"]
        dy = after[moved_step]["my"] - before[moved_step]["my"]
        # the view's own shift, read off the shapes that stayed put
        shifts_x = sorted(after[s]["mx"] - before[s]["mx"] for s in others)
        shifts_y = sorted(after[s]["my"] - before[s]["my"] for s in others)
        mid = len(others) // 2
        dx -= shifts_x[mid]
        dy -= shifts_y[mid]
        return {"ok": (abs(dx) + abs(dy)) >= want // 2, "dx": dx, "dy": dy,
                "wanted": want, "relative_to": len(others)}

    def _align_to_origin(self, n: int, before_positions: dict):
        """Put a just-inserted shape back on the scenario's insertion point.

        Only acts when there is already a shape to measure against — the first
        shape of a scenario *defines* the point, and with nothing else on the
        canvas any drift is both unobservable and harmless.
        """
        if not before_positions:
            return None
        after = self._positions()
        target = self._insert_origin({k: v for k, v in after.items() if k != n})
        new = after.get(n)
        if target is None or new is None:
            return None
        dx = int(round((target[0] - new["mx"]) / drawio_ops.PX_PER_ARROW_PRESS)) \
            * drawio_ops.PX_PER_ARROW_PRESS
        dy = int(round((target[1] - new["my"]) / drawio_ops.PX_PER_ARROW_PRESS)) \
            * drawio_ops.PX_PER_ARROW_PRESS
        if abs(dx) < drawio_ops.PX_PER_ARROW_PRESS and abs(dy) < drawio_ops.PX_PER_ARROW_PRESS:
            return None
        el, _ = self.tracker.element_for_step(n)
        if el is None:
            return None
        self.log("[insert] step %d landed %+d,%+d off the insertion point; correcting"
                 % (n, -dx, -dy))
        self._nudge(el, dx, dy)
        return {"dx": dx, "dy": dy}

    def _do_double_click(self, step, n):
        obj = (step.object or "").strip()
        el, info, kind = self._resolve_object(obj)
        if kind in ("created", "connector"):
            if el is None:
                return "failed", {"reason": "unknown reference %r" % obj}
            drawio_ops.open_editor_on(self.driver, el)
            self.editor_open_on = obj
            self.java_lines.append("actions.doubleClick(cell).perform();   // %s" % obj)
            return "ok", {"editing": obj}
        res = self._click_by_text(obj)
        if not res["ok"]:
            return "failed", res
        return "ok", res

    def _do_fill(self, step, n):
        text = step.value or ""
        obj = (step.object or "").strip()
        if not text:
            return "failed", {"reason": "nothing to type"}

        if self.editor_open_on is not None:
            target = self.editor_open_on
            _, near, _ = self._resolve_object(target)
            res = drawio_ops.type_into_open_editor(self.driver, text, near=near)
            self.editor_open_on = None
            self.java_lines.append('actions.sendKeys("%s").perform();   // into %s'
                                   % (text, target))
            return ("ok" if res["ok"] else "failed"), {"target": target, **res}

        el, info, kind = self._resolve_object(obj)
        if kind in ("created", "connector") and el is not None:
            res = drawio_ops.label_cell(self.driver, el, text)
            self.java_lines.append('actions.doubleClick(cell).sendKeys("%s").perform();' % text)
            return ("ok" if res["ok"] else "failed"), res
        return "failed", {"reason": "no editor open and no resolvable target for %r" % obj}

    def _do_move(self, step, n):
        obj = (step.object or "").strip()
        el, info, kind = self._resolve_object(obj)
        if el is None:
            return "failed", {"reason": "unknown reference %r" % obj}
        # Measure the displacement against the other shapes on the canvas rather
        # than against the cell's own earlier coordinates. draw.io re-anchors the
        # whole view when the canvas grows, which moves every reported coordinate
        # together; a self-comparison then reads that shift as movement — a 150px
        # nudge was recorded as +950 in the wrong direction. A difference of
        # differences cancels it.
        m = CREATED_RE.search(obj)
        moved_step = int(m.group(1)) if m else None
        before = self._positions()
        drawio_ops.move_cell(self.driver, el, step.value or "", measure=False)
        after = self._positions()
        res = self._displacement(moved_step, before, after, step.value or "")
        if res.get("ok") and moved_step is not None:
            px, py = self.displacement.get(moved_step, (0, 0))
            self.displacement[moved_step] = (px + res["dx"], py + res["dy"])
        self.java_lines.append(
            "for (int i = 0; i < %d; i++) { actions.keyDown(Keys.SHIFT)"
            ".sendKeys(Keys.ARROW_%s).keyUp(Keys.SHIFT).perform(); }"
            % (drawio_ops.MOVE_STEP_PX // drawio_ops.PX_PER_ARROW_PRESS,
               (step.value or "down").upper()))
        return ("ok" if res["ok"] else "failed"), res

    def _do_connect(self, step, n):
        src_txt = (step.object or "").strip()
        dst_txt = (step.related_object or "").strip()
        src_el, _, _ = self._resolve_object(src_txt)
        dst_el, _, _ = self._resolve_object(dst_txt)
        if src_el is None or dst_el is None:
            return "failed", {"reason": "unresolved endpoints",
                              "src": src_txt, "dst": dst_txt}
        known = drawio_ops.known_cells(self.driver)
        res = drawio_ops.connect_cells(self.driver, src_el, dst_el)
        if res["ok"]:
            a = CREATED_RE.search(src_txt)
            b = CREATED_RE.search(dst_txt)
            if a and b:
                self.tracker.record_connector(int(a.group(1)), int(b.group(1)), known)
        self.java_lines.append("actions.clickAndHold(src).moveToElement(dst).release().perform();")
        return ("ok" if res["ok"] else "failed"), res

    def _do_resize(self, step, n, grow: bool):
        """Grow or shrink a shape along one edge.

        draw.io resizes the selection with Ctrl+Arrow, by the same 10px grid the
        plain arrows move it on. The old corpus uses "extend"/"shrink" in a
        handful of scenarios (scenario_051 among them); without a handler those
        steps were reported as unsupported.
        """
        obj = (step.object or "").strip()
        el, info, kind = self._resolve_object(obj)
        if el is None:
            return "failed", {"reason": "unknown reference %r" % obj}
        direction = (step.value or "").lower()
        key = drawio_ops._ARROW.get(direction)
        if key is None:
            return "failed", {"reason": "unknown direction %r" % step.value}
        # Shrinking is the same gesture towards the opposite side.
        if not grow:
            opposite = {"left": "right", "right": "left", "up": "down", "top": "down",
                        "down": "up", "bottom": "up"}
            key = drawio_ops._ARROW[opposite[direction]]
        before = drawio_ops._info_of(self.driver, el)
        drawio_ops.select_cell(self.driver, el)
        presses = drawio_ops.MOVE_STEP_PX // drawio_ops.PX_PER_ARROW_PRESS
        for _ in range(presses):
            (ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(key)
             .key_up(Keys.CONTROL).perform())
            time.sleep(0.02)
        time.sleep(0.5)
        after = drawio_ops._info_of(self.driver, el)
        if before is None or after is None:
            return "failed", {"reason": "cell not measurable"}
        dw, dh = after["w"] - before["w"], after["h"] - before["h"]
        self.java_lines.append(
            "for (int i = 0; i < %d; i++) { actions.keyDown(Keys.CONTROL)"
            ".sendKeys(Keys.ARROW_%s).keyUp(Keys.CONTROL).perform(); }"
            % (presses, direction.upper()))
        return ("ok" if (abs(dw) + abs(dh)) > 0 else "failed"), {"dw": dw, "dh": dh}

    def _do_extend(self, step, n):
        return self._do_resize(step, n, grow=True)

    def _do_shrink(self, step, n):
        return self._do_resize(step, n, grow=False)

    def _do_delete(self, step, n):
        el, _, kind = self._resolve_object((step.object or "").strip())
        if el is None:
            return "failed", {"reason": "unknown reference"}
        drawio_ops.select_cell(self.driver, el)
        ActionChains(self.driver).send_keys(Keys.DELETE).perform()
        time.sleep(0.6)
        self.java_lines.append("actions.sendKeys(Keys.DELETE).perform();")
        return "ok", {}

    def _do_press(self, step, n):
        key_map = {"esc": Keys.ESCAPE, "escape": Keys.ESCAPE, "enter": Keys.ENTER,
                   "tab": Keys.TAB, "space": Keys.SPACE, "delete": Keys.DELETE}
        key = key_map.get((step.value or "").lower())
        if key is None:
            return "failed", {"reason": "unsupported key %r" % step.value}
        ActionChains(self.driver).send_keys(key).perform()
        time.sleep(0.4)
        self.java_lines.append("actions.sendKeys(Keys.%s).perform();" % (step.value or "").upper())
        return "ok", {}

    _HANDLERS = {
        "open": _do_open,
        "click": _do_click,
        "double click": _do_double_click,
        "fill": _do_fill,
        "enter": _do_fill,
        "move": _do_move,
        "connect": _do_connect,
        "link": _do_connect,
        "delete": _do_delete,
        "remove": _do_delete,
        "extend": _do_extend,
        "scale up": _do_extend,
        "shrink": _do_shrink,
        "scale down": _do_shrink,
        "press": _do_press,
    }

    # -------------------------------------------------------------------- run
    def run(self, descriptions: list, parser) -> dict:
        """Execute a scenario's descriptions in order.

        ``descriptions`` keeps its original indexing: entry i is step i+1, which
        is what "the element created in step N" refers to.
        """
        results = []
        t0 = time.time()
        for i, desc in enumerate(descriptions):
            n = i + 1
            try:
                step = parser.process_step(desc)
            except Exception as exc:
                results.append(StepResult(n, desc, status="parse_error",
                                          detail={"error": repr(exc)}))
                continue
            if step is None:
                results.append(StepResult(n, desc, status="unparsed"))
                continue

            action = (step.action or "").lower().strip()
            handler = self._HANDLERS.get(action)
            if handler is None:
                results.append(StepResult(n, desc, action, "unsupported",
                                          {"reason": "no handler for %r" % action}))
                continue

            t = time.time()
            try:
                status, detail = handler(self, step, n)
            except Exception as exc:
                status, detail = "error", {"error": "%s: %s" % (type(exc).__name__, exc),
                                           "traceback": traceback.format_exc(limit=4)}
            detail = dict(detail or {})
            detail["seconds"] = round(time.time() - t, 2)
            results.append(StepResult(n, desc, action, status, detail))
            self.log("[step %d/%d] %-12s %-8s %s"
                     % (n, len(descriptions), action, status, desc[:60]))

        cells = cell_tracker.cell_info(self.driver)
        labels = cell_tracker.canvas_labels(self.driver)
        counted = {"ok": 0, "failed": 0, "error": 0, "unparsed": 0,
                   "unsupported": 0, "parse_error": 0, "skipped": 0}
        for r in results:
            counted[r["status"]] = counted.get(r["status"], 0) + 1
        return {
            "steps": results,
            "counts": counted,
            "step_success_rate": round(counted["ok"] / len(results), 4) if results else 0.0,
            "total_sec": round(time.time() - t0, 1),
            "cells": cells,
            "n_vertices": sum(1 for c in cells if c["kind"] != "edge"),
            "n_edges": sum(1 for c in cells if c["kind"] == "edge"),
            "labels": [l["text"] for l in labels],
        }

    def java_script(self) -> str:
        head = [
            "import org.openqa.selenium.*;",
            "import org.openqa.selenium.interactions.Actions;",
            "",
            "public class GeneratedTest {",
            "    public static void main(String[] args) {",
            "        WebDriver driver = new ChromeDriver();",
            "        Actions actions = new Actions(driver);",
            "",
        ]
        body = ["        " + line for line in self.java_lines]
        tail = ["", "        driver.quit();", "    }", "}"]
        return "\n".join(head + body + tail)
