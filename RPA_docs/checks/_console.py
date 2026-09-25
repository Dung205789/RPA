#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Make these scripts printable on a Windows console.

The default code page here is cp1252, so a report written in Vietnamese dies on
its first "đ" with a UnicodeEncodeError — after doing all the work. Importing
this module switches the process's own streams to UTF-8 and leaves everything
else alone.
"""
from __future__ import annotations

import sys


def utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


utf8()
