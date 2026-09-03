#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turn a flowchart image into an RPA_Datasets-format scenario.

Added 2026-09-03. This is the bridge between the new image benchmark and the
step-description language the RPA executor already speaks.

Two stages, deliberately split:

  1. **Read the picture (VLM).** One call, few-shot, returns a small structured
     graph: nodes with a shape type, a label and a normalised position, plus
     edges with optional labels. Nothing about draw.io or about step numbering.
  2. **Write the scenario (deterministic).** Python turns that graph into the
     exact step vocabulary of RPA_Datasets/data/drawio, following
     scenario_050.json phase for phase: insert every shape and nudge it into
     place, then label every shape, then draw and label every connector.

The split is the point. The DSL's hard part is bookkeeping — every later step
refers to a shape as "the element created in step N", and N is a 1-based index
into the very list being built. A model asked to emit that directly gets the
indices wrong; a model asked only to read the picture does not have to.

**No leakage.** The only input is the PNG. The benchmark's answer keys
(`*.png.graph.json`) and its source `*.xml` are never opened — not by this file
and not by anything it calls. Nothing here is conditioned on a case id.

Two facts about draw.io drive the geometry, both measured (see drawio_ops):
  * a click-inserted shape always lands at the centre of the current view, so
    every shape starts at the *same* point and all placement is expressed as
    moves away from it. The first conversion assumed each shape started where the
    previous one had ended, which stacked five of a chain's shapes on one spot.
  * one "Move" step is MOVE_STEP_PX (150) model pixels, so positions quantise to
    a 150px grid.

Usage:
    python image_to_scenario.py --images "D:/SVG_agent/data/datasets/easy/*.png" \\
        --out ../RPA_Datasets_new30_v2
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import drawio_ops
from llm_client import LLMClient, extract_json, load_env

HERE = Path(__file__).resolve().parent
ICON_DIR = HERE / "shape_icons"
DRAWIO_URL = "https://app.diagrams.net/"

# The shape vocabulary, and the icon that draws each one. Built by
# build_shape_icons.py straight from draw.io's own shape search, so every entry
# is verified to insert the shape it names.
# Known substitution: "rounded rectangle" is drawn with the plain rectangle icon.
# draw.io puts the two side by side in the General palette and they differ by a
# corner radius of a few pixels; at thumbnail size their ink masks are 97%
# identical, so no icon-based selection can separate them, and every alternative
# the shape search offers is a different shape (a double-bordered frame, a
# document). It is recorded per scenario in "_shape_substitutions" rather than
# hidden, because it costs shape-type accuracy on 949 of the benchmark's 3516
# nodes and the reader should see that in the numbers.
SHAPE_SUBSTITUTIONS = {"rounded rectangle": "rectangle"}

SHAPE_ICONS = {
    "rectangle": "rectangle.png",
    "rounded rectangle": "rectangle.png",
    "ellipse": "ellipse.png",
    "diamond": "diamond.png",
    "parallelogram": "parallelogram.png",
    "hexagon": "hexagon.png",
    "trapezoid": "trapezoid.png",
    "document": "document.png",
    "cylinder": "cylinder.png",
}

# Placement constants. A move is 150px, so neighbours have to be at least a
# couple of moves apart or they quantise onto the same cell of the grid.
TARGET_MIN_SEP_PX = 1.7 * drawio_ops.MOVE_STEP_PX
MAX_SPAN_PX = 2400
MAX_MOVES_PER_AXIS = 10


PROMPT = """You are reading a flowchart image and describing it as data.

Return ONE JSON object, nothing else:

{
  "nodes": [
    {"id": "n1", "type": "<shape type>", "label": "<exact text in the shape>",
     "x": <0..1>, "y": <0..1>}
  ],
  "edges": [
    {"from": "<node id>", "to": "<node id>", "label": "<text on the arrow, or null>"}
  ]
}

Rules:
- "type" MUST be one of: rectangle, rounded rectangle, ellipse, diamond,
  parallelogram, hexagon, trapezoid, document, cylinder.
  Judge it from the outline only, never from what the text says:
  a four-corner box with rounded corners is "rounded rectangle"; with square
  corners it is "rectangle"; a slanted box is "parallelogram"; a box with two
  slanted sides and parallel top/bottom is "trapezoid"; a six-sided box is
  "hexagon"; a box with a wavy bottom edge is "document"; a can/drum shape is
  "cylinder"; a rotated square standing on a corner is "diamond"; an oval or
  stadium shape is "ellipse".
- "label" is the text inside the shape, transcribed exactly, including any
  question mark. Use "" when a shape has no text.
- "x" and "y" are the CENTRE of the shape as a fraction of the image width and
  height, with (0,0) at the top-left corner. Be precise: these decide the layout.
- "edges" follow the arrowheads: "from" is the tail, "to" is the head. Include
  every arrow, including ones that loop back to an earlier shape or to the same
  shape. "label" is the small text sitting on the arrow (often Yes/No), or null.
- Report exactly what is drawn. Do not add, merge, reorder or tidy anything.

Worked example (for a picture of a five-step chain with one decision):

{
  "nodes": [
    {"id": "n1", "type": "ellipse", "label": "Start", "x": 0.50, "y": 0.08},
    {"id": "n2", "type": "rounded rectangle", "label": "Load the file", "x": 0.50, "y": 0.30},
    {"id": "n3", "type": "diamond", "label": "Valid?", "x": 0.50, "y": 0.54},
    {"id": "n4", "type": "rectangle", "label": "Show an error", "x": 0.18, "y": 0.78},
    {"id": "n5", "type": "ellipse", "label": "Done", "x": 0.50, "y": 0.92}
  ],
  "edges": [
    {"from": "n1", "to": "n2", "label": null},
    {"from": "n2", "to": "n3", "label": null},
    {"from": "n3", "to": "n4", "label": "No"},
    {"from": "n3", "to": "n5", "label": "Yes"},
    {"from": "n4", "to": "n2", "label": null}
  ]
}

Now describe the attached image."""


# ---------------------------------------------------------------- stage 1
def read_image(image_path: str, client: LLMClient, cache_dir: Path | None = None,
               log=print) -> dict:
    """Ask the VLM for the graph in the picture. Cached by file content."""
    raw = Path(image_path).read_bytes()
    digest = hashlib.sha1(raw).hexdigest()[:16]
    cache_file = (cache_dir / ("%s.json" % digest)) if cache_dir else None
    if cache_file and cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    reply = client.vision(PROMPT, image_path)
    graph = extract_json(reply["text"])
    graph["_vlm"] = {"provider": reply["provider"], "model": reply["model"]}
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(graph, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    return graph


# ---------------------------------------------------------------- stage 2
def _pixel_scale(nodes: list) -> float:
    """Pick how many pixels one unit of normalised distance is worth.

    Chosen from the drawing itself: the closest pair of shapes has to end up at
    least ~1.7 move steps apart, or rounding to the 150px move grid collapses
    them onto each other. Capped so a wide chart does not sprawl past the canvas.
    """
    seps = []
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            d = max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))
            if d > 0.02:
                seps.append(d)
    if not seps:
        return 900.0
    scale = TARGET_MIN_SEP_PX / min(seps)
    span = max(
        max(n["x"] for n in nodes) - min(n["x"] for n in nodes),
        max(n["y"] for n in nodes) - min(n["y"] for n in nodes)) or 1.0
    return min(scale, MAX_SPAN_PX / span)


def _moves(delta_px: float) -> int:
    steps = int(round(delta_px / drawio_ops.MOVE_STEP_PX))
    return max(-MAX_MOVES_PER_AXIS, min(MAX_MOVES_PER_AXIS, steps))


def build_scenario(graph: dict, case_id: str, icon_dir: Path = ICON_DIR) -> dict:
    """Translate a graph into the RPA_Datasets step language.

    Phase order follows scenario_050.json exactly: all inserts and moves, then
    all shape labels, then all connectors with their labels.
    """
    nodes = [n for n in graph.get("nodes", []) if n.get("id")]
    if not nodes:
        raise ValueError("no nodes in graph")
    # reading order, so the scenario builds the chart the way a person reads it
    nodes.sort(key=lambda n: (round(float(n.get("y", 0)), 3), float(n.get("x", 0))))

    scale = _pixel_scale(nodes)
    # The shape nearest the middle is the one that stays where draw.io drops it;
    # everything else is expressed as moves from that point, which keeps the
    # finished chart centred and the move counts small.
    cx = sum(float(n["x"]) for n in nodes) / len(nodes)
    cy = sum(float(n["y"]) for n in nodes) / len(nodes)
    anchor = min(nodes, key=lambda n: (float(n["x"]) - cx) ** 2 + (float(n["y"]) - cy) ** 2)

    descriptions = ['Open "%s"' % DRAWIO_URL]
    assets: dict = {}
    step_of: dict = {}
    unknown_types = []
    substituted = []

    # phase 1 - insert and place
    for node in nodes:
        raw_type = str(node.get("type", "")).strip().lower()
        icon = SHAPE_ICONS.get(raw_type)
        if icon is None:
            unknown_types.append({"id": node["id"], "type": node.get("type")})
            icon = SHAPE_ICONS["rectangle"]
        elif raw_type in SHAPE_SUBSTITUTIONS:
            substituted.append({"id": node["id"], "type": raw_type,
                                "drawn_as": SHAPE_SUBSTITUTIONS[raw_type]})
        assets[icon] = {"type": "image", "path": str((icon_dir / icon).resolve())}

        descriptions.append("Click on [%s]" % icon)
        step = len(descriptions)
        step_of[node["id"]] = step

        dx = (float(node["x"]) - float(anchor["x"])) * scale
        dy = (float(node["y"]) - float(anchor["y"])) * scale
        nx, ny = _moves(dx), _moves(dy)
        descriptions += ["Move the element created in step %d %s"
                         % (step, "right" if nx > 0 else "left")] * abs(nx)
        descriptions += ["Move the element created in step %d %s"
                         % (step, "down" if ny > 0 else "up")] * abs(ny)

    # phase 2 - label the shapes
    for node in nodes:
        label = (node.get("label") or "").strip()
        if not label:
            continue
        step = step_of[node["id"]]
        descriptions.append("Double click on the element created in step %d" % step)
        descriptions.append('Fill "%s" into the element created in step %d' % (label, step))

    # phase 3 - connectors, then their labels
    for edge in graph.get("edges", []):
        a, b = step_of.get(edge.get("from")), step_of.get(edge.get("to"))
        if a is None or b is None:
            continue
        descriptions.append(
            "Connect the element created in step %d to the element created in step %d" % (a, b))
        label = (edge.get("label") or "")
        if label and str(label).strip().lower() not in ("null", "none"):
            descriptions.append("Double click on connector_from_step%d_to_step%d" % (a, b))
            descriptions.append('Fill "%s"' % str(label).strip())

    return {
        "id": case_id,
        "url": DRAWIO_URL,
        "environment": {"theme": "light"},
        "descriptions": descriptions,
        "assets": assets,
        "_source": "image_to_scenario.py — VLM read of the PNG only, then a "
                   "deterministic translation into the RPA_Datasets step language",
        "_vlm": graph.get("_vlm"),
        "_placement": {"px_per_normalised_unit": round(scale, 1),
                       "move_step_px": drawio_ops.MOVE_STEP_PX,
                       "anchor_node": anchor["id"]},
        "_unsupported_shapes": unknown_types,
        "_shape_substitutions": substituted,
    }


# ---------------------------------------------------------------------- cli
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", required=True, help="glob of source PNGs")
    ap.add_argument("--out", required=True, help="directory for the scenario JSONs")
    ap.add_argument("--cache", default=str(HERE / ".vlm_cache"),
                    help="where VLM reads are cached, keyed by image content")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--providers", default=None,
                    help="comma-separated override, e.g. 'openai,anthropic'")
    args = ap.parse_args(argv)

    paths = sorted(Path(p) for p in glob.glob(args.images))
    if args.limit:
        paths = paths[: args.limit]
    if not paths:
        print("no images matched %r" % args.images, file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache)

    providers = args.providers.split(",") if args.providers else None
    client = LLMClient(providers=providers,
                       log=lambda *a: print(*a, file=sys.stderr, flush=True))

    ok, failed = 0, []
    for i, p in enumerate(paths, 1):
        case_id = p.stem
        try:
            graph = read_image(str(p), client, cache_dir)
            scenario = build_scenario(graph, case_id)
            (out_dir / ("%s.json" % case_id)).write_text(
                json.dumps(scenario, ensure_ascii=False, indent=2), encoding="utf-8")
            ok += 1
            print("[%d/%d] %-30s %d nodes %d edges -> %d steps"
                  % (i, len(paths), case_id, len(graph.get("nodes", [])),
                     len(graph.get("edges", [])), len(scenario["descriptions"])),
                  file=sys.stderr, flush=True)
        except Exception as exc:
            failed.append({"id": case_id, "error": "%s: %s" % (type(exc).__name__, exc)})
            print("[%d/%d] %-30s FAILED %s" % (i, len(paths), case_id, exc),
                  file=sys.stderr, flush=True)

    print(json.dumps({"n_total": len(paths), "n_ok": ok, "failed": failed},
                     ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
