"""Expt-10 tests. Exact subproblem reuse is memorization."""

from __future__ import annotations

from collections import Counter

from config import QUALITY_LOSS_MARGIN
from construct import find_alternative_cover, replay_placements
from continuation import ContinuationTable, replay_suffix, state_key
from environment import Action, PackingEnv
from inventory import Inventory
from pieces import PIECE_TYPES, catalogue_hash, cells_mask, placed_cells
from solver import Ledger

FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_unsuccessful_store_writes_nothing():
    env = PackingEnv(budget=80, inventory=Inventory({"I": 5, "O": 5, "M": 5, "N": 5}))
    env.step(Action.place("I", 0, 0, 0))
    table = ContinuationTable()
    ledger = Ledger()
    table.learn_from_success(env, ledger)
    assert len(table.entries) == 0
    assert ledger.learning_cost == 0


def test_first_write_wins():
    inv = {t: 8 for t in PIECE_TYPES}
    env_a = PackingEnv(budget=80, inventory=Inventory(inv))
    env_a.step(Action.place("A", 0, 0, 0))
    env_a.step(Action.place("A", 0, 2, 0))
    env_a.mask |= (1 << 75) - 1
    env_b = PackingEnv(budget=80, inventory=Inventory(inv))
    env_b.step(Action.place("A", 0, 0, 0))
    env_b.step(Action.place("M", 0, 5, 0))
    env_b.mask |= (1 << 75) - 1
    table = ContinuationTable()
    ledger = Ledger()
    table.learn_from_success(env_a, ledger)
    first = table.lookup(PackingEnv(budget=80, inventory=Inventory(inv)))
    table.learn_from_success(env_b, ledger)
    second = table.lookup(PackingEnv(budget=80, inventory=Inventory(inv)))
    assert first is not None
    assert first == second
    assert table.n_overwrites >= 1


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
    table = ContinuationTable()
    table.freeze()
    ledger = Ledger()
    assert table.learn_from_success(env, ledger) == 0


def test_alternative_cover_differs_from_original_prefix():
    prefix = [("A", 0, 0, 0), ("A", 0, 2, 0)]
    cells = []
    for piece, rotation, x, y in prefix:
        cells.extend(placed_cells(piece, rotation, x, y))
    mask = cells_mask(cells)
    original = tuple(Counter(p[0] for p in prefix).get(t, 0) for t in PIECE_TYPES)
    alt = find_alternative_cover(mask, original, max_pieces=4)
    assert alt is not None
    alt_types = tuple(Counter(p[0] for p in alt).get(t, 0) for t in PIECE_TYPES)
    assert alt_types != original
    env = replay_placements({t: 4 for t in PIECE_TYPES}, alt)
    assert int(env.mask) == mask


def test_source_has_no_shape_labels():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for path in (root / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
