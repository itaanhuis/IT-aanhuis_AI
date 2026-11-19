#!/usr/bin/env python3
"""
it_aanhuis.py - startscript voor de IT-aanhuis Helpdesk AI.

Start:  python it_aanhuis.py      (of dubbelklik run.bat op Windows)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from itaanhuis.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main() or 0)
