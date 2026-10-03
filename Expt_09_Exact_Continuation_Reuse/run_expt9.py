"""Expt-9 entry. Exact continuation reuse."""

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


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable"


def _validation() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--run-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--n-boxes", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [name for name, flag in (("audit", args.audit), ("smoke", args.smoke), ("diagnostic", args.diagnostic), ("report", args.report)) if flag]
    if len(modes) != 1:
        parser.error("choose one of --audit, --smoke, --diagnostic, or --report")
    preset = modes[0]
    if preset == "report":
        if not args.run_dir:
            parser.error("--report requires --run-dir")
        run_dir = Path(args.run_dir)
        write_report(
            run_dir,
            json.loads((run_dir / "config.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "runtime.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "target_audit.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "offline.json").read_text(encoding="utf-8")),
        )
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    audit = audit_implementation()
    (run_dir / "target_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if preset == "audit":
        (ROOT / "reports").mkdir(exist_ok=True)
        (ROOT / "reports" / "AUDIT.md").write_text("# Expt-9 audit\n\n" + json.dumps(audit, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"run": str(run_dir), "not_abstraction": True}))
        return
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    result = run_experiment(config)
    write_csv(run_dir / "eval.csv", result["rows"])
    persist = {k: v for k, v in result.items() if k != "rows"}
    (run_dir / "offline.json").write_text(json.dumps(persist, indent=2), encoding="utf-8")
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "n_store": len(result["store_ids"]),
        "n_fresh": len(result["fresh_ids"]),
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, audit, result)
    print(
        json.dumps(
            {
                "run": str(run_dir),
                "n_keys": result["n_keys"],
                "hit_rate_recurring": result["recurrence_hit_rate_recurring"],
                "hit_rate_fresh": result["recurrence_hit_rate_fresh"],
                "useful_on_recurring": result["useful_on_recurring"],
            }
        )
    )


if __name__ == "__main__":
    main()
