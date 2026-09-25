#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm `RPA_docs/splits.json` is what it claims to be.

Added 2026-09-22 for the G0.4 gate line: *"`RPA_docs/splits.json` tồn tại, tất
định, tái sinh được."* Existing is easy to check by looking; the other two are
not, and a split file that quietly drifted would let a tuned-on case slip into
the held-out set without anyone noticing.

Four things are asserted:

1. **Reproducible.** Re-running ``build_splits.py`` in memory produces byte-for-
   byte the same assignment as the file on disk.
2. **Deterministic.** The rule is ``sha256(case_id) % 100 < 20`` and nothing
   else: no RNG, no seed, no ordering dependence. Checked by recomputing every
   membership from the id alone.
3. **Stratified.** The held-out share is close to 20% inside every band, which
   is what keeps the two sets comparable (`PLAN.md` §Bất biến 3).
4. **Complete.** Every case on disk appears exactly once.

    python RPA_docs/checks/verify_splits.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent
DOCUMENTS = DOCS.parent
sys.path.insert(0, str(HERE))
import _console  # noqa: F401,E402


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_splits", HERE / "build_splits.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    path = DOCS / "splits.json"
    if not path.is_file():
        print("FAIL  RPA_docs/splits.json does not exist")
        return 1
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    builder = _load_builder()

    problems = []

    # 1 + 4 -- rebuild and compare
    rebuilt = builder.build()
    if rebuilt != on_disk:
        # report where, not just that
        keys = set(rebuilt) | set(on_disk)
        for k in sorted(keys):
            if rebuilt.get(k) != on_disk.get(k):
                problems.append("corpus %r differs between the file and a rebuild" % k)
    print("%-52s %s" % ("rebuild reproduces splits.json",
                        "OK" if rebuilt == on_disk else "MISMATCH"))

    # 2 -- every membership follows from the id alone
    wrong = []
    total = held = 0
    per_band = {}
    for corpus, bands in on_disk.items():
        if not isinstance(bands, dict):
            continue
        for band, sets in bands.items():
            if not isinstance(sets, dict):
                continue
            for which, ids in sets.items():
                if not isinstance(ids, list):
                    continue
                if which not in ("tuning", "holdout"):
                    continue
                for cid in ids:
                    total += 1
                    want = builder.is_holdout(cid)
                    got = (which == "holdout")
                    held += int(got)
                    key = "%s/%s" % (corpus, band)
                    row = per_band.setdefault(key, [0, 0])
                    row[0] += 1
                    row[1] += int(got)
                    if want != got:
                        wrong.append(cid)
    print("%-52s %s" % ("every id's set follows from sha256(id) alone",
                        "OK" if not wrong else "%d wrong" % len(wrong)))
    if wrong:
        problems.append("ids in the wrong set: %s" % wrong[:5])

    # 3 -- stratification
    print("\n%-34s %6s %8s %8s" % ("band", "n", "holdout", "share"))
    print("-" * 60)
    for key in sorted(per_band):
        n, h = per_band[key]
        share = h / n if n else 0
        flag = "" if n < 20 or 0.08 <= share <= 0.34 else "   <-- off"
        print("%-34s %6d %8d %7.1f%%%s" % (key, n, h, 100 * share, flag))
        if n >= 20 and not 0.08 <= share <= 0.34:
            problems.append("%s holds out %.1f%%, far from 20%%" % (key, 100 * share))
    print("-" * 60)
    print("%-34s %6d %8d %7.1f%%" % ("TOTAL", total, held,
                                     100 * held / total if total else 0))

    # 5 -- no id in both sets
    for corpus, bands in on_disk.items():
        if not isinstance(bands, dict):
            continue
        for band, sets in bands.items():
            if not isinstance(sets, dict):
                continue
            both = set(sets.get("tuning", [])) & set(sets.get("holdout", []))
            if both:
                problems.append("%s/%s: %d ids in both sets" % (corpus, band, len(both)))

    print()
    if problems:
        for p in problems:
            print("FAIL  %s" % p)
        return 1
    print("splits.json is deterministic, reproducible and stratified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
