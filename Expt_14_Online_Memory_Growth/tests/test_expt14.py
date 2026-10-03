"""Expt-14 tests. Solve-before-insert, billed insertion, first write, per-stream copies."""

from __future__ import annotations

import inspect
import random

from config import QUALITY_LOSS_MARGIN, diagnostic_config, smoke_config
from continuation import ContinuationTable, state_key
from environment import Action, PackingEnv
from inventory import Inventory
from pieces import catalogue_hash

FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def _full_env(stack, inventory):
    env = PackingEnv(budget=80, inventory=Inventory(dict(inventory)))
    for piece, rotation, x, y in stack:
        assert env.step(Action.place(piece, rotation, x, y)).accepted
    return env


def _m_column_stack():
    return [("M", 0, x, y) for x in range(10) for y in (0, 4)]


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_config_primary_conditions():
    for cfg in (smoke_config(), diagnostic_config()):
        data = cfg.to_dict()
        assert data["conditions"] == ["primitive", "frozen_exact", "growing_exact"]
        assert data["transformation_matching_in_primary"] is False
        assert data["first_write_wins"] is True
        assert data["future_tasks_chosen_by_memory"] is False


def test_grow_bills_probe_and_write_and_first_write_wins():
    stack = _m_column_stack()
    env = _full_env(stack, {"M": 20})
    assert env.occupied == 80
    table = ContinuationTable()
    first = table.grow_from_success(env, 75.0, source="s0:0")
    assert first["probed"] == len(stack)
    assert first["written"] == len(stack)
    assert first["cost"] == 2 * len(stack)
    again = table.grow_from_success(env, 75.0, source="s0:1")
    assert again["written"] == 0
    assert again["cost"] == len(stack)
    empty = PackingEnv(budget=80, inventory=Inventory({"M": 20}))
    assert table.source_of(state_key(empty)) == "s0:0"


def test_frozen_copy_does_not_grow_and_copies_are_independent():
    env = _full_env(_m_column_stack(), {"M": 20})
    base = ContinuationTable()
    base.freeze()
    frozen = base.copy(frozen=True)
    a = base.copy(frozen=False)
    b = base.copy(frozen=False)
    assert frozen.grow_from_success(env, 75.0, "x")["written"] == 0
    assert a.grow_from_success(env, 75.0, "a")["written"] > 0
    assert len(b.entries) == 0
    assert len(base.entries) == 0


def test_below_quality_not_inserted():
    env = _full_env(_m_column_stack()[:5], {"M": 20})
    table = ContinuationTable()
    assert table.grow_from_success(env, 75.0, "x")["written"] == 0


def test_stream_solves_before_insert():
    from experiment import run_stream

    source = inspect.getsource(run_stream)
    assert source.index("mode=\"exact\"") < source.index("grow_from_success")
    assert "mode=\"learned\"" not in source and "mode=\"supplied\"" not in source


def test_family_stream_is_table_blind():
    import family_gen

    source = inspect.getsource(family_gen.sample_family_stream)
    for token in ("ContinuationTable", "lookup", "entries"):
        assert token not in source


def test_declare_families_deterministic():
    from family_gen import declare_families

    assert declare_families(3, random.Random(5)) == declare_families(3, random.Random(5))


def test_source_has_no_shape_labels():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for path in (root / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
