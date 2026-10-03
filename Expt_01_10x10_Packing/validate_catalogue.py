"""Independent catalogue feasibility check (hidden from the agent)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

from mga.paths import RESULTS_DIR
from mga.validation import save_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=RESULTS_DIR / "catalogue_validation.json")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--n", type=int, default=2)
    args = parser.parse_args()
    payload = save_validation(args.output, n=args.n, timeout=args.timeout)
    print(f"status={payload['status']} n_found={payload['n_found']} -> {args.output}")


if __name__ == "__main__":
    main()
