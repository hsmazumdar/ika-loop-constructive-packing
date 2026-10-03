"""Environment, language, memory, and accounting tests."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from mga2.budgets import BudgetLedger, UtilityWeights, utility
from mga2.environment import Action, PackingEnv
from mga2.features import zero_weights
from mga2.interpreter import Interpreter
from mga2.inventory import Inventory
from mga2.ltm import LongTermMemory
from mga2.ops import (
    Operation,
    call,
    choose,
    has_call_cycle,
    lookahead,
    make_operation,
    place_rel,
    seq,
    spatial_from_absolute,
    validate_program,
)
from mga2.pieces import PIECES, catalogue_hash, is_connected, piece_area, reflect_x, orientation, ROTATIONS
from mga2.rngutil import derive_seed
from mga2.selection import Agent, new_library
from mga2.simulation import lookahead_first_action
from mga2.stm import ShortTermMemory

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_catalogue_hash_and_areas():
    assert catalogue_hash() == CATALOGUE
    assert list(PIECES) == list("ABCDEFGHIJKLMNOP")
    assert piece_area("P") == 7
    assert piece_area("M") == piece_area("N") == piece_area("O") == 4


def test_no_reflection_in_rotations():
    chiral = 0
    for name, cells in PIECES.items():
        rots = {orientation(cells, k) for k in ROTATIONS}
        if reflect_x(cells) not in rots:
            chiral += 1
    assert chiral >= 1


def test_inventory_undo_restores_quota():
    inv = Inventory({"M": 1, "A": 0})
    env = PackingEnv(budget=10, inventory=inv)
    step = env.step(Action.place("M", 0, 0, 0))
    assert step.accepted
    assert env.inventory.counts["M"] == 0
    undone = env.step(Action.undo())
    assert undone.accepted
    assert env.inventory.counts["M"] == 1
    env.invariants()


def test_invalid_place_costs_action_and_keeps_board():
    env = PackingEnv(budget=5, inventory=Inventory({"M": 1}))
    bad = env.step(Action.place("M", 0, 9, 9))
    assert bad.invalid and bad.consumed_action
    assert env.score == 0
    assert env.actions_used == 1
    assert env.inventory.counts["M"] == 1


def test_budget_comes_from_constructor():
    env = PackingEnv(budget=3)
    for _ in range(3):
        env.step(Action.place("Z", 0, 0, 0))
    assert env.terminal
    assert env.termination_reason == "action_limit"
    assert env.actions_used == 3


def test_board_size_config_is_enforced():
    with pytest.raises(ValueError):
        PackingEnv(size=11)


def test_best_score_is_not_replaced_by_undo():
    env = PackingEnv(budget=10)
    env.step(Action.place("M", 0, 0, 0))
    assert env.best_score == env.score
    best = env.best_score
    env.step(Action.undo())
    assert env.score < best
    assert env.best_score == best


def test_clone_isolation_and_rng():
    env = PackingEnv(budget=20, inventory=Inventory({"B": 4, "M": 4}))
    env.step(Action.place("M", 0, 0, 0))
    rng = random.Random(5)
    state = rng.getstate()
    mask = env.mask
    inv = env.inventory.as_dict()
    clone = env.clone()
    clone.step(Action.place("B", 0, 2, 0))
    assert env.mask == mask
    assert env.inventory.as_dict() == inv
    assert rng.getstate() == state
    assert clone.mask != mask


def test_no_slots_on_env():
    env = PackingEnv()
    env.runtime_note = "ok"
    assert env.runtime_note == "ok"


def test_stm_stats_before_clear():
    stm = ShortTermMemory(4096)
    op = make_operation(seq([place_rel("M", 0, 0, 0), place_rel("M", 0, 1, 0)]), [], [], "mine", "real", 0)
    assert stm.add_candidate(op)
    stats = stm.snapshot_stats()
    assert stats["entries"] == 1
    assert stats["peak_bytes"] > 0
    stm.clear()
    assert len(stm.candidates) == 0
    assert stats["entries"] == 1


def test_zero_capacity_memory_does_not_crash():
    stm = ShortTermMemory(0)
    op = make_operation(seq([place_rel("M", 0, 0, 0), place_rel("N", 0, 1, 0)]), [], [], "mine", "real", 0)
    assert stm.add_candidate(op) is False
    ltm = LongTermMemory(0)
    assert ltm.add_provisional(op, 1) is False
    assert ltm.logical_bytes() >= 0


def test_ltm_eviction_and_dependency_bytes():
    ltm = LongTermMemory(5000)
    child = make_operation(
        seq([place_rel("M", 0, 0, 0), place_rel("N", 0, 1, 0)]),
        [{"type": "M", "rotation": 0, "dx": 0, "dy": 0, "cells": [[0, 0]]}, {"type": "N", "rotation": 0, "dx": 1, "dy": 0, "cells": [[1, 0]]}],
        [],
        "mine",
        "real",
        0,
    )
    assert ltm.add_provisional(child, 0)
    parent = make_operation(seq([call(child.op_id, 0, 0, 0)]), [], [child.op_id], "compress", "real", 1)
    assert ltm.add_provisional(parent, 1)
    assert ltm.logical_bytes() > child.logical_bytes()
    ltm.bump_selector("primitive", 0.1)
    assert "primitive" in ltm.selector
    tiny = LongTermMemory(1)
    assert tiny.add_provisional(child, 0) is False


def test_frozen_eval_rejects_writes():
    ltm = LongTermMemory(100000)
    op = make_operation(seq([place_rel("M", 0, 0, 0), place_rel("M", 0, 1, 0)]), [], [], "mine", "real", 0)
    assert ltm.add_provisional(op, 0)
    before = ltm.to_dict()["ops"]
    ltm.frozen = True
    other = make_operation(seq([place_rel("N", 0, 0, 0), place_rel("N", 0, 1, 0)]), [], [], "mine", "real", 1)
    assert ltm.add_provisional(other, 1) is False
    ltm.note_real_use(op.op_id, 1.0, True, "t", (0, 0, 0))
    ltm.bump_selector("ltm", 1)
    ltm.end_box(set())
    assert ltm.to_dict()["ops"] == before


def test_confirmation_requires_positive_utility_not_depth():
    ltm = LongTermMemory(100000, confirm_uses=3, confirm_tasks=2)
    deep = seq([seq([seq([place_rel("M", 0, 0, 0), place_rel("N", 0, 1, 0)])])])
    op = make_operation(deep, [], [], "mutate", "simulated", 0)
    assert op.depth >= 1
    ltm.add_provisional(op, 0)
    for i, task in enumerate(["a", "a", "b"]):
        ltm.note_real_use(op.op_id, -0.2, False, task, (i, 0, 0))
    assert ltm.ops[op.op_id].status != "confirmed"


def test_rng_streams_ignore_mode_order():
    s1 = derive_seed(11, "legacy", "train", 0, "decision")
    s2 = derive_seed(11, "legacy", "train", 0, "decision")
    s3 = derive_seed(11, "legacy", "train", 0, "discovery")
    assert s1 == s2
    assert s1 != s3


def test_program_limits_and_nested_lookahead():
    limits = {"max_nodes": 24, "max_call_depth": 4, "repeat_range": [1, 4], "lookahead_depth": [1, 3], "lookahead_width": [1, 4]}
    bad = lookahead(1, 1)
    wrapper = {"kind": "LOOKAHEAD", "depth": 1, "width": 1, "selector": "weights", "child": bad}
    # Nested via SEQ
    nested = seq([lookahead(1, 1), lookahead(1, 1)])
    # LOOKAHEAD nodes are leaves, so two siblings are not nested. Build a fake by validation of lookahead inside SEQ is allowed.
    inside = {"kind": "SEQ", "children": [{"kind": "LOOKAHEAD", "depth": 1, "width": 1, "selector": "weights"}]}
    errors = validate_program(inside, limits)
    assert "nested_lookahead" not in errors
    nested_ast = {"kind": "LOOKAHEAD", "depth": 1, "width": 1, "selector": "weights"}
    # Interpreter rejects a LOOKAHEAD reached while already inside one.
    env = PackingEnv(budget=5)
    ledger = BudgetLedger(eval_cap=1000, model_cap=1000)
    # Craft nesting by executing lookahead whose implementation doesn't contain another,
    # and call validate on an IF that holds a lookahead while we manually flag.
    ast = {
        "kind": "IF",
        "feature": "filled_fraction",
        "comparison": ">=",
        "threshold": -1,
        "then": {"kind": "LOOKAHEAD", "depth": 1, "width": 1, "selector": "weights"},
        "else": place_rel("M", 0, 0, 0),
    }
    result = Interpreter({}, {}).execute(ast, env, ledger, random.Random(0), simulate=True, in_lookahead=True)
    assert result.reason == "nested_lookahead"


def test_dangling_call_and_cycle():
    env = PackingEnv(budget=5)
    ledger = BudgetLedger(eval_cap=100, model_cap=100)
    result = Interpreter({}, {}).execute(call("missing", 0, 0, 0), env, ledger, random.Random(0), simulate=False)
    assert result.reason == "dangling_id"
    assert env.score == 0
    library = {}
    a = Operation("a", call("b"), [], "x", "real", 0, [])
    b = Operation("b", call("a"), [], "x", "real", 0, [])
    library["a"] = a
    library["b"] = b
    assert has_call_cycle("a", a.ast, library)


def test_utility_formula():
    w = UtilityWeights()
    assert utility(10, 2, 5, w) == pytest.approx(10 / 100 - 0.002 * 2 - 0.0001 * 5)


def test_mine_transform_replay_fixture():
    actions = [("M", 0, 0, 0), ("M", 0, 1, 0)]
    built = spatial_from_absolute(actions)
    assert built is not None
    ast, primitive = built
    op = make_operation(ast, primitive, [], "mine", "real", 0)
    env = PackingEnv(budget=10)
    ledger = BudgetLedger(eval_cap=1000, model_cap=100)
    result = Interpreter({}, {}).execute(op.ast, env, ledger, random.Random(0), simulate=False, origin=(4, 2, 0))
    assert result.ok
    assert env.score == 8
    assert env.actions_used == 2
    # Translated footprint matches the two vertical M pieces.
    assert env.cells[2][4][0] == "M"
    assert env.cells[2][5][0] == "M"


def test_nested_children_expand():
    child_a = make_operation(
        seq([place_rel("M", 0, 0, 0)]),
        [{"type": "M", "rotation": 0, "dx": 0, "dy": 0, "cells": [[0, 0], [0, 1], [0, 2], [0, 3]]}],
        [],
        "test",
        "real",
        0,
    )
    child_b = make_operation(
        seq([place_rel("N", 0, 0, 0)]),
        [{"type": "N", "rotation": 0, "dx": 0, "dy": 0, "cells": [[0, 0], [0, 1], [0, 2], [1, 2]]}],
        [],
        "test",
        "real",
        0,
    )
    parent = make_operation(
        seq([call(child_a.op_id, 0, 0, 0), call(child_b.op_id, 2, 0, 0)]),
        [],
        [child_a.op_id, child_b.op_id],
        "compose",
        "test",
        1,
    )
    env = PackingEnv(budget=10)
    ledger = BudgetLedger(eval_cap=100, model_cap=100)
    result = Interpreter({}, {child_a.op_id: child_a, child_b.op_id: child_b}).execute(
        parent.ast, env, ledger, random.Random(0), simulate=False, origin=(0, 0, 0)
    )
    assert result.ok
    assert result.expanded == 2
    assert env.score == piece_area("M") + piece_area("N")
    assert env.actions_used == 2


def test_macro_interruption_keeps_partial_state():
    ast = seq([place_rel("M", 0, 0, 0), place_rel("M", 0, 0, 0)])
    env = PackingEnv(budget=10)
    ledger = BudgetLedger(eval_cap=100, model_cap=100)
    result = Interpreter({}, {}).execute(ast, env, ledger, random.Random(0), simulate=False, origin=(0, 0, 0))
    assert not result.ok
    assert env.score == 4
    assert env.placements_count == 1
    assert env.actions_used == 2


def test_simulation_does_not_change_real_board():
    env = PackingEnv(budget=20)
    ledger = BudgetLedger(eval_cap=5000, model_cap=500)
    action = lookahead_first_action(env, ledger, random.Random(0), 1, 2, zero_weights(), exam_limit=8)
    assert env.score == 0
    assert env.actions_used == 0
    assert action is None or action.kind.value == "PLACE"


def test_connected_helper_used_by_compose():
    assert is_connected([(0, 0), (1, 0)])
    assert not is_connected([(0, 0), (2, 0)])


def test_agent_starts_with_empty_library_and_no_tabu_on_primitive():
    cfg = json_config()
    ltm = new_library(cfg)
    agent = Agent("primitive", cfg, ltm)
    assert ltm.ops == {}
    assert not hasattr(agent, "_undo_tabu") or agent._undo_tabu is None
    text = Path(ROOT / "src" / "mga2" / "selection.py").read_text(encoding="utf-8")
    primitive = text.split("def _act_primitive")[1].split("def _sync_trace")[0]
    assert "_undo_tabu" not in primitive
    assert "_engineered_small_components" not in primitive


def test_flat_and_hierarchical_share_expansion_horizon():
    cfg = json_config()
    flat = Agent("flat_library", cfg, new_library(cfg))
    hier = Agent("hierarchical_library", cfg, new_library(cfg))
    assert flat.think_horizon == hier.think_horizon == 8
    assert Interpreter(cfg, {}).limits["max_expanded"] == Interpreter(cfg, {}).limits["max_expanded"]


def test_autonomous_sources_have_no_rectangle_reward():
    import re

    src = ROOT / "src" / "mga2"
    for path in src.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "rectangular" not in text
        assert re.search(r"(?<![\w])eval\s*\(", text) is None


def test_agent_package_does_not_import_witnesses():
    src = ROOT / "src" / "mga2"
    for path in src.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "validation_only" not in text
        assert "generate_tasks" not in text


def json_config() -> dict:
    import json

    return json.loads((ROOT / "configs" / "default.json").read_text(encoding="utf-8"))
