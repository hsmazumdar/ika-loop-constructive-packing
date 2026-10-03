"""Enumerate connected placement groups and admit three libraries.

All three arms see the same enumerated pool. Rectangularity is applied only
as a designer filter on the rectangle arm. Support is the number of distinct
training task ids, not repeated copies inside one board.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from itertools import combinations

from mga3.environment import Action, PackingEnv
from mga3.inventory import Inventory
from mga3.policy import _SHAPE_INDEX, macro_fits
from mga3.ops import (
    canonical_form,
    connected_steps,
    inventory_demand,
    operation_id,
    placement_params,
    rectangle_geometry,
    rotate_steps,
    steps_from_absolute,
    translate_steps,
)
from mga3.pieces import ALL_PLACEMENTS, PIECE_TYPES


def _fits_empty(steps: list[dict], inventory: dict[str, int]) -> bool:
    demand = inventory_demand(steps)
    inv = Inventory(inventory)
    if not inv.fits_multiset(demand):
        return False
    env = PackingEnv(budget=max(8, len(steps) + 2), inventory=inv)
    for step in steps:
        params = placement_params(step["type"], step["cells"])
        if params is None:
            return False
        rotation, x, y = params
        result = env.step(Action.place(step["type"], rotation, x, y))
        if not result.accepted:
            return False
    return True


def _has_site(steps: list[dict], env: PackingEnv, trial_cap: int = 24) -> bool:
    if not env.inventory.fits_multiset(inventory_demand(steps)):
        return False
    trials = 0
    for k in range(4):
        turned = rotate_steps(steps, k)
        if macro_fits(env, turned):
            return True
        first = turned[0]
        cells = [tuple(c) for c in first["cells"]]
        min_x = min(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        norm = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
        for placement in _SHAPE_INDEX.get((first["type"], norm), []):
            trials += 1
            ox = placement.x - min_x
            oy = placement.y - min_y
            if macro_fits(env, translate_steps(turned, ox, oy)):
                return True
            if trials >= trial_cap:
                return False
    return False


def applies_to_inventory(steps: list[dict], inventory: dict[str, int]) -> bool:
    """Offline check: some rigid rotation has a legal site on an empty board."""
    demand = inventory_demand(steps)
    if not Inventory(inventory).fits_multiset(demand):
        return False
    for k in range(4):
        turned = rotate_steps(steps, k)
        first = turned[0]
        shape = tuple(sorted(tuple(c) for c in first["cells"]))
        min_x = min(x for x, _ in shape)
        min_y = min(y for _, y in shape)
        seen = 0
        for placement in ALL_PLACEMENTS:
            if placement.piece_type != first["type"]:
                continue
            placed = tuple(sorted(placement.cells))
            if len(placed) != len(shape):
                continue
            ox = placement.x - min_x
            oy = placement.y - min_y
            shifted = tuple(sorted((x + ox, y + oy) for x, y in shape))
            if shifted != placed:
                continue
            seen += 1
            if _fits_empty(translate_steps(turned, ox, oy), inventory):
                return True
            if seen > 40:
                break
    return False


def applies_to_solution(steps: list[dict], solution: dict) -> bool:
    """Legal site on the empty board or on a prefix of this training solution.

    Prefixes are partial boards from the recorded teacher trace. A hit here is
    still training experience, not a held-out witness.
    """
    inventory = solution.get("inventory") or {}
    if not Inventory(inventory).fits_multiset(inventory_demand(steps)):
        return False
    placements = solution.get("placements") or []
    cuts = {0}
    if placements:
        cuts.add(len(placements) // 2)
        cuts.add(max(0, len(placements) - len(steps)))
    for cut in sorted(cuts):
        env = PackingEnv(budget=max(len(placements) + 4, 8), inventory=Inventory(inventory))
        failed = False
        for placement in placements[:cut]:
            result = env.step(
                Action.place(placement["type"], int(placement["rotation"]), int(placement["x"]), int(placement["y"]))
            )
            if not result.accepted:
                failed = True
                break
        if failed or env.terminal:
            continue
        if _has_site(steps, env):
            return True
    return False


def enumerate_groups(solutions: list[dict], window: int) -> list[dict]:
    """Bounded order-windows. The same function feeds every arm."""
    merged: dict[str, dict] = {}
    for solution in solutions:
        placements = solution["placements"]
        n = len(placements)
        for start in range(n):
            block = placements[start : start + window]
            upper = min(4, len(block))
            for size in range(2, upper + 1):
                for comb in combinations(range(len(block)), size):
                    chosen = [block[i] for i in comb]
                    steps = steps_from_absolute(chosen)
                    if not connected_steps(steps):
                        continue
                    canon_steps, _k, canon = canonical_form(steps)
                    if not connected_steps(canon_steps):
                        continue
                    geo = rectangle_geometry(canon_steps)
                    op_id = operation_id(canon)
                    slot = merged.get(op_id)
                    position = (
                        solution["task_id"],
                        solution["solution_id"],
                        tuple((p["type"], p["rotation"], p["x"], p["y"]) for p in chosen),
                    )
                    if slot is None:
                        slot = {
                            "op_id": op_id,
                            "steps": canon_steps,
                            "canonical": canon,
                            "rectangular": geo["rectangular"],
                            "width": geo["width"],
                            "height": geo["height"],
                            "area": geo["area"],
                            "n_pieces": len(canon_steps),
                            "demand": inventory_demand(canon_steps),
                            "task_ids": set(),
                            "positions": set(),
                            "example": {
                                "task_id": solution["task_id"],
                                "solution_id": solution["solution_id"],
                                "placements": chosen,
                            },
                        }
                        merged[op_id] = slot
                    slot["task_ids"].add(solution["task_id"])
                    slot["positions"].add(position)
    return list(merged.values())


def _nbytes(record: dict) -> int:
    payload = {
        "op_id": record["op_id"],
        "steps": [
            {"type": step["type"], "cells": [list(c) for c in step["cells"]]} for step in record["steps"]
        ],
        "demand": record["demand"],
        "support_tasks": sorted(record["support_tasks"]),
        "rectangular": record["rectangular"],
        "area": record["area"],
        "width": record["width"],
        "height": record["height"],
    }
    return len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _finish(raw: dict, validation_hits: int, n_valid: int) -> dict:
    support_tasks = sorted(raw["task_ids"])
    record = {
        "op_id": raw["op_id"],
        "steps": raw["steps"],
        "canonical": raw["canonical"],
        "rectangular": raw["rectangular"],
        "width": raw["width"],
        "height": raw["height"],
        "area": raw["area"],
        "n_pieces": raw["n_pieces"],
        "demand": raw["demand"],
        "support_tasks": support_tasks,
        "support_positions": len(raw["positions"]),
        "validation_hits": validation_hits,
        "train_success": (validation_hits / n_valid) if n_valid else 0.0,
        "example": raw["example"],
        "provenance": "teacher_training_solutions",
    }
    record["nbytes"] = _nbytes(record)
    return record


def _rank_key(record: dict) -> tuple:
    return (
        -len(record["support_tasks"]),
        -int(record["validation_hits"]),
        int(record["nbytes"]),
        record["op_id"],
    )


def _admit(records: list[dict], byte_cap: int, rejections: list[dict], arm: str) -> list[dict]:
    kept = []
    used = 0
    for record in sorted(records, key=_rank_key):
        if used + record["nbytes"] > byte_cap:
            rejections.append({"op_id": record["op_id"], "arm": arm, "reason": "byte_cap"})
            continue
        kept.append(record)
        used += record["nbytes"]
    return kept


def build_libraries(
    solutions: list[dict],
    config: dict,
    validation_ids: set[str] | None = None,
) -> dict:
    """Mine on solutions whose task ids are not in validation_ids.

    ``solutions`` must already be the training prefix. Validation solutions are
    passed separately and are not added to frequency counts.
    """
    window = int(config.get("window", 10))
    byte_cap = int(config.get("byte_cap", 256 * 1024))
    min_support = int(config.get("min_support_tasks", 2))
    match_seed = int(config.get("match_seed", 20260929))
    mine_solutions = solutions
    valid_solutions = []
    if validation_ids:
        mine_solutions = [s for s in solutions if s["task_id"] not in validation_ids]
        valid_solutions = [s for s in solutions if s["task_id"] in validation_ids]
    pool = enumerate_groups(mine_solutions, window)
    n_valid_tasks = len({s["task_id"] for s in valid_solutions})
    rejections: list[dict] = []
    finished = []
    for raw in pool:
        if len(raw["task_ids"]) < min_support:
            rejections.append({"op_id": raw["op_id"], "arm": "pool", "reason": "support_below_minimum"})
            continue
        hits = 0
        if n_valid_tasks:
            for solution in valid_solutions:
                if applies_to_solution(raw["steps"], solution):
                    hits += 1
            if hits <= 0:
                rejections.append({"op_id": raw["op_id"], "arm": "pool", "reason": "no_validation_applicability"})
                continue
        finished.append(_finish(raw, hits, n_valid_tasks))
    rectangles = [r for r in finished if r["rectangular"]]
    non_rect = [r for r in finished if not r["rectangular"]]
    rect_lib = _admit(rectangles, byte_cap, rejections, "rect_mined")
    neutral_lib = _admit(finished, byte_cap, rejections, "neutral_mined")
    neutral_rect = sum(1 for r in neutral_lib if r["rectangular"])
    matched, mismatches = _match(rect_lib, non_rect, byte_cap, match_seed, rejections)
    return {
        "pool_ops": len(pool),
        "admitted_candidates": len(finished),
        "rectangle_candidates": len(rectangles),
        "neutral_rectangles": neutral_rect,
        "validation_tasks": n_valid_tasks,
        "rejections": rejections,
        "mismatches": mismatches,
        "libraries": {
            "rect_mined": rect_lib,
            "neutral_mined": neutral_lib,
            "matched_control": matched,
        },
        "bytes": {
            "rect_mined": sum(r["nbytes"] for r in rect_lib),
            "neutral_mined": sum(r["nbytes"] for r in neutral_lib),
            "matched_control": sum(r["nbytes"] for r in matched),
        },
    }


def _match(rect_lib, non_rect, byte_cap, match_seed, rejections):
    rng = random.Random(match_seed)
    used_ids = set()
    kept = []
    used_bytes = 0
    mismatches = []
    if not rect_lib:
        mismatches.append({"reason": "empty_rectangle_library"})
        return kept, mismatches
    for target in rect_lib:
        best_dist = None
        bucket = []
        for cand in non_rect:
            if cand["op_id"] in used_ids:
                continue
            dist = (
                abs(cand["n_pieces"] - target["n_pieces"]) * 100
                + abs(cand["area"] - target["area"]) * 10
                + abs(sum(cand["demand"].values()) - sum(target["demand"].values()))
            )
            if best_dist is None or dist < best_dist:
                best_dist = dist
                bucket = [cand]
            elif dist == best_dist:
                bucket.append(cand)
        if not bucket:
            mismatches.append({"target": target["op_id"], "reason": "no_remaining_non_rectangle"})
            continue
        rng.shuffle(bucket)
        choice = bucket[0]
        if used_bytes + choice["nbytes"] > byte_cap:
            rejections.append({"op_id": choice["op_id"], "arm": "matched_control", "reason": "byte_cap"})
            mismatches.append({"target": target["op_id"], "reason": "byte_cap"})
            continue
        used_ids.add(choice["op_id"])
        kept.append(choice)
        used_bytes += choice["nbytes"]
    return kept, mismatches


def library_document(name: str, ops: list[dict], meta: dict) -> dict:
    return {
        "arm": name,
        "frozen": True,
        "ops": ops,
        "nbytes": sum(op["nbytes"] for op in ops),
        "n_ops": len(ops),
        "meta": meta,
    }


def assert_no_mutation(document: dict) -> bool:
    """Frozen evaluation must not append operations."""
    if document.get("frozen"):
        return False
    document.setdefault("ops", []).append({"op_id": "illegal"})
    return True
