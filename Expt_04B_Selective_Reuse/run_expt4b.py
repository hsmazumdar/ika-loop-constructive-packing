"""Expt-4B entry point."""

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

from analysis import write_plots, write_report  # noqa: E402
from config import CONDITION_NAMES, apply_overrides, diagnostic_config, smoke_config  # noqa: E402
from experiment import (  # noqa: E402
    assert_splits,
    load_split,
    operation_rows,
    phase_pools,
    reserve_train_val,
    run_lifetime,
    write_tables,
)
from pieces import catalogue_hash  # noqa: E402


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable"


def _validation() -> bool:
    completed = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT)
    return completed.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--condition", default=None)
    parser.add_argument("--train-boxes", type=int, default=None)
    parser.add_argument("--memory-capacity", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [name for name, flag in (("smoke", args.smoke), ("diagnostic", args.diagnostic)) if flag]
    if len(modes) != 1:
        parser.error("choose one of --smoke or --diagnostic")
    preset = modes[0]
    if not args.skip_validation and not _validation():
        print("validation failed; the lifetime was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    conditions = CONDITION_NAMES
    if args.condition:
        if args.condition not in CONDITION_NAMES:
            parser.error("unknown condition")
        conditions = (args.condition,)
    train_all = load_split("train")
    heldout = load_split("test")
    if config.heldout_limit:
        heldout = heldout[: int(config.heldout_limit)]
    train, train_val = reserve_train_val(train_all, config.train_val_count)
    _unused, phase_b, probe = phase_pools(train, config.master_seed, config.probe_count)
    assert_splits(train, heldout, probe, train_val)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    train_rows = []
    checkpoint_rows = []
    pair_rows = []
    op_rows = []
    for seed in config.seeds:
        for name in conditions:
            print(f"condition {name} seed {seed}", flush=True)
            outcome = run_lifetime(config, name, int(seed), train, heldout, probe, phase_b, train_val)
            train_rows.extend(outcome["train_rows"])
            checkpoint_rows.extend(outcome["checkpoint_rows"])
            pair_rows.extend(outcome["pair_rows"])
            op_rows.extend(operation_rows(name, int(seed), outcome["memory"]))
    write_tables(run_dir, train_rows, checkpoint_rows, pair_rows, op_rows)
    write_plots(run_dir, checkpoint_rows, train_rows)
    meta = {"preset": preset, "python": platform.python_version(), "git": _git_commit(), "catalogue_hash": catalogue_hash()}
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, checkpoint_rows, pair_rows, op_rows)
    print(json.dumps({"run": str(run_dir), "train_rows": len(train_rows), "checkpoints": len(checkpoint_rows), "pairs": len(pair_rows)}))


if __name__ == "__main__":
    main()
