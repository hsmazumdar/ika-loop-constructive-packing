"""Expt-7B entry. Frozen Expt-7 artifacts; no retraining."""

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
from experiment import expt7_dir, load_artifacts, load_split_eval, run_audit, write_csv  # noqa: E402
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
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if preset == "report":
        if not args.run_dir:
            parser.error("--report requires --run-dir")
        run_dir = Path(args.run_dir)
        import csv

        def _read(name):
            path = run_dir / name
            if not path.exists() or path.stat().st_size == 0:
                return []
            with path.open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))

        write_report(
            run_dir,
            json.loads((run_dir / "config.json").read_text(encoding="utf-8")),
            json.loads((run_dir / "runtime.json").read_text(encoding="utf-8")),
            _read("box_audit.csv"),
            _read("decisions.csv"),
            _read("ranker_decisions.csv"),
            _read("counterfactuals.csv"),
            _read("recall_levels.csv"),
            json.loads((run_dir / "cost_ledger.json").read_text(encoding="utf-8")),
        )
        return
    run_dir = ROOT / "results" / f"{stamp}_{preset}"
    run_dir.mkdir(parents=True)
    src = expt7_dir()
    if preset == "audit":
        payload = {
            "expt7_result": str(src),
            "exists": src.exists(),
            "libraries": [p.name for p in src.glob("library_seed*.json")],
            "rankers": [p.name for p in src.glob("ranker_seed*.json")],
            "consultation_identity": "consultation_cost = retrieval + applicability + learned_site_checks + index_probes + ranking",
            "expt7_recall_was_operation_level": True,
        }
        (run_dir / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (ROOT / "reports").mkdir(exist_ok=True)
        (ROOT / "reports" / "AUDIT.md").write_text(
            "# Expt-7B provenance\n\n" + json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(payload))
        return
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    tasks = load_split_eval()[: config.n_boxes]
    bundles = load_artifacts(config, config.seeds)
    frozen = {
        "reconstruction": False,
        "retrain": False,
        "seeds": [
            {
                "seed": b["seed"],
                "library_hash": b["library_hash"],
                "n_active": b["n_active"],
                "quality_threshold": b["quality"].threshold,
            }
            for b in bundles
        ],
    }
    (run_dir / "frozen_sources.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    result = run_audit(config, tasks, bundles)
    write_csv(run_dir / "box_audit.csv", result["box_rows"])
    write_csv(run_dir / "decisions.csv", result["decision_rows"])
    write_csv(run_dir / "ranker_decisions.csv", result["ranker_rows"])
    write_csv(run_dir / "counterfactuals.csv", result["counterfactuals"])
    write_csv(run_dir / "recall_levels.csv", result["recall_rows"])
    write_csv(run_dir / "oracle_action_recall.csv", result["oracle_action_rows"])
    (run_dir / "cost_ledger.json").write_text(json.dumps(result["ledger"], indent=2), encoding="utf-8")
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "expt7_result": str(src),
        "n_boxes": len(tasks),
        "n_pairs": len(result["box_rows"]),
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, result["box_rows"], result["decision_rows"], result["ranker_rows"], result["counterfactuals"], result["recall_rows"], result["ledger"])
    n_commit = sum(int(r["n_commitments"]) for r in result["box_rows"])
    print(json.dumps({"run": str(run_dir), "pairs": len(result["box_rows"]), "commitments": n_commit, "ranker_rows": len(result["ranker_rows"])}))


if __name__ == "__main__":
    main()
