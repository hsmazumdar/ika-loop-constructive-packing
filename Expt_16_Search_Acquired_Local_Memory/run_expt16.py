"""Expt-16 entry. Search-acquired local memory (bounded acquisition diagnosis)."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from analysis import write_report  # noqa: E402
from config import apply_overrides, diagnostic_config, smoke_config  # noqa: E402
from experiment import audit_implementation, run_experiment, write_csv  # noqa: E402
from pieces import catalogue_hash  # noqa: E402

ROW_KEYS = {"acquisition_rows": "acquisition.csv", "box_rows": "boxes.csv", "counterfactual_rows": "counterfactuals.csv"}


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable"


def _validation() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--run-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [n for n, f in (("smoke", args.smoke), ("diagnostic", args.diagnostic), ("report", args.report)) if f]
    if len(modes) != 1:
        parser.error("choose one of --smoke, --diagnostic, or --report")
    preset = modes[0]
    if preset == "report":
        if not args.run_dir:
            parser.error("--report requires --run-dir")
        run_dir = Path(args.run_dir)
        write_report(
            run_dir,
            json.loads((run_dir / "config.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "runtime.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "offline.json").read_text(encoding="utf-8")),
        )
        return
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    (run_dir / "target_audit.json").write_text(json.dumps(audit_implementation(), indent=2), encoding="utf-8")
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    result = run_experiment(config)
    for key, name in ROW_KEYS.items():
        write_csv(run_dir / name, result[key])
    (run_dir / "entries.json").write_text(json.dumps(result["entries"], indent=2), encoding="utf-8")
    persist = {k: v for k, v in result.items() if k not in ROW_KEYS and k != "entries"}
    (run_dir / "offline.json").write_text(json.dumps(persist, indent=2), encoding="utf-8")
    meta = {"preset": preset, "python": platform.python_version(), "git": _git_commit(), "catalogue_hash": catalogue_hash()}
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, persist)
    print(json.dumps({"run": str(run_dir), "decision": result["decision"]["row"]}))


if __name__ == "__main__":
    main()
