"""Expt-6 tests: snapshots, enumeration, oracle selection, accounting."""

from __future__ import annotations

from pathlib import Path

from config import QUALITY_LOSS_MARGIN, Config
from diagnostic import solve_gated, solve_retrieve_check
from enumerate_ops import enumerate_legal
from environment import PackingEnv
from experiment import provenance_audit
from gates import LinearGate, commit_vector, consult_vector
from inventory import Inventory
from library_io import definition_hash, library_hash, memory_from_json, memory_to_json
from memory import LearnedOperation, make_memory
from miner import canonical_form, steps_from_absolute
from oracle import diagnose_pair, select_free_oracle
from pieces import catalogue_hash, placed_cells
from snapshot import remaining_cap, restore_rng, run_primitive_snapshots, state_fingerprint
from solver import make_rng

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN", "reject M0003")


def test_catalogue_and_margin():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_source_has_no_shape_labels():
    for path in (ROOT / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name


def _dummy_op(status="active", extra_steps=None):
    placements = [
        {"type": "M", "cells": placed_cells("M", 0, 0, 0)},
        {"type": "M", "cells": placed_cells("M", 0, 1, 0)},
    ]
    if extra_steps:
        placements.extend(extra_steps)
    steps, geo = canonical_form(steps_from_absolute(placements))
    return LearnedOperation("M0001", 1, [], steps, 12, geo, [0.0] * 8, 0, 0, status=status)


def _dummy_memory(config, overlapping=False):
    memory = make_memory(config, hierarchical=True, selective_retire=False)
    extra = None
    if overlapping:
        extra = [{"type": "M", "cells": placed_cells("M", 0, 0, 0)}]
    op = _dummy_op(extra_steps=extra)
    memory.operations.append(op)
    return memory, op


def _open_gate():
    names = ("occupancy",)
    return LinearGate(names=names, weights=[0.0], bias=10.0, threshold=0.5, frozen=True)


def test_retrieve_check_preserves_primitive_trace_and_evals_including_cap():
    config = Config(q_min=75, scan=16, physical=20, eval_cap=8)
    task = {"task_id": "p", "inventory": {"M": 8, "O": 4}}
    memory, _op = _dummy_memory(config)
    prim = run_primitive_snapshots(config, task, 11, "d", 0)
    check = solve_retrieve_check(config, task, 11, "d", 0, memory)
    prim_gated = solve_gated(config, task, 11, "d", 0, None, "primitive")
    assert prim["trace"] == check["primitive_trace"]
    assert prim["primitive_evals"] == check["primitive_evals"]
    assert prim["Q"] == check["Q"] == prim_gated["Q"]
    assert check["A"] == check["primitive_evals"] + check["retrieval_cost"] + check["applicability_cost"] + check["learned_evals"] + check["gate_cost"]
    assert check["A"] > prim["A"]
    assert check["A_identity_ok"] is True
    assert prim["termination"] == "eval_cap"
    assert check["termination"] == "eval_cap"


def test_accounting_reconciles_on_gated_solve():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    prim = solve_gated(config, task, 11, "t", 0, None, "primitive")
    assert prim["A"] == prim["primitive_evals"] + prim["retrieval_cost"] + prim["applicability_cost"] + prim["learned_evals"] + prim["gate_cost"]
    assert prim["A_identity_ok"] is True


def test_snapshot_restore_matches_primitive_suffix():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    prim = run_primitive_snapshots(config, task, 11, "t", 0)
    assert prim["snapshots"]
    snap = prim["snapshots"][0]
    cap = remaining_cap(config.eval_cap, snap["prefix_A"])
    env = snap["env"].clone()
    rng = make_rng(0, "x", "y", 0, "select")
    restore_rng(rng, snap["rng_state"])
    from snapshot import primitive_remaining

    skip = primitive_remaining(config, env, rng, set(snap["tabu"]), cap, want_trace=True)
    assert skip["Q"] == prim["Q"]
    assert skip["A"] == prim["A"] - snap["prefix_A"]
    assert skip["trace"] == prim["trace"]


def test_enumeration_is_read_only():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    memory, op = _dummy_memory(config)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    rng = make_rng(11, "p", "e", 0, "select")
    before_state = rng.getstate()
    before_mask = env.mask
    before_counts = dict(env.inventory.counts)
    before_fp = state_fingerprint(env, 0, before_state)
    enum = enumerate_legal(op, env, 24)
    assert rng.getstate() == before_state
    assert env.mask == before_mask
    assert env.inventory.counts == before_counts
    assert state_fingerprint(env, 0, rng.getstate()) == before_fp
    assert enum["n_legal"] >= 1


def test_oracle_prefers_primitive_on_effort_tie_and_rejects_quality_loss():
    prim_a, prim_q, margin = 100.0, 80.0, 1.0
    quality_loss = {
        "quality_vs_primitive_box": False,
        "Q_commit": 70.0,
        "A_box_candidate": 10.0,
        "state_index": 0,
        "action_key": "a",
    }
    tie = {
        "quality_vs_primitive_box": True,
        "Q_commit": 80.0,
        "A_box_candidate": 100.0,
        "state_index": 0,
        "action_key": "b",
    }
    better = {
        "quality_vs_primitive_box": True,
        "Q_commit": 80.0,
        "A_box_candidate": 90.0,
        "state_index": 1,
        "action_key": "c",
    }
    assert select_free_oracle([quality_loss], prim_a, prim_q, margin) is None
    assert select_free_oracle([tie], prim_a, prim_q, margin) is None
    selected = select_free_oracle([quality_loss, tie, better], prim_a, prim_q, margin)
    assert selected["action_key"] == "c"
    assert selected["A_box_candidate"] < prim_a


def test_zero_legal_candidates_still_pay_scan_cost():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400, chooser_cost=1, occupancy_schedule=(0,), max_states_per_box=1)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    memory = make_memory(config, hierarchical=True, selective_retire=False)
    consult = _open_gate()
    commit = _open_gate()
    bundle = {"memory": memory, "consult_gate": consult, "commit_gate": commit, "library_hash": library_hash(memory)}
    ledger = {}
    result = diagnose_pair(config, task, 11, 0, bundle, ledger)
    assert result["box"]["n_candidates"] == 0
    assert result["box"]["A_oracle_free"] == result["box"]["A_primitive"]
    assert result["box"]["saving_oracle_free"] == 0
    assert result["box"]["C_box"] >= config.chooser_cost
    assert result["box"]["A_oracle_scan"] == result["box"]["A_oracle_free"] + result["box"]["C_box_charged"]
    assert result["box"]["A_oracle_scan"] > result["box"]["A_oracle_free"]


def test_incomplete_enumeration_is_marked():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    _memory, op = _dummy_memory(config)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    enum = enumerate_legal(op, env, 1)
    full = enumerate_legal(op, env, 10**6)
    if full["n_legal_uncapped"] > 1:
        assert enum["incomplete"] is True
        assert enum["n_legal"] == 1
    else:
        assert enum["incomplete"] is False


def test_duplicate_and_overlap_placements_rejected():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=400)
    env = PackingEnv(budget=20, inventory=Inventory({"M": 4}))
    memory, op = _dummy_memory(config)
    enum = enumerate_legal(op, env, 100)
    keys = [p["action_key"] for p in enum["placements"]]
    assert len(keys) == len(set(keys))
    overlap_mem, overlap_op = _dummy_memory(config, overlapping=True)
    overlap_enum = enumerate_legal(overlap_op, env, 100)
    assert overlap_enum["n_legal"] == 0 or all(
        len({tuple(c) for step in rec["site"] for c in step["cells"]}) == sum(len(step["cells"]) for step in rec["site"])
        for rec in overlap_enum["placements"]
    )


def test_library_and_gate_hashes_unchanged():
    config = Config()
    memory, op = _dummy_memory(config)
    payload = memory_to_json(memory)
    h1 = library_hash(memory)
    d1 = definition_hash(op)
    restored = memory_from_json(payload, config)
    assert library_hash(restored) == h1
    assert definition_hash(restored.operations[0]) == d1
    gate = LinearGate(names=("occupancy",), weights=[0.2], bias=-0.1, threshold=0.4, frozen=True, op_bias={"M0001": -0.5})
    again = LinearGate.from_dict(gate.to_dict())
    assert again.to_dict() == gate.to_dict()
    assert again.frozen is True


def test_audit_records_missing_expt5_libraries():
    audit = provenance_audit()
    assert audit["reconstruction_required"] is True
    assert audit["missing_library_files"]
    assert audit["catalogue_hash"] == catalogue_hash()


def test_consult_commit_vectors_have_no_op_name_features():
    vec = commit_vector(0, {"M": 2}, 0, 0, 2, 1, 0.1, False)
    assert "M0003" not in str(vec)
    assert consult_vector(0, {"M": 2}, 0, 0)[0] == 0.0
