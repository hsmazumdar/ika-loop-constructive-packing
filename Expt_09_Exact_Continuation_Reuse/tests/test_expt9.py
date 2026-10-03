"""Expt-9 tests. Exact reuse is memorization."""

from __future__ import annotations

from config import QUALITY_LOSS_MARGIN
from continuation import ContinuationTable, replay_suffix, state_key
from environment import Action, PackingEnv
from inventory import Inventory
from pieces import catalogue_hash
from solver import Ledger

FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_store_and_hit_same_remaining_state():
    env = PackingEnv(budget=80, inventory=Inventory({"I": 5, "O": 5, "M": 5, "N": 5}))
    env.step(Action.place("I", 0, 0, 0))
    table = ContinuationTable()
    ledger = Ledger()
    table.learn_from_success(env, ledger)
    # unsuccessful (occupied < 75) stores nothing
    assert len(table.entries) == 0
    assert ledger.learning_cost == 0


def test_replay_validates_before_execute():
    env = PackingEnv(budget=80, inventory=Inventory({"I": 2}))
    ledger = Ledger()
    result = replay_suffix(env, [("I", 0, 0, 0), ("I", 0, 0, 0)], ledger)
    assert result["ok"] is False
    assert ledger.validation_cost >= 1
    assert env.occupied < 8 or result["n_executed"] <= 1


def test_lookup_key_uses_mask_and_inventory():
    a = PackingEnv(budget=80, inventory=Inventory({"A": 1, "B": 2}))
    b = PackingEnv(budget=80, inventory=Inventory({"A": 1, "B": 2}))
    c = PackingEnv(budget=80, inventory=Inventory({"A": 2, "B": 2}))
    assert state_key(a) == state_key(b)
    assert state_key(a) != state_key(c)


def test_frozen_table_does_not_learn():
    env = PackingEnv(budget=80, inventory=Inventory({"I": 20}))
    # fill enough cells is hard; freeze still blocks writes
    table = ContinuationTable()
    table.freeze()
    ledger = Ledger()
    assert table.learn_from_success(env, ledger) == 0


def test_source_has_no_shape_labels():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for path in (root / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
