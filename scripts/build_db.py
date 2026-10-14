#!/usr/bin/env python3
"""Build the SQLite analysis database from cleaned CSVs."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from olist_bi.db import build

build()
