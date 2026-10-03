"""Expt-8 entry. Frozen libraries. Offline action-level prediction before any new deployment."""

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
from experiment import (  # noqa: E402
    audit_frozen_implementation,
    expt7_dir,
    load_artifacts,
    load_json_tasks,
    maybe_run_wholebox,
    run_offline,
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


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items() if k != "models_by_seed"}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, tuple):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


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
    src = expt7_dir()
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
            json.loads((run_dir / "wholebox.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "cost_ledger.json").read_text(encoding="utf-8")),
        )
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    if preset == "audit":
        audit = audit_frozen_implementation([])
        audit["expt7_result"] = str(src)
        audit["exists"] = src.exists()
        (run_dir / "target_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        (ROOT / "reports").mkdir(exist_ok=True)
        (ROOT / "reports" / "AUDIT.md").write_text("# Expt-8 target audit\n\n" + json.dumps(audit, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"run": str(run_dir), "train_deploy_mismatch": audit.get("train_deploy_action_mismatch"), "cap_mismatch": audit.get("cap_mismatch")}))
        return
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    dev_path = ROOT.parent / "Expt_06_Frozen_Library_Opportunity" / "data" / "eval.json"
    tasks = load_json_tasks(dev_path)[: config.n_boxes]
    bundles = load_artifacts(config, config.seeds)
    audit = audit_frozen_implementation(bundles)
    (run_dir / "target_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    offline = run_offline(config, tasks, bundles)
    write_csv(run_dir / "labels_fit.csv", offline["labels_fit"])
    write_csv(run_dir / "labels_val.csv", offline["labels_val"])
    slim_scored = []
    for row in offline["scored_val"]:
        slim_scored.append({k: row[k] for k in row if k not in ("context_vector", "action_vector")})
    write_csv(run_dir / "scored_val.csv", slim_scored)
    wholebox = maybe_run_wholebox(config, offline, bundles)
    if wholebox.get("rows"):
        write_csv(run_dir / "fresh_eval.csv", wholebox["rows"])
    (run_dir / "offline.json").write_text(
        json.dumps(
            {
                "fit_ids": offline["fit_ids"],
                "val_ids": offline["val_ids"],
                "pooled": offline["pooled"],
                "predictor_summaries": offline["predictor_summaries"],
                "beats_constant": offline["beats_constant"],
                "proceed_placement": offline["proceed_placement"],
                "proceed_wholebox": offline["proceed_wholebox"],
                "placement_table": offline["placement_table"],
                "chosen_n_placements": offline["chosen_n_placements"],
                "remaining_check": offline["remaining_check"],
                "gate_first": offline["gate_first"],
                "gate_all": offline["gate_all"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "wholebox.json").write_text(json.dumps({k: v for k, v in wholebox.items() if k != "rows"} | {"n_rows": len(wholebox.get("rows") or [])}, indent=2), encoding="utf-8")
    (run_dir / "cost_ledger.json").write_text(json.dumps(offline["ledger"], indent=2), encoding="utf-8")
    frozen = [{"seed": b["seed"], "library_hash": b["library_hash"], "n_active": b["n_active"]} for b in bundles]
    (run_dir / "frozen_sources.json").write_text(json.dumps({"retrain": False, "seeds": frozen}, indent=2), encoding="utf-8")
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "expt7_result": str(src),
        "n_fit": len(offline["fit_ids"]),
        "n_val": len(offline["val_ids"]),
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, audit, offline, wholebox, offline["ledger"])
    print(
        json.dumps(
            {
                "run": str(run_dir),
                "fit": len(offline["labels_fit"]),
                "val": len(offline["labels_val"]),
                "beats_constant": offline["beats_constant"],
                "proceed_placement": offline["proceed_placement"],
                "proceed_wholebox": offline["proceed_wholebox"],
            }
        )
    )


if __name__ == "__main__":
    main()
