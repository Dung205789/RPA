#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Produce a reference picture for the old corpus, which ships none.

Added 2026-09-03, for requirement 5 of the brief: the image benchmark has answer
keys, RPA_Datasets does not, so its cases need something to be scored against.

Where the reference comes from
------------------------------
The old scenarios are fully explicit about the diagram they want. "Click on
[diamond.png]" names a shape, "Move the element created in step 11 up" names a
displacement, "Fill \"Before 7 am?\"" names its text, and "Connect the element
created in step 4 to the element created in step 8" names an arrow. Nothing is
left to interpretation, so the reference is *derived* from the script rather than
guessed at by a model. That is the whole reason to prefer this over asking an LLM
to imagine the intended picture: the script already is the specification, and a
model reading it would only add noise.

The derived graph is then drawn by draw.io itself — handed to the editor through
its documented ``#R<xml>`` URL entry point — so the reference and the run's output
are the same kind of picture from the same renderer, which is what makes comparing
them fair.

What this does and does not measure
-----------------------------------
It measures whether the robot drew what its script said. It does not judge
whether the script's own layout is good; a scenario that asks for two shapes on
top of each other gets a reference with two shapes on top of each other. The
placement constant (one Move = 150px, every shape inserted at the same point) is
the one draw.io actually exhibits — see drawio_ops — so reference and run share
it, and a layout difference between them is a real execution difference.

Usage:
  python scenario_to_gold.py --scenarios "RPA_Datasets/data/drawio/*.json" \\
      --out result/old100_gold --port 9231
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.parse
import xml.sax.saxutils as sax
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).resolve().parent
RPA_DRAWIO_DIR = DOCUMENTS_DIR / "RPA_drawio"

MOVE_PX = 150

# Which bracketed images name a shape, and how draw.io draws each one. Any other
# image in a scenario is a UI icon (a menu entry, the zoom control), and a click
# on it creates no cell.
SHAPE_STYLES = {
    "rectangle": ("rounded=0;whiteSpace=wrap;html=1;", 120, 60),
    "rounded_rectangle": ("rounded=1;whiteSpace=wrap;html=1;", 120, 60),
    "ellipse": ("ellipse;whiteSpace=wrap;html=1;", 120, 80),
    "diamond": ("rhombus;whiteSpace=wrap;html=1;", 80, 80),
    "parallelogram": ("shape=parallelogram;perimeter=parallelogramPerimeter;"
                      "whiteSpace=wrap;html=1;fixedSize=1;", 120, 60),
    "hexagon": ("shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;"
                "fixedSize=1;", 120, 80),
    "trapezoid": ("shape=trapezoid;perimeter=trapezoidPerimeter;whiteSpace=wrap;"
                  "html=1;fixedSize=1;", 120, 60),
    "document": ("shape=document;whiteSpace=wrap;html=1;boundedLbl=1;", 120, 80),
    "cylinder": ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;"
                 "size=15;", 60, 80),
}

CLICK_IMG_RE = re.compile(r"^Click on \[(.+?)\]\s*$", re.IGNORECASE)
MOVE_RE = re.compile(r"^Move the element created in step (\d+)\s+(?:to the\s+)?(\w+)",
                     re.IGNORECASE)
FILL_INTO_RE = re.compile(r'^Fill "(.*)" into the element created in step (\d+)',
                          re.IGNORECASE)
FILL_BARE_RE = re.compile(r'^Fill "(.*)"\s*$', re.IGNORECASE)
DBL_CONN_RE = re.compile(r"^Double click on connector_from_step(\d+)_to_step(\d+)",
                         re.IGNORECASE)
CONNECT_RE = re.compile(r"^Connect the element created in step (\d+) to the element "
                        r"created in step (\d+)", re.IGNORECASE)

_DIR = {"up": (0, -1), "top": (0, -1), "down": (0, 1), "bottom": (0, 1),
        "left": (-1, 0), "right": (1, 0)}


def expected_graph(descriptions: list) -> dict:
    """Read a scenario's own words into the diagram it asks for."""
    shapes: dict = {}          # step number -> shape record
    edges: list = []
    pending_edge = None        # the connector a "Double click on connector_..." selected

    for i, desc in enumerate(descriptions):
        n = i + 1
        d = desc.strip()

        m = CLICK_IMG_RE.match(d)
        if m:
            stem = Path(m.group(1)).stem.lower()
            if stem in SHAPE_STYLES:
                style, w, h = SHAPE_STYLES[stem]
                shapes[n] = {"step": n, "type": stem, "style": style,
                             "w": w, "h": h, "dx": 0, "dy": 0, "label": ""}
            continue

        m = MOVE_RE.match(d)
        if m:
            step, direction = int(m.group(1)), m.group(2).lower()
            vec = _DIR.get(direction)
            if vec and step in shapes:
                shapes[step]["dx"] += vec[0]
                shapes[step]["dy"] += vec[1]
            continue

        m = FILL_INTO_RE.match(d)
        if m:
            text, step = m.group(1), int(m.group(2))
            if step in shapes:
                shapes[step]["label"] = text
            continue

        m = DBL_CONN_RE.match(d)
        if m:
            pending_edge = (int(m.group(1)), int(m.group(2)))
            continue

        m = FILL_BARE_RE.match(d)
        if m and pending_edge:
            for e in edges:
                if (e["a"], e["b"]) == pending_edge:
                    e["label"] = m.group(1)
            pending_edge = None
            continue

        m = CONNECT_RE.match(d)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a in shapes and b in shapes:
                edges.append({"a": a, "b": b, "label": ""})
            continue

    return {"shapes": shapes, "edges": edges}


def to_mxgraph_xml(graph: dict) -> str:
    """Render the derived graph as a draw.io document."""
    shapes = graph["shapes"]
    if not shapes:
        return ""
    parts = ['<mxGraphModel dx="800" dy="600" grid="1" gridSize="10" page="1" '
             'pageWidth="850" pageHeight="1100" math="0" shadow="0"><root>'
             '<mxCell id="0" /><mxCell id="1" parent="0" />']
    # Every shape starts at the same point and is displaced by its Move steps,
    # which is exactly how draw.io behaves for click-inserted shapes.
    for step, s in sorted(shapes.items()):
        x = 400 + s["dx"] * MOVE_PX - s["w"] // 2
        y = 500 + s["dy"] * MOVE_PX - s["h"] // 2
        parts.append(
            '<mxCell id="s%d" value="%s" style="%s" vertex="1" parent="1">'
            '<mxGeometry x="%d" y="%d" width="%d" height="%d" as="geometry" /></mxCell>'
            % (step, sax.escape(s["label"]), s["style"], x, y, s["w"], s["h"]))
    for i, e in enumerate(graph["edges"]):
        parts.append(
            '<mxCell id="e%d" value="%s" style="edgeStyle=orthogonalEdgeStyle;'
            'rounded=0;html=1;" edge="1" parent="1" source="s%d" target="s%d">'
            '<mxGeometry relative="1" as="geometry" /></mxCell>'
            % (i, sax.escape(e["label"]), e["a"], e["b"]))
    parts.append("</root></mxGraphModel>")
    return "".join(parts)


def render_xml(driver, xml: str, log=print) -> bool:
    """Open an mxGraph document in draw.io by putting it in the URL.

    draw.io reads a diagram from the ``#R<url-encoded xml>`` fragment. That is a
    documented, supported entry point, and it is far steadier than driving the
    Extras > Edit Diagram dialog: recent builds render that dialog with CodeMirror
    rather than a plain textarea, so there is nothing to type into (measured
    2026-09-03 — the dialog opened and reported zero visible textareas).
    """
    import cell_tracker
    import rpa_env

    url = "https://app.diagrams.net/?lang=en&splash=0#R" + urllib.parse.quote(xml, safe="")
    driver.get(url)
    rpa_env.wait_ready(driver, log=lambda *a: None)
    time.sleep(1.5)
    if rpa_env.editor_state(driver).get("dialogs"):
        rpa_env.dismiss_dialogs(driver)
        time.sleep(0.8)
    return len(cell_tracker.cell_elements(driver)) > 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    os.chdir(RPA_DRAWIO_DIR)
    sys.path.insert(0, str(RPA_DRAWIO_DIR))
    os.environ["RPA_CHROME_DEBUG_PORT"] = str(args.port)

    import rpa_env
    import by_text
    from run_drawio_v2 import crop_to_canvas   # noqa: E402

    pattern = args.scenarios
    if not Path(pattern).is_absolute():
        pattern = str(DOCUMENTS_DIR / pattern)
    paths = sorted(Path(p) for p in glob.glob(pattern))
    if args.limit:
        paths = paths[: args.limit]

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = DOCUMENTS_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rpa_env.launch_chrome(port=args.port)
    rpa_env.wait_for_debug_port(args.port)
    driver = by_text.setup_chrome_driver(use_existing=True)

    rows = []
    try:
        for i, p in enumerate(paths, 1):
            sc = json.loads(p.read_text(encoding="utf-8"))
            cid = sc.get("id", p.stem)
            graph = expected_graph(sc.get("descriptions", []))
            row = {"id": cid, "n_shapes": len(graph["shapes"]),
                   "n_edges": len(graph["edges"])}
            if not graph["shapes"]:
                row["status"] = "not_a_drawing_scenario"
                rows.append(row)
                print("[%d/%d] %-16s no shapes — menu-only scenario"
                      % (i, len(paths), cid), file=sys.stderr, flush=True)
                continue
            xml = to_mxgraph_xml(graph)
            (out_dir / ("%s.xml" % cid)).write_text(xml, encoding="utf-8")
            (out_dir / ("%s.graph.json" % cid)).write_text(
                json.dumps(graph, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8")
            try:
                ok = render_xml(driver, xml, log=lambda *a: None)
                if ok:
                    rpa_env.settle_for_screenshot(driver)
                    rpa_env.fit_page(driver)
                    rpa_env.settle_for_screenshot(driver)
                    full = out_dir / ("%s.full.png" % cid)
                    driver.save_screenshot(str(full))
                    crop_to_canvas(driver, full, out_dir / ("%s.png" % cid))
                    full.unlink(missing_ok=True)
                    row["status"] = "rendered"
                else:
                    row["status"] = "render_failed"
            except Exception as exc:
                row["status"] = "error"
                row["error"] = "%s: %s" % (type(exc).__name__, exc)
            rows.append(row)
            print("[%d/%d] %-16s %-14s shapes=%d edges=%d"
                  % (i, len(paths), cid, row["status"], row["n_shapes"], row["n_edges"]),
                  file=sys.stderr, flush=True)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        rpa_env.kill_chrome_on_port(args.port)

    summary = {"n_total": len(rows),
               "n_rendered": sum(1 for r in rows if r.get("status") == "rendered"),
               "n_menu_only": sum(1 for r in rows
                                  if r.get("status") == "not_a_drawing_scenario"),
               "rows": rows}
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
