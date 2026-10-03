"""Reconstruct Expt-5 libraries from recorded training streams. Gates load from disk."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from config import Config, EXPT6_SNAPSHOTS
from gates import LinearGate
from library_io import library_hash, memory_from_json, memory_to_json
from memory import Episode, clone_library_only, make_memory
from miner import AbstractionMiner
from promotion import paired_should_promote
from solver import make_rng, solve_box

ROOT = Path(__file__).resolve().parents[1]
EXPT5_DIR = ROOT.parent / "Expt_05_Consult_and_Commit_Gates" / "results" / "20260929_212658_diagnostic"
EXPT6_SNAP = ROOT / "snapshots"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json_split(name: str) -> list[dict]:
    return list(json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))["tasks"])


def reserve_train_val(train: list[dict], count: int) -> tuple[list[dict], list[dict]]:
    if count <= 0:
        return list(train), []
    return list(train[count:]) or list(train), list(train[:count])


def train_library(config: Config, seed: int, train: list[dict], train_val: list[dict]):
    memory = make_memory(config, hierarchical=True, selective_retire=True)
    miner = AbstractionMiner(config, memory)
    sample_rng = make_rng(seed, "selective_hierarchical", "train", 0, "sample")
    for index in range(config.train_boxes):
        if index == 0 or (index + 1) % 10 == 0:
            print(f"reconstruct seed {seed} box {index + 1}/{config.train_boxes}", flush=True)
        task = train[sample_rng.randrange(len(train))]
        outcome = solve_box(config, task, seed, "train", index, memory, learn=True, abstention=True)
        trace = outcome.pop("decisions_trace")
        if outcome["acceptable"]:
            episode = Episode(index, task["task_id"], dict(task["inventory"]), trace, outcome["Q"], outcome["A"], True)
            for op in miner.observe(episode):
                if train_val:
                    ok, _ = paired_should_promote(config, op, memory, train_val[index % len(train_val)], seed, index, True)
                    if ok:
                        memory.promote(op, index, "paired_utility")
        memory.age(index)
        memory.enforce_pressure(index)
    return clone_library_only(memory)


def load_gates(seed: int) -> tuple[LinearGate, LinearGate, str]:
    path = EXPT5_DIR / f"gates_seed{seed}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    consult = LinearGate.from_dict(payload["consult"])
    commit = LinearGate.from_dict(payload["commit"])
    return consult, commit, file_sha(path)


def reconstruct_seed(config: Config, seed: int, snapshot_dir: Path) -> dict:
    train_all = load_json_split("train")
    train, train_val = reserve_train_val(train_all, config.train_val_count)
    memory = train_library(config, seed, train, train_val)
    payload = memory_to_json(memory)
    path = snapshot_dir / f"library_seed{seed}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    consult, commit, gate_sha = load_gates(seed)
    return {
        "seed": seed,
        "reconstruction": True,
        "source_result": str(EXPT5_DIR),
        "library_path": str(path),
        "library_hash": payload["library_hash"],
        "library_file_sha256": file_sha(path),
        "n_active": len(memory.active()),
        "n_operations": len(memory.operations),
        "operations": [
            {
                "op_id": op.op_id,
                "definition_hash": item["definition_hash"],
                "depth": op.depth,
                "children": list(op.children),
                "status": op.status,
                "n_steps": len(op.steps),
                "leaf_piece_counts": _leaf_counts(op),
            }
            for op, item in zip(memory.operations, payload["operations"])
        ],
        "gate_file_sha256": gate_sha,
        "consult_threshold": consult.threshold,
        "commit_threshold": commit.threshold,
        "memory": memory,
        "consult_gate": consult,
        "commit_gate": commit,
    }


def _leaf_counts(op) -> dict:
    counts: dict[str, int] = {}
    for step in op.steps:
        counts[step["type"]] = counts.get(step["type"], 0) + 1
    return counts


def load_snapshot(config: Config, seed: int, snapshot_dir: Path) -> dict:
    path = snapshot_dir / f"library_seed{seed}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    memory = memory_from_json(payload, config)
    consult, commit, gate_sha = load_gates(seed)
    info = {
        "seed": seed,
        "reconstruction": True,
        "library_path": str(path),
        "library_hash": payload["library_hash"],
        "library_file_sha256": file_sha(path),
        "n_active": len(memory.active()),
        "gate_file_sha256": gate_sha,
        "memory": memory,
        "consult_gate": consult,
        "commit_gate": commit,
    }
    return info
