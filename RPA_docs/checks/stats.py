#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Intervals, because `PLAN.md` §Bất biến 6 says a point estimate is not a result.

Wilson rather than the textbook normal interval: the rates that matter here sit
at or near 0 (false pass must be 0) and near 1 (N3 pass), and the normal
interval is worst exactly there — at 0/50 it returns [0, 0], which would let a
run claim certainty it has not earned. Wilson gives [0, 0.071] for 0/50, which
is the honest statement: fifty clean steps do not prove a rate below 2%.
"""
from __future__ import annotations

import math


def wilson(successes: int, n: int, z: float = 1.959963985) -> tuple:
    """95% Wilson score interval for a proportion."""
    if n <= 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def fmt_rate(successes: int, n: int, pct: bool = True) -> str:
    """``12.3% [9.8, 15.2]  (61/496)`` — the form every table in this project uses."""
    if n <= 0:
        return "n/a (0 steps)"
    lo, hi = wilson(successes, n)
    scale = 100.0 if pct else 1.0
    unit = "%" if pct else ""
    return "%.2f%s [%.2f, %.2f]  (%d/%d)" % (
        scale * successes / n, unit, scale * lo, scale * hi, successes, n)


def needed_for_upper_bound(target: float, z: float = 1.959963985) -> int:
    """How many clean observations are needed before the upper bound clears ``target``.

    `ORACLE.md` §3.1 wants the false-pass upper bound below 2%; this says how big
    the review sample has to be for zero findings to support that claim.
    """
    n = 1
    while n < 100000:
        if wilson(0, n, z)[1] < target:
            return n
        n += 1
    return n


if __name__ == "__main__":
    print("0 findings out of n, 95%% upper bound:")
    for n in (20, 50, 100, 150, 190, 200, 300):
        print("  n=%-4d upper bound %.3f%%" % (n, 100 * wilson(0, n)[1]))
    print("\nto claim false pass < 2%% with zero findings: n >= %d"
          % needed_for_upper_bound(0.02))
