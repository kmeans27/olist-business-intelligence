#!/usr/bin/env python3
"""Fetch raw Olist CSVs, then apply documented cleaning rules."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from olist_bi.data import fetch, clean  # noqa

fetch()
clean()
