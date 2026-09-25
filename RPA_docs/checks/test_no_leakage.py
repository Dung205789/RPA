#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The leakage test G0.5 asks for: red when the answer key is touched, green otherwise.

Three separate things are checked, because each catches a different way the
invariant can be broken:

1. **The guard bites.** With ``leak_guard.arm()`` in force, opening a
   ``*.png.graph.json`` or a dataset ``*.xml`` raises. A guard nobody has seen
   fail is not a guard.
2. **The guard lets real work through.** The same armed process can still open
   the case's PNG, the scenario JSON and the shape icons. A guard that blocks
   everything would be "passed" by a harness that does nothing.
3. **Nothing on the execution path names an answer key.** A static read of every
   module the harness imports for execution: no ``graph.json``, no reach into
   ``data/datasets/*/*.xml``. This catches a leak that a particular run happens
   not to exercise.

    python RPA_docs/checks/test_no_leakage.py
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest RPA_docs/checks/test_no_leakage.py -q
"""
from __future__ import annotations

import glob
import re
import subprocess
import sys
from pathlib import Path

DOCUMENTS = Path(__file__).resolve().parents[2]
RPA_DRAWIO = DOCUMENTS / "RPA_drawio"
sys.path.insert(0, str(RPA_DRAWIO))

# Everything the harness imports to *run* a scenario. The judges
# (`judge_drawings.py`, `RPA_docs/checks/graph_score.py`) are deliberately absent:
# reading the answer key is their job.
EXECUTION_PATH = [
    RPA_DRAWIO / "drawio_executor.py",
    RPA_DRAWIO / "drawio_ops.py",
    RPA_DRAWIO / "cell_tracker.py",
    RPA_DRAWIO / "palette_matcher.py",
    RPA_DRAWIO / "rpa_env.py",
    RPA_DRAWIO / "step_parser.py",
    RPA_DRAWIO / "by_text.py",
    RPA_DRAWIO / "image_to_scenario.py",
    RPA_DRAWIO / "mx_oracle.py",
    RPA_DRAWIO / "oracle_steps.py",
    RPA_DRAWIO / "oracle_verdict.py",
    DOCUMENTS / "run_drawio_v2.py",
]

_SMELLS = [
    re.compile(r"graph\.json"),
    re.compile(r"datasets?[^\"']*\*\.xml"),
    re.compile(r"answer[_ ]?key", re.IGNORECASE),
]


def _sample_answer_key():
    hits = sorted(glob.glob(str(DOCUMENTS.parent / "data" / "datasets" / "*"
                                / "*.png.graph.json")))
    return hits[0] if hits else None


def _sample_source_xml():
    hits = sorted(glob.glob(str(DOCUMENTS.parent / "data" / "datasets" / "*" / "*.xml")))
    return hits[0] if hits else None


def test_guard_pattern_matches_keys_and_xml():
    import leak_guard
    key, xml = _sample_answer_key(), _sample_source_xml()
    assert key, "no answer key on disk to test against"
    assert leak_guard.is_forbidden(key), key
    assert leak_guard.is_forbidden(xml), xml


def test_guard_allows_the_png_and_the_scenario():
    import leak_guard
    key = _sample_answer_key()
    png = key.replace(".png.graph.json", ".png")
    assert not leak_guard.is_forbidden(png), png
    assert not leak_guard.is_forbidden(
        str(DOCUMENTS / "RPA_Datasets_new30_v2" / "easy_e01_v1_s5b0l0.json"))
    assert not leak_guard.is_forbidden(str(RPA_DRAWIO / "shape_icons" / "rectangle.png"))
    # The harness writes its own model.xml into result/ — that is the drawing, not
    # the source, and must stay openable.
    assert not leak_guard.is_forbidden(str(DOCUMENTS / "result" / "x" / "model.xml"))


def test_armed_process_refuses_the_key_and_allows_the_png():
    """Run it in a child: an audit hook cannot be removed once installed."""
    key = _sample_answer_key()
    png = key.replace(".png.graph.json", ".png")
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "import leak_guard; leak_guard.arm()\n"
        "open(%r, 'rb').close()\n"                       # the PNG must work
        "try:\n"
        "    open(%r, 'rb').close()\n"
        "except leak_guard.LeakageError:\n"
        "    print('BLOCKED')\n"
        "else:\n"
        "    print('LEAKED')\n" % (str(RPA_DRAWIO), png, key)
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         timeout=60)
    assert "BLOCKED" in out.stdout, out.stdout + out.stderr


def _prose_lines(text: str) -> set:
    """Line numbers that are comment or docstring, i.e. prose rather than code.

    Stating the rule in a docstring — "the answer key is never opened here" — is
    the opposite of breaking it, so those lines must not trip the scan. Only
    strings that *are* docstrings are excused; a path in an ordinary string
    literal is still code and still counts.
    """
    import ast
    import io
    import tokenize
    lines = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                lines.update(range(tok.start[0], tok.end[0] + 1))
    except (tokenize.TokenError, IndentationError):
        pass
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return lines
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return lines


def test_execution_path_never_names_an_answer_key():
    offenders = []
    for path in EXECUTION_PATH:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        prose = _prose_lines(text)
        for line_no, line in enumerate(text.splitlines(), 1):
            if line_no in prose:
                continue
            for rx in _SMELLS:
                if rx.search(line):
                    offenders.append("%s:%d: %s" % (path.name, line_no, line.strip()[:90]))
    assert not offenders, "execution path names answer-key material:\n" + "\n".join(offenders)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except AssertionError as exc:
            failed += 1
            print("FAIL  %s\n      %s" % (t.__name__, exc))
    print("\n%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
