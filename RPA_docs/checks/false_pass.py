#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""How often does each ruler say "pass" when the step did not do its job?

Added 2026-09-22 for G0.7 and the two G0 gate lines about false passes
(`RPA_docs/ORACLE.md` §3.1). This is the project's most important number: a test
tool that reports *pass* while the application misbehaves is worse than no test
tool, and `main.tex` §RQ1 already admits the fallback cannot catch it.

Two rulers are compared on the same steps of the same run:

* **the old ruler** — the executor's own ``status``. For ``Move`` its criterion
  is ``(|dx| + |dy|) >= distance // 2`` measured through the SVG, i.e. 75px out
  of a demanded 150px counts as done (`DIAGNOSIS.md` L1).
* **the new ruler** — ``oracle_verdict``, reading draw.io's model.

Neither is ground truth for the other, so the script does two separate things:

1. **Old-ruler false pass**, adjudicated by the new ruler. Defensible because
   the new ruler reads a different source through different code, and because
   its own error rate is bounded by (2).
2. **New-ruler false pass**, adjudicated by review. The script draws a seeded,
   action-stratified sample of steps the *new* ruler passed, prints every piece
   of evidence needed to judge each one, and — once a reviewer has written their
   calls into ``review_adjudication.json`` — reports the rate with a Wilson
   interval. Until that file exists the number is reported as *not yet measured*,
   never as zero.

Sample size: zero findings out of 50 only bounds the rate at 7.1%. The <2%
upper bound `ORACLE.md` §3.1 demands needs 189 clean steps, which is why the
default sample is 200.

    python RPA_docs/checks/false_pass.py result/g0_baseline
    python RPA_docs/checks/false_pass.py result/g0_baseline --write-sample
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCUMENTS = HERE.parents[1]
sys.path.insert(0, str(HERE))
import _console  # noqa: F401,E402
import stats  # noqa: E402

SEED = 20260922


def load_run(run_dir: Path) -> list:
    """Every graded step of every case, with both rulers' opinions side by side."""
    rows = []
    for case in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        vfile = case / "verdicts.json"
        if not vfile.is_file():
            continue
        data = json.loads(vfile.read_text(encoding="utf-8"))
        report = {}
        rfile = case / "report.json"
        if rfile.is_file():
            try:
                for s in json.loads(rfile.read_text(encoding="utf-8")).get("steps", []):
                    report[s["n"]] = s
            except Exception:
                pass
        for v in data.get("steps", []):
            step = report.get(v["n"], {})
            rows.append({
                "case": case.name,
                "n": v["n"],
                "action": v["action"],
                "level": v["level"],
                "oracle": v["verdict"],
                "executor": v.get("executor_status"),
                "reason": v.get("reason"),
                "measured": v.get("measured"),
                "diff": v.get("diff"),
                "description": step.get("description"),
                "executor_detail": {k: val for k, val in (step.get("detail") or {}).items()
                                    if k not in ("oracle", "traceback")},
            })
    return rows


def confusion(rows: list) -> dict:
    c = Counter()
    for r in rows:
        if r["oracle"] == "no-verdict":
            c["no-verdict"] += 1
            continue
        c["%s/%s" % ("ok" if r["executor"] == "ok" else "not-ok", r["oracle"])] += 1
    return dict(c)


def sample_for_review(rows: list, size: int, seed: int = SEED) -> list:
    """Steps the *new* ruler passed, spread across the actions it passed them for.

    Stratified because a flat sample of this corpus would be three quarters
    ``move``, and a ruler can be wrong in a way that only shows on ``connect``.
    """
    pool = defaultdict(list)
    for r in rows:
        if r["oracle"] == "pass":
            pool[r["action"]].append(r)
    if not pool:
        return []
    out = []
    actions = sorted(pool)
    per = max(1, size // len(actions))
    for a in actions:
        rng = random.Random("%s:%d" % (a, seed))
        items = sorted(pool[a], key=lambda r: (r["case"], r["n"]))
        out.extend(rng.sample(items, min(per, len(items))))
    # top up to `size` from whatever is left, still seeded
    remaining = [r for a in actions for r in pool[a] if r not in out]
    rng = random.Random(seed)
    rng.shuffle(remaining)
    out.extend(remaining[: max(0, size - len(out))])
    return sorted(out, key=lambda r: (r["case"], r["n"]))


def write_sample(rows: list, path: Path) -> None:
    lines = [
        "# Mẫu rà tay — bước được **thước mới** đánh đạt",
        "",
        "Mỗi mục dưới đây là một bước mà oracle nói *đạt*. Việc của người rà:",
        "đọc bằng chứng, quyết định bước đó có thật sự đạt hậu điều kiện không,",
        "rồi ghi phán quyết vào `review_adjudication.json` cùng thư mục:",
        "",
        "```json",
        '{"<case>:<n>": "agree" | "false-pass" | "unsure", ...}',
        "```",
        "",
        "`false-pass` nghĩa là oracle nói đạt nhưng ứng dụng làm sai — theo",
        "`PLAN.md` §Bất biến 9 đó là lỗi chặn: dừng, sửa, chạy lại.",
        "",
        "---",
        "",
    ]
    for r in rows:
        lines.append("### `%s:%d` — %s (%s)" % (r["case"], r["n"], r["action"], r["level"]))
        lines.append("")
        lines.append("* bước: `%s`" % (r["description"] or "—"))
        lines.append("* oracle đo được: `%s`" % json.dumps(r["measured"], ensure_ascii=False))
        diff = r.get("diff") or {}
        compact = {k: v for k, v in diff.items() if v}
        lines.append("* model đổi: `%s`" % (json.dumps(compact, ensure_ascii=False)
                                            if compact else "không đổi"))
        lines.append("* executor nói: `%s`" % r["executor"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--write-sample", action="store_true")
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = DOCUMENTS / run_dir
    rows = load_run(run_dir)
    if not rows:
        print("no verdicts.json under %s — was the run made with the oracle?" % run_dir)
        return 2

    graded = [r for r in rows if r["oracle"] != "no-verdict"]
    print("Lượt chạy : %s" % run_dir)
    print("Bước      : %d tổng, %d có phán định\n" % (len(rows), len(graded)))

    c = confusion(rows)
    print("%-28s %8s %8s" % ("", "oracle đạt", "oracle hỏng"))
    print("-" * 48)
    print("%-28s %8d %8d" % ("executor nói ok", c.get("ok/pass", 0), c.get("ok/fail", 0)))
    print("%-28s %8d %8d" % ("executor nói hỏng", c.get("not-ok/pass", 0),
                             c.get("not-ok/fail", 0)))
    print("-" * 48)
    print("không phán định được: %d\n" % c.get("no-verdict", 0))

    n_ok = c.get("ok/pass", 0) + c.get("ok/fail", 0)
    n_notok = c.get("not-ok/pass", 0) + c.get("not-ok/fail", 0)
    print("THƯỚC CŨ (trạng thái của executor), thước mới làm trọng tài")
    print("  báo đạt sai : %s" % stats.fmt_rate(c.get("ok/fail", 0), n_ok))
    print("  báo hỏng sai: %s" % stats.fmt_rate(c.get("not-ok/pass", 0), n_notok))

    # per action, where the old ruler is wrong
    per = defaultdict(lambda: [0, 0])
    for r in graded:
        if r["executor"] != "ok":
            continue
        per[r["action"]][0] += 1
        per[r["action"]][1] += int(r["oracle"] == "fail")
    print("\n  theo hành động:")
    for a in sorted(per, key=lambda k: -per[k][1]):
        n, bad = per[a]
        if not n:
            continue
        print("    %-14s %s" % (a, stats.fmt_rate(bad, n)))

    sample = sample_for_review(rows, args.sample)
    sample_path = run_dir / "review_sample.md"
    if args.write_sample:
        write_sample(sample, sample_path)
        print("\nMẫu rà tay: %d bước -> %s" % (len(sample), sample_path))

    print("\nTHƯỚC MỚI (oracle), người rà làm trọng tài")
    adj_path = run_dir / "review_adjudication.json"
    if not adj_path.is_file():
        print("  chưa đo — %s chưa tồn tại." % adj_path.name)
        print("  Cỡ mẫu cần để cận trên KTC 95%% xuống dưới 2%% với 0 phát hiện: %d bước."
              % stats.needed_for_upper_bound(0.02))
        return 0
    adj = json.loads(adj_path.read_text(encoding="utf-8"))
    calls = {k: v for k, v in adj.items() if not k.startswith("_")}
    bad = sum(1 for v in calls.values() if v == "false-pass")
    unsure = sum(1 for v in calls.values() if v == "unsure")
    print("  đã rà      : %d bước (%d chưa chắc)" % (len(calls), unsure))
    print("  báo đạt sai: %s" % stats.fmt_rate(bad, len(calls)))
    if bad:
        print("\n  LỖI CHẶN — PLAN.md §Bất biến 9. Các bước bị bác:")
        for k, v in sorted(calls.items()):
            if v == "false-pass":
                print("    %s" % k)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
