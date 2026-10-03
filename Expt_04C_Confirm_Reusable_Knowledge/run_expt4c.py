"""Expt-4C entry point. Does not modify Expt-4B."""

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

from analysis import pairwise_rows, seed_summary, write_plots, write_report  # noqa: E402
from config import TRAIN_CONDITIONS, apply_overrides, confirm_config, smoke_config  # noqa: E402
from experiment import (  # noqa: E402
    assert_splits,
    final_evaluations,
    load_split,
    reserve_train_val,
    run_lifetime,
    write_csv,
)
from pieces import catalogue_hash  # noqa: E402
from tools.generate_final_test import generate  # noqa: E402


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable"


def _validation() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode == 0


def _ensure_test(limit: int | None) -> list[dict]:
    path = ROOT / "data" / "test.json"
    if not path.exists():
        generate()
    tasks = load_split("test")
    if limit is not None:
        return tasks[:limit]
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--train-boxes", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [name for name, flag in (("smoke", args.smoke), ("confirm", args.confirm)) if flag]
    if len(modes) != 1:
        parser.error("choose one of --smoke or --confirm")
    preset = modes[0]
    if not args.skip_validation and not _validation():
        print("validation failed; the confirmation was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else confirm_config()
    config = apply_overrides(config, args)
    train_all = load_split("train")
    development = load_split("development")
    train, train_val = reserve_train_val(train_all, config.train_val_count)
    test = _ensure_test(8 if preset == "smoke" else None)
    assert_splits(train, development, test, train_val)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    train_rows = []
    checkpoint_rows = []
    test_rows = []
    for seed in config.seeds:
        memories = {}
        for name in TRAIN_CONDITIONS:
            print(f"condition {name} seed {seed}", flush=True)
            outcome = run_lifetime(config, name, int(seed), train, development, train_val)
            train_rows.extend(outcome["train_rows"])
            checkpoint_rows.extend(outcome["checkpoint_rows"])
            memories[name] = outcome["memory"]
        print(f"final test seed {seed}", flush=True)
        test_rows.extend(final_evaluations(config, int(seed), test, memories))
    pairs = pairwise_rows(test_rows, config.quality_loss_margin)
    seeds = seed_summary(pairs)
    write_csv(run_dir / "train_boxes.csv", train_rows)
    write_csv(run_dir / "checkpoints.csv", checkpoint_rows)
    write_csv(run_dir / "final_test.csv", test_rows)
    write_csv(run_dir / "pairwise_vs_primitive.csv", pairs)
    write_csv(run_dir / "seed_summaries.csv", seeds)
    write_plots(run_dir, test_rows, pairs)
    meta = {"preset": preset, "python": platform.python_version(), "git": _git_commit(), "catalogue_hash": catalogue_hash(), "n_test": len(test)}
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, test_rows, pairs, seeds)
    print(json.dumps({"run": str(run_dir), "train_rows": len(train_rows), "test_rows": len(test_rows), "n_test": len(test)}))


if __name__ == "__main__":
    main()
