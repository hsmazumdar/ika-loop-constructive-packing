"""Expt-4D tests."""

from __future__ import annotations

from pathlib import Path

from analysis import attach_savings
from config import QUALITY_LOSS_MARGIN, Config
from diagnostic import solve_diagnostic
from environment import Action, PackingEnv
from experiment import assert_dev_disjoint, load_split, reserve_train_val
from inventory import Inventory
from memory import LearnedOperation, make_memory
from miner import canonical_form, steps_from_absolute
from pieces import catalogue_hash, placed_cells
from retrieval import state_features

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_effort_saving_sign_is_primitive_minus_agent():
    assert QUALITY_LOSS_MARGIN == 1.0
    rows = attach_savings(
        [
            {"seed": 1, "task_id": "t", "mode": "primitive", "Q": 80, "A": 2000},
            {"seed": 1, "task_id": "t", "mode": "normal_reuse", "Q": 80, "A": 1800},
        ],
        1.0,
    )
    agent = next(r for r in rows if r["mode"] == "normal_reuse")
    assert agent["effort_saving"] == 200.0
    assert agent["quality_loss"] is False


def test_quality_loss_rate_is_not_mean_quality():
    rows = attach_savings(
        [
            {"seed": 1, "task_id": "a", "mode": "primitive", "Q": 80, "A": 1000},
            {"seed": 1, "task_id": "a", "mode": "normal_reuse", "Q": 80, "A": 1100},
            {"seed": 1, "task_id": "b", "mode": "primitive", "Q": 80, "A": 1000},
            {"seed": 1, "task_id": "b", "mode": "normal_reuse", "Q": 70, "A": 900},
        ],
        1.0,
    )
    reuse = [r for r in rows if r["mode"] == "normal_reuse"]
    assert sum(1 for r in reuse if r["quality_loss"]) == 1
    mean_q = sum(r["Q"] for r in reuse) / 2
    assert mean_q == 75.0


def test_catalogue_and_dev_disjoint():
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"
    train_all = load_split("train")
    development = load_split("development")
    train, val = reserve_train_val(train_all, 4)
    assert_dev_disjoint(train, development, val)


def test_env_clone_preserves_remaining_inventory():
    env = PackingEnv(budget=20, inventory=Inventory({"M": 2}))
    env.step(Action.place("M", 0, 0, 0))
    other = env.clone()
    assert other.inventory.counts["M"] == 1
    env.step(Action.place("M", 0, 1, 0))  # x=1, y=0: adjacent column, no overlap
    assert other.occupied == 4
    assert env.occupied == 8
    assert other.inventory.counts["M"] == 1
    assert env.inventory.counts["M"] == 0


def test_primitive_modes_match_without_library():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=800)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    a = solve_diagnostic(config, task, 11, "d", 0, None, "primitive")
    b = solve_diagnostic(config, task, 11, "d", 0, None, "retrieve_check_then_primitive")
    assert a["Q"] == b["Q"]
    assert a["A"] == b["A"]


def test_retrieve_check_adds_evaluations_without_changing_primitive_choice():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=800, retrieval_pool=4, top_k=2, anchors=4)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    feats = list(state_features(env))
    steps, geo = canonical_form(
        steps_from_absolute(
            [
                {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
                {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
            ]
        )
    )
    memory = make_memory(config, hierarchical=True, selective_retire=False)
    op = LearnedOperation("M0001", 1, [], steps, 12, geo, feats, 0, 0, status="active")
    memory.operations.append(op)
    prim = solve_diagnostic(config, task, 11, "d", 0, None, "primitive")
    check = solve_diagnostic(config, task, 11, "d", 0, memory, "retrieve_check_then_primitive")
    assert check["Q"] == prim["Q"]
    assert check["A"] > prim["A"]
    assert check["added_option_only"] is True


def test_source_has_no_shape_labels():
    for path in ROOT.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
