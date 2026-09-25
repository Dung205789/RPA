#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print a finished run in the shape `RPA_docs/ORACLE.md` §6 requires.

Added 2026-09-22. §6 is explicit that a run missing any line of the template
"chưa được coi là đã báo cáo", so every section is printed even when the answer
is *chưa đo* — a silently dropped row is how a missing measurement turns into an
assumed one.

    python RPA_docs/checks/report.py result/g0_baseline
    python RPA_docs/checks/report.py result/g0_baseline --band          # split by band
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCUMENTS = HERE.parents[1]
sys.path.insert(0, str(HERE))
import _console  # noqa: F401,E402
import baselines  # noqa: E402
import false_pass  # noqa: E402
import graph_score as gs  # noqa: E402
import stats  # noqa: E402

FIGURE_KEYS = ["node_f1", "node_count_recall", "node_excess", "edge_f1",
               "edge_recall", "edge_excess", "label_accuracy",
               "shape_type_accuracy", "edge_label_accuracy", "layout_score",
               "overall"]


def band_of(case_id: str) -> str:
    for b in ("easy", "medium", "hard"):
        if case_id.startswith(b + "_"):
            return b
    return "—"


def split_of(case_id: str) -> str:
    """tuning or holdout, straight out of the frozen split file."""
    path = DOCUMENTS / "RPA_docs" / "splits.json"
    if not path.is_file():
        return "?"
    data = json.loads(path.read_text(encoding="utf-8"))
    for corpus in ("new_corpus", "old_corpus"):
        for band, sets in (data.get(corpus) or {}).items():
            if not isinstance(sets, dict):
                continue
            if case_id in sets.get("holdout", []):
                return "giữ kín"
            if case_id in sets.get("tuning", []):
                return "chỉnh"
    return "?"


def silent_wrong_element(row: dict) -> bool:
    """The action happened, cleanly, to the wrong cell.

    `ORACLE.md` §3.1 calls this out as its own class because it is the one the
    existing fallback cannot see: nothing throws, the canvas changes, and the
    change lands somewhere else. Detected here from the model diff — the right
    *kind* of change occurred, but the cell the step named was not the cell it
    occurred to.
    """
    if row["oracle"] != "fail":
        return False
    diff = row.get("diff") or {}
    m = row.get("measured") or {}
    target = m.get("cell")
    action = row["action"]
    if action == "move":
        moved = set(diff.get("moved") or {})
        return bool(moved) and (target not in moved)
    if action == "fill":
        touched = set(diff.get("relabelled") or {})
        return bool(touched) and (target not in touched)
    if action == "double_click":
        editing = m.get("editing")
        return bool(editing) and editing != target
    if action == "connect":
        return bool(m.get("edge")) and (m.get("source") != m.get("want_source")
                                        or m.get("target") != m.get("want_target"))
    if action == "delete":
        removed = set(diff.get("removed") or {})
        return bool(removed) and (target not in removed)
    if action in ("extend", "shrink"):
        resized = set(diff.get("resized") or {})
        return bool(resized) and (target not in resized)
    return False


def _split_ran(run_dir: Path, case_dirs: list):
    """Cases the harness completed, and cases it never managed to start.

    "Never started" is read off ``summary.json``: a row with no ``n_steps`` is a
    case the harness abandoned — browser gone, restart refused — not a case that
    drew nothing.
    """
    ran, missing = [], []
    by_id = {}
    summary_file = run_dir / "summary.json"
    if summary_file.is_file():
        try:
            for row in json.loads(summary_file.read_text(encoding="utf-8")).get("rows", []):
                by_id[row.get("id")] = row
        except Exception:
            pass
    for case in case_dirs:
        row = by_id.get(case.name) or {}
        if (case / "verdicts.json").is_file() and row.get("n_steps"):
            ran.append(case)
        else:
            missing.append((case.name, (row.get("error") or "no verdicts written")[:80]))
    for cid, row in by_id.items():
        if not row.get("n_steps") and cid not in {c.name for c in case_dirs}:
            missing.append((cid, (row.get("error") or "no case directory")[:80]))
    return ran, missing


def cost_rows(run_dir: Path) -> dict:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    secs = sorted(r.get("total_sec") or 0 for r in summary["rows"] if r.get("total_sec"))
    return {"n": len(secs), "median": _median(secs), "p95": _pct(secs, 95),
            "summary": summary}


def _median(xs):
    if not xs:
        return None
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _pct(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round(p / 100.0 * len(s))) - 1))
    return s[k]


def _mean(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


def _fmt(v, nd=4):
    return "chưa đo" if v is None else ("%.*f" % (nd, v))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--band", action="store_true", help="also break the figure level down by band")
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = DOCUMENTS / run_dir
    if not run_dir.is_dir():
        print("no such run: %s" % run_dir)
        return 2

    env = {}
    if (run_dir / "env.json").is_file():
        env = json.loads((run_dir / "env.json").read_text(encoding="utf-8"))
    steps = false_pass.load_run(run_dir)
    case_dirs = sorted(p for p in run_dir.iterdir() if p.is_dir())
    # A case the harness never got to is not a case that scored zero. Folding the
    # two together turns a browser crash into a low pass rate, which is the exact
    # species of misleading number this report exists to prevent: on
    # `result/g0_baseline` it read 59.99% where the 20 cases that actually ran
    # scored 99.7%. Rates are computed over the cases that ran; the ones that did
    # not are counted, named, and printed separately.
    ran, missing = _split_ran(run_dir, case_dirs)
    # An abandoned case still leaves a verdicts.json behind — the harness writes
    # one before it discovers the browser is gone, and every row in it says
    # "no-verdict". Those rows must not reach the denominators either.
    ran_names = {c.name for c in ran}
    steps = [r for r in steps if r["case"] in ran_names]
    figure = [r for r in (gs.score_case(d) for d in ran) if r]
    cost = cost_rows(run_dir)
    ids = [d.name for d in ran]
    splits = Counter(split_of(i) for i in ids)

    out = []
    A = out.append
    A("Lượt chạy : %s          Ngày: %s" % (run_dir.relative_to(DOCUMENTS)
                                            if run_dir.is_relative_to(DOCUMENTS) else run_dir,
                                            env.get("date", "?")))
    A("Corpus    : %s  n=%d case chạy xong   Tập: %s"
      % (_corpus_name(ids), len(ids),
         ", ".join("%s %d" % (k, v) for k, v in sorted(splits.items()))))
    if missing:
        A("KHÔNG CHẠY: %d case — mọi tỉ lệ dưới đây tính trên %d case đã chạy,"
          % (len(missing), len(ids)))
        A("            KHÔNG phải trên %d case của bộ." % (len(ids) + len(missing)))
        for cid, why in missing[:12]:
            A("            %-30s %s" % (cid, why))
        if len(missing) > 12:
            A("            ... và %d case nữa" % (len(missing) - 12))
    A("Môi trường: draw.io %s @ %s | Chrome %s | commit %s%s"
      % (env.get("drawio_build", "?"), env.get("drawio_url", "?"),
         env.get("chrome", "?"), (env.get("repo_commit") or "?")[:10],
         " (cây làm việc bẩn)" if env.get("repo_dirty") else ""))
    A("Mức phán định báo cáo: N3 + N4")
    A("")

    # ---- floor ----
    A("-- Sàn --")
    key_paths = baselines.keys_for(None)
    key_paths = [p for p in key_paths if Path(p).name.split(".png")[0] in set(ids)]
    if key_paths:
        for name, build in baselines.BASELINES:
            row = baselines.mean_scores(key_paths, build)
            A("  %-20s: overall %s   bố cục %s   nodeF1 %s   cạnhF1 %s"
              % (name, _fmt(row["overall"]), _fmt(row["layout_score"]),
                 _fmt(row["node_f1"]), _fmt(row["edge_f1"])))
    else:
        A("  chưa đo — không tìm thấy answer key cho các case của lượt này")
    A("")

    # ---- step level ----
    graded = [r for r in steps if r["oracle"] != "no-verdict"]
    n_steps = len(steps)
    kinds = Counter()
    for case in ran:
        vf = case / "verdicts.json"
        if not vf.is_file():
            continue
        data = json.loads(vf.read_text(encoding="utf-8"))
        kinds.update((data.get("summary") or {}).get("kinds", {}).values())
    n_ok_exec = sum(1 for r in steps if r["executor"] == "ok")
    fp = sum(1 for r in steps if r["executor"] == "ok" and r["oracle"] == "fail")
    ff = sum(1 for r in steps if r["executor"] in ("failed", "error") and r["oracle"] == "pass")
    silent = sum(1 for r in steps if silent_wrong_element(r))

    A("-- Mức bước --  (n=%d bước, %d có phán định)" % (n_steps, len(graded)))
    A("  đạt N3              : %s" % stats.fmt_rate(kinds.get("pass", 0), n_steps))
    A("  hỏng gốc            : %s" % stats.fmt_rate(kinds.get("root", 0), n_steps))
    A("  hỏng kéo theo       : %s" % stats.fmt_rate(kinds.get("cascade", 0), n_steps))
    A("  không phán định được: %s" % stats.fmt_rate(kinds.get("no-verdict", 0), n_steps))
    A("  báo đạt sai (thước cũ, oracle trọng tài): %s" % stats.fmt_rate(fp, n_ok_exec))
    A("  báo hỏng sai (thước cũ)                 : %s"
      % stats.fmt_rate(ff, sum(1 for r in steps if r["executor"] in ("failed", "error"))))
    A("  hỏng thầm lặng                          : %s" % stats.fmt_rate(silent, n_steps))
    adj = run_dir / "review_adjudication.json"
    A("  báo đạt sai của THƯỚC MỚI               : %s"
      % (_review_rate(adj) if adj.is_file() else
         "chưa đo — cần %s" % adj.name))
    A("")
    A("  theo hành động:")
    per = defaultdict(lambda: Counter())
    for r in steps:
        per[r["action"]][r["oracle"]] += 1
        per[r["action"]]["level"] = r["level"]
    for a in sorted(per):
        c = per[a]
        tot = c["pass"] + c["fail"] + c["no-verdict"]
        A("    %-14s %-7s %s" % (a, c["level"], stats.fmt_rate(c["pass"], tot)))
    A("")

    # ---- figure level ----
    A("-- Mức hình (oracle tất định, mẫu số = số đếm bản tham chiếu) --")
    if figure:
        A("  n=%d case chấm được" % len(figure))
        for k in FIGURE_KEYS:
            A("  %-22s: %s" % (k, _fmt(_mean(figure, k))))
        A("  sai số vị trí sau Procrustes (phần đường chéo): trung vị %s, p95 %s"
          % (_fmt(_mean(figure, "position_error_median")),
             _fmt(_mean(figure, "position_error_p95"))))
        if args.band:
            A("")
            by = defaultdict(list)
            for r in figure:
                by[band_of(r["id"])].append(r)
            A("  %-8s %5s %9s %9s %9s %9s" % ("band", "n", "overall", "bố cục",
                                              "nodeF1", "cạnhF1"))
            for b in sorted(by):
                rs = by[b]
                A("  %-8s %5d %9s %9s %9s %9s"
                  % (b, len(rs), _fmt(_mean(rs, "overall"), 3),
                     _fmt(_mean(rs, "layout_score"), 3), _fmt(_mean(rs, "node_f1"), 3),
                     _fmt(_mean(rs, "edge_f1"), 3)))
    else:
        A("  chưa đo — không case nào có cả model.xml và answer key")
    A("")

    # ---- stability ----
    A("-- Ổn định --")
    rep = run_dir / "repeatability.json"
    if rep.is_file():
        d = json.loads(rep.read_text(encoding="utf-8"))
        A("  đồ thị cuối đẳng cấu qua %d lần: %s" % (d.get("runs", 0),
                                                      _fmt(d.get("isomorphic_rate"))))
        A("  phán định ổn định              : %s" % _fmt(d.get("verdict_stability")))
        A("  vị trí p95 giữa các lần        : %s" % _fmt(d.get("position_p95"), 1))
    else:
        A("  chưa đo — cần 20 case x 5 lần (ORACLE §3.2, việc G1.6)")
    A("")

    # ---- cost ----
    A("-- Chi phí --")
    A("  thời gian/case: trung vị %ss, p95 %ss"
      % (_fmt(cost["median"], 1), _fmt(cost["p95"], 1)))
    A("  gọi LLM khi chạy: 0 — kịch bản đã sinh sẵn; chi phí VLM nằm ở bước")
    A("                    image_to_scenario.py, đo riêng (việc G2.3)")
    A("")

    # ---- eyeballs ----
    A("-- Đã nhìn bằng mắt --")
    eye = run_dir / "eyeballed.md"
    if eye.is_file():
        for line in eye.read_text(encoding="utf-8").splitlines():
            if line.strip():
                A("  " + line.rstrip())
    else:
        A("  chưa làm — cần ≥10 case, mỗi case một dòng mô tả sai ở đâu (%s)" % eye.name)

    print("\n".join(out))
    (run_dir / "report.txt").write_text("\n".join(out), encoding="utf-8")
    return 0


def _corpus_name(ids):
    bands = Counter(band_of(i) for i in ids)
    if set(bands) <= {"easy", "medium", "hard"}:
        return "benchmark ảnh drawio (%s)" % ", ".join(
            "%s %d" % (b, n) for b, n in sorted(bands.items()))
    return "RPA_Datasets drawio"


def _review_rate(path: Path) -> str:
    adj = json.loads(path.read_text(encoding="utf-8"))
    calls = {k: v for k, v in adj.items() if not k.startswith("_")}
    bad = sum(1 for v in calls.values() if v == "false-pass")
    return stats.fmt_rate(bad, len(calls))


if __name__ == "__main__":
    raise SystemExit(main())
