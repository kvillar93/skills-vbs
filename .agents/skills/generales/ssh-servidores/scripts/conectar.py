#!/usr/bin/env python3
"""Punto de entrada único: local o Cloud Agent.

Equivale a ssh_via_op.py. Existe para que las skills digan un solo comando.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from ssh_via_op import main

if __name__ == "__main__":
    raise SystemExit(main())
