"""Expt-8C entry. Audit provenance, freeze 8B models, score unseen boxes once."""

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
    generate_unseen,
    load_artifacts,
    maybe_run_wholebox,
    run_unseen,
    write_csv,
)
from freeze import freeze_from_expt8b, load_frozen  # noqa: E402
from pieces import catalogue_hash  # noqa: E402
from provenance import write_manifest  # noqa: E402


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
        freeze = freeze_from_expt8b()
        audit["frozen_models"] = {
            "labels_fit_sha256": freeze["labels_fit_sha256"],
            "model_payload_sha256": freeze["model_payload_sha256"],
            "n_fit_labels": freeze["n_fit_labels"],
            "label_remaining_budget": freeze["label_remaining_budget"],
            "cache_key": freeze["cache_key"],
        }
        (run_dir / "target_audit.json").write_text(json.dumps({k: v for k, v in audit.items() if k != "box_uses"}, indent=2), encoding="utf-8")
        write_manifest(audit, ROOT / "data" / "box_manifest.csv")
        (ROOT / "reports").mkdir(exist_ok=True)
        (ROOT / "reports" / "AUDIT.md").write_text(
            "# Expt-8C audit\n\n"
            + json.dumps({k: v for k, v in audit.items() if k != "box_uses"}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "run": str(run_dir),
                    "holdout_reused": audit.get("n_holdout_with_prior_use"),
                    "fit_y_changed": (audit.get("fit_label_comparison") or {}).get("n_y_changed"),
                    "model_payload_sha256": freeze["model_payload_sha256"],
                }
            )
        )
        return
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    freeze_from_expt8b()
    frozen = load_frozen()
    bundles = load_artifacts(config, config.seeds)
    audit = audit_frozen_implementation(bundles)
    write_manifest(audit, ROOT / "data" / "box_manifest.csv")
    slim_audit = {k: v for k, v in audit.items() if k != "box_uses"}
    (run_dir / "target_audit.json").write_text(json.dumps(slim_audit, indent=2), encoding="utf-8")
    tasks = generate_unseen(config)
    offline = run_unseen(config, tasks, bundles, frozen)
    write_csv(run_dir / "labels_unseen.csv", offline["labels_unseen"])
    slim = [{k: row[k] for k in row if k not in ("context_vector", "action_vector")} for row in offline["scored_unseen"]]
    write_csv(run_dir / "scored_unseen.csv", slim)
    wholebox = maybe_run_wholebox(config, offline, bundles)
    persist = {k: v for k, v in offline.items() if k not in ("labels_unseen", "scored_unseen")}
    (run_dir / "offline.json").write_text(json.dumps(persist, indent=2), encoding="utf-8")
    (run_dir / "wholebox.json").write_text(json.dumps(wholebox, indent=2), encoding="utf-8")
    (run_dir / "cost_ledger.json").write_text(json.dumps(offline["ledger"], indent=2), encoding="utf-8")
    frozen_src = [{"seed": b["seed"], "library_hash": b["library_hash"], "n_active": b["n_active"]} for b in bundles]
    (run_dir / "frozen_sources.json").write_text(
        json.dumps(
            {
                "retrain": False,
                "threshold_retune": False,
                "seeds": frozen_src,
                "labels_fit_sha256": frozen.get("labels_fit_sha256"),
                "model_payload_sha256": frozen.get("model_payload_sha256"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "expt7_result": str(src),
        "n_unseen": len(offline["unseen_ids"]),
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(run_dir, config.to_dict(), meta, slim_audit, offline, wholebox, offline["ledger"])
    print(
        json.dumps(
            {
                "run": str(run_dir),
                "unseen": len(offline["labels_unseen"]),
                "beats_constant": offline["beats_constant"],
                "convincing_offline": offline["convincing_offline"],
                "proceed_wholebox": offline["proceed_wholebox"],
            }
        )
    )


if __name__ == "__main__":
    main()
