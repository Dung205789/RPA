#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Make the no-leakage rule impossible to break by accident.

Added 2026-09-22 for G0.5 (`RPA_docs/PLAN.md`). Invariant 1 says the execution
path may open a case's ``.png`` and nothing else — never ``*.png.graph.json``
(the answer key) and never the source ``*.xml`` the image was rendered from.
Until now that was a rule people had to remember. This turns it into a runtime
error: with the guard armed, the interpreter itself refuses the open.

It uses ``sys.addaudithook``, so it sees every file open in the process
regardless of which library does it — ``open()``, ``pathlib``, ``json.load``,
``cv2.imread``, a C extension going through CPython's audit events. There is no
way to route around it short of removing this call.

The judges are a different process, or at least a different entry point, and
must *not* arm it: scoring a drawing is exactly the moment the answer key is
supposed to be read (`ORACLE.md`, `graph_score.py`).

    from leak_guard import arm
    arm()                         # in the harness, before any scenario runs
"""
from __future__ import annotations

import os
import re
import sys

# What an answer key looks like, wherever the benchmark is mounted. The pattern
# is on the file name and its parent, not an absolute path, so moving the corpus
# does not quietly disarm the guard.
_FORBIDDEN = re.compile(
    r"(?:"
    r"\.png\.graph\.json$"          # the answer key itself
    r"|[/\\]data[/\\]datasets[^/\\]*[/\\][^/\\]+[/\\][^/\\]+\.xml$"   # the source drawing
    r")", re.IGNORECASE)


class LeakageError(RuntimeError):
    """The execution path tried to open something only the judge may see."""


_armed = False
_allow = []


def arm(allow: list | None = None) -> None:
    """Refuse, from here on, any attempt to open an answer key in this process."""
    global _armed
    if _armed:
        return
    if allow:
        _allow.extend(os.path.normcase(os.path.abspath(p)) for p in allow)

    def hook(event, args):
        if event != "open":
            return
        path = args[0]
        if not isinstance(path, (str, bytes, os.PathLike)):
            return
        text = os.fsdecode(path)
        if not _FORBIDDEN.search(text.replace("\\", "/")) and not _FORBIDDEN.search(text):
            return
        if os.path.normcase(os.path.abspath(text)) in _allow:
            return
        raise LeakageError(
            "the execution path tried to open %r — answer keys and source XML are "
            "for the judge only (PLAN.md §Bất biến 1)" % text)

    sys.addaudithook(hook)
    _armed = True


def is_forbidden(path: str) -> bool:
    """Exposed so the test can assert on the pattern without arming anything."""
    text = os.fsdecode(path)
    return bool(_FORBIDDEN.search(text.replace("\\", "/")) or _FORBIDDEN.search(text))
