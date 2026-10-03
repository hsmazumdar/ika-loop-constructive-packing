"""Expt-7 tests: index, budget, ranking abstention, hashes."""

from __future__ import annotations

from pathlib import Path

from config import QUALITY_LOSS_MARGIN, Config
from diagnostic import solve_gated
from environment import PackingEnv
from experiment import choose_k, shortlist_recall_from_oracle_rows
from index import LibraryIndex
from inventory import Inventory
from library_io import library_hash, memory_from_json, memory_to_json
from memory import LearnedOperation, make_memory
from miner import canonical_form, steps_from_absolute
from pieces import catalogue_hash, placed_cells
from policy import solve_indexed
from ranker import LinearRegressor, QualityModel, RANK_NAMES, rank_vector
from reconstruct import EXPT5_DIR

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN", "reject M0003")


def test_catalogue_and_margin():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_no_shape_labels():
    for path in (ROOT / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name


def _dummy_memory(config):
    steps, geo = canonical_form(steps_from_absolute([
        {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
        {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
    ]))
    memory = make_memory(config, hierarchical=True, selective_retire=False)
    memory.operations.append(LearnedOperation("M0001", 1, [], steps, 12, geo, [0.0] * 8, 0, 0, status="active"))
    return memory


def test_index_filters_missing_pieces_and_is_billed():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400)
    memory = _dummy_memory(config)
    index = LibraryIndex(memory)
    posted, probes, checks = index.query({"O": 4}, 0)
    assert posted == []
    assert probes == 1
    assert checks >= 0
    posted2, _p, _c = index.query({"M": 4}, 0)
    assert len(posted2) == 1
    env = PackingEnv(budget=20, inventory=Inventory({"M": 4}))
    before = env.mask
    index.query(env.inventory.as_dict(), env.occupied)
    assert env.mask == before


def test_index_does_not_encode_occupancy_bands():
    text = (ROOT / "src" / "index.py").read_text(encoding="utf-8")
    assert "occupancy_schedule" not in text
    assert "GOOD_CORNER" not in text


def test_consult_budget_stops_library_access():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400, consult_budget=0, k_shortlist=2)
    memory = _dummy_memory(config)
    index = LibraryIndex(memory)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    prim = solve_gated(config, task, 11, "t", 0, None, "primitive")
    indexed = solve_indexed(config, task, 11, "t", 0, memory, index, ranked=False, k=2, consult_budget=0)
    assert indexed["primitive_evals"] == prim["primitive_evals"]
    assert indexed["Q"] == prim["Q"]
    assert indexed["index_cost"] == 0
    assert indexed["A"] == indexed["primitive_evals"] + indexed["index_cost"] + indexed["ranking_cost"] + indexed["learned_evals"] + indexed["applicability_cost"] + indexed["retrieval_cost"] + indexed["gate_cost"]
    assert indexed["A_identity_ok"] is True


def test_shortlist_recall_counts_states_not_placements():
    rows = [
        {"seed": "1", "task_id": "a", "state_index": "0", "op_id": "M0001", "definition_hash": "aa", "beneficial_free": "True"},
        {"seed": "1", "task_id": "a", "state_index": "0", "op_id": "M0001", "definition_hash": "aa", "beneficial_free": "True"},
        {"seed": "1", "task_id": "a", "state_index": "1", "op_id": "M0002", "definition_hash": "bb", "beneficial_free": "True"},
        {"seed": "1", "task_id": "a", "state_index": "1", "op_id": "M0001", "definition_hash": "aa", "beneficial_free": "False"},
    ]
    rec1 = shortlist_recall_from_oracle_rows(rows, 1)
    rec2 = shortlist_recall_from_oracle_rows(rows, 2)
    assert rec1["n_states_with_oracle_useful"] == 2
    assert rec2["n_states_with_oracle_useful"] == 2
    assert choose_k([rec1, rec2]) in (1, 2)


def test_rank_vector_has_no_op_name_features():
    vec = rank_vector(0, {"M": 2}, 0, 0, 2, 1, 0.1, False, 8)
    assert "M0003" not in str(vec)
    assert len(vec) == len(RANK_NAMES)


def test_quality_model_roundtrip():
    model = QualityModel(RANK_NAMES, [0.0] * len(RANK_NAMES), -1.0, {"M0001": -0.5}, 0.6, True)
    again = QualityModel.from_dict(model.to_dict())
    assert again.to_dict() == model.to_dict()
    reg = LinearRegressor(RANK_NAMES, [0.0] * len(RANK_NAMES), 1.0, True)
    assert LinearRegressor.from_dict(reg.to_dict()).predict([0.0] * len(RANK_NAMES)) == 1.0


def test_frozen_gates_files_exist():
    assert (EXPT5_DIR / "gates_seed11.json").exists()
    snap = ROOT / "snapshots" / "library_seed11.json"
    assert snap.exists()
    payload = __import__("json").loads(snap.read_text(encoding="utf-8"))
    memory = memory_from_json(payload, Config())
    assert library_hash(memory) == payload["library_hash"]
    assert memory_to_json(memory)["library_hash"] == payload["library_hash"]
