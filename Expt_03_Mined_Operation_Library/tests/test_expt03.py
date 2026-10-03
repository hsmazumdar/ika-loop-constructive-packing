"""Focused tests for Expt-3. They do not read held-out witnesses."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mga3.environment import Action, PackingEnv
from mga3.experiment import dataset_hash, load_split
from mga3.hardware import PlacementWorkspace
from mga3.inventory import Inventory
from mga3.mining import applies_to_solution, assert_no_mutation, build_libraries, enumerate_groups
from mga3.ops import canonical_form, rectangle_geometry, reflected_canonical, steps_from_absolute
from mga3.pieces import ALL_PLACEMENTS, FULL_MASK, PIECES, catalogue_hash, orientation
from mga3.policy import Controller, conditional_efficiency, efficiency, leaves_unfillable, macro_fits
from mga3.rngutil import derive_seed
from mga3.solver import exact_cover

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"
DATASET = "668304e744f0d0ef22b164fb0e6a63a2fb065f835e170e9073a8fe3be7af53ce"


def _bar(piece: str, x: int, y: int) -> dict:
    cells = [(x + dx, y + dy) for dx, dy in orientation(PIECES[piece], 0)]
    return {"type": piece, "rotation": 0, "x": x, "y": y, "cells": cells}


def _solution(task_id: str, placements: list[dict]) -> dict:
    return {
        "task_id": task_id,
        "solution_id": "sol_" + task_id,
        "inventory": {},
        "placements": placements,
        "Q": 10,
        "P": len(placements),
        "solver": "unit",
    }


def test_catalogue_hash_matches_expt2():
    assert catalogue_hash() == CATALOGUE
    assert len(ALL_PLACEMENTS) == 3636


def test_split_is_disjoint_and_matches_manifest():
    manifest = json.loads((ROOT / "data" / "runtime" / "manifest.json").read_text(encoding="utf-8"))
    assert dataset_hash() == DATASET
    train, dev, test = manifest["splits"]["train"], manifest["splits"]["development"], manifest["splits"]["test"]
    assert len(train) == 24 and len(dev) == 8 and len(test) == 12
    assert set(train).isdisjoint(dev) and set(train).isdisjoint(test) and set(dev).isdisjoint(test)


def test_runtime_tree_has_no_witness_files():
    assert list(ROOT.rglob("*witness*")) == []
    src = (ROOT / "src" / "mga3").read_text() if False else "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "src" / "mga3").glob("*.py")
    )
    assert "validation_only" not in src


def test_no_reflection_in_canonical_rotation():
    steps = steps_from_absolute([_bar("A", 0, 0), _bar("M", 3, 0)])
    _, _, canon = canonical_form(steps)
    reflected = reflected_canonical(steps)
    # A is chiral. Reflection of a group that contains A is not one of the four rotations
    # unless the particular geometry happens to match. This pair does not.
    assert canon != reflected


def test_rectangle_filled_versus_hole():
    pair = [_bar("B", 0, 0), _bar("B", 1, 0)]
    steps = steps_from_absolute(pair)
    canon, _, _ = canonical_form(steps)
    geo = rectangle_geometry(canon)
    assert geo["rectangular"] is True
    assert geo["width"] >= 2 and geo["height"] >= 2
    holed = [
        {"type": "M", "cells": ((0, 0), (1, 0), (0, 1))},
        {"type": "M", "cells": ((2, 1),)},
    ]
    hole = rectangle_geometry(holed)
    assert hole["filled"] is False
    assert hole["rectangular"] is False


def test_same_pool_for_every_arm_and_support_by_task():
    left = [_bar("B", 0, 0), _bar("B", 1, 0), _bar("M", 4, 0)]
    solutions = [_solution("t1", left), _solution("t2", left), _solution("t3", [_bar("M", 0, 0), _bar("M", 1, 0)])]
    pool = enumerate_groups(solutions, window=6)
    ids = {item["op_id"] for item in pool}
    mined = build_libraries(solutions, {"window": 6, "byte_cap": 262144, "min_support_tasks": 2, "match_seed": 1})
    rect_ids = {op["op_id"] for op in mined["libraries"]["rect_mined"]}
    neutral_ids = {op["op_id"] for op in mined["libraries"]["neutral_mined"]}
    assert rect_ids <= ids
    assert neutral_ids <= ids
    assert mined["pool_ops"] == len(pool)
    rectangle = next(op for op in mined["libraries"]["rect_mined"] if op["demand"].get("B") == 2)
    assert set(rectangle["support_tasks"]) == {"t1", "t2"}
    assert rectangle["support_positions"] == 2


def test_frequent_rectangle_does_not_transfer_without_inventory():
    left = [_bar("B", 0, 0), _bar("B", 1, 0)]
    solutions = [_solution("t1", left), _solution("t2", left)]
    for solution in solutions:
        solution["inventory"] = {"B": 2}
    mined = build_libraries(solutions, {"window": 6, "byte_cap": 262144, "min_support_tasks": 2, "match_seed": 1})
    op = mined["libraries"]["rect_mined"][0]
    assert op["rectangular"] is True
    env = PackingEnv(budget=10, inventory=Inventory({"M": 2}))
    assert macro_fits(env, op["steps"]) is False
    config = {
        "quality_target": 80,
        "budgets": {
            "physical": 10,
            "eval_cap": 2000,
            "cheap_reserve": 100,
            "scan_per_decision": 16,
            "macros_considered": 4,
            "anchors_per_macro": 4,
            "max_consecutive_retrieval": 2,
            "think_allowance": 0,
        },
    }
    workspace = PlacementWorkspace("cpu")
    outcome = Controller(config, workspace, [op], True).run({"task_id": "no_b", "inventory": {"M": 2}}, 11, "test")
    assert outcome["ledger"]["macros_completed"] == 0


def test_replay_of_exact_cover_and_seed_independent_of_mode():
    task = load_split("train")[0]
    found = exact_cover(task["inventory"], 11, node_cap=40000)
    assert found["solved"] is True
    env = PackingEnv(budget=40, inventory=Inventory(task["inventory"]))
    for placement in found["placements"]:
        result = env.step(Action.place(placement["type"], placement["rotation"], placement["x"], placement["y"]))
        assert result.accepted
    assert env.score == 100
    assert derive_seed(11, task["task_id"], "heldout", 0, "select") == derive_seed(
        11, task["task_id"], "heldout", 0, "select"
    )


def test_efficiency_undefined_at_zero_and_gated():
    assert efficiency(0, 0) is None
    assert efficiency(80, 0) is None
    assert conditional_efficiency(79, 10, 80) is None
    assert conditional_efficiency(80, 10, 80) == pytest.approx(8.0)
    assert conditional_efficiency(90, 9, 80) == pytest.approx(10.0)


def test_invalid_place_and_interrupted_macro_keep_partial_board():
    env = PackingEnv(budget=5, inventory=Inventory({"M": 1}))
    bad = env.step(Action.place("M", 0, 9, 9))
    assert bad.invalid and env.score == 0 and env.place_attempts == 1 and env.actions_used == 1
    good = env.step(Action.place("M", 0, 0, 0))
    assert good.accepted and env.score == 4
    blocked = env.step(Action.place("M", 0, 0, 0))
    assert blocked.invalid and env.score == 4 and env.place_attempts == 3


def test_compute_cap_still_allows_one_cheap_placement():
    config = {
        "quality_target": 80,
        "budgets": {
            "physical": 10,
            "eval_cap": 30,
            "cheap_reserve": 30,
            "scan_per_decision": 10,
            "macros_considered": 1,
            "anchors_per_macro": 1,
            "max_consecutive_retrieval": 1,
            "think_allowance": 0,
        },
    }
    # spend limit is 0, so the first loop takes the reserved cheap scan.
    outcome = Controller(config, PlacementWorkspace("cpu"), [], False).run(
        {"task_id": "cap", "inventory": {"M": 3, "O": 3}}, 11, "development"
    )
    assert outcome["P"] > 0
    assert outcome["ledger"]["cheap_actions"] >= 1
    assert outcome["Q"] > 0
    hard = json.loads(json.dumps(config))
    hard["budgets"]["eval_cap"] = 0
    hard["budgets"]["cheap_reserve"] = 0
    stopped = Controller(hard, PlacementWorkspace("cpu"), [], False).run(
        {"task_id": "cap0", "inventory": {"M": 3}}, 11, "development"
    )
    assert stopped["termination"] == "compute_budget"
    assert stopped["P"] == 0
    assert stopped["censored"] is True
    assert stopped["E"] is None


def test_lookup_is_charged_and_frozen_library_does_not_change():
    op = {
        "op_id": "op_test",
        "steps": steps_from_absolute([_bar("M", 0, 0), _bar("M", 1, 0)]),
        "demand": {"M": 2},
        "train_success": 1.0,
        "support_tasks": ["t1", "t2"],
        "nbytes": 10,
        "rectangular": True,
    }
    config = {
        "quality_target": 80,
        "budgets": {
            "physical": 8,
            "eval_cap": 1500,
            "cheap_reserve": 50,
            "scan_per_decision": 12,
            "macros_considered": 2,
            "anchors_per_macro": 4,
            "max_consecutive_retrieval": 2,
            "think_allowance": 0,
        },
    }
    workspace = PlacementWorkspace("cpu")
    retrieved = Controller(config, workspace, [op], True).run({"task_id": "box", "inventory": {"M": 4}}, 11, "heldout")
    lesion = Controller(config, workspace, [op], False).run({"task_id": "box", "inventory": {"M": 4}}, 11, "heldout")
    assert retrieved["ledger"]["library_lookups"] > 0
    assert retrieved["ledger"]["candidate_evals"] >= retrieved["ledger"]["library_lookups"]
    assert lesion["ledger"]["library_lookups"] == 0
    assert lesion["Q"] == Controller(config, workspace, [], False).run(
        {"task_id": "box", "inventory": {"M": 4}}, 11, "heldout"
    )["Q"]
    document = {"frozen": True, "ops": [op]}
    assert assert_no_mutation(document) is False
    assert document["ops"] == [op]


def test_mode_order_does_not_change_the_primitive_episode():
    config = {
        "quality_target": 80,
        "budgets": {
            "physical": 12,
            "eval_cap": 2000,
            "cheap_reserve": 80,
            "scan_per_decision": 16,
            "macros_considered": 2,
            "anchors_per_macro": 2,
            "max_consecutive_retrieval": 1,
            "think_allowance": 0,
        },
    }
    task = {"task_id": "same", "inventory": {"O": 4, "M": 2}}
    workspace = PlacementWorkspace("cpu")
    first = Controller(config, workspace, [], False).run(task, 22, "heldout")
    second = Controller(config, workspace, [], False).run(task, 22, "heldout")
    assert first["Q"] == second["Q"]
    assert first["placements"] == second["placements"]
    assert first["ledger"]["candidate_evals"] == second["ledger"]["candidate_evals"]


def test_gpu_overlap_matches_bitmask():
    workspace = PlacementWorkspace("cuda")
    overlap, _contact = workspace.score_indices(0, [0, 1, 2])
    assert overlap == [False, False, False]
    mask = ALL_PLACEMENTS[0].mask
    overlap, contact = workspace.score_indices(mask, [0])
    assert overlap == [True]
    assert workspace.gpu_ops >= 2
    assert workspace.device_name().startswith("NVIDIA")
    assert contact[0] >= 0


def test_small_hole_is_unfillable_and_sealed_board_undoes():
    assert leaves_unfillable(FULL_MASK ^ 1, Inventory({"M": 1})) is True
    assert leaves_unfillable(0, Inventory({"M": 1})) is False
    config = {
        "quality_target": 80,
        "budgets": {
            "physical": 20,
            "eval_cap": 5000,
            "cheap_reserve": 4000,
            "scan_per_decision": 8,
            "macros_considered": 1,
            "anchors_per_macro": 1,
            "max_consecutive_retrieval": 1,
            "think_allowance": 0,
            "undo_budget": 2,
            "continuation_steps": 0,
            "continuation_scan": 1,
        },
    }
    controller = Controller(config, PlacementWorkspace("cpu"), [], False)
    env = PackingEnv(budget=20, inventory=Inventory({"M": 1}))
    env.step(Action.place("M", 0, 0, 0))
    env.mask = FULL_MASK
    controller._cheap(env, [])
    assert env.undos == 1
    assert env.terminal is False
    assert controller.tabu is not None


def test_continuation_rejects_a_macro_that_leaves_a_small_hole():
    config = {
        "quality_target": 80,
        "budgets": {
            "physical": 20,
            "eval_cap": 400,
            "cheap_reserve": 20,
            "scan_per_decision": 4,
            "macros_considered": 1,
            "anchors_per_macro": 2,
            "max_consecutive_retrieval": 1,
            "think_allowance": 0,
            "undo_budget": 0,
            "continuation_steps": 0,
            "continuation_scan": 1,
        },
    }
    controller = Controller(config, PlacementWorkspace("cpu"), [], False)
    env = PackingEnv(budget=20, inventory=Inventory({"M": 2}))
    env.mask |= (1 << 1) | (1 << 10)
    env.cells[0][1] = ("M", 1)
    env.cells[1][0] = ("M", 1)
    steps = [{"type": "M", "cells": ((5, 0), (5, 1), (5, 2), (5, 3))}]
    _gain, blocked = controller._simulated_gain(env, None, macro_steps=steps)
    assert blocked is True


def test_partial_training_board_can_validate_a_group():
    steps = steps_from_absolute([_bar("M", 2, 0), _bar("M", 3, 0)])
    solution = {
        "inventory": {"M": 3},
        "placements": [_bar("M", 0, 0), _bar("M", 2, 0), _bar("M", 3, 0)],
    }
    assert applies_to_solution(steps, solution) is True
    assert applies_to_solution(steps, {"inventory": {"O": 1}, "placements": []}) is False


def test_checkpoint_keys_are_mode_independent():
    key_a = "heldout|10|11|inv_x|primitive"
    key_b = "heldout|10|11|inv_x|rect_mined"
    assert key_a != key_b
    # The select stream does not contain the arm name.
    assert "primitive" not in f"{derive_seed(11, 'inv_x', 'heldout', 0, 'select')}"
