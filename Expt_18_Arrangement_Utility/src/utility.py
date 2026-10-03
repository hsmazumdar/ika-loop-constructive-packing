"""Sample legal placements and score one commit against primitive. No policy."""

from __future__ import annotations

import random
from collections import Counter

from diagnostic import _finish_reason, primitive_step
from environment import Action
from pieces import BOARD_SIZE, placed_cells
from solver import Ledger


def stage_name(occupied: int, early_below: int, middle_below: int) -> str:
    if occupied < early_below:
        return "early"
    if occupied < middle_below:
        return "middle"
    return "late"


def sample_indices(n_boxes: int, stride: int, limit: int) -> list[int]:
    """Stride through manifest order. Fit counts do not choose the boxes."""
    return list(range(0, int(n_boxes), int(stride)))[: int(limit)]


def select_patterns(frozen: list[dict], config) -> list[dict]:
    """High-support patterns are all kept. Two-inventory patterns are a seeded draw."""
    high = [item for item in frozen if int(item["n_inventories"]) >= int(config.high_support)]
    low = [item for item in frozen if int(item["n_inventories"]) == 2]
    order = list(range(len(low)))
    random.Random(int(config.sample_seed)).shuffle(order)
    picked = [low[i] for i in order[: int(config.support_two_sample)]]
    chosen = high + picked
    if config.pattern_limit is not None:
        chosen = chosen[: int(config.pattern_limit)]
    return chosen


def normalize_pattern(raw: dict, index: int) -> dict:
    return {
        "pattern_index": int(index),
        "pieces": int(raw["pieces"]),
        "n_inventories": int(raw["n_inventories"]),
        "n_boxes": int(raw["n_boxes"]),
        "counts": {str(k): int(v) for k, v in raw["counts"].items()},
        "anchors": tuple((str(p), int(r), int(x), int(y)) for p, r, x, y in raw["anchors"]),
        "cells": tuple((int(x), int(y)) for x, y in raw["cells"]),
    }


def first_translation(pattern: dict, occupied: set[tuple[int, int]], remaining: Counter) -> tuple[int, tuple[int, int] | None]:
    """First row-major origin that fits. Checks match the Expt-17 scanner until it stops."""
    checks = 1
    for piece, need in pattern["counts"].items():
        if remaining[piece] < int(need):
            return checks, None
    cells = pattern["cells"]
    for ox in range(BOARD_SIZE):
        for oy in range(BOARD_SIZE):
            checks += 1
            ok = True
            for dx, dy in cells:
                x, y = ox + dx, oy + dy
                checks += 1
                if x < 0 or y < 0 or x >= BOARD_SIZE or y >= BOARD_SIZE or (x, y) in occupied:
                    ok = False
                    break
            if ok:
                return checks, (ox, oy)
    return checks, None


def _occupied(env) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for inst in env.stack:
        cells.update(inst.cells)
    return cells


def _remaining(env) -> Counter:
    return Counter({str(k): int(v) for k, v in env.inventory.counts.items() if int(v) > 0})


def earliest_in_stage(snaps: list[dict], pattern: dict, stage: str, config) -> tuple[int, dict | None, tuple[int, int] | None]:
    """Stop at the first prefix in this stage with a legal translation. One placement, not every origin."""
    checks = 0
    for snap in snaps:
        name = stage_name(int(snap["occupied"]), int(config.early_below), int(config.middle_below))
        if name != stage:
            continue
        cost, origin = first_translation(pattern, _occupied(snap["env"]), _remaining(snap["env"]))
        checks += cost
        if origin is not None:
            return checks, snap, origin
    return checks, None, None


def commit_pattern(env, ledger: Ledger, pattern: dict, origin: tuple[int, int]) -> bool:
    """Place every anchor. One check per piece and per cell, whether or not the placement is legal."""
    ox, oy = origin
    for piece, rotation, dx, dy in pattern["anchors"]:
        ledger.charge("validation", 1)
        if env.terminal or not env.inventory.can_take(piece):
            return False
        cells = placed_cells(piece, int(rotation), int(dx) + int(ox), int(dy) + int(oy))
        for _cell in cells:
            ledger.charge("validation", 1)
        if not env._can_place_cells(cells):
            return False
        result = env.step(Action.place(piece, int(rotation), int(dx) + int(ox), int(dy) + int(oy)))
        if not result.accepted:
            return False
    return True


def continue_primitive(config, env, rng, tabu, ledger: Ledger, search_cap: int) -> dict:
    """Primitive search only. Validation already on the ledger is not part of the search cap."""
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.primitive_evals < int(search_cap):
        stop, _token = primitive_step(config, env, rng, tabu, ledger)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    reason = _finish_reason(env, ledger.primitive_evals, int(search_cap), config, reason)
    return {
        "Q": float(env.score),
        "A": int(ledger.A),
        "primitive_evals": int(ledger.primitive_evals),
        "validation": int(ledger.validation_cost),
        "acceptable": bool(env.score >= config.q_min),
        "termination": reason,
    }


def _restore(snap: dict):
    env = snap["env"].clone()
    rng = random.Random()
    rng.setstate(snap["rng_state"])
    return env, rng, set(snap["tabu"])


def replay_branch(config, snap: dict, pattern: dict | None, origin: tuple[int, int] | None) -> dict:
    env, rng, tabu = _restore(snap)
    # The primitive trajectory stopped here. Replaying it must not take another step.
    # A commit is a different action, so the commit branch may search afterward.
    if pattern is None and not snap.get("open_prefix", True):
        return {
            "Q": float(env.score),
            "A": 0,
            "primitive_evals": 0,
            "validation": 0,
            "acceptable": bool(env.score >= config.q_min),
            "termination": "trajectory_end",
            "valid": True,
        }
    ledger = Ledger()
    search_cap = max(0, int(config.eval_cap) - int(snap["prefix_A"]))
    valid = True
    if pattern is not None:
        valid = commit_pattern(env, ledger, pattern, origin)
        if not valid:
            return {
                "Q": None,
                "A": int(ledger.A),
                "primitive_evals": 0,
                "validation": int(ledger.validation_cost),
                "acceptable": False,
                "termination": "validation_fail",
                "valid": False,
            }
    out = continue_primitive(config, env, rng, tabu, ledger, search_cap)
    out["valid"] = valid
    return out


def box_opportunity(candidates: list[dict], config) -> dict:
    """One number per box: the best quality-preserving saving. Overlapping suffixes are not added."""
    usable = [row for row in candidates if row.get("quality_preserving_benefit")]
    largest = None
    if candidates:
        valid = [row for row in candidates if row.get("valid") and row.get("replay_ok") and row.get("effort_saving") is not None]
        if valid:
            largest = max(valid, key=lambda row: (row["effort_saving"], -row["pattern_index"]))
    if not usable:
        return {
            "n_candidates": len(candidates),
            "n_quality_preserving": 0,
            "ideal_saving": 0,
            "ideal_pattern": None,
            "ideal_stage": None,
            "ideal_occupied": None,
            "ideal_quality_delta": None,
            "counts_as_benefit": False,
            "largest_valid_saving": None if largest is None else largest["effort_saving"],
            "largest_valid_quality_delta": None if largest is None else largest["quality_delta"],
            "largest_valid_lost_quality": None if largest is None else bool(largest.get("quality_loss")),
        }
    best = max(usable, key=lambda row: (row["effort_saving"], -int(row["pattern_index"]), 0 if row["stage"] == "early" else 1))
    return {
        "n_candidates": len(candidates),
        "n_quality_preserving": len(usable),
        "ideal_saving": int(best["effort_saving"]),
        "ideal_pattern": int(best["pattern_index"]),
        "ideal_stage": best["stage"],
        "ideal_occupied": best.get("occupied"),
        "ideal_quality_delta": best["quality_delta"],
        "counts_as_benefit": int(best["effort_saving"]) >= int(config.min_saving),
        "largest_valid_saving": None if largest is None else largest["effort_saving"],
        "largest_valid_quality_delta": None if largest is None else largest["quality_delta"],
        "largest_valid_lost_quality": None if largest is None else bool(largest.get("quality_loss")),
    }


def decide(config, fresh_boxes: list[dict], family_boxes: list[dict], n_placements: int, n_replay_failed: int) -> dict:
    if n_placements and (n_replay_failed / n_placements) > float(config.max_replay_failure_fraction):
        row = "inconclusive_replay"
        text = (
            "The primitive branch did not reproduce the saved trajectory often enough for these "
            "comparisons to be evidence. No retrieval decision is drawn."
        )
    else:
        fresh_benefit = [box for box in fresh_boxes if box.get("counts_as_benefit")]
        family_benefit = [box for box in family_boxes if box.get("counts_as_benefit")]
        patterns = {box["ideal_pattern"] for box in fresh_benefit}
        stages = {box["ideal_stage"] for box in fresh_benefit}
        broad = (
            len(fresh_benefit) >= int(config.min_benefit_boxes)
            and len(patterns) >= int(config.min_patterns_broad)
            and len(stages) >= 2
        )
        if broad:
            row = "build_budgeted_matcher"
            text = (
                "Quality-preserving benefit on the sample covers independent fresh boxes, more than "
                "one stage, and more than two patterns. A later experiment may build a budgeted matcher. "
                "This run did not build one, and it does not show that recognition is cheap."
            )
        elif fresh_benefit or family_benefit:
            row = "narrow_retrieval"
            text = (
                "Quality-preserving benefit appears, but only for a few patterns or contexts. "
                "The next question would be a narrowly targeted retrieval rule, not a general matcher. "
                "The Expt-17 cost gate on exhaustive translation search still stands."
            )
        else:
            row = "stop_pattern_reuse"
            text = (
                "Even the best quality-preserving candidate in each sampled box stays under the "
                "declared saving floor. Stop this pattern-reuse branch. The Expt-17 cost gate is "
                "unchanged, and this is not a claim that every unsampled placement is useless."
            )
    return {
        "row": row,
        "text": text,
        "n_fresh_benefit_boxes": sum(1 for box in fresh_boxes if box.get("counts_as_benefit")),
        "n_family_benefit_boxes": sum(1 for box in family_boxes if box.get("counts_as_benefit")),
        "fresh_patterns": sorted({box["ideal_pattern"] for box in fresh_boxes if box.get("counts_as_benefit")}),
        "fresh_stages": sorted({box["ideal_stage"] for box in fresh_boxes if box.get("counts_as_benefit")}),
        "commitment": "diagnostic counterfactuals only; no pattern was admitted to a policy",
        "cost_gate": "not relaxed",
    }
