"""Validation required before a pilot or full lifetime."""

from __future__ import annotations

from pathlib import Path

import random

from abstraction_miner import AbstractionMiner, canonical_form, expand_primitives, steps_from_absolute
from controls import knockout
from config import Config
from environment import Action, PackingEnv
from evaluator import assert_split_disjoint, load_split, solve_box
from flat_memory_agent import make_memory
from inventory import Inventory
from memory import Episode, LearnedOperation
from pieces import catalogue_hash, placed_cells
from retrieval import state_features

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN", "rectangle_geometry")


def _bar(piece: str, x: int, y: int) -> dict:
    cells = placed_cells(piece, 0, x, y)
    return {"type": piece, "rotation": 0, "x": x, "y": y, "cells": cells}


def _decision(piece: str, x: int, y: int, features: list[float]) -> dict:
    placed = _bar(piece, x, y)
    return {
        "op_id": f"O_{piece}_0",
        "depth": 0,
        "placements": [placed],
        "features": features,
    }


def _episode(index: int, decisions: list[dict]) -> Episode:
    return Episode(index, f"e{index}", {"M": 2}, decisions, q=8, a=10, acceptable=True)


def test_catalogue_hash_and_quality_match_expt3():
    assert catalogue_hash() == CATALOGUE
    env = PackingEnv(budget=5, inventory=Inventory({"M": 1}))
    result = env.step(Action.place("M", 0, 0, 0))
    assert result.accepted
    assert env.score == 4
    assert env.score == env.mask.bit_count()


def test_splits_do_not_leak_and_primitive_score_is_the_expt3_prior():
    train = load_split("train")
    held = load_split("test")
    probe = [{"task_id": "b_probe", "inventory": {"M": 1}}]
    assert_split_disjoint(train, held, probe)
    assert train and held
    assert {task["task_id"] for task in train}.isdisjoint({task["task_id"] for task in held})
    config = Config()
    assert (config.score_area, config.score_contact, config.score_boundary) == (1.0, 0.2, 0.05)


def test_primitive_A_counts_candidates_not_internal_execution():
    config = Config(q_min=8, scan=16, physical=20, eval_cap=4000, seeds=(11,))
    task = {"task_id": "unit_m", "inventory": {"M": 2, "O": 2}}
    outcome = solve_box(config, task, 11, "test", 0, None, learn=False)
    assert outcome["A"] == outcome["primitive_evals"]
    assert outcome["internal_execution"] == 0
    assert outcome["A"] > outcome["successful_placements"]
    assert outcome["Q"] >= 4


def test_empty_hierarchical_memory_matches_primitive():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=4000)
    task = {"task_id": "unit_match", "inventory": {"M": 3, "O": 2}}
    memory = make_memory(config, hierarchical=True, unlimited=False, control=False)
    left = solve_box(config, task, 11, "test", 0, None, learn=False)
    right = solve_box(config, task, 11, "test", 0, memory, learn=False)
    assert left["Q"] == right["Q"]
    assert left["A"] == right["A"]
    assert left["successful_placements"] == right["successful_placements"]


def test_hierarchy_expands_to_the_primitive_sequence_and_flat_stops_at_depth_one():
    features = [0.0, 1.0, 0.0]
    window = [_decision("M", 0, 0, features), _decision("M", 1, 0, features)]
    config = Config(min_support=2, max_promotions_per_episode=4, operation_capacity=8, episodic_capacity=8)
    hierarchical = make_memory(config, hierarchical=True, unlimited=False, control=False)
    flat = make_memory(config, hierarchical=False, unlimited=False, control=False)
    control = make_memory(config, hierarchical=True, unlimited=False, control=True)
    miner_h = AbstractionMiner(config, hierarchical, control=False)
    miner_f = AbstractionMiner(config, flat, control=False)
    miner_c = AbstractionMiner(config, control, control=True)
    rng = random.Random(1)
    for index in (1, 2):
        miner_h.observe(_episode(index, window), rng)
        miner_f.observe(_episode(index, window), random.Random(1))
        miner_c.observe(_episode(index, window), random.Random(2))
    assert hierarchical.operations
    op = hierarchical.operations[0]
    assert op.depth == 1
    expanded = expand_primitives(op)
    assert len(expanded) == 2
    _canon_steps, geometry = canonical_form(steps_from_absolute([_bar("M", 0, 0), _bar("M", 1, 0)]))
    _stored, stored_geometry = canonical_form(expanded)
    assert geometry == stored_geometry
    assert all(item.depth == 1 for item in flat.operations)
    higher = {
        "op_id": op.op_id,
        "depth": 1,
        "placements": [_bar("M", 0, 0), _bar("M", 1, 0)],
        "features": features,
    }
    tail = _decision("O", 2, 0, features)
    pair = [higher, tail]
    for index in (3, 4):
        miner_h.observe(_episode(index, pair), random.Random(3))
        miner_f.observe(_episode(index, pair), random.Random(3))
    assert any(item.depth >= 2 for item in hierarchical.operations)
    assert all(item.depth == 1 for item in flat.operations)
    deep = next(item for item in hierarchical.operations if item.depth >= 2)
    assert len(expand_primitives(deep)) == 3
    assert control.operations
    real_keys = {item.canonical for item in hierarchical.operations}
    control_keys = {item.canonical for item in control.operations}
    assert real_keys.isdisjoint(control_keys)


def test_macro_internal_placements_are_not_added_to_A():
    config = Config(q_min=8, scan=8, physical=20, eval_cap=500, anchors=32, top_k=1, retrieval_pool=4, applicability_min=0.0)
    task = {"task_id": "macro_box", "inventory": {"M": 2}}
    env = PackingEnv(budget=20, inventory=Inventory({"M": 2}))
    features = list(state_features(env))
    steps, _geometry = canonical_form(steps_from_absolute([_bar("M", 0, 0), _bar("M", 1, 0)]))
    memory = make_memory(config, hierarchical=True, unlimited=False, control=False)
    op = LearnedOperation(
        op_id="M0001",
        depth=1,
        children=["O_M_0", "O_M_0"],
        steps=steps,
        nbytes=32,
        canonical="unit-macro",
        context=features,
        created_at=0,
        last_used=0,
        successes=2,
        attempts_saved=1,
        utility=5,
    )
    memory.operations.append(op)
    outcome = solve_box(config, task, 11, "test", 0, memory, learn=False)
    assert outcome["internal_execution"] == 2
    assert outcome["primitive_evals"] == 0
    assert outcome["A"] == outcome["retrieval_cost"] + outcome["learned_evals"]
    assert outcome["Q"] == 8


def test_empty_knockout_uses_the_same_evaluation_seed():
    config = Config(q_min=12, scan=12, physical=16, eval_cap=2000)
    task = {"task_id": "knock", "inventory": {"M": 4}}
    memory = make_memory(config, hierarchical=True, unlimited=False, control=False)
    intact = solve_box(config, task, 11, "heldout", 0, memory, learn=False)
    other = solve_box(config, task, 11, "heldout", 0, knockout(memory, "all", random.Random(0)), learn=False)
    assert intact["Q"] == other["Q"]
    assert intact["A"] == other["A"]


def test_memory_pressure_forgets_low_utility():
    config = Config(operation_capacity=1, byte_cap=10**9, decay=0.0)
    memory = make_memory(config, hierarchical=True, unlimited=False, control=False)
    low = LearnedOperation("M0001", 1, ["a"], [{"type": "M", "cells": ((0, 0),)}], 10, "low", [0.0], 0, 0, utility=-5)
    high = LearnedOperation("M0002", 1, ["b"], [{"type": "O", "cells": ((0, 0),)}], 10, "high", [0.0], 1, 1, utility=5)
    assert memory.add_operation(low, 1)
    assert memory.add_operation(high, 2)
    assert [op.op_id for op in memory.operations] == ["M0002"]
    assert any(event["kind"] == "delete" for event in memory.events)


def test_source_has_no_shape_labels():
    for path in ROOT.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
