"""Train the frozen learner; diagnose with corrected accounting. Promotion unchanged."""

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


def _ids(tasks: list[dict]) -> set[str]:
    return {t["task_id"] for t in tasks}


def assert_splits(train, development, fresh, train_val) -> None:
    train_ids = _ids(train) | _ids(train_val)
    if train_ids & _ids(development):
        raise RuntimeError("development overlaps training")
    if train_ids & _ids(fresh):
        raise RuntimeError("fresh boxes overlap training")
    if _ids(development) & _ids(fresh):
        raise RuntimeError("fresh boxes overlap the original development set")
    test_path = ROOT.parent / "Expt_04C_Confirm_Reusable_Knowledge" / "data" / "test.json"
    if test_path.exists():
        test_ids = _ids(json.loads(test_path.read_text(encoding="utf-8"))["tasks"])
        if test_ids & _ids(development) or test_ids & _ids(fresh):
            raise RuntimeError("a diagnostic split overlaps the Expt-4C final test set")


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


def diagnose(config: Config, seed: int, tasks: list[dict], memory, split_name: str) -> tuple[list[dict], list[dict]]:
    rows = []
    replays = []
    for index, task in enumerate(tasks):
        traces = {}
        for mode in DIAGNOSTIC_MODES:
            outcome = solve_diagnostic(
                config, task, seed, split_name, index, memory if mode != "primitive" else None, mode
            )
            outcome.update({"seed": seed, "experience": config.train_boxes, "split": split_name})
            traces[mode] = outcome.get("primitive_trace")
            rows.append(outcome)
        check = next(r for r in rows[-3:] if r["mode"] == "retrieve_check_then_primitive")
        prim = next(r for r in rows[-3:] if r["mode"] == "primitive")
        check["primitive_trace_matches"] = traces["retrieve_check_then_primitive"] == traces["primitive"]
        prim["primitive_trace_matches"] = True
        batch = counterfactual_replays(config, task, seed, f"{split_name}-cf", index, memory, split_name)
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
