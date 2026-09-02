#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert 30 SVG_agent data/datasets cases (10 easy/10 medium/10 hard, the same
sample as data/benchmarks/supervisor_check30) into RPA_Datasets-style scenario
JSON ({"id","url","descriptions","assets"}), so the OLD RPA_drawio executor can
attempt them, to test its compatibility with the NEW dataset.

"Few-shot image -> structured spec" step: reused, not re-implemented. SVG_agent's
own src/understand/constraints.parse_task() already did this exact VLM parse for
these 30 cases during the supervisor_check30 benchmark run (results/drawio/<id>_NL/
result.json: spec_from_llm.shapes + .constraints, plan with laid-out cx/cy). This
script only adds a NEW, deterministic translation from that spec to the
RPA_Datasets step-description DSL (click shape icon -> nudge into place -> label
-> connect) — it does not call an LLM again and does not touch RPA_drawio itself.

Known approximation (documented, not hidden): one "Move <dir>" step in RPA_drawio
is 15x Shift+Arrow key presses (generator.py execute_python_action), a sizeable
jump whose exact px/step was never fixed by the original authors. We use 100px
per step as a rough calibration (SVG_agent's canvas is ~1200x800) — this recreates
*relative* placement, not pixel-exact position; that limitation is reported, not
silently absorbed into the numbers.

Icon coverage gap (also reported): RPA_Datasets/images/drawio only ships icons for
{ellipse, rectangle, diamond, parallelogram}. New-dataset shapes outside that set
(rounded rectangle, hexagon, trapezoid, document, cylinder) are mapped to the
closest available icon (rounded rectangle -> rectangle.png) or, where there is no
reasonable match (hexagon/trapezoid/document/cylinder), left mapped to
rectangle.png and flagged in the scenario's "_unsupported_shapes" field.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SVG_AGENT_DIR = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = Path(__file__).resolve().parent
RPA_DATASETS_DIR = DOCUMENTS_DIR / "RPA_Datasets"
ICONS_DIR = RPA_DATASETS_DIR / "images" / "drawio"

MANIFEST = SVG_AGENT_DIR / "data" / "benchmarks" / "supervisor_check30" / "manifest.json"
RESULTS_DIR = SVG_AGENT_DIR / "results" / "drawio"

SHAPE_TO_ICON = {
    "ellipse": "ellipse.png",
    "rectangle": "rectangle.png",
    "rounded rectangle": "rectangle.png",
    "diamond": "diamond.png",
    "parallelogram": "parallelogram.png",
}
UNSUPPORTED_FALLBACK = "rectangle.png"  # hexagon/trapezoid/document/cylinder: no matching icon shipped

PX_PER_MOVE_STEP = 100
MAX_MOVE_STEPS_PER_AXIS = 8
DRAWIO_URL = "https://app.diagrams.net/"


def load_spec_and_plan(case_id: str) -> tuple[dict, list[dict]]:
    result_path = RESULTS_DIR / f"{case_id}_NL" / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    return result["spec_from_llm"], result["plan"]


def move_steps_for_delta(dx: float, dy: float, created_step: int) -> list[str]:
    """Bug fixed 2026-09-02: every RPA_Datasets "Move" step names WHICH element
    to move — "Move the element created in step N <dir>" (see scenario_050.json
    steps 5-19) — a bare "Move down" has no subject and never matches the click
    step. The earlier version emitted bare direction words, so
    step_created_elements[N] was never populated for N = one of these dangling
    Move steps, and every later "Fill"/"Connect" that referenced that N (itself
    miscomputed as the last Move step's index, not the Click step's) failed
    with NoSuchElementException. Both mistakes are fixed here.
    """
    steps = []
    n_x = min(MAX_MOVE_STEPS_PER_AXIS, round(abs(dx) / PX_PER_MOVE_STEP))
    n_y = min(MAX_MOVE_STEPS_PER_AXIS, round(abs(dy) / PX_PER_MOVE_STEP))
    direction_x = "right" if dx > 0 else "left"
    direction_y = "down" if dy > 0 else "up"
    steps += [f"Move the element created in step {created_step} {direction_x}"] * n_x
    steps += [f"Move the element created in step {created_step} {direction_y}"] * n_y
    return steps


def build_scenario(case_id: str) -> dict:
    spec, plan = load_spec_and_plan(case_id)
    shapes_by_id = {s["id"]: s for s in spec["shapes"]}
    plan_by_id = {p["id"]: p for p in plan}

    order = [p["id"] for p in plan]  # drawing order = layout/executor order
    descriptions = [f'Open "{DRAWIO_URL}"']
    assets: dict[str, dict] = {}
    unsupported = []
    step_of_shape: dict[str, int] = {}
    prev_cx, prev_cy = None, None

    for shape_id in order:
        shape = shapes_by_id[shape_id]
        p = plan_by_id[shape_id]
        shape_type = shape["type"]
        icon = SHAPE_TO_ICON.get(shape_type)
        if icon is None:
            icon = UNSUPPORTED_FALLBACK
            unsupported.append({"id": shape_id, "type": shape_type})
        asset_name = icon  # shared icon reused across shapes of the same type; fine, find_element re-resolves by name each step
        assets[asset_name] = {"type": "image", "path": str((ICONS_DIR / icon).resolve())}

        descriptions.append(f"Click on [{asset_name}]")
        step_num = len(descriptions)  # the CLICK step — every later reference to this shape uses this index
        step_of_shape[shape_id] = step_num

        cx, cy = p["cx"], p["cy"]
        if prev_cx is not None:
            descriptions.extend(move_steps_for_delta(cx - prev_cx, cy - prev_cy, step_num))
        prev_cx, prev_cy = cx, cy

        if shape.get("label"):
            descriptions.append(f"Double click on the element created in step {step_num}")
            descriptions.append(f'Fill "{shape["label"]}" into the element created in step {step_num}')

    for c in spec.get("constraints", []):
        if c.get("type") != "connect":
            continue
        a_step, b_step = step_of_shape.get(c["a"]), step_of_shape.get(c["b"])
        if a_step is None or b_step is None:
            continue
        descriptions.append(
            f"Connect the element created in step {a_step} to the element created in step {b_step}")
        if c.get("label"):
            descriptions.append(f"Double click on connector_from_step{a_step}_to_step{b_step}")
            descriptions.append(f'Fill "{c["label"]}"')

    scenario = {
        "id": case_id,
        "url": DRAWIO_URL,
        "environment": {"theme": "light"},
        "descriptions": descriptions,
        "assets": assets,
        "_source": "SVG_agent data/datasets, converted via existing VLM parse (src/understand/constraints.parse_task) + new deterministic step translator",
        "_unsupported_shapes": unsupported,
    }
    return scenario


def main(argv=None):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out_dir = DOCUMENTS_DIR / "RPA_Datasets_new30"
    out_dir.mkdir(parents=True, exist_ok=True)

    ok, failed = 0, []
    for case in manifest["cases"]:
        case_id = case["id"]
        try:
            scenario = build_scenario(case_id)
        except Exception as exc:
            failed.append({"id": case_id, "error": f"{type(exc).__name__}: {exc}"})
            continue
        (out_dir / f"{case_id}.json").write_text(
            json.dumps(scenario, ensure_ascii=False, indent=2), encoding="utf-8")
        ok += 1

    print(json.dumps({"n_total": len(manifest["cases"]), "n_ok": ok, "failed": failed}, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
