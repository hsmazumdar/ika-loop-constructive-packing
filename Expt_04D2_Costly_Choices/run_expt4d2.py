"""Expt-4D2 entry: accounting audit, then costly-choice replays. No larger training run."""

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

from analysis import attach_savings, write_plots, write_report  # noqa: E402
from audit import run_existing_audit, write_audit_report  # noqa: E402
from config import apply_overrides, diagnostic_config, smoke_config  # noqa: E402
from experiment import (  # noqa: E402
    assert_splits,
    diagnose,
    load_split,
    reserve_train_val,
    train_library,
    write_csv,
)
from pieces import catalogue_hash  # noqa: E402
from tools.generate_fresh import generate  # noqa: E402


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable"


def _validation() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode == 0


def _ensure_fresh(limit: int) -> list[dict]:
    path = ROOT / "data" / "fresh.json"
    if not path.exists():
        generate(target=limit)
    tasks = load_split("fresh")
    return tasks[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true", help="accounting + existing 15 replays only")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--train-boxes", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [name for name, flag in (("audit", args.audit), ("smoke", args.smoke), ("diagnostic", args.diagnostic)) if flag]
    if len(modes) != 1:
        parser.error("choose one of --audit, --smoke, or --diagnostic")
    preset = modes[0]
    if preset != "audit" and not args.skip_validation and not _validation():
        print("validation failed; diagnostics were not started")
        sys.exit(1)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    audit, existing_table, existing_summary = run_existing_audit(run_dir)
    write_csv(run_dir / "existing_replays.csv", existing_table)
    write_audit_report(run_dir / "AUDIT.md", audit, existing_summary, existing_table)
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    write_audit_report(ROOT / "reports" / "AUDIT.md", audit, existing_summary, existing_table)
    if preset == "audit":
        meta = {"preset": "audit", "python": platform.python_version(), "git": _git_commit(), "catalogue_hash": catalogue_hash()}
        (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        write_report(run_dir, {"quality_loss_margin": 1.0}, meta, [], [], existing_table, existing_summary, audit)
        print(json.dumps({"run": str(run_dir), "existing_replays": len(existing_table)}))
        return
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    train_all = load_split("train")
    development = load_split("development")
    train, train_val = reserve_train_val(train_all, config.train_val_count)
    fresh = _ensure_fresh(4 if preset == "smoke" else config.fresh_boxes)
    assert_splits(train, development, fresh, train_val)
    diag_rows = []
    replay_rows = []
    for seed in config.seeds:
        print(f"train library seed {seed}", flush=True)
        memory = train_library(config, int(seed), train, train_val)
        print(f"diagnose seed {seed} library={len(memory.active())}", flush=True)
        for split_name, tasks in (("development", development), ("fresh", fresh)):
            rows, replays = diagnose(config, int(seed), tasks, memory, split_name)
            diag_rows.extend(rows)
            replay_rows.extend(replays)
    annotated = attach_savings(diag_rows, config.quality_loss_margin)
    write_csv(run_dir / "diagnostics.csv", annotated)
    write_csv(run_dir / "new_replays.csv", replay_rows)
    write_plots(run_dir, annotated, replay_rows)
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "n_development": len(development),
        "n_fresh": len(fresh),
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, annotated, replay_rows, existing_table, existing_summary, audit)
    print(json.dumps({"run": str(run_dir), "diag_rows": len(diag_rows), "new_replays": len(replay_rows), "existing": len(existing_table)}))


if __name__ == "__main__":
    main()
