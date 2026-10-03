"""Training-solution corpus. Teacher cost is recorded apart from agent evaluation."""

from __future__ import annotations

import hashlib
import json
import time

from mga3.environment import Action, PackingEnv
from mga3.inventory import Inventory
from mga3.solver import exact_cover


def _mask(placements: list[dict]) -> int:
    mask = 0
    for placement in placements:
        for x, y in placement["cells"]:
            mask |= 1 << (int(y) * 10 + int(x))
    return mask


def replay_ok(inventory: dict, placements: list[dict], minimum_q: int) -> tuple[bool, int, int]:
    env = PackingEnv(budget=max(len(placements) + 2, 8), inventory=Inventory(inventory))
    for placement in placements:
        result = env.step(
            Action.place(placement["type"], int(placement["rotation"]), int(placement["x"]), int(placement["y"]))
        )
        if not result.accepted:
            return False, env.score, env.place_attempts
    return env.score >= minimum_q and env.invalid_places == 0, env.score, env.place_attempts


def _record(task, placements, solver, seed, nodes, seconds, minimum_q) -> dict | None:
    ok, score, attempts = replay_ok(task["inventory"], placements, minimum_q)
    if not ok:
        return None
    payload = json.dumps(
        {"task": task["task_id"], "mask": _mask(placements), "solver": solver},
        sort_keys=True,
    )
    return {
        "task_id": task["task_id"],
        "solution_id": "sol_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16],
        "inventory": {k: int(v) for k, v in task["inventory"].items()},
        "placements": placements,
        "Q": int(score),
        "P": int(attempts),
        "solver": solver,
        "seed": int(seed),
        "nodes": int(nodes),
        "seconds": float(seconds),
        "mask": _mask(placements),
        "provenance": "teacher_experience",
        "label": "Teacher tiling. Not an agent-discovered packing.",
    }


def build_corpus(tasks: list[dict], config: dict, workspace, train_ids: set[str]) -> tuple[list[dict], dict]:
    teacher = config.get("teacher", {})
    seeds = list(teacher.get("seeds", [11, 22, 33]))
    node_cap = int(teacher.get("node_cap", 40000))
    per_task = int(teacher.get("max_solutions_per_task", 2))
    beam = int(teacher.get("gpu_trajectories", 256))
    minimum_q = int(config.get("quality_target", 80))
    solutions: list[dict] = []
    cost = {
        "exact_nodes": 0,
        "exact_seconds": 0.0,
        "gpu_seconds": 0.0,
        "gpu_ops": 0,
        "tasks": 0,
        "exact_solutions": 0,
        "gpu_solutions": 0,
        "rejected_replay": 0,
    }
    gpu_before = workspace.gpu_ops
    for task in tasks:
        if task["task_id"] not in train_ids:
            raise RuntimeError(f"refusing non-training task {task['task_id']}")
        cost["tasks"] += 1
        print(f"teacher {cost['tasks']}/{len(tasks)} {task['task_id']}", flush=True)
        seen = set()
        for seed in seeds:
            if sum(1 for s in solutions if s["task_id"] == task["task_id"]) >= per_task:
                break
            found = exact_cover(task["inventory"], seed, node_cap)
            cost["exact_nodes"] += found["nodes"]
            cost["exact_seconds"] += found["seconds"]
            if not found["solved"]:
                continue
            record = _record(task, found["placements"], "teacher_exact_cover", seed, found["nodes"], found["seconds"], minimum_q)
            if record is None:
                cost["rejected_replay"] += 1
                continue
            if record["mask"] in seen:
                continue
            seen.add(record["mask"])
            solutions.append(record)
            cost["exact_solutions"] += 1
        if sum(1 for s in solutions if s["task_id"] == task["task_id"]) < per_task:
            started = time.perf_counter()
            beamed = workspace.beam_fill(task["inventory"], beam, seed=seeds[0] + 17)
            cost["gpu_seconds"] += time.perf_counter() - started
            if beamed:
                record = _record(task, beamed, "teacher_gpu_beam", seeds[0], 0, cost["gpu_seconds"], minimum_q)
                if record is None:
                    cost["rejected_replay"] += 1
                elif record["mask"] not in seen:
                    seen.add(record["mask"])
                    solutions.append(record)
                    cost["gpu_solutions"] += 1
    cost["gpu_ops"] = int(workspace.gpu_ops - gpu_before)
    cost["solutions"] = len(solutions)
    cost["quality_min"] = min((s["Q"] for s in solutions), default=None)
    cost["quality_max"] = max((s["Q"] for s in solutions), default=None)
    return solutions, cost


def chronological(solutions: list[dict], task_order: list[str]) -> list[dict]:
    rank = {task_id: i for i, task_id in enumerate(task_order)}
    return sorted(solutions, key=lambda s: (rank.get(s["task_id"], 10**9), s["solver"], s["seed"], s["solution_id"]))


def prefix_by_tasks(solutions: list[dict], task_order: list[str], n_tasks: int) -> list[dict]:
    keep = set(task_order[:n_tasks])
    ordered = chronological(solutions, task_order)
    return [s for s in ordered if s["task_id"] in keep]
