#!/usr/bin/env python3
"""Run GOD from a checkout without installing it: ./god capabilities -r ~/ov"""

import sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit("GOD requires Python 3.11+")
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from god.cli import main  # noqa: E402

raise SystemExit(main())
