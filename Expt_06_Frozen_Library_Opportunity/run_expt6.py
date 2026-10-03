"""Expt-6 entry. Frozen libraries and gates; no learning."""

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
from config import apply_overrides, diagnostic_config, smoke_config  # noqa: E402
from experiment import (  # noqa: E402
    assert_splits,
    ensure_boxes,
    freeze_libraries,
    operation_summary,
    provenance_audit,
    read_csv,
    run_pairs,
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


def _deps() -> dict:
    out = {}
    for name in ("numpy", "matplotlib", "pytest"):
        try:
            mod = __import__(name)
            out[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            out[name] = "missing"
    return out


def _validation() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode == 0


def _write_meta(run_dir: Path, preset: str, extra: dict) -> dict:
    meta = {
        "preset": preset,
        "python": platform.python_version(),
        "git": _git_commit(),
        "catalogue_hash": catalogue_hash(),
        "source_hashes": source_hashes(),
        "dependencies": _deps(),
        **extra,
    }
    (run_dir / "runtime.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def _load_rows(run_dir: Path) -> tuple[list[dict], list[dict], list[dict], dict, dict]:
    box_rows = read_csv(run_dir / "box_results.csv")
    state_rows = read_csv(run_dir / "state_opportunities.csv")
    cand_rows = read_csv(run_dir / "candidate_replays.csv")
    ledger = json.loads((run_dir / "cost_ledger.json").read_text(encoding="utf-8")) if (run_dir / "cost_ledger.json").exists() else {}
    audit = json.loads((run_dir / "audit.json").read_text(encoding="utf-8")) if (run_dir / "audit.json").exists() else {}
    return box_rows, state_rows, cand_rows, ledger, audit


def cmd_audit(run_dir: Path) -> dict:
    audit = provenance_audit()
    (run_dir / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "AUDIT.md").write_text(
        "\n".join(
            [
                "# Expt-6 provenance audit",
                "",
                audit["reconstruction_note"],
                "",
                f"- Expt-5 result: `{audit['expt5_result']}`",
                f"- Catalogue hash: `{audit['catalogue_hash']}`",
                f"- Missing library files: {audit['missing_library_files']}",
                f"- Remaining budget: `{audit['remaining_budget']}`",
                f"- Occupancy schedule: {audit['occupancy_schedule']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return audit


def cmd_report(run_dir: Path) -> None:
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8")) if (run_dir / "config.json").exists() else {}
    meta = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8")) if (run_dir / "runtime.json").exists() else {}
    box_rows, state_rows, cand_rows, ledger, audit = _load_rows(run_dir)
    write_plots(run_dir, box_rows, state_rows, cand_rows)
    write_report(run_dir, config, meta, box_rows, state_rows, cand_rows, ledger, audit)


def _estimate_from_smoke() -> dict | None:
    results = ROOT / "results"
    if not results.exists():
        return None
    smokes = sorted(results.glob("*_smoke"), reverse=True)
    if not smokes:
        return None
    latest = smokes[0]
    runtime = json.loads((latest / "runtime.json").read_text(encoding="utf-8")) if (latest / "runtime.json").exists() else {}
    box_rows = read_csv(latest / "box_results.csv")
    if not box_rows:
        return None
    elapsed = float(runtime.get("elapsed_s") or 0)
    n = max(1, len(box_rows))
    per_pair = elapsed / n
    mean_cand = sum(float(r.get("n_candidates") or 0) for r in box_rows) / n
    return {
        "smoke_dir": str(latest),
        "smoke_pairs": n,
        "elapsed_s": elapsed,
        "seconds_per_pair": per_pair,
        "mean_candidates": mean_cand,
    }


def cmd_run(preset: str, args, *, resume_dir: Path | None = None) -> Path:
    if not args.skip_validation and not _validation():
        print("validation failed; the run was not started")
        sys.exit(1)
    config = smoke_config() if preset == "smoke" else diagnostic_config()
    config = apply_overrides(config, args)
    smoke_tasks = ensure_boxes("smoke", 4 if preset == "smoke" else 4, 2026092961)
    extra = [ROOT / "data" / "smoke.json"]
    if preset == "smoke":
        tasks = smoke_tasks[: config.n_boxes]
        split_note = assert_splits(tasks)
    else:
        tasks = ensure_boxes("eval", config.n_boxes, 2026092962, extra_blocked=extra)
        split_note = assert_splits(tasks, smoke_tasks)
    if resume_dir is not None:
        run_dir = resume_dir
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = ROOT / "results" / f"{stamp}_{preset}"
        run_dir.mkdir(parents=True)
    audit = cmd_audit(run_dir)
    snapshot_dir = ROOT / "snapshots"
    estimate = _estimate_from_smoke()
    declared_limit_s = 6 * 3600
    reduction = None
    if preset == "diagnostic" and estimate is not None:
        states_factor = config.max_states_per_box / 4.0
        cand_factor = config.max_candidates_per_state / 8.0
        predicted = estimate["seconds_per_pair"] * len(config.seeds) * len(tasks) * max(1.0, states_factor) * max(1.0, cand_factor)
        if predicted > declared_limit_s and config.max_candidates_per_state > 12:
            from dataclasses import replace

            config = replace(config, max_candidates_per_state=12)
            reduction = {
                "reason": "smoke-based estimate exceeded 6h",
                "predicted_s": predicted,
                "max_candidates_per_state": 12,
                "label": "sampled_candidate_oracle if any state truncates",
            }
        estimate = dict(estimate)
        estimate["predicted_diagnostic_s"] = predicted
        estimate["declared_limit_s"] = declared_limit_s
        estimate["reduction"] = reduction
        (run_dir / "diagnostic_estimate.json").write_text(json.dumps(estimate, indent=2), encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    started = datetime.now().timestamp()
    print("freeze libraries", flush=True)
    bundles = freeze_libraries(config, snapshot_dir, config.seeds)
    frozen_sources = {
        "reconstruction": True,
        "snapshot_dir": str(snapshot_dir),
        "seeds": [
            {
                "seed": b["seed"],
                "library_hash": b["library_hash"],
                "library_file_sha256": b["library_file_sha256"],
                "gate_file_sha256": b["gate_file_sha256"],
                "n_active": b["n_active"],
            }
            for b in bundles
        ],
        "expt5": audit,
        "split": split_note,
        "task_ids": [t["task_id"] for t in tasks],
    }
    (run_dir / "frozen_sources.json").write_text(json.dumps(frozen_sources, indent=2), encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        json.dumps({"preset": preset, "task_ids": [t["task_id"] for t in tasks], "seeds": list(config.seeds), "n_boxes": len(tasks)}, indent=2),
        encoding="utf-8",
    )
    write_csv(run_dir / "operation_summary.csv", operation_summary(bundles))
    print(f"run {len(bundles)} libraries x {len(tasks)} boxes", flush=True)
    result = run_pairs(config, tasks, bundles, run_dir, resume=resume_dir is not None)
    verify = verify_frozen(bundles, snapshot_dir)
    (run_dir / "hash_verify.json").write_text(json.dumps(verify, indent=2), encoding="utf-8")
    ledger = result["ledger"]
    ledger["elapsed_s"] = datetime.now().timestamp() - started
    ledger["n_pairs"] = result["n_pairs"]
    ledger["n_computed"] = result["n_computed"]
    (run_dir / "cost_ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    meta = _write_meta(
        run_dir,
        preset,
        {
            "n_boxes": len(tasks),
            "n_pairs": result["n_pairs"],
            "elapsed_s": ledger["elapsed_s"],
            "library_hashes": [b["library_hash"] for b in bundles],
            "reduction": reduction,
        },
    )
    write_plots(run_dir, result["box_rows"], result["state_rows"], result["candidate_rows"])
    write_report(run_dir, config.to_dict(), meta, result["box_rows"], result["state_rows"], result["candidate_rows"], ledger, audit)
    print(json.dumps({"run": str(run_dir), "pairs": result["n_pairs"], "computed": result["n_computed"], "elapsed_s": ledger["elapsed_s"]}))
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--run-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--n-boxes", type=int, default=None)
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--skip-validation", action="store_true")
    args = parser.parse_args()
    modes = [name for name, flag in (("audit", args.audit), ("smoke", args.smoke), ("diagnostic", args.diagnostic), ("report", args.report), ("resume", args.resume)) if flag]
    if len(modes) != 1:
        parser.error("choose one of --audit, --smoke, --diagnostic, --report, or --resume")
    preset = modes[0]
    if preset == "report":
        if not args.run_dir:
            parser.error("--report requires --run-dir")
        cmd_report(Path(args.run_dir))
        return
    if preset == "resume":
        if not args.run_dir:
            parser.error("--resume requires --run-dir")
        run_dir = Path(args.run_dir)
        name = run_dir.name
        inner = "smoke" if name.endswith("_smoke") else "diagnostic"
        cmd_run(inner, args, resume_dir=run_dir)
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if preset == "audit":
        run_dir = ROOT / "results" / f"{stamp}_audit"
        run_dir.mkdir(parents=True)
        audit = cmd_audit(run_dir)
        _write_meta(run_dir, "audit", {"reconstruction_required": audit["reconstruction_required"]})
        print(json.dumps({"run": str(run_dir), "reconstruction_required": True}))
        return
    cmd_run(preset, args)


if __name__ == "__main__":
    main()
