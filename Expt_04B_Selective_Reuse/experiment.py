"""Five-condition diagnostic lifetimes. Held-out boxes never enter mining or pairing."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from pieces import piece_area
from config import CONDITION_NAMES, Config
from memory import Episode, make_memory
from miner import AbstractionMiner
from promotion import paired_should_promote
from solver import make_rng, solve_box

ROOT = Path(__file__).resolve().parent


def load_split(name: str) -> list[dict]:
    payload = json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))
    return list(payload["tasks"])


def shift_inventory(inventory: dict[str, int], rng: random.Random) -> dict[str, int]:
    updated = {name: int(count) for name, count in inventory.items() if int(count) > 0}
    donated = 0
    for name in list(updated):
        if piece_area(name) < 5:
            continue
        move = updated[name] // 2
        if move <= 0:
            continue
        updated[name] -= move
        donated += move
        if updated[name] <= 0:
            del updated[name]
    small = ["M", "N", "O"]
    rng.shuffle(small)
    for index in range(donated):
        name = small[index % 3]
        updated[name] = updated.get(name, 0) + 1
    return updated


def phase_pools(train: list[dict], seed: int, probe_count: int) -> tuple[list[dict], list[dict], list[dict]]:
    shifted = []
    for task in train:
        rng = make_rng(seed, task["task_id"], "environment", 0, "shift")
        inventory = shift_inventory(dict(task["inventory"]), rng)
        shifted.append({"task_id": "b_" + task["task_id"], "family": "shifted_inventory", "inventory": inventory})
    probe = shifted[:probe_count]
    phase_b = shifted[probe_count:] or shifted
    return train, phase_b, probe


def reserve_train_val(train: list[dict], count: int) -> tuple[list[dict], list[dict]]:
    if count <= 0:
        return list(train), []
    val = list(train[:count])
    rest = list(train[count:]) or list(train)
    return rest, val


def assert_splits(train: list[dict], heldout: list[dict], probe: list[dict], train_val: list[dict]) -> None:
    train_ids = {t["task_id"] for t in train}
    held_ids = {t["task_id"] for t in heldout}
    probe_ids = {t["task_id"] for t in probe}
    val_ids = {t["task_id"] for t in train_val}
    if train_ids & held_ids:
        raise RuntimeError("training ids leaked into held-out")
    if val_ids & held_ids:
        raise RuntimeError("train-val ids leaked into held-out")
    if probe_ids & held_ids:
        raise RuntimeError("probe ids overlap held-out")
    if any(not t["task_id"].startswith("b_") for t in probe):
        raise RuntimeError("probe tasks must be shifted")


def flags(name: str) -> dict:
    if name == "primitive":
        return {"use_memory": False, "utility": False, "abstention": False, "support_promote": False}
    if name == "current_hierarchy":
        return {"use_memory": True, "utility": False, "abstention": False, "support_promote": True}
    if name == "utility_promotion":
        return {"use_memory": True, "utility": True, "abstention": False, "support_promote": False}
    if name == "contextual_abstention":
        return {"use_memory": True, "utility": False, "abstention": True, "support_promote": True}
    if name == "both":
        return {"use_memory": True, "utility": True, "abstention": True, "support_promote": False}
    raise KeyError(name)


def _mean_depth(memory) -> float:
    ops = [] if memory is None else memory.active()
    if not ops:
        return 0.0
    return sum(op.depth for op in ops) / len(ops)


def _max_depth(memory) -> int:
    ops = [] if memory is None else memory.active()
    return 0 if not ops else max(op.depth for op in ops)


def run_lifetime(config: Config, condition: str, seed: int, train: list[dict], heldout: list[dict], probe: list[dict], phase_b: list[dict], train_val: list[dict]) -> dict:
    spec = flags(condition)
    memory = make_memory(config, selective_retire=spec["utility"]) if spec["use_memory"] else None
    miner = AbstractionMiner(config, memory) if memory is not None else None
    rows = []
    checkpoints = []
    pair_rows = []
    discounted = False

    def evaluate(experience: int, distribution: str, tasks: list[dict], tag: str) -> None:
        for index, task in enumerate(tasks):
            outcome = solve_box(
                config, task, seed, tag, index, memory, learn=False, abstention=spec["abstention"]
            )
            outcome.pop("decisions_trace", None)
            outcome.update({"condition": condition, "seed": seed, "experience": experience, "distribution": distribution, "split": tag})
            checkpoints.append(outcome)

    def maybe_checkpoint(experience: int) -> None:
        if experience not in set(config.checkpoints):
            return
        evaluate(experience, "A", heldout, "heldout")
        evaluate(experience, "B", probe, "probe")

    maybe_checkpoint(0)
    sample_rng = make_rng(seed, condition, "train", 0, "sample")
    for index in range(config.train_boxes):
        if index == config.change_at and memory is not None and not discounted and spec["utility"]:
            memory.discount_after_change(index)
            discounted = True
        pool = train if index < config.change_at else phase_b
        distribution = "A" if index < config.change_at else "B"
        task = pool[sample_rng.randrange(len(pool))]
        outcome = solve_box(
            config, task, seed, "train", index, memory, learn=memory is not None, abstention=spec["abstention"]
        )
        trace = outcome.pop("decisions_trace")
        if miner is not None and outcome["acceptable"]:
            episode = Episode(index, task["task_id"], dict(task["inventory"]), trace, outcome["Q"], outcome["A"], True)
            new_ops = miner.observe(episode)
            for op in new_ops:
                if spec["support_promote"]:
                    memory.promote(op, index, "recurrence")
                elif spec["utility"] and train_val:
                    val_task = train_val[index % len(train_val)]
                    ok, record = paired_should_promote(
                        config, op, memory, val_task, seed, index, spec["abstention"]
                    )
                    record.update({"condition": condition, "seed": seed, "experience": index})
                    pair_rows.append(record)
                    if ok:
                        memory.promote(op, index, "paired_utility")
                    else:
                        memory.events.append({"time": index, "kind": "keep_provisional", "op_id": op.op_id})
        if memory is not None:
            memory.age(index)
            memory.enforce_pressure(index)
        outcome.update(
            {
                "condition": condition,
                "seed": seed,
                "experience": index + 1,
                "distribution": distribution,
                "split": "train",
                "library_size": 0 if memory is None else len(memory.active()),
                "provisional_size": 0 if memory is None else len(memory.all_by_status("provisional")),
                "inactive_size": 0 if memory is None else len(memory.all_by_status("inactive")),
                "memory_bytes": 0 if memory is None else memory.bytes_used(),
                "mean_depth": _mean_depth(memory),
                "max_depth": _max_depth(memory),
            }
        )
        rows.append(outcome)
        maybe_checkpoint(index + 1)
    return {
        "condition": condition,
        "seed": seed,
        "train_rows": rows,
        "checkpoint_rows": checkpoints,
        "pair_rows": pair_rows,
        "memory": memory,
    }


def write_tables(run_dir: Path, train_rows, checkpoint_rows, pair_rows, op_rows) -> None:
    _write_csv(run_dir / "train_boxes.csv", train_rows)
    _write_csv(run_dir / "checkpoints.csv", checkpoint_rows)
    _write_csv(run_dir / "paired_validations.csv", pair_rows)
    _write_csv(run_dir / "operations.csv", op_rows)


def operation_rows(condition: str, seed: int, memory) -> list[dict]:
    if memory is None:
        return []
    rows = []
    for op in memory.operations:
        rows.append(
            {
                "condition": condition,
                "seed": seed,
                "op_id": op.op_id,
                "status": op.status,
                "depth": op.depth,
                "retrievals": op.retrievals,
                "applicability_failures": op.applicability_failures,
                "commitments": op.commitments,
                "successes": op.successes,
                "failures": op.failures,
                "average_q": op.average_q,
                "paired_savings": op.paired_savings,
                "attempts_saved": op.attempts_saved,
                "utility": op.utility,
                "nbytes": op.nbytes,
                "children": "|".join(op.children),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
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
