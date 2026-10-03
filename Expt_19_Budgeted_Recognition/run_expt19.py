"""Expt-19 entry. Recognition only. No commitment."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "Expt_16_Search_Acquired_Local_Memory" / "src"))
sys.path.insert(0, str(REPO / "Expt_18_Arrangement_Utility" / "src"))
sys.path.insert(0, str(ROOT / "src"))

from analysis import write_report  # noqa: E402
from config import diagnostic_config, smoke_config  # noqa: E402
from experiment import audit_implementation, run_experiment, write_csv  # noqa: E402
from pieces import catalogue_hash  # noqa: E402


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable"


def _validation() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    if args.smoke == args.diagnostic:
        parser.error("choose one of --smoke or --diagnostic")
    preset = "smoke" if args.smoke else "diagnostic"
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    (run_dir / "target_audit.json").write_text(json.dumps(audit_implementation(), indent=2), encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    result = run_experiment(config)
    write_csv(run_dir / "development.csv", result["development_rows"])
    write_csv(run_dir / "boxes.csv", result["box_rows"])
    write_csv(run_dir / "reference_actions.csv", result["action_rows"])
    meta = {"preset": preset, "python": platform.python_version(), "git": _git_commit(), "catalogue_hash": catalogue_hash()}
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, result)
    print(json.dumps({"run": str(run_dir), "decision": result["decision"]["row"], "budget": result["budget"]}))


if __name__ == "__main__":
    main()
