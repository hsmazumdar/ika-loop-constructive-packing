"""Expt-4D2 tests: accounting isolation and replay labels."""

from __future__ import annotations

from pathlib import Path

from audit import enrich_replays, run_existing_audit
from config import QUALITY_LOSS_MARGIN, Config
from diagnostic import propose_learned, solve_diagnostic
from environment import Action, PackingEnv
from experiment import assert_splits, load_split, reserve_train_val
from inventory import Inventory
from memory import LearnedOperation, make_memory
from miner import canonical_form, steps_from_absolute
from pieces import catalogue_hash, placed_cells
from retrieval import state_features
from solver import Ledger, make_rng

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue_and_margin():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_existing_audit_finds_cap_truncation():
    audit, table, summary = run_existing_audit(ROOT / "results")
    assert audit["n_pairs"] == 24
    assert audit["n_cap_truncated"] == 1
    assert audit["n_primitive_eval_match"] == 23
    assert abs(audit["mean_retrieval"] - 54.96) < 0.1
    assert summary["n"] == 15
    assert summary["n_effort_ok"] == 9
    assert summary["n_acceptable_success"] < summary["n_effort_ok"]
    assert summary["n_composed"] == 0
    assert table[0]["effort_saving_remaining"] <= table[-1]["effort_saving_remaining"]


def test_quality_gate_is_not_effort_alone():
    rows = enrich_replays(
        [
            {
                "seed": 1,
                "task_id": "t",
                "op_id": "M0001",
                "depth": 1,
                "composed": False,
                "check_cost": 9,
                "effort_saving_remaining": 96,
                "A_remaining_primitive": 800,
                "A_remaining_after_commit": 704,
                "Q_remaining_primitive": 78,
                "Q_remaining_after_commit": 70,
                "occupied_at_choice": 0,
                "internal_execution": 2,
                "features": json_empty_features(),
            }
        ]
    )
    assert rows[0]["effort_ok"] is True
    assert rows[0]["quality_ok"] is False
    assert rows[0]["acceptable_success"] is False


def json_empty_features() -> str:
    import json

    return json.dumps([0.0] * 40)


def _dummy_memory(config, task):
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
    return memory, op


def test_retrieval_does_not_consume_select_rng_or_mutate_env():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=800)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    memory, op = _dummy_memory(config, task)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    env.step(Action.place("M", 0, 0, 0))
    select_rng = make_rng(11, "p", "d", 0, "select")
    before_state = select_rng.getstate()
    before_mask = env.mask
    before_counts = dict(env.inventory.counts)
    before_rule = op.applicability
    consult = Ledger()
    propose_learned(config, env, memory, 11, "p", "d", 0, 0, consult)
    after = make_rng(11, "p", "d", 0, "select")
    assert after.getstate() == before_state
    assert env.mask == before_mask
    assert env.inventory.counts == before_counts
    assert op.applicability is before_rule
    assert consult.A > 0


def test_retrieve_check_matches_primitive_trace_and_evals():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    memory, _op = _dummy_memory(config, task)
    prim = solve_diagnostic(config, task, 11, "d", 0, None, "primitive")
    check = solve_diagnostic(config, task, 11, "d", 0, memory, "retrieve_check_then_primitive")
    assert prim["primitive_trace"] == check["primitive_trace"]
    assert prim["primitive_evals"] == check["primitive_evals"]
    assert prim["Q"] == check["Q"]
    assert check["A"] == check["primitive_evals"] + check["retrieval_cost"] + check["applicability_cost"] + check["learned_evals"]
    assert check["A"] > prim["A"]
    assert check["A_identity_ok"] is True


def test_splits_reject_overlap():
    train_all = load_split("train")
    development = load_split("development")
    train, val = reserve_train_val(train_all, 4)
    assert_splits(train, development, [{"task_id": "fresh_only", "inventory": {"M": 1}}], val)


def test_source_has_no_shape_labels():
    for path in ROOT.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
