"""Launch the manual demonstration GUI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mga2.gui import launch  # noqa: E402


if __name__ == "__main__":
    launch()
