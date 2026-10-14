#!/usr/bin/env python3
import sys
from pathlib import Path

# make the src/ package importable from tests without an install step
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
