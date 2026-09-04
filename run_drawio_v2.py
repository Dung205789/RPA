#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch runner for the repaired draw.io RPA path.

Added 2026-09-03, alongside the original run_rpa_drawio_batch.py rather than
replacing it, so the "old code, old dataset" baseline stays reproducible.

Differences from the original harness, all of them consequences of what the
baseline runs turned out to be measuring:

* It owns its browser. The old harness required a Chrome the operator had already
  started; that Chrome was reporting the page hidden, so draw.io never drew its
  shape palette and every image lookup searched a page that had no shapes on it.
* It records a per-step outcome. The old summary's "ok" only meant the scenario
  raised no exception at harness level — 89 of 100 old cases and 23 of 30 new
  ones were "ok" with near-empty canvases.
* It resets the editor between cases, so one scenario's leftovers cannot be
  counted as the next one's work.

Usage:
  python run_drawio_v2.py --scenarios "RPA_Datasets_new30_v2/*.json" \
      --dataset-root RPA_Datasets --out result/new30_v2 [--limit N] [--port 9222]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).resolve().parent
RPA_DRAWIO_DIR = DOCUMENTS_DIR / "RPA_drawio"
RPA_DATASETS_DIR = DOCUMENTS_DIR / "RPA_Datasets"

BRACKET_RE = re.compile(r"\[(.*?)\]")


def log(*args):
    print(*args, file=sys.stderr, flush=True)


def resolve_asset_refs(descriptions, assets, dataset_root: Path):
    """Replace ``[assetname]`` with the absolute path the scenario's own assets
    map points at. The executor only knows how to treat a bracketed image path as
    a file, so this substitution belongs in the harness."""
    out = []
    for desc in descriptions:
        def _sub(m):
            name = m.group(1)
            asset = assets.get(name)
            if asset and asset.get("path"):
                p = Path(asset["path"])
                if not p.is_absolute():
                    p = dataset_root / p
                return "[%s]" % p
            return m.group(0)
        out.append(BRACKET_RE.sub(_sub, desc))
    return out


def crop_to_canvas(driver, full_png: Path, out_png: Path):
    """Cut the drawing area out of a full-window screenshot."""
    from PIL import Image
    rect = driver.execute_script("""
    const c = document.querySelector('.geDiagramContainer');
    if (!c) return null;
    const r = c.getBoundingClientRect();
    return {x: r.x, y: r.y, w: r.width, h: r.height, dpr: window.devicePixelRatio || 1,
            iw: window.innerWidth};
    """)
    if not rect:
        return None
    img = Image.open(full_png)
    scale = img.width / float(rect["iw"]) if rect["iw"] else 1.0
    box = (int(rect["x"] * scale), int(rect["y"] * scale),
           int((rect["x"] + rect["w"]) * scale), int((rect["y"] + rect["h"]) * scale))
    img.crop(box).save(out_png)
    return out_png


_DEAD_SESSION = ("invalid session id", "chrome not reachable", "no such window",
                 "disconnected", "target window already closed",
                 "unable to connect to renderer", "session deleted")


def session_is_dead(exc: Exception) -> bool:
    """Did the browser go away, as opposed to this scenario failing?"""
    text = ("%s %s" % (type(exc).__name__, exc)).lower()
    return any(marker in text for marker in _DEAD_SESSION)


def restart_browser(port: int, log=print):
    """Bring up a fresh Chrome and attach to it.

    A batch has to survive the browser dying. On the first full run of the old
    corpus Chrome went away during scenario_046 and every one of the 55 scenarios
    after it failed instantly on `invalid session id` — 55 cases lost to one
    crash. Detecting that and starting over costs a minute; not detecting it costs
    the rest of the run.
    """
    import by_text
    import rpa_env
    rpa_env.kill_chrome_on_port(port)
    time.sleep(2)
    rpa_env.launch_chrome(port=port)
    if not rpa_env.wait_for_debug_port(port):
        raise RuntimeError("Chrome did not come back up on port %d" % port)
    log("[harness] browser restarted on port %d" % port)
    return by_text.setup_chrome_driver(use_existing=True)


def run_one(executor_cls, driver, parser, scenario_path: Path, dataset_root: Path,
            out_dir: Path) -> dict:
    import cell_tracker

    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    sid = scenario.get("id", scenario_path.stem)
    descriptions = resolve_asset_refs(scenario.get("descriptions", []),
                                      scenario.get("assets", {}), dataset_root)

    case_dir = out_dir / sid
    case_dir.mkdir(parents=True, exist_ok=True)

    ex = executor_cls(driver, log=log)
    t0 = time.time()
    try:
        report = ex.run(descriptions, parser)
        status = "ran"
        error = None
    except Exception as exc:
        report = {"steps": [], "counts": {}, "step_success_rate": 0.0}
        status = "exception"
        error = "%s: %s" % (type(exc).__name__, exc)
        (case_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")

    shot = case_dir / "after.png"
    canvas_shot = None
    try:
        import rpa_env
        rpa_env.settle_for_screenshot(driver)
        rpa_env.fit_page(driver)
        rpa_env.settle_for_screenshot(driver)
        driver.save_screenshot(str(shot))
        # A second image cropped to the drawing area alone. The judge compares it
        # against a reference that is only a diagram, and a full editor screenshot
        # hands it a shape palette, a toolbar and a format panel to explain away.
        canvas_shot = crop_to_canvas(driver, shot, case_dir / "canvas.png")
    except Exception as exc:
        (case_dir / "screenshot_error.txt").write_text(repr(exc), encoding="utf-8")
        shot = None

    (case_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (case_dir / "GeneratedTest.java").write_text(ex.java_script(), encoding="utf-8")
    (case_dir / "scenario_input.json").write_text(
        json.dumps({"id": sid, "descriptions": descriptions}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    counts = report.get("counts", {})
    return {
        "id": sid,
        "status": status,
        "error": error,
        "n_steps": len(descriptions),
        "n_ok": counts.get("ok", 0),
        "n_failed": counts.get("failed", 0) + counts.get("error", 0),
        "n_unparsed": counts.get("unparsed", 0) + counts.get("parse_error", 0),
        "step_success_rate": report.get("step_success_rate", 0.0),
        "n_vertices": report.get("n_vertices"),
        "n_edges": report.get("n_edges"),
        "labels": report.get("labels"),
        "total_sec": round(time.time() - t0, 1),
        "screenshot": str(shot) if shot else None,
        "canvas": str(canvas_shot) if canvas_shot else None,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--dataset-root", default=str(RPA_DATASETS_DIR))
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--port", type=int, default=9222,
                    help="debugging port for this worker's own Chrome")
    ap.add_argument("--keep-browser", action="store_true",
                    help="leave Chrome running afterwards, for inspection")
    args = ap.parse_args(argv)

    os.chdir(RPA_DRAWIO_DIR)          # stanza / sentence-transformers paths are cwd-relative
    sys.path.insert(0, str(RPA_DRAWIO_DIR))
    os.environ["RPA_CHROME_DEBUG_PORT"] = str(args.port)

    import rpa_env
    import by_text
    from drawio_executor import DrawioExecutor
    from step_parser import StepParser

    dataset_root = Path(args.dataset_root)
    if not dataset_root.is_absolute():
        dataset_root = DOCUMENTS_DIR / dataset_root
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = DOCUMENTS_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pattern = args.scenarios
    if not Path(pattern).is_absolute():
        pattern = str(DOCUMENTS_DIR / pattern)
    paths = sorted(Path(p) for p in glob.glob(pattern))
    if args.limit:
        paths = paths[: args.limit]
    if not paths:
        log("[harness] no scenarios matched %r" % pattern)
        return 1

    log("[harness] loading StepParser (stanza + action matcher, one-time)...")
    parser = StepParser()

    log("[harness] starting Chrome on port %d" % args.port)
    rpa_env.launch_chrome(port=args.port)
    if not rpa_env.wait_for_debug_port(args.port):
        log("[harness] Chrome debugging port never came up")
        return 2
    driver = by_text.setup_chrome_driver(use_existing=True)

    rows = []
    try:
        for i, p in enumerate(paths, 1):
            log("[harness] [%d/%d] %s" % (i, len(paths), p.name))
            try:
                row = run_one(DrawioExecutor, driver, parser, p, dataset_root, out_dir)
            except Exception as exc:
                row = {"id": p.stem, "status": "harness_error",
                       "error": "%s: %s" % (type(exc).__name__, exc)}
                traceback.print_exc(file=sys.stderr)

            # A dead browser is not this scenario's failure, it is the end of every
            # scenario after it unless the batch restarts. Retry the case once on a
            # fresh browser, so a crash costs one case instead of the rest of the run.
            died = row.get("status") in ("exception", "harness_error") and any(
                m in (row.get("error") or "").lower() for m in _DEAD_SESSION)
            if died:
                log("[harness]   browser died; restarting and retrying %s" % p.name)
                try:
                    driver = restart_browser(args.port, log=log)
                    row = run_one(DrawioExecutor, driver, parser, p, dataset_root, out_dir)
                except Exception as exc:
                    row = {"id": p.stem, "status": "harness_error",
                           "error": "restart failed: %s: %s" % (type(exc).__name__, exc)}
            log("[harness]   -> %s  steps %s/%s ok  vertices=%s edges=%s  %ss"
                % (row.get("status"), row.get("n_ok"), row.get("n_steps"),
                   row.get("n_vertices"), row.get("n_edges"), row.get("total_sec")))
            rows.append(row)
            (out_dir / "summary.json").write_text(
                json.dumps(_summarize(rows), ensure_ascii=False, indent=2),
                encoding="utf-8")
    finally:
        if not args.keep_browser:
            try:
                driver.quit()
            except Exception:
                pass
            rpa_env.kill_chrome_on_port(args.port)

    summary = _summarize(rows)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"},
                     ensure_ascii=False, indent=2))
    return 0


def _summarize(rows):
    done = [r for r in rows if r.get("n_steps")]
    total_steps = sum(r["n_steps"] for r in done)
    total_ok = sum(r["n_ok"] for r in done)
    return {
        "n_cases": len(rows),
        "n_ran": sum(1 for r in rows if r.get("status") == "ran"),
        "n_exception": sum(1 for r in rows if r.get("status") in ("exception", "harness_error")),
        "steps_total": total_steps,
        "steps_ok": total_ok,
        "step_success_rate": round(total_ok / total_steps, 4) if total_steps else 0.0,
        "cases_with_any_edge": sum(1 for r in done if (r.get("n_edges") or 0) > 0),
        "rows": rows,
    }


if __name__ == "__main__":
    raise SystemExit(main())
