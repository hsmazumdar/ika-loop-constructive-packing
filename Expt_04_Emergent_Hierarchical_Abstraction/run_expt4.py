"""Entry point.

The objective of this experiment is not to discover a better packing heuristic.
Packing is the observable environment. The experiment asks whether repeated
information can autonomously become compressed reusable knowledge, and whether
that knowledge allows future problems to be solved with less deliberation.
"""

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

from analysis import write_knowledge, write_report  # noqa: E402
from config import apply_overrides, full_config, pilot_config, smoke_config  # noqa: E402
from evaluator import (  # noqa: E402
    AGENT_NAMES,
    assert_split_disjoint,
    load_split,
    run_lifetime,
    write_tables,
    _phase_pools,
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
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--agent", default=None)
    parser.add_argument("--train-boxes", type=int, default=None)
    parser.add_argument("--memory-capacity", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [name for name, flag in (("smoke", args.smoke), ("pilot", args.pilot), ("full", args.full)) if flag]
    if len(modes) != 1:
        parser.error("choose one of --smoke, --pilot, or --full")
    preset = modes[0]
    if not args.skip_validation and not _validation():
        print("validation failed; the lifetime was not started")
        sys.exit(1)
    config = {"smoke": smoke_config, "pilot": pilot_config, "full": full_config}[preset]()
    config = apply_overrides(config, args)
    agents = AGENT_NAMES
    if args.agent:
        if args.agent not in AGENT_NAMES:
            parser.error("unknown agent")
        agents = (args.agent,)
    train = load_split("train")
    heldout = load_split("test")
    if config.heldout_limit:
        heldout = heldout[: int(config.heldout_limit)]
    _phase_a, phase_b, probe = _phase_pools(train, config.master_seed, config.probe_count)
    assert_split_disjoint(train, heldout, probe)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    train_rows = []
    checkpoint_rows = []
    special_rows = []
    memories = {}
    for seed in config.seeds:
        for name in agents:
            print(f"agent {name} seed {seed}", flush=True)
            outcome = run_lifetime(config, name, int(seed), train, heldout, probe, phase_b)
            train_rows.extend(outcome["train_rows"])
            checkpoint_rows.extend(outcome["checkpoint_rows"])
            special_rows.extend(outcome["special_rows"])
            if name == "hierarchical":
                memories[name] = outcome["memory"]
    write_tables(run_dir, train_rows, checkpoint_rows, special_rows)
    write_knowledge(run_dir, memories)
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta)
    print(json.dumps({"run": str(run_dir), "train_rows": len(train_rows), "checkpoints": len(checkpoint_rows)}))


if __name__ == "__main__":
    main()
