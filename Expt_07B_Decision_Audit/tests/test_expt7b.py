"""Expt-7B tests."""

from __future__ import annotations

from pathlib import Path

from config import QUALITY_LOSS_MARGIN, Config
from diagnostic import a_components
from experiment import expt7_dir
from pieces import catalogue_hash
from solver import Ledger

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_consultation_includes_index_and_ranking():
    primitive = Ledger()
    consult = Ledger()
    consult.charge("index", 3)
    consult.charge("ranking", 2)
    consult.charge("applicability", 4)
    consult.charge("learned", 8)
    parts = a_components(primitive, consult)
    assert parts["consultation_cost"] == 17
    assert parts["index_cost"] == 3
    assert parts["ranking_cost"] == 2
    assert parts["A"] == 17
    assert parts["A_identity_ok"] is True


def test_budget_zero_skips_index():
    from audit import solve_ranked_audit, solve_primitive_traced
    from index import LibraryIndex
    from memory import LearnedOperation, make_memory
    from miner import canonical_form, steps_from_absolute
    from pieces import placed_cells
    from ranker import LinearRegressor, QualityModel, RANK_NAMES

    config = Config(q_min=12, scan=16, physical=20, eval_cap=400, k_shortlist=2, consult_budget=0)
    steps, geo = canonical_form(steps_from_absolute([
        {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
        {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
    ]))
    memory = make_memory(config, hierarchical=True, selective_retire=False)
    memory.operations.append(LearnedOperation("M0001", 1, [], steps, 12, geo, [0.0] * 8, 0, 0, status="active"))
    index = LibraryIndex(memory)
    z = [0.0] * len(RANK_NAMES)
    benefit = LinearRegressor(RANK_NAMES, z, 0.0, True)
    quality = QualityModel(RANK_NAMES, z, 0.0, {}, 1.0, True)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    prim = solve_primitive_traced(config, task, 11, "expt7", 0)
    ranked = solve_ranked_audit(config, task, 11, "expt7", 0, memory, index, benefit, quality, 2, 0, {}, {}, collect_counterfactuals=False)
    assert ranked["primitive_trace"] == prim["primitive_trace"]
    assert ranked["consult_attempts"] == 0
    assert ranked["n_commitments"] == 0
    assert ranked["A"] == prim["A"]
    assert ranked["index_cost"] == 0
    assert ranked["ranking_cost"] == 0


def test_op_recall_is_not_action_recall():
    from experiment import op_and_action_recall_from_rows

    op_states = [
        {"seed": "11", "task_id": "a", "state_index": "0", "shortlist_hit": "True"},
        {"seed": "11", "task_id": "a", "state_index": "1", "shortlist_hit": "True"},
    ]
    actions = [
        {"seed": "11", "task_id": "a", "state_index": "0", "placement_found": True, "beneficial_free": False},
        {"seed": "11", "task_id": "a", "state_index": "1", "placement_found": True, "beneficial_free": True},
    ]
    rec = op_and_action_recall_from_rows(op_states, actions)
    assert rec["n_oracle_useful_states"] == 2
    assert rec["op_recall_hits"] == 2
    assert rec["action_recall_hits"] == 1


def test_source_has_no_shape_labels():
    for path in (ROOT / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name


def test_expt7_artifacts_exist():
    src = expt7_dir()
    assert src.exists()
    assert (src / "ranker_seed11.json").exists()
    assert (src / "library_seed11.json").exists()
