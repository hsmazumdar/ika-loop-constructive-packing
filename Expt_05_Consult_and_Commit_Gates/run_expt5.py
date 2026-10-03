"""Expt-5 entry. Library learner unchanged; two gates trained then frozen."""

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
from config import apply_overrides, diagnostic_config, smoke_config  # noqa: E402
from experiment import (  # noqa: E402
    assert_splits,
    collect_labels,
    evaluate,
    fit_gates,
    load_split,
    reserve_train_val,
    train_library,
    write_csv,
)
from pieces import catalogue_hash  # noqa: E402
from tools.generate_eval import generate  # noqa: E402


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable"


def _validation() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode == 0


def _ensure_eval(limit: int) -> list[dict]:
    path = ROOT / "data" / "eval.json"
    if path.exists():
        tasks = load_split("eval")
        if len(tasks) >= limit:
            return tasks[:limit]
    generate(target=max(int(limit), 16))
    return load_split("eval")[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--train-boxes", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [name for name, flag in (("smoke", args.smoke), ("diagnostic", args.diagnostic)) if flag]
    if len(modes) != 1:
        parser.error("choose one of --smoke or --diagnostic")
    preset = modes[0]
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    train_all = load_split("train")
    development = load_split("development")
    train, train_val = reserve_train_val(train_all, config.train_val_count)
    eval_tasks = _ensure_eval(config.eval_boxes)
    assert_splits(train, development, eval_tasks, train_val)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    eval_rows = []
    all_labels = []
    gate_summaries = []
    learning_a = 0
    for seed in config.seeds:
        print(f"train library seed {seed}", flush=True)
        memory = train_library(config, int(seed), train, train_val)
        print(f"collect gate labels seed {seed} library={len(memory.active())}", flush=True)
        labels, cost = collect_labels(config, int(seed), train, memory)
        learning_a += cost
        consult_gate, commit_gate, summary = fit_gates(config, labels)
        summary["seed"] = int(seed)
        gate_summaries.append(summary)
        all_labels.extend(labels)
        (run_dir / f"gates_seed{seed}.json").write_text(
            json.dumps({"consult": consult_gate.to_dict(), "commit": commit_gate.to_dict(), "summary": summary}, indent=2),
            encoding="utf-8",
        )
        print(f"eval seed {seed}", flush=True)
        eval_rows.extend(evaluate(config, int(seed), eval_tasks, memory, consult_gate, commit_gate))
    annotated = attach_savings(eval_rows, config.quality_loss_margin)
    write_csv(run_dir / "eval.csv", annotated)
    write_csv(run_dir / "gate_labels.csv", all_labels)
    write_plots(run_dir, annotated)
    merged = {
        "n_commit_labels": sum(s.get("n_commit_labels", 0) for s in gate_summaries),
        "n_consult_states": sum(s.get("n_consult_states", 0) for s in gate_summaries),
        "n_unchosen": sum(s.get("n_unchosen", 0) for s in gate_summaries),
        "n_selected": sum(s.get("n_selected", 0) for s in gate_summaries),
        "consult_threshold": [s.get("consult_threshold") for s in gate_summaries],
        "commit_threshold": [s.get("commit_threshold") for s in gate_summaries],
        "commit_op_bias": {s["seed"]: s.get("commit_op_bias") for s in gate_summaries},
    }
    (run_dir / "gate_summary.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "n_eval": len(eval_tasks),
        "learning_A": learning_a,
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, annotated, merged, learning_a)
    print(json.dumps({"run": str(run_dir), "eval_rows": len(eval_rows), "labels": len(all_labels), "learning_A": learning_a}))


if __name__ == "__main__":
    main()
