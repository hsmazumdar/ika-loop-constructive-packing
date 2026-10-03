"""Expt-5 tests."""

from __future__ import annotations

from pathlib import Path

from config import EVAL_CONDITIONS, QUALITY_LOSS_MARGIN, Config
from diagnostic import solve_gated
from experiment import load_split, reserve_train_val
from gates import CONSULT_NAMES, LinearGate, commit_vector, consult_vector, fit_gate, sample_weight
from pieces import catalogue_hash

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN", "reject M0003")


def test_catalogue_and_conditions():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"
    assert EVAL_CONDITIONS[0] == "primitive"
    assert "both_gates" in EVAL_CONDITIONS


def test_no_hardcoded_m0003_rule():
    text = (ROOT / "gates.py").read_text(encoding="utf-8")
    assert "M0003" not in text
    for path in ROOT.glob("*.py"):
        body = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in body, path.name


def test_severe_loss_outweighs_modest_gain():
    modest = sample_weight(96.0, True, 400.0, 8.0)
    disaster = sample_weight(-6761.0, False, 400.0, 8.0)
    assert disaster > 10 * modest


def test_gate_learns_without_hand_rule():
    good = {
        "vector": consult_vector(0, {"M": 9, "B": 4}, 0, 0),
        "y": True,
        "remaining_saving": 96.0,
        "quality_ok": True,
        "op_id": None,
    }
    bad = {
        "vector": consult_vector(0, {"C": 8, "H": 4}, 0, 0),
        "y": False,
        "remaining_saving": -2000.0,
        "quality_ok": False,
        "op_id": None,
    }
    gate = fit_gate(CONSULT_NAMES, [good, bad] * 8, use_op_bias=False, steps=40, scale=400.0, quality_fail_weight=8.0)
    assert gate.admit(good["vector"]) != gate.admit(bad["vector"]) or gate.probability(good["vector"]) >= gate.probability(bad["vector"])


def test_gate_cost_is_billed():
    config = Config(q_min=12, scan=16, physical=20, eval_cap=800)
    task = {"task_id": "p", "inventory": {"M": 3, "O": 2}}
    dummy = LinearGate(names=("occupancy",), weights=[0.0], bias=-10.0, threshold=0.5, frozen=True)
    prim = solve_gated(config, task, 11, "t", 0, None, "primitive")
    gated = solve_gated(config, task, 11, "t", 0, None, "consult_gate_only", dummy, None)
    # no memory: consult gate is not asked (use_memory false). With memory=None both should match.
    assert prim["A"] == gated["A"]
    assert prim["Q"] == gated["Q"]
    assert prim["A"] == prim["primitive_evals"] + prim["gate_cost"] + prim["retrieval_cost"] + prim["applicability_cost"] + prim["learned_evals"]


def test_commit_vector_includes_op_stats_not_name():
    vec = commit_vector(0, {"M": 2}, 0, 0, 2, 1, 0.1, False)
    names_ok = "M0003" not in str(vec)
    assert names_ok
    assert vec[-4] == 2 / 5.0


def test_train_eval_are_disjoint_files():
    train, val = reserve_train_val(load_split("train"), 4)
    development = load_split("development")
    train_ids = {t["task_id"] for t in train} | {t["task_id"] for t in val}
    assert not (train_ids & {t["task_id"] for t in development})
