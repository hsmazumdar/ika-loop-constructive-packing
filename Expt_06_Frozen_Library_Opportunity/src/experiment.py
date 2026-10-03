"""Load frozen sources, generate disjoint boxes, run the opportunity diagnostic."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import Config, EXPT5_LEARNING_A, EXPT5_RESULT
from library_io import library_hash, memory_to_json
from oracle import diagnose_pair
from reconstruct import EXPT5_DIR, file_sha, load_gates, load_snapshot, reconstruct_seed
from tools.generate_boxes import BLOCKED_PATHS, generate, load_tasks


def load_split(name: str) -> list[dict]:
    return list(json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))["tasks"])


def _ids(tasks: list[dict]) -> set[str]:
    return {t["task_id"] for t in tasks}


def prior_task_ids() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for rel in BLOCKED_PATHS:
        path = Path(rel)
        if not path.exists():
            found[str(path)] = set()
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        found[str(path)] = {t["task_id"] for t in payload.get("tasks") or []}
    return found


def assert_splits(eval_tasks: list[dict], smoke_tasks: list[dict] | None = None) -> dict:
    eval_ids = _ids(eval_tasks)
    prior = prior_task_ids()
    overlaps = {src: sorted(ids & eval_ids) for src, ids in prior.items() if ids & eval_ids}
    missing = [src for src, ids in prior.items() if not Path(src).exists()]
    if smoke_tasks is not None:
        smoke_ids = _ids(smoke_tasks)
        if smoke_ids & eval_ids:
            overlaps["smoke_vs_eval"] = sorted(smoke_ids & eval_ids)
    if overlaps:
        raise RuntimeError(f"eval boxes overlap prior splits: {overlaps}")
    return {"prior_sources": {k: len(v) for k, v in prior.items()}, "missing_prior_files": missing, "n_eval": len(eval_ids)}


def ensure_boxes(name: str, target: int, seed: int, extra_blocked: list[Path] | None = None) -> list[dict]:
    path = ROOT / "data" / f"{name}.json"
    if path.exists():
        tasks = load_split(name)
        if len(tasks) >= target:
            return tasks[:target]
    generate(target=target, seed=seed, out_name=name, extra_blocked=extra_blocked)
    return load_split(name)[:target]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    serialised = []
    for row in rows:
        copied = dict(row)
        for key, value in list(copied.items()):
            if isinstance(value, (list, dict)):
                copied[key] = json.dumps(value)
        serialised.append(copied)
    fields = []
    for row in serialised:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in serialised:
            writer.writerow({key: row.get(key) for key in fields})


def read_csv(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_hashes() -> dict[str, str]:
    hashes = {}
    for path in sorted((ROOT / "src").glob("*.py")):
        hashes[path.name] = file_sha(path)
    for name in ("run_expt6.py", "analysis.py"):
        path = ROOT / name
        if path.exists():
            hashes[name] = file_sha(path)
    return hashes


def provenance_audit() -> dict:
    gates = {}
    missing_libraries = []
    for seed in (11, 22, 33):
        gate_path = EXPT5_DIR / f"gates_seed{seed}.json"
        lib_path = EXPT5_DIR / f"library_seed{seed}.json"
        gates[str(seed)] = {
            "path": str(gate_path),
            "exists": gate_path.exists(),
            "sha256": file_sha(gate_path) if gate_path.exists() else None,
        }
        if not lib_path.exists():
            missing_libraries.append(str(lib_path))
    from pieces import catalogue_hash

    return {
        "expt5_result": str(EXPT5_DIR),
        "expt5_result_configured": EXPT5_RESULT,
        "gates": gates,
        "libraries_serialized_in_expt5": False,
        "missing_library_files": missing_libraries,
        "reconstruction_required": True,
        "reconstruction_note": (
            "Expt-5 stored frozen gates only. Libraries are reconstructed from the recorded "
            "80-box training streams and marked reconstruction=True. Exact library-hash match "
            "with the unpublished in-memory Expt-5 objects cannot be verified."
        ),
        "catalogue_hash": catalogue_hash(),
        "source_hashes": source_hashes(),
        "historical_expt5_learning_A": EXPT5_LEARNING_A,
        "a_identity": "A = primitive_evals + retrieval + applicability + learned_site_checks + gate_checks",
        "remaining_budget": "eval_cap - prefix_primitive_A",
        "occupancy_schedule": [0, 10, 20, 30, 40, 50, 60],
        "oracle_sees_futures": True,
        "gui_does_not_train": True,
    }


def freeze_libraries(config: Config, snapshot_dir: Path, seeds: tuple[int, ...]) -> list[dict]:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    bundles = []
    for seed in seeds:
        path = snapshot_dir / f"library_seed{seed}.json"
        if path.exists():
            print(f"load frozen library seed {seed}", flush=True)
            info = load_snapshot(config, int(seed), snapshot_dir)
        else:
            print(f"reconstruct library seed {seed}", flush=True)
            info = reconstruct_seed(config, int(seed), snapshot_dir)
        start_hash = info["library_hash"]
        end_hash = library_hash(info["memory"])
        if start_hash != end_hash:
            raise RuntimeError(f"library hash drifted during load seed {seed}")
        gate_path = EXPT5_DIR / f"gates_seed{seed}.json"
        consult, commit, gate_sha = load_gates(int(seed))
        if consult.frozen is False or commit.frozen is False:
            raise RuntimeError(f"gates were not frozen for seed {seed}")
        info["gate_file_sha256"] = gate_sha
        info["gate_path"] = str(gate_path)
        bundles.append(info)
    return bundles


def verify_frozen(bundles: list[dict], snapshot_dir: Path) -> dict:
    checks = []
    for bundle in bundles:
        seed = bundle["seed"]
        path = snapshot_dir / f"library_seed{seed}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        live = library_hash(bundle["memory"])
        disk = payload["library_hash"]
        file_hash = file_sha(path)
        ok = live == disk == bundle["library_hash"] and file_hash == bundle["library_file_sha256"]
        gate_now = file_sha(EXPT5_DIR / f"gates_seed{seed}.json")
        checks.append(
            {
                "seed": seed,
                "library_hash_ok": ok,
                "gate_hash_ok": gate_now == bundle["gate_file_sha256"],
                "library_hash": live,
                "gate_file_sha256": gate_now,
            }
        )
        if not ok:
            raise RuntimeError(f"library hash changed after evaluation seed {seed}")
        if gate_now != bundle["gate_file_sha256"]:
            raise RuntimeError(f"gate file changed during evaluation seed {seed}")
    return {"ok": True, "checks": checks}


def operation_summary(bundles: list[dict]) -> list[dict]:
    rows = []
    for bundle in bundles:
        for op in bundle["memory"].operations:
            rows.append(
                {
                    "seed": bundle["seed"],
                    "library_hash": bundle["library_hash"],
                    "op_id": op.op_id,
                    "definition_hash": next(
                        item["definition_hash"] for item in memory_to_json(bundle["memory"])["operations"] if item["op_id"] == op.op_id
                    ),
                    "depth": op.depth,
                    "composed": op.depth > 1,
                    "status": op.status,
                    "n_steps": len(op.steps),
                    "children": json.dumps(list(op.children)),
                }
            )
    return rows


def done_keys(box_rows: list[dict]) -> set[tuple[str, str]]:
    keys = set()
    for row in box_rows:
        keys.add((str(row["seed"]), str(row["task_id"])))
    return keys


def run_pairs(
    config: Config,
    tasks: list[dict],
    bundles: list[dict],
    run_dir: Path,
    *,
    resume: bool = False,
) -> dict:
    box_path = run_dir / "box_results.csv"
    state_path = run_dir / "state_opportunities.csv"
    cand_path = run_dir / "candidate_replays.csv"
    box_rows = read_csv(box_path) if resume else []
    state_rows = read_csv(state_path) if resume else []
    cand_rows = read_csv(cand_path) if resume else []
    skip = done_keys(box_rows)
    ledger = {
        "skip_A": 0,
        "commit_A": 0,
        "skip_rollouts": 0,
        "commit_rollouts": 0,
        "C_box_sum": 0,
        "gate_probes": 0,
        "incomplete_pairs": 0,
        "primitive_boxes": 0,
        "cache_hits": 0,
        "historical_expt5_learning_A": EXPT5_LEARNING_A,
        "historical_expt5_learning_scope": "Expt-5 counterfactual remaining-solves plus collection retrieve/check on training boxes",
    }
    started = 0
    n_total = len(bundles) * len(tasks)
    for bundle in bundles:
        for index, task in enumerate(tasks):
            key = (str(bundle["seed"]), str(task["task_id"]))
            if key in skip:
                ledger["cache_hits"] = ledger.get("cache_hits", 0) + 1
                continue
            started += 1
            print(
                f"pair seed={bundle['seed']} box={index + 1}/{len(tasks)} {task['task_id']} "
                f"({len(skip) + started}/{n_total})",
                flush=True,
            )
            result = diagnose_pair(config, task, int(bundle["seed"]), index, bundle, ledger)
            box_rows.append(result["box"])
            state_rows.extend(result["states"])
            cand_rows.extend(result["candidates"])
            write_csv(box_path, box_rows)
            write_csv(state_path, state_rows)
            write_csv(cand_path, cand_rows)
            print(
                f"  A_prim={result['box']['A_primitive']} A_free={result['box']['A_oracle_free']} "
                f"C_box={result['box']['C_box']} n_cand={result['box']['n_candidates']} "
                f"complete={result['box']['oracle_complete']}",
                flush=True,
            )
    return {
        "box_rows": box_rows,
        "state_rows": state_rows,
        "candidate_rows": cand_rows,
        "ledger": ledger,
        "n_pairs": len(box_rows),
        "n_computed": started,
    }
