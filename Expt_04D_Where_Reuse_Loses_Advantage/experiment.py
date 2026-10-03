"""Train the frozen Expt-4B/4C mechanism, then diagnose on development boxes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from config import Config, DIAGNOSTIC_MODES
from diagnostic import counterfactual_replays, solve_diagnostic
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


def assert_dev_disjoint(train: list[dict], development: list[dict], train_val: list[dict]) -> None:
    train_ids = {t["task_id"] for t in train} | {t["task_id"] for t in train_val}
    dev_ids = {t["task_id"] for t in development}
    if train_ids & dev_ids:
        raise RuntimeError("development overlaps training")
    test_path = ROOT.parent / "Expt_04C_Confirm_Reusable_Knowledge" / "data" / "test.json"
    if test_path.exists():
        test_ids = {t["task_id"] for t in json.loads(test_path.read_text(encoding="utf-8"))["tasks"]}
        if test_ids & dev_ids:
            raise RuntimeError("development overlaps the Expt-4C final test set")


def train_library(config: Config, seed: int, train: list[dict], train_val: list[dict]):
    memory = make_memory(config, hierarchical=True, selective_retire=True)
    miner = AbstractionMiner(config, memory)
    sample_rng = make_rng(seed, "selective_hierarchical", "train", 0, "sample")
    for index in range(config.train_boxes):
        task = train[sample_rng.randrange(len(train))]
        outcome = solve_box(
            config, task, seed, "train", index, memory, learn=True, abstention=True
        )
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


def diagnose(config: Config, seed: int, development: list[dict], memory) -> tuple[list[dict], list[dict]]:
    rows = []
    replays = []
    for index, task in enumerate(development):
        for mode in DIAGNOSTIC_MODES:
            outcome = solve_diagnostic(config, task, seed, "development", index, memory if mode != "primitive" else None, mode)
            outcome.update({"seed": seed, "experience": config.train_boxes, "split": "development"})
            rows.append(outcome)
        batch = counterfactual_replays(config, task, seed, "development-cf", index, memory)
        for rec in batch:
            rec["seed"] = seed
        replays.extend(batch)
    return rows, replays


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
