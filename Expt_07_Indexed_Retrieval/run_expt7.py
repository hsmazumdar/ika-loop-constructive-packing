"""Expt-7 entry. Frozen libraries; index and ranker trained then frozen."""

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

from analysis import write_plots, write_report  # noqa: E402
from config import EXPT6_DEV, apply_overrides, diagnostic_config, smoke_config  # noqa: E402
from experiment import (  # noqa: E402
    assert_splits,
    choose_budget,
    choose_k,
    collect_ranker_labels,
    ensure_boxes,
    fit_ranker,
    freeze_libraries,
    load_json_tasks,
    read_csv,
    run_eval,
    run_recall_diagnostic,
    shortlist_recall_from_oracle_rows,
    source_hashes,
    verify_frozen,
    write_csv,
)
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
        config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
        meta = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8"))
        rows = read_csv(run_dir / "eval.csv")
        recall = json.loads((run_dir / "recall.json").read_text(encoding="utf-8"))
        selection = json.loads((run_dir / "selection.json").read_text(encoding="utf-8"))
        ledger = json.loads((run_dir / "cost_ledger.json").read_text(encoding="utf-8"))
        write_plots(run_dir, rows)
        write_report(run_dir, config, meta, rows, recall, selection, ledger)
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    if preset == "audit":
        audit = {
            "libraries": "Expt-6 snapshots copied into Expt_07_Indexed_Retrieval/snapshots",
            "gates": str(ROOT.parent / "Expt_05_Consult_and_Commit_Gates" / "results" / "20260929_212658_diagnostic"),
            "dev_oracle_rows": EXPT6_DEV,
            "reconstruction": False if (ROOT / "snapshots" / "library_seed11.json").exists() else True,
        }
        (run_dir / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        print(json.dumps({"run": str(run_dir), **audit}))
        return
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    smoke_tasks = ensure_boxes("smoke", 4, 2026092971)
    extra = [ROOT / "data" / "smoke.json"]
    eval_tasks = smoke_tasks[: config.n_boxes] if preset == "smoke" else ensure_boxes("eval", config.n_boxes, 2026092972, extra)
    split_note = assert_splits(eval_tasks, None if preset == "smoke" else smoke_tasks)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    snapshot_dir = ROOT / "snapshots"
    bundles = freeze_libraries(config, snapshot_dir, config.seeds)
    index_build = [{"seed": b["seed"], "build_s": b["index"].build_s, "n_bytes": b["index"].n_bytes, "n_entries": len(b["index"].entries)} for b in bundles]
    for bundle in bundles:
        (run_dir / f"index_seed{bundle['seed']}.json").write_text(json.dumps(bundle["index"].to_json(), indent=2), encoding="utf-8")
        (run_dir / f"library_seed{bundle['seed']}.json").write_text((snapshot_dir / f"library_seed{bundle['seed']}.json").read_text(encoding="utf-8"), encoding="utf-8")
    dev_csv = ROOT.parent / Path(EXPT6_DEV) / "candidate_replays.csv"
    dev_rows = read_csv(dev_csv) if dev_csv.exists() else []
    if preset == "smoke" and dev_rows:
        dev_rows = [r for r in dev_rows if str(r.get("seed")) == "11"][:400]
    recalls = [shortlist_recall_from_oracle_rows(dev_rows, k) for k in config.k_candidates]
    k = choose_k(recalls) if not (len(config.k_candidates) == 1) else int(config.k_candidates[0])
    print(f"frozen K={k} from development recall {recalls}", flush=True)
    train = json.loads((ROOT / "data" / "train.json").read_text(encoding="utf-8"))["tasks"]
    rankers = {}
    learning_a = 0
    all_labels = []
    for bundle in bundles:
        print(f"collect ranker labels seed {bundle['seed']}", flush=True)
        labels, cost = collect_ranker_labels(config, int(bundle["seed"]), train, bundle, max(config.k_candidates))
        learning_a += cost
        all_labels.extend(labels)
        benefit, quality = fit_ranker(config, labels)
        rankers[int(bundle["seed"])] = (benefit, quality)
        (run_dir / f"ranker_seed{bundle['seed']}.json").write_text(
            json.dumps({"benefit": benefit.to_dict(), "quality": quality.to_dict()}, indent=2),
            encoding="utf-8",
        )
    write_csv(run_dir / "ranker_labels.csv", all_labels)
    if preset == "smoke":
        budget = int(config.consult_budget)
        budget_info = {"chosen": budget, "table": [{"consult_budget": budget, "note": "smoke: frozen without sweep"}]}
    else:
        dev_path = ROOT.parent / "Expt_06_Frozen_Library_Opportunity" / "data" / "eval.json"
        dev_tasks = load_json_tasks(dev_path)[: config.n_dev_boxes]
        print("select consult budget on Expt-6 eval boxes (development)", flush=True)
        budget_info = choose_budget(config, dev_tasks, bundles, k, rankers)
        budget = int(budget_info["chosen"])
    print(f"frozen consult_budget={budget}", flush=True)
    selection = {"k": k, "consult_budget": budget, "dev_recall": recalls, "budget_table": budget_info.get("table")}
    (run_dir / "selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
    print(f"eval {len(bundles)} libraries x {len(eval_tasks)} boxes", flush=True)
    rows = run_eval(config, eval_tasks, bundles, k, budget, rankers)
    write_csv(run_dir / "eval.csv", rows)
    print("shortlist opportunity recall (sampled oracle, diagnosis only)", flush=True)
    ledger = {"skip_A": 0, "commit_A": 0, "skip_rollouts": 0, "commit_rollouts": 0, "learning_A": learning_a}
    recall_boxes, recall_states = run_recall_diagnostic(config, eval_tasks, bundles, k, ledger)
    n_useful = sum(1 for r in recall_states)
    n_hit = sum(1 for r in recall_states if r.get("shortlist_hit"))
    recall = {
        "k": k,
        "n_states_with_oracle_useful": n_useful,
        "n_shortlist_contains_useful": n_hit,
        "recall": None if not n_useful else n_hit / n_useful,
        "n_pairs": len(recall_boxes),
    }
    write_csv(run_dir / "recall_states.csv", recall_states)
    (run_dir / "recall.json").write_text(json.dumps(recall, indent=2), encoding="utf-8")
    verify = verify_frozen(bundles, snapshot_dir)
    (run_dir / "hash_verify.json").write_text(json.dumps(verify, indent=2), encoding="utf-8")
    (run_dir / "cost_ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps({"task_ids": [t["task_id"] for t in eval_tasks], "split": split_note, "k": k, "consult_budget": budget}, indent=2), encoding="utf-8")
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "source_hashes": source_hashes(),
        "reconstruction": False,
        "index_build": index_build,
        "n_eval": len(eval_tasks),
        "learning_A": learning_a,
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (run_dir / "figures").mkdir(exist_ok=True)
    write_plots(run_dir, rows)
    write_report(run_dir, config.to_dict(), meta, rows, recall, selection, ledger)
    print(json.dumps({"run": str(run_dir), "eval_rows": len(rows), "k": k, "consult_budget": budget, "recall": recall.get("recall"), "learning_A": learning_a}))


if __name__ == "__main__":
    main()
