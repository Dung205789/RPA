#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""External harness for documents/RPA_drawio — added 2026-09-02, not part of the
original repo, does not modify any of its files.

Loops over scenario JSON files (RPA_Datasets format: {"id","url","descriptions",
"assets"}) and drives them through the *unmodified* RPA_drawio pipeline
(StepParser -> Generator.generate_script_with_steps), the same call sequence
generator.py's own __main__ demo uses. Results go to documents/result/<batch>/.

Prerequisite: Chrome must already be running with
  --remote-debugging-port=9222 --user-data-dir=C:\\selenium\\ChromeProfile
(generate_script_with_steps connects via use_existing=True; it does not launch
its own browser). Also must run with the RPA_drawio venv (documents/RPA_drawio/venv_rpa).

Usage:
  python run_rpa_drawio_batch.py --scenarios "RPA_Datasets/data/drawio/*.json" --out result/rpa_datasets_run --limit 5
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


def resolve_asset_refs(descriptions: list[str], assets: dict, dataset_root: Path) -> list[str]:
    """Replace `[assetname]` with `[absolute\\path\\to\\file]` using the scenario's
    own "assets" map. The stock RPA_drawio code has no assets-lookup of its own —
    it only knows how to treat a bracketed [png/jpg path] as a literal file path or
    URL (find_element.is_image_input + by_image.process_url_with_image) — so this
    substitution belongs in the harness, not in RPA_drawio's files.
    """
    out = []
    for desc in descriptions:
        def _sub(m):
            name = m.group(1)
            asset = assets.get(name)
            if asset and asset.get("path"):
                abs_path = str((dataset_root / asset["path"]).resolve())
                return f"[{abs_path}]"
            return m.group(0)  # not an asset ref (e.g. a URL already in brackets) — leave as-is
        out.append(BRACKET_RE.sub(_sub, desc))
    return out


def load_scenario(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def capture_screenshot(case_dir: Path) -> str | None:
    """Attach a short-lived Selenium session to the already-running Chrome (same
    debug port Generator used) purely to screenshot the current canvas state,
    then quit that session. Quitting an *attached* (use_existing=True) session
    does not close the real browser window — Selenium only ends the automation
    session it created, not a browser it didn't launch — so this never
    interferes with the next scenario's own attach.
    """
    import by_text
    try:
        shot_driver = by_text.setup_chrome_driver(use_existing=True)
        try:
            path = str(case_dir / "after.png")
            shot_driver.save_screenshot(path)
            return path
        finally:
            shot_driver.quit()
    except Exception as exc:
        (case_dir / "screenshot_error.txt").write_text(f"{type(exc).__name__}: {exc}", encoding="utf-8")
        return None


def run_one(parser, scenario_path: Path, dataset_root: Path, out_dir: Path) -> dict:
    from generator import Generator  # imported lazily so --help works without the venv

    scenario = load_scenario(scenario_path)
    sid = scenario.get("id", scenario_path.stem)
    url = scenario["url"]
    descriptions = resolve_asset_refs(scenario.get("descriptions", []), scenario.get("assets", {}), dataset_root)

    steps = []
    unparsed = []
    for d in descriptions:
        step = parser.process_step(d)
        if step is None:
            unparsed.append(d)
        else:
            steps.append(step)

    row = {"id": sid, "n_descriptions": len(descriptions), "n_unparsed": len(unparsed),
           "unparsed": unparsed, "status": "error", "error": None,
           "n_steps_attempted": len(steps), "total_sec": None}

    case_dir = out_dir / sid
    case_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    try:
        gen = Generator()
        full_script, step_codes = gen.generate_script_with_steps(url, steps)
        row["total_sec"] = round(time.time() - t0, 1)
        row["status"] = "ok"
        row["n_step_codes"] = len(step_codes)
        (case_dir / "GeneratedTest.java").write_text(full_script, encoding="utf-8")
        (case_dir / "step_codes.json").write_text(
            json.dumps(step_codes, ensure_ascii=False, indent=2), encoding="utf-8")
        (case_dir / "steps_info.json").write_text(
            json.dumps(gen.steps_info, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    except Exception as exc:  # one bad scenario must not kill the whole batch
        row["total_sec"] = round(time.time() - t0, 1)
        row["status"] = "exception"
        row["error"] = f"{type(exc).__name__}: {exc}"
        (case_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")

    row["screenshot"] = capture_screenshot(case_dir)  # taken before moving to the next scenario, either outcome

    (case_dir / "scenario_input.json").write_text(
        json.dumps({"id": sid, "url": url, "descriptions": descriptions}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", required=True,
                    help="glob pattern for scenario json files, e.g. RPA_Datasets/data/drawio/*.json")
    ap.add_argument("--dataset-root", default=str(RPA_DATASETS_DIR),
                    help="root that scenario 'assets[*].path' is relative to")
    ap.add_argument("--out", required=True, help="output dir, relative to documents/")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    os.chdir(RPA_DRAWIO_DIR)  # StepParser/action_matcher/by_text model paths are cwd-relative
    sys.path.insert(0, str(RPA_DRAWIO_DIR))

    from step_parser import StepParser
    print(f"[harness] loading StepParser (stanza + action-matcher model, one-time)...", file=sys.stderr)
    parser = StepParser()

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
        print(f"[harness] no scenarios matched {pattern!r}", file=sys.stderr)
        return 1

    rows = []
    for i, p in enumerate(paths, 1):
        print(f"[harness] [{i}/{len(paths)}] {p.name}", file=sys.stderr)
        try:
            row = run_one(parser, p, dataset_root, out_dir)
        except Exception as exc:  # scenario-file-level failure (bad json etc.)
            row = {"id": p.stem, "status": "harness_error", "error": f"{type(exc).__name__}: {exc}"}
            traceback.print_exc(file=sys.stderr)
        print(f"[harness]   -> {row['status']}"
              + (f" ({row.get('error')})" if row.get("error") else ""), file=sys.stderr)
        rows.append(row)

    summary = {
        "n_total": len(rows),
        "n_ok": sum(1 for r in rows if r["status"] == "ok"),
        "n_exception": sum(1 for r in rows if r["status"] == "exception"),
        "n_harness_error": sum(1 for r in rows if r["status"] == "harness_error"),
        "rows": rows,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
