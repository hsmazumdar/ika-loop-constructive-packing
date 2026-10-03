"""Expt-4B validation. Held-out boxes must never enter pairing or mining."""

from __future__ import annotations

from pathlib import Path

from config import Config, smoke_config
from experiment import assert_splits, flags, load_split, reserve_train_val
from memory import LearnedOperation, make_memory
from miner import canonical_form, connected_steps, steps_from_absolute
from pieces import catalogue_hash, placed_cells
from promotion import paired_should_promote
from retrieval import cosine, state_features
from solver import solve_box

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN", "rectangle_geometry")


def test_catalogue_and_q_match_expt4():
    assert catalogue_hash() == CATALOGUE
    from environment import Action, PackingEnv
    from inventory import Inventory

    env = PackingEnv(budget=5, inventory=Inventory({"M": 1}))
    assert env.step(Action.place("M", 0, 0, 0)).accepted
    assert env.score == 4


def test_train_val_never_overlaps_heldout():
    train_all = load_split("train")
    held = load_split("test")
    train, val = reserve_train_val(train_all, 4)
    assert_splits(train, held, [{"task_id": "b_x", "inventory": {}}], val)
    assert {t["task_id"] for t in val}.isdisjoint({t["task_id"] for t in held})


def test_provisional_operations_are_not_used():
    config = Config(q_min=8, scan=16, physical=20, eval_cap=400, seeds=(11,))
    task = {"task_id": "unit_m", "inventory": {"M": 2, "O": 2}}
    memory = make_memory(config)
    steps, _geo = canonical_form(steps_from_absolute([
        {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
        {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
    ]))
    op = LearnedOperation("M0001", 1, ["a", "b"], steps, 10, "canon", [0.0] * 8, 0, 0, status="provisional")
    memory.operations.append(op)
    none = solve_box(config, task, 11, "test", 0, None, learn=False, abstention=False)
    with_p = solve_box(config, task, 11, "test", 0, memory, learn=False, abstention=False)
    assert none["A"] == with_p["A"]
    assert none["Q"] == with_p["Q"]
    assert with_p["internal_execution"] == 0


def test_empty_active_library_matches_primitive():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=800)
    task = {"task_id": "match", "inventory": {"M": 3, "O": 2}}
    memory = make_memory(config)
    left = solve_box(config, task, 11, "test", 0, None, learn=False, abstention=False)
    right = solve_box(config, task, 11, "test", 0, memory, learn=False, abstention=True)
    assert left["Q"] == right["Q"]
    assert left["A"] == right["A"]


def test_internal_execution_not_added_to_A():
    config = Config(q_min=8, scan=8, physical=20, eval_cap=500, anchors=32, top_k=1, retrieval_pool=4, applicability_min=-1.0)
    task = {"task_id": "macro_box", "inventory": {"M": 2}}
    steps, _geo = canonical_form(steps_from_absolute([
        {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
        {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
    ]))
    memory = make_memory(config)
    op = LearnedOperation("M0001", 1, ["O_M_0", "O_M_0"], steps, 32, "unit-macro", [0.0] * 40, 0, 0, status="active")
    memory.operations.append(op)
    outcome = solve_box(config, task, 11, "test", 0, memory, learn=False, abstention=False)
    assert outcome["internal_execution"] == 2
    assert outcome["A"] == outcome["retrieval_cost"] + outcome["learned_evals"] + outcome["applicability_cost"] + outcome["primitive_evals"]
    assert outcome["Q"] == 8


def test_connected_steps_reject_disjoint_cells():
    a = {"type": "M", "cells": ((0, 0), (0, 1), (0, 2), (0, 3))}
    b = {"type": "M", "cells": ((9, 9), (9, 8), (9, 7), (9, 6))}
    assert not connected_steps([a, b])


def test_condition_flags():
    assert flags("primitive")["use_memory"] is False
    assert flags("current_hierarchy")["support_promote"] is True
    assert flags("utility_promotion")["utility"] is True
    assert flags("contextual_abstention")["abstention"] is True
    assert flags("both")["utility"] and flags("both")["abstention"]


def test_paired_promotion_requires_lower_A_and_quality():
    config = smoke_config()
    config = Config(**{**config.to_dict(), "pair_eval_cap": 400, "q_min": 8, "scan": 12, "physical": 16, "eval_cap": 800})
    task = {"task_id": "pair", "inventory": {"M": 4}}
    memory = make_memory(config)
    steps, _geo = canonical_form(steps_from_absolute([
        {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
        {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
    ]))
    candidate = LearnedOperation("M0099", 1, ["x", "y"], steps, 20, "pair-canon", [0.1] * 8, 0, 0, status="provisional")
    ok, record = paired_should_promote(config, candidate, memory, task, 11, 0, False)
    assert "A_with" in record and "A_without" in record
    assert record["promoted"] == ok
    if ok:
        assert record["A_with"] < record["A_without"]


def test_discount_can_deactivate():
    config = Config(retire_utility=0.0, env_discount=0.0, decay=0.0)
    memory = make_memory(config)
    op = LearnedOperation("M0001", 1, ["a"], [{"type": "M", "cells": ((0, 0),)}], 10, "x", [0.0], 0, 0, status="active", successes=5, utility=5)
    memory.operations.append(op)
    memory.discount_after_change(10)
    assert op.status in {"active", "inactive"}
    assert op.successes == 0


def test_source_has_no_shape_labels():
    for path in ROOT.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name


def test_cosine_unknown_is_zero():
    assert cosine([], []) == 0.0
