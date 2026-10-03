"""Expt-4C tests. Quality-loss margin is fixed in config before runs."""

from __future__ import annotations

from pathlib import Path

from analysis import classify
from config import QUALITY_LOSS_MARGIN, Config
from experiment import assert_splits, load_split, reserve_train_val
from memory import Episode, LearnedOperation, clone_library_only, make_memory
from miner import AbstractionMiner, canonical_form, steps_from_absolute
from pieces import catalogue_hash, placed_cells
from solver import solve_box

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_margin_declared_before_runs():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert Config().quality_loss_margin == 1.0


def test_catalogue_hash():
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_splits_disjoint():
    train_all = load_split("train")
    development = load_split("development")
    train, val = reserve_train_val(train_all, 4)
    test = [{"task_id": "held_unique", "inventory": {"M": 1}}]
    assert_splits(train, development, test, val)


def test_flat_memory_max_depth_is_one():
    memory = make_memory(Config(), hierarchical=False)
    assert memory.hierarchical is False
    assert memory.max_depth == 1


def test_transfer_drops_episodes_keeps_applicability():
    config = Config()
    memory = make_memory(config, hierarchical=True)
    steps, _geo = canonical_form(
        steps_from_absolute(
            [
                {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
                {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
            ]
        )
    )
    op = LearnedOperation("M0001", 1, ["a", "b"], steps, 12, "c", [0.1] * 8, 0, 0, status="active")
    rule = op.ensure_rule(8, 0.05)
    rule.observe([0.2] * 8, True)
    memory.operations.append(op)
    memory.remember_episode(Episode(1, "e", {"M": 2}, [], 8, 10, True))
    transferred = clone_library_only(memory)
    assert transferred.episodes == []
    assert len(transferred.active()) == 1
    assert transferred.active()[0].applicability is not None
    assert transferred.active()[0].applicability.success_n == 1


def test_lesion_matches_primitive():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=800)
    task = {"task_id": "match", "inventory": {"M": 3, "O": 2}}
    left = solve_box(config, task, 11, "test", 0, None, learn=False, abstention=False)
    right = solve_box(config, task, 11, "test", 0, None, learn=False, abstention=True)
    assert left["Q"] == right["Q"]
    assert left["A"] == right["A"]


def test_classify_win_requires_margin_and_lower_A():
    prim = {"Q": 80, "A": 1000}
    assert classify({"Q": 80, "A": 900}, prim, 1.0) == "win"
    assert classify({"Q": 79, "A": 900}, prim, 1.0) == "win"
    assert classify({"Q": 78, "A": 900}, prim, 1.0) == "quality_loss"
    assert classify({"Q": 80, "A": 1000}, prim, 1.0) == "tie"
    assert classify({"Q": 80, "A": 1100}, prim, 1.0) == "effort_loss"


def test_source_has_no_shape_labels():
    for path in ROOT.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
