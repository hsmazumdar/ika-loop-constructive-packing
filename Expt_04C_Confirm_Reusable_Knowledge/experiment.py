"""Expt-4C lifetimes. Learning is frozen on development checkpoints and final test."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from config import Config, TRAIN_CONDITIONS
from memory import Episode, clone_library_only, make_memory
from miner import AbstractionMiner
from promotion import paired_should_promote
from solver import make_rng, solve_box

ROOT = Path(__file__).resolve().parent


def load_split(name: str) -> list[dict]:
    payload = json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))
    return list(payload["tasks"])


def reserve_train_val(train: list[dict], count: int) -> tuple[list[dict], list[dict]]:
    if count <= 0:
        return list(train), []
    return list(train[count:]) or list(train), list(train[:count])


def assert_splits(train: list[dict], development: list[dict], test: list[dict], train_val: list[dict]) -> None:
    groups = {
        "train": {t["task_id"] for t in train} | {t["task_id"] for t in train_val},
        "development": {t["task_id"] for t in development},
        "test": {t["task_id"] for t in test},
    }
    if groups["train"] & groups["development"]:
        raise RuntimeError("train overlaps development")
    if groups["train"] & groups["test"]:
        raise RuntimeError("train overlaps test")
    if groups["development"] & groups["test"]:
        raise RuntimeError("development overlaps test")
    if {t["task_id"] for t in train_val} & groups["test"]:
        raise RuntimeError("pairing boxes overlap test")


def condition_spec(name: str) -> dict:
    if name == "primitive":
        return {"use_memory": False, "hierarchical": False}
    if name == "selective_flat":
        return {"use_memory": True, "hierarchical": False}
    if name == "selective_hierarchical":
        return {"use_memory": True, "hierarchical": True}
    raise KeyError(name)


def _annotate(outcome: dict, **fields) -> dict:
    outcome.update(fields)
    outcome.pop("decisions_trace", None)
    return outcome


def evaluate_frozen(config, tasks, seed, memory, tag: str, condition: str, experience: int) -> list[dict]:
    rows = []
    for index, task in enumerate(tasks):
        outcome = solve_box(
            config, task, seed, tag, index, memory, learn=False, abstention=memory is not None
        )
        rows.append(
            _annotate(
                outcome,
                condition=condition,
                seed=seed,
                experience=experience,
                split=tag,
            )
        )
    return rows


def run_lifetime(config: Config, name: str, seed: int, train: list[dict], development: list[dict], train_val: list[dict]) -> dict:
    spec = condition_spec(name)
    memory = None
    miner = None
    if spec["use_memory"]:
        memory = make_memory(config, hierarchical=spec["hierarchical"], selective_retire=True)
        miner = AbstractionMiner(config, memory)
    train_rows = []
    checkpoints = []

    def maybe_checkpoint(experience: int) -> None:
        if experience not in set(config.checkpoints):
            return
        checkpoints.extend(evaluate_frozen(config, development, seed, memory, "development", name, experience))

    maybe_checkpoint(0)
    sample_rng = make_rng(seed, name, "train", 0, "sample")
    for index in range(config.train_boxes):
        task = train[sample_rng.randrange(len(train))]
        outcome = solve_box(
            config, task, seed, "train", index, memory, learn=memory is not None, abstention=memory is not None
        )
        trace = outcome.pop("decisions_trace")
        if miner is not None and outcome["acceptable"]:
            episode = Episode(index, task["task_id"], dict(task["inventory"]), trace, outcome["Q"], outcome["A"], True)
            new_ops = miner.observe(episode)
            for op in new_ops:
                if train_val:
                    val_task = train_val[index % len(train_val)]
                    ok, _record = paired_should_promote(config, op, memory, val_task, seed, index, True)
                    if ok:
                        memory.promote(op, index, "paired_utility")
        if memory is not None:
            memory.age(index)
            memory.enforce_pressure(index)
        train_rows.append(
            _annotate(
                outcome,
                condition=name,
                seed=seed,
                experience=index + 1,
                split="train",
                library_size=0 if memory is None else len(memory.active()),
                memory_bytes=0 if memory is None else memory.bytes_used(),
                max_depth=0 if memory is None or not memory.active() else max(op.depth for op in memory.active()),
            )
        )
        maybe_checkpoint(index + 1)
    return {"condition": name, "seed": seed, "train_rows": train_rows, "checkpoint_rows": checkpoints, "memory": memory}


def final_evaluations(config, seed: int, test: list[dict], memories: dict) -> list[dict]:
    rows = []
    experience = config.train_boxes
    rows.extend(evaluate_frozen(config, test, seed, None, "test", "primitive", experience))
    rows.extend(evaluate_frozen(config, test, seed, memories.get("selective_flat"), "test", "selective_flat", experience))
    hier = memories.get("selective_hierarchical")
    rows.extend(evaluate_frozen(config, test, seed, hier, "test", "selective_hierarchical", experience))
    transferred = clone_library_only(hier) if hier is not None else None
    rows.extend(evaluate_frozen(config, test, seed, transferred, "test", "transfer", experience))
    rows.extend(evaluate_frozen(config, test, seed, None, "test", "lesion", experience))
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})
