"""Run a reproducible MGA Expt-1 experiment preset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

from mga.experiment import run_preset
from mga.paths import CONFIGS_DIR, RESULTS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MGA Expt-1 packing experiment")
    parser.add_argument("--config", type=Path, default=CONFIGS_DIR / "default.json")
    parser.add_argument("--preset", choices=("tiny", "smoke"), default="smoke")
    parser.add_argument(
        "--time-budget-seconds",
        type=float,
        default=None,
        help="Optional wall-clock cap. Partial outputs are saved if the cap is hit.",
    )
    args = parser.parse_args()
    out = run_preset(args.config, args.preset, time_budget_seconds=args.time_budget_seconds)
    print(f"Wrote results to {out}")
    print(f"Latest pointer: {RESULTS_DIR / 'LATEST_RUN.txt'}")


if __name__ == "__main__":
    main()
