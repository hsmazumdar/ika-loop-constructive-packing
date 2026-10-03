"""Launch the Expt-1 desktop demonstration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

from mga.gui import main


if __name__ == "__main__":
    main()
