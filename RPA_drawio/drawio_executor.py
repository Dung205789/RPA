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
            for cand in match["ranked"][:2]:
                known = drawio_ops.known_cells(self.driver)
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
                if created:
                    self.tracker.record_created(n, known)
                if res.get("ok"):
                    self.java_lines.append("// click %s (%s, score %.2f)"
                                           % (obj, cand["tag"], cand["score"]))
                    return "ok", {"score": cand["score"], "palette": cand["palette"],
                                  "title": cand["title"] or cand["text"],
                                  "created_cell": created}
                self.log("[click] candidate %s failed, trying next" % cand["tag"])
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
        # Re-resolve through the tracker afterwards rather than comparing raw
        # handles: draw.io sometimes rebuilds a cell's node when it scrolls back
        # into view, and the tracker's position fallback recovers from that. The
        # first version compared handles directly and reported "cell disappeared
        # during move" for a shape that was plainly still on the canvas.
        before = dict(info)
        res = drawio_ops.move_cell(self.driver, el, step.value or "", measure=False)
        after_el, after = self._resolve_object(obj)[0], self._resolve_object(obj)[1]
        if after is None:
            res = {"ok": False, "reason": "cell not recoverable after move"}
        else:
            dx, dy = after["mx"] - before["mx"], after["my"] - before["my"]
            res = {"ok": (abs(dx) + abs(dy)) >= drawio_ops.MOVE_STEP_PX // 2,
                   "dx": dx, "dy": dy, "wanted": drawio_ops.MOVE_STEP_PX}
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
