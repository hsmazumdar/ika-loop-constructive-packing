"""Train library, collect gate labels, freeze gates, evaluate factorial on fresh boxes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from collect import collect_box
from config import Config, EVAL_CONDITIONS
from diagnostic import solve_gated
from gates import COMMIT_NAMES, CONSULT_NAMES, choose_threshold, fit_gate
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


def assert_splits(train, development, eval_tasks, train_val) -> None:
    train_ids = _ids(train) | _ids(train_val)
    if train_ids & _ids(development):
        raise RuntimeError("development overlaps training")
    if train_ids & _ids(eval_tasks):
        raise RuntimeError("eval boxes overlap training")
    if _ids(development) & _ids(eval_tasks):
        raise RuntimeError("eval boxes overlap development")
    blocked = []
    for rel in (
        ROOT.parent / "Expt_04C_Confirm_Reusable_Knowledge" / "data" / "test.json",
        ROOT.parent / "Expt_04D2_Costly_Choices" / "data" / "fresh.json",
    ):
        if rel.exists():
            blocked.extend(json.loads(rel.read_text(encoding="utf-8"))["tasks"])
    if _ids(blocked) & _ids(eval_tasks):
        raise RuntimeError("eval boxes overlap a held-out prior split")


def train_library(config: Config, seed: int, train: list[dict], train_val: list[dict]):
    memory = make_memory(config, hierarchical=True, selective_retire=True)
    miner = AbstractionMiner(config, memory)
    sample_rng = make_rng(seed, "selective_hierarchical", "train", 0, "sample")
    for index in range(config.train_boxes):
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


def _state_key(row: dict) -> tuple:
    return (row["task_id"], int(row["occupied_at_choice"]), int(row["actions_used"]))


def _split_by_box(rows: list[dict], frac: float = 0.75) -> tuple[list[dict], list[dict]]:
    boxes = sorted({row["task_id"] for row in rows})
    cut = max(1, int(len(boxes) * frac)) if boxes else 0
    train_ids = set(boxes[:cut])
    val_ids = set(boxes[cut:]) or train_ids
    train_rows = [row for row in rows if row["task_id"] in train_ids]
    val_rows = [row for row in rows if row["task_id"] in val_ids]
    return train_rows, val_rows


def fit_gates(config: Config, records: list[dict]) -> tuple[object, object, dict]:
    commit_rows = [
        {
            "vector": row["commit_vector"],
            "y": bool(row["acceptable_success"]),
            "remaining_saving": float(row["effort_saving_remaining"]),
            "quality_ok": bool(row["quality_ok"]),
            "op_id": row["op_id"],
        }
        for row in records
    ]
    by_state: dict[tuple, list[dict]] = {}
    for row in records:
        by_state.setdefault(_state_key(row), []).append(row)
    consult_rows = []
    for items in by_state.values():
        any_success = any(bool(item["acceptable_success"]) for item in items)
        worst = min(float(item["effort_saving_remaining"]) for item in items)
        quality_ok = all(bool(item["quality_ok"]) for item in items) if not any_success else True
        consult_rows.append(
            {
                "vector": items[0]["consult_vector"],
                "y": any_success,
                "remaining_saving": worst if not any_success else max(float(i["effort_saving_remaining"]) for i in items),
                "quality_ok": quality_ok,
                "op_id": None,
                "task_id": items[0]["task_id"],
            }
        )
        for item in items:
            item["_state_success"] = any_success
    commit_fit, commit_val = _split_by_box(records)
    consult_fit, consult_val = _split_by_box(consult_rows)
    commit_gate = fit_gate(
        COMMIT_NAMES,
        [
            {
                "vector": r["commit_vector"],
                "y": bool(r["acceptable_success"]),
                "remaining_saving": float(r["effort_saving_remaining"]),
                "quality_ok": bool(r["quality_ok"]),
                "op_id": r["op_id"],
            }
            for r in commit_fit
        ],
        use_op_bias=True,
        steps=config.gate_steps,
        scale=config.severe_loss_scale,
        quality_fail_weight=config.quality_fail_weight,
    )
    consult_gate = fit_gate(
        CONSULT_NAMES,
        consult_fit,
        use_op_bias=False,
        steps=config.gate_steps,
        scale=config.severe_loss_scale,
        quality_fail_weight=config.quality_fail_weight,
    )
    commit_val_rows = [
        {
            "vector": r["commit_vector"],
            "y": bool(r["acceptable_success"]),
            "remaining_saving": float(r["effort_saving_remaining"]),
            "quality_ok": bool(r["quality_ok"]),
            "op_id": r["op_id"],
        }
        for r in commit_val
    ]
    choose_threshold(commit_gate, commit_val_rows, True)
    choose_threshold(consult_gate, consult_val, False)
    summary = {
        "n_commit_labels": len(commit_rows),
        "n_consult_states": len(consult_rows),
        "n_unchosen": sum(1 for r in records if not r["selected_by_current_policy"]),
        "n_selected": sum(1 for r in records if r["selected_by_current_policy"]),
        "commit_threshold": commit_gate.threshold,
        "consult_threshold": consult_gate.threshold,
        "commit_op_bias": dict(commit_gate.op_bias),
        "consult_weights": {name: w for name, w in zip(CONSULT_NAMES, consult_gate.weights)},
        "commit_weights": {name: w for name, w in zip(COMMIT_NAMES, commit_gate.weights)},
    }
    return consult_gate, commit_gate, summary


def collect_labels(config: Config, seed: int, train: list[dict], memory) -> tuple[list[dict], int]:
    sample_rng = make_rng(seed, "gate-collect", "train", 0, "boxes")
    n = min(int(config.collect_boxes), len(train))
    boxes = [train[sample_rng.randrange(len(train))] for _ in range(n)]
    records = []
    learning_a = 0
    for index, task in enumerate(boxes):
        box_rng = make_rng(seed, task["task_id"], "gate-collect", index, "unchosen")
        batch, cost = collect_box(config, task, seed, "gate-collect", index, memory, "train", box_rng)
        records.extend(batch)
        learning_a += cost
    return records, learning_a


def evaluate(config: Config, seed: int, tasks: list[dict], memory, consult_gate, commit_gate) -> list[dict]:
    rows = []
    for index, task in enumerate(tasks):
        for name in EVAL_CONDITIONS:
            mem = None if name == "primitive" else memory
            cgate = consult_gate if name in ("consult_gate_only", "both_gates") else None
            kgate = commit_gate if name in ("commit_gate_only", "both_gates") else None
            outcome = solve_gated(config, task, seed, "eval", index, mem, name, cgate, kgate)
            outcome.update({"seed": seed, "experience": config.train_boxes, "split": "eval"})
            rows.append(outcome)
    return rows


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
