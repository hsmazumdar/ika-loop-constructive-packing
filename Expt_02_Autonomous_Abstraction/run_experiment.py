"""Launch or resume an Expt-2 run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mga2.experiment import execute_run, load_config  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=["tiny", "discovery_smoke", "memory_sweep", "expt2a"])
    parser.add_argument("--config")
    parser.add_argument("--label", default="")
    parser.add_argument("--cheap-scan-reserve", type=int, default=None)
    parser.add_argument("--wall-cap-minutes", type=float, default=None)
    parser.add_argument("--resume")
    args = parser.parse_args()
    if args.resume:
        state = execute_run("resume", {}, args.wall_cap_minutes, resume=Path(args.resume))
    else:
        if args.preset is None:
            raise SystemExit("pass --preset or --resume")
        if args.preset == "memory_sweep":
            raise SystemExit(
                "memory_sweep is configured in configs/memory_sweep.json and is not launched in this delivery"
            )
        if args.preset == "expt2a":
            from mga2.experiment import execute_expt2a

            config_path = Path(args.config) if args.config else ROOT / "configs" / "expt2a.json"
            state = execute_expt2a(load_config(config_path))
            print(json.dumps({"run_dir": state.get("run_dir"), "complete": state.get("complete"), "stop_reason": state.get("stop_reason"), "report": state.get("report"), "planned": state.get("planned"), "completed": len(state.get("completed", []))}))
            return
        config_path = Path(args.config) if args.config else ROOT / "configs" / (
            "smoke.json" if args.preset == "discovery_smoke" else "default.json"
        )
        wall = args.wall_cap_minutes
        if args.preset == "discovery_smoke" and wall is None:
            wall = 30.0
        if args.preset == "discovery_smoke":
            manifest = ROOT / "data" / "runtime" / "manifest.json"
            if not manifest.exists():
                from tools.generate_tasks import generate

                generate(load_config(config_path))
        config = load_config(config_path)
        if args.label:
            config["run_label"] = args.label
        if args.cheap_scan_reserve is not None:
            config.setdefault("budgets", {})["cheap_scan_reserve"] = args.cheap_scan_reserve
        state = execute_run(args.preset, config, wall, resume=None)
    print(json.dumps({"run_dir": state.get("run_dir"), "complete": state.get("complete"), "stop_reason": state.get("stop_reason"), "report": state.get("report"), "planned": state.get("planned"), "completed": len(state.get("completed", []))}))


if __name__ == "__main__":
    main()
