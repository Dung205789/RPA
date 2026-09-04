#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score a run by looking at what it drew.

Added 2026-09-03. The metric was chosen by the person running this study: judge
the pictures, not an XML diff. So for each case this shows a VLM two images — the
reference diagram and the canvas the robot produced — and asks for a structured
comparison.

Two things keep the number honest:

* **The judge is told which image is which, and nothing else.** It never sees the
  scenario text, the case id, the step log, or how many shapes were expected.
  Everything it reports has to come from the two pictures.
* **The sub-counts are what matter.** An overall 0-1 score alone hides the
  difference between "drew four of six shapes correctly" and "drew six shapes,
  all mislabelled". The rubric asks for shapes / labels / arrows separately, the
  way the run can actually fail.

Usage:
  python judge_drawings.py --results result/new30_v2 \\
      --references "D:/SVG_agent/data/datasets/*/{id}.png" --out result/new30_v2/judge.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DOCUMENTS_DIR / "RPA_drawio"))

from llm_client import LLMClient, extract_json  # noqa: E402


PROMPT = """You are comparing two flowchart pictures.

IMAGE 1 is the REFERENCE: the diagram that was supposed to be drawn.
IMAGE 2 is the RESULT: what an automation robot actually drew on a canvas.

Compare them and return ONE JSON object, nothing else:

{
  "reference": {"shapes": <int>, "arrows": <int>, "labelled_arrows": <int>},
  "result":    {"shapes": <int>, "arrows": <int>},
  "shapes_matched": <int>,
  "shape_types_matched": <int>,
  "labels_matched": <int>,
  "arrows_matched": <int>,
  "arrow_labels_matched": <int>,
  "layout_similarity": <0.0-1.0>,
  "overall": <0.0-1.0>,
  "verdict": "<one sentence>",
  "problems": ["<short specific problem>", "..."]
}

How to count, strictly:

- "shapes_matched": shapes in the RESULT that correspond to a shape in the
  REFERENCE, matched by their text. A shape with no text matches only if its
  position and outline leave no doubt.
- "shape_types_matched": of those matched shapes, how many also have the right
  OUTLINE (oval / rectangle / rounded rectangle / diamond / parallelogram /
  hexagon / trapezoid / document / cylinder). Judge the outline only, never the
  wording inside.
- "labels_matched": matched shapes whose text is the same, ignoring case and
  surrounding whitespace. Different wording is not a match.
- "arrows_matched": arrows in the RESULT that join the same pair of shapes, in
  the same direction, as an arrow in the REFERENCE.
- "reference.labelled_arrows": how many arrows in the REFERENCE carry text.
- "arrow_labels_matched": of the matched arrows, how many carry the same text as
  the reference arrow does. Count only arrows the reference actually labels.
- "layout_similarity": is the arrangement recognisably the same picture — the
  same rough top-to-bottom order, branches on the same side? 1.0 identical
  arrangement, 0.0 unrelated. Exact pixel positions do not matter; overlapping or
  stacked shapes do.
- "overall": your judgement of how well the RESULT reproduces the REFERENCE, with
  content (shapes, text, arrows) counting for much more than placement. An empty
  or near-empty RESULT is 0.0.

Count only what you can see. If the RESULT is blank, say so in "verdict" and
report zeros. Do not give credit for intent."""


def find_reference(case_id: str, pattern: str):
    """Resolve a reference image path for a case id.

    ``pattern`` may contain ``{id}`` and a glob, e.g.
    "D:/SVG_agent/data/datasets/*/{id}.png".
    """
    hits = glob.glob(pattern.replace("{id}", case_id))
    return Path(hits[0]) if hits else None


# The judge is asked for exactly these keys; a reply has occasionally used a
# slightly different name for one of them (observed: "arrows_arrows" instead of
# "arrows_matched" on one of 30 cases). Accepting the near-miss here is what
# keeps one model typo from silently zeroing a real count in the aggregate.
_KEY_ALIASES = {
    "arrows_matched": ("arrows_arrows", "matched_arrows"),
    "shapes_matched": ("matched_shapes",),
    "labels_matched": ("matched_labels",),
    "shape_types_matched": ("types_matched", "shape_type_matched"),
    "arrow_labels_matched": ("matched_arrow_labels",),
}


def _normalise_keys(verdict: dict) -> dict:
    for canonical, aliases in _KEY_ALIASES.items():
        if verdict.get(canonical) is None:
            for alias in aliases:
                if alias in verdict:
                    verdict[canonical] = verdict[alias]
                    break
    return verdict


def judge_case(client: LLMClient, reference: Path, produced: Path) -> dict:
    reply = client.vision_multi(PROMPT, [str(reference), str(produced)], max_tokens=2048)
    verdict = _normalise_keys(extract_json(reply["text"]))
    verdict["_judge"] = {"provider": reply["provider"], "model": reply["model"]}
    return verdict


def _rate(part, whole):
    return round(part / whole, 4) if whole else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True,
                    help="run output dir containing <case>/canvas.png")
    ap.add_argument("--references", required=True,
                    help="glob with {id}, e.g. 'D:/SVG_agent/data/datasets/*/{id}.png'")
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--providers", default=None)
    ap.add_argument("--image", default="canvas.png",
                    help="which image in each case dir to judge")
    args = ap.parse_args(argv)

    results_dir = Path(args.results)
    if not results_dir.is_absolute():
        results_dir = DOCUMENTS_DIR / results_dir
    out_path = Path(args.out) if args.out else results_dir / "judge.json"
    if not out_path.is_absolute():
        out_path = DOCUMENTS_DIR / out_path

    cases = sorted(d for d in results_dir.iterdir() if d.is_dir())
    if args.limit:
        cases = cases[: args.limit]

    client = LLMClient(providers=args.providers.split(",") if args.providers else None,
                       log=lambda *a: print(*a, file=sys.stderr, flush=True))

    rows = []
    for i, case_dir in enumerate(cases, 1):
        cid = case_dir.name
        produced = case_dir / args.image
        if not produced.exists():
            produced = case_dir / "after.png"
        reference = find_reference(cid, args.references)
        if reference is None or not produced.exists():
            rows.append({"id": cid, "status": "skipped",
                         "reason": "missing %s" % ("reference" if reference is None
                                                   else "result image")})
            print("[%d/%d] %-30s SKIP" % (i, len(cases), cid), file=sys.stderr)
            continue
        try:
            v = judge_case(client, reference, produced)
            v["id"] = cid
            v["status"] = "judged"
            rows.append(v)
            print("[%d/%d] %-30s overall=%.2f shapes %s/%s labels %s arrows %s/%s"
                  % (i, len(cases), cid, v.get("overall", 0),
                     v.get("shapes_matched"), v.get("reference", {}).get("shapes"),
                     v.get("labels_matched"),
                     v.get("arrows_matched"), v.get("reference", {}).get("arrows")),
                  file=sys.stderr, flush=True)
        except Exception as exc:
            rows.append({"id": cid, "status": "error",
                         "reason": "%s: %s" % (type(exc).__name__, exc)})
            print("[%d/%d] %-30s ERROR %s" % (i, len(cases), cid, exc), file=sys.stderr)
        out_path.write_text(json.dumps(_summarise(rows), ensure_ascii=False, indent=2),
                            encoding="utf-8")

    summary = _summarise(rows)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "cases"},
                     ensure_ascii=False, indent=2))
    return 0


def _summarise(rows):
    judged = [r for r in rows if r.get("status") == "judged"]
    def tot(key, sub=None):
        return sum((r.get(key, {}) or {}).get(sub, 0) if sub else (r.get(key) or 0)
                   for r in judged)
    ref_shapes, ref_arrows = tot("reference", "shapes"), tot("reference", "arrows")
    return {
        "n_cases": len(rows),
        "n_judged": len(judged),
        "mean_overall": round(sum(r.get("overall", 0) for r in judged) / len(judged), 4)
                        if judged else 0.0,
        "mean_layout_similarity": round(
            sum(r.get("layout_similarity", 0) for r in judged) / len(judged), 4)
            if judged else 0.0,
        "shape_recall": _rate(tot("shapes_matched"), ref_shapes),
        "shape_type_accuracy": _rate(tot("shape_types_matched"), tot("shapes_matched")),
        "label_accuracy": _rate(tot("labels_matched"), ref_shapes),
        "arrow_recall": _rate(tot("arrows_matched"), ref_arrows),
        # Denominated by the arrows the reference actually labels: most arrows in
        # a flowchart carry no text, and dividing by every matched arrow scored a
        # pair of identical images at 0.33.
        "arrow_label_accuracy": _rate(tot("arrow_labels_matched"),
                                      tot("reference", "labelled_arrows")),
        "totals": {"reference_shapes": ref_shapes, "reference_arrows": ref_arrows,
                   "reference_labelled_arrows": tot("reference", "labelled_arrows"),
                   "result_shapes": tot("result", "shapes"),
                   "result_arrows": tot("result", "arrows")},
        "cases": rows,
    }


if __name__ == "__main__":
    raise SystemExit(main())
