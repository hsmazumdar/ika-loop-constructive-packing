"""Paired validation on training-only problems. Held-out boxes are never used."""

from __future__ import annotations

from dataclasses import replace

from memory import LearnedOperation, OperationMemory, clone_active
from solver import solve_box


def _arm(config, task, seed, repetition, memory, abstention: bool, tag: str) -> dict:
    return solve_box(
        config,
        task,
        seed,
        f"pair-{tag}",
        repetition,
        memory,
        learn=False,
        abstention=abstention,
        eval_cap=config.pair_eval_cap,
    )


def _with_ops(base: OperationMemory, extra: list[LearnedOperation]) -> OperationMemory:
    copied = clone_active(base)
    copied.operations = [op for op in copied.operations if op.status == "active"]
    for op in extra:
        copied.operations.append(replace(op, status="active"))
    return copied


def paired_should_promote(config, candidate: LearnedOperation, memory: OperationMemory, task: dict, seed: int, time_index: int, abstention: bool) -> tuple[bool, dict]:
    """Promote if A falls and the quality gate is preserved, vs matched start without the candidate."""
    without = _arm(config, task, seed, time_index, memory, abstention, "without")
    with_mem = _with_ops(memory, [candidate])
    with_c = _arm(config, task, seed, time_index, with_mem, abstention, "with")
    quality_ok = with_c["Q"] >= config.q_min or with_c["Q"] >= without["Q"]
    effort_down = with_c["A"] < without["A"]
    composition_ok = True
    children_row = None
    if candidate.depth > 1:
        child_ids = set(candidate.children)
        children = [op for op in memory.active() if op.op_id in child_ids]
        child_mem = _with_ops(memory, children)
        children_row = _arm(config, task, seed, time_index, child_mem, abstention, "children")
        composition_ok = with_c["A"] < children_row["A"]
    ok = quality_ok and effort_down and composition_ok
    record = {
        "candidate": candidate.op_id,
        "depth": candidate.depth,
        "Q_with": with_c["Q"],
        "A_with": with_c["A"],
        "Q_without": without["Q"],
        "A_without": without["A"],
        "A_children": None if children_row is None else children_row["A"],
        "promoted": ok,
        "task_id": task["task_id"],
        "pair_eval_with": with_c["A"],
        "pair_eval_without": without["A"],
        "internal_with": with_c["internal_execution"],
        "internal_without": without["internal_execution"],
        "elapsed_with": with_c["elapsed_s"],
        "elapsed_without": without["elapsed_s"],
    }
    if ok:
        candidate.paired_savings += float(without["A"] - with_c["A"])
        candidate.recompute(memory.fail_penalty, memory.storage_weight)
    return ok, record
