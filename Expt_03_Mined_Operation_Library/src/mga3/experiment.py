"""Bounded comparison runner. Held-out scores are not used to pick an arm."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

from mga3.corpus import build_corpus, chronological, prefix_by_tasks
from mga3.hardware import PlacementWorkspace
from mga3.mining import build_libraries, library_document
from mga3.pieces import catalogue_hash
from mga3.policy import Controller

EXPT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = EXPT_ROOT.parent

ARMS = (
    "primitive",
    "rect_mined",
    "neutral_mined",
    "matched_control",
    "rect_mined_no_retrieval",
)


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_split(name: str) -> list[dict]:
    payload = json.loads((EXPT_ROOT / "data" / "runtime" / f"{name}.json").read_text(encoding="utf-8"))
    return list(payload["tasks"])


def dataset_hash() -> str:
    manifest = json.loads((EXPT_ROOT / "data" / "runtime" / "manifest.json").read_text(encoding="utf-8"))
    raw = json.dumps(manifest["splits"], sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def source_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted((EXPT_ROOT / "src" / "mga3").glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def apply_preset(config: dict, preset: str | None) -> dict:
    out = json.loads(json.dumps(config))
    out["preset"] = preset or "configured"
    if preset == "tiny":
        out["seeds"] = [11]
        out["snapshots"] = [0, 2]
        out["train_limit"] = 2
        out["heldout_limit"] = 1
        out["dev_limit"] = 1
        out["teacher"]["gpu_trajectories"] = 64
        out["teacher"]["seeds"] = [11, 22]
        out["teacher"]["max_solutions_per_task"] = 1
    elif preset == "discovery_smoke":
        out["train_limit"] = None
        out["heldout_limit"] = None
        out["dev_limit"] = None
    else:
        out.setdefault("train_limit", None)
        out.setdefault("heldout_limit", None)
        out.setdefault("dev_limit", None)
    return out


def snapshot_plan(requested: list[int], n_tasks: int) -> tuple[list[int], list[dict]]:
    notes = []
    chosen = []
    for size in requested:
        if size <= n_tasks:
            chosen.append(size)
        else:
            notes.append({"requested": size, "status": "unavailable", "available_tasks": n_tasks})
    if n_tasks not in chosen:
        chosen.append(n_tasks)
        notes.append({"requested": None, "status": "added_actual_corpus_size", "available_tasks": n_tasks})
    return sorted(set(chosen)), notes


def _library_for(arm: str, mined: dict) -> tuple[list[dict], bool]:
    libs = mined["libraries"]
    if arm == "primitive":
        return [], False
    if arm == "rect_mined":
        return list(libs["rect_mined"]), True
    if arm == "neutral_mined":
        return list(libs["neutral_mined"]), True
    if arm == "matched_control":
        return list(libs["matched_control"]), True
    if arm == "rect_mined_no_retrieval":
        return list(libs["rect_mined"]), False
    raise KeyError(arm)


def _validation_ids(task_ids: list[str]) -> set[str]:
    if len(task_ids) < 4:
        return set()
    n_valid = max(1, len(task_ids) // 4)
    return set(task_ids[-n_valid:])


def run_episode(config, workspace, library, retrieve, task, seed, phase) -> dict:
    controller = Controller(config, workspace, library, retrieve)
    return controller.run(task, seed, phase)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "phase", "snapshot", "arm", "seed", "task_id", "Q", "best_Q", "P", "E",
        "target_met", "attempts_to_target", "censored", "undos", "physical",
        "invalid_places", "termination", "candidate_evals", "guard_evals",
        "library_lookups", "feature_evals", "model_transitions", "sim_expansions",
        "gpu_ops", "macros_invoked", "macros_completed", "macros_interrupted",
        "cheap_actions", "library_ops", "library_bytes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def execute(config: dict, run_dir: Path, wall_cap_minutes: float | None, resume: bool) -> dict:
    from mga3.report import write_report
    from mga3.gui import write_replay_snapshot

    run_dir.mkdir(parents=True, exist_ok=True)
    train = load_split("train")
    development = load_split("development")
    test = load_split("test")
    if config.get("train_limit"):
        train = train[: int(config["train_limit"])]
    if config.get("heldout_limit"):
        test = test[: int(config["heldout_limit"])]
    if config.get("dev_limit"):
        development = development[: int(config["dev_limit"])]
    train_ids = {task["task_id"] for task in load_split("train")}
    workspace = PlacementWorkspace(config.get("device", "cuda"))
    corpus_path = EXPT_ROOT / "data" / "corpus" / "solutions.jsonl"
    cost_path = EXPT_ROOT / "data" / "corpus" / "teacher_cost.json"
    if corpus_path.exists() and not config.get("train_limit"):
        solutions = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        teacher_cost = json.loads(cost_path.read_text(encoding="utf-8")) if cost_path.exists() else {}
    else:
        solutions, teacher_cost = build_corpus(train, config, workspace, train_ids)
        corpus_path.parent.mkdir(parents=True, exist_ok=True)
        if not config.get("train_limit"):
            with corpus_path.open("w", encoding="utf-8") as handle:
                for solution in solutions:
                    handle.write(json.dumps(solution) + "\n")
            cost_path.write_text(json.dumps(teacher_cost, indent=2), encoding="utf-8")
    order = [task["task_id"] for task in train]
    solutions = chronological(solutions, order)
    sizes, snapshot_notes = snapshot_plan(list(config["snapshots"]), len(order))
    checkpoint_path = run_dir / "checkpoint.json"
    done = set()
    rows: list[dict] = []
    traces = run_dir / "traces.jsonl"
    if not resume and traces.exists():
        traces.unlink()
    if resume and checkpoint_path.exists():
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        done = set(payload.get("completed", []))
        if (run_dir / "episodes.csv").exists():
            with (run_dir / "episodes.csv").open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
    schedule = []
    for task in development:
        for arm in ("primitive", "rect_mined"):
            schedule.append({
                "phase": "development",
                "snapshot": sizes[-1],
                "seed": int(config["seeds"][0]),
                "task_id": task["task_id"],
                "arm": arm,
            })
    for size in sizes:
        for seed in config["seeds"]:
            for task in test:
                for arm in config["arms"]:
                    schedule.append({
                        "phase": "heldout",
                        "snapshot": size,
                        "seed": int(seed),
                        "task_id": task["task_id"],
                        "arm": arm,
                    })
    (run_dir / "schedule.json").write_text(json.dumps(schedule, indent=2), encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    mined_by_size: dict[int, dict] = {}
    mine_seconds = 0.0
    started = time.perf_counter()
    stop_reason = "finished"
    tasks_by_id = {task["task_id"]: task for task in train + development + test}
    trace_handle = traces.open("a", encoding="utf-8")
    try:
        for item in schedule:
            key = f"{item['phase']}|{item['snapshot']}|{item['seed']}|{item['task_id']}|{item['arm']}"
            if key in done:
                continue
            if wall_cap_minutes is not None and (time.perf_counter() - started) >= wall_cap_minutes * 60.0:
                stop_reason = "wall_cap"
                break
            size = int(item["snapshot"])
            if size not in mined_by_size:
                t0 = time.perf_counter()
                prefix_ids = order[:size]
                prefix = prefix_by_tasks(solutions, order, size)
                valid = _validation_ids(prefix_ids)
                mined = build_libraries(prefix, config, valid)
                mined_by_size[size] = mined
                mine_seconds += time.perf_counter() - t0
                for arm_name, ops in mined["libraries"].items():
                    document = library_document(arm_name, ops, {"snapshot": size, "pool_ops": mined["pool_ops"]})
                    (run_dir / f"library_{arm_name}_{size}.json").write_text(
                        json.dumps(document, indent=2), encoding="utf-8"
                    )
                (run_dir / f"rejections_{size}.json").write_text(
                    json.dumps({"rejections": mined["rejections"], "mismatches": mined["mismatches"], "bytes": mined["bytes"]}, indent=2),
                    encoding="utf-8",
                )
            library, retrieve = _library_for(item["arm"], mined_by_size[size])
            outcome = run_episode(
                config, workspace, library, retrieve, tasks_by_id[item["task_id"]], int(item["seed"]), item["phase"]
            )
            row = {
                "phase": item["phase"],
                "snapshot": size,
                "arm": item["arm"],
                "seed": int(item["seed"]),
                "task_id": item["task_id"],
                "Q": outcome["Q"],
                "best_Q": outcome["best_Q"],
                "P": outcome["P"],
                "E": "" if outcome["E"] is None else round(outcome["E"], 6),
                "target_met": outcome["target_met"],
                "attempts_to_target": outcome["attempts_to_target"],
                "censored": outcome["censored"],
                "undos": outcome["undos"],
                "physical": outcome["physical"],
                "invalid_places": outcome["invalid_places"],
                "termination": outcome["termination"],
                "candidate_evals": outcome["ledger"]["candidate_evals"],
                "guard_evals": outcome["ledger"]["guard_evals"],
                "library_lookups": outcome["ledger"]["library_lookups"],
                "feature_evals": outcome["ledger"]["feature_evals"],
                "model_transitions": outcome["ledger"]["model_transitions"],
                "sim_expansions": outcome["ledger"]["sim_expansions"],
                "gpu_ops": outcome["ledger"]["gpu_ops"],
                "macros_invoked": outcome["ledger"]["macros_invoked"],
                "macros_completed": outcome["ledger"]["macros_completed"],
                "macros_interrupted": outcome["ledger"]["macros_interrupted"],
                "cheap_actions": outcome["ledger"]["cheap_actions"],
                "library_ops": len(library),
                "library_bytes": sum(op["nbytes"] for op in library),
            }
            rows.append(row)
            if len(rows) % 20 == 0 or len(rows) == 1:
                print(
                    f"episode {len(rows)}/{len(schedule)} {item['phase']} snap={size} {item['arm']} Q={outcome['Q']}",
                    flush=True,
                )
            trace_handle.write(json.dumps({
                "key": key,
                "row": row,
                "events": outcome["events"],
                "placements": outcome["placements"],
            }) + "\n")
            trace_handle.flush()
            done.add(key)
            checkpoint_path.write_text(json.dumps({
                "completed": sorted(done),
                "stop_reason": "running",
                "episodes": len(rows),
            }, indent=2), encoding="utf-8")
            _write_csv(run_dir / "episodes.csv", rows)
    finally:
        trace_handle.close()
    complete = stop_reason == "finished" and len(done) >= len(schedule)
    summary = {
        "complete": complete,
        "stop_reason": stop_reason if len(done) < len(schedule) else "finished",
        "episodes": len(rows),
        "planned": len(schedule),
        "catalogue_hash": catalogue_hash(),
        "dataset_hash": dataset_hash(),
        "source_hash": source_hash(),
        "device": workspace.device_name(),
        "cuda_bytes": workspace.memory_bytes(),
        "teacher_cost": teacher_cost,
        "mine_seconds": mine_seconds,
        "snapshot_notes": snapshot_notes,
        "snapshots": sizes,
        "wall_seconds": time.perf_counter() - started,
        "corpus_solutions": len(solutions),
    }
    (run_dir / "RUN_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    checkpoint_path.write_text(json.dumps({
        "completed": sorted(done),
        "stop_reason": summary["stop_reason"],
        "episodes": len(rows),
        "complete": summary["complete"],
    }, indent=2), encoding="utf-8")
    write_report(run_dir, config, summary, rows, solutions, mined_by_size)
    write_replay_snapshot(run_dir, solutions, mined_by_size)
    return summary
