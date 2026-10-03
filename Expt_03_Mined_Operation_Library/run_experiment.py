"""Entry points. Paths are resolved from this file's directory."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mga3.experiment import EXPT_ROOT, apply_preset, execute, load_config  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "default.json"))
    parser.add_argument("--preset", default=None)
    parser.add_argument("--wall-cap-minutes", type=float, default=None)
    parser.add_argument("--resume", default=None)
    args = parser.parse_args()
    config = apply_preset(load_config(Path(args.config)), args.preset)
    if args.resume:
        run_dir = Path(args.resume)
        if not run_dir.is_absolute():
            run_dir = ROOT / run_dir
        summary = execute(config, run_dir, args.wall_cap_minutes, resume=True)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = args.preset or "run"
        run_dir = ROOT / "results" / f"{stamp}_{label}"
        summary = execute(config, run_dir, args.wall_cap_minutes, resume=False)
    print(json.dumps({"run": str(run_dir), "complete": summary["complete"], "episodes": summary["episodes"], "stop": summary["stop_reason"]}))


if __name__ == "__main__":
    main()
