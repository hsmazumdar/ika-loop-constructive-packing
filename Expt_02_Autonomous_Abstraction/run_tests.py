"""Run the Expt-2 correctness tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(ROOT / "tests")]))
