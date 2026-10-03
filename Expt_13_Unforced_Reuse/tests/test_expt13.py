"""Expt-13 tests. Frozen memory; no constructed prefixes on evaluation; family generator is table-blind."""

from __future__ import annotations

import inspect
import random
from pathlib import Path

from config import QUALITY_LOSS_MARGIN, diagnostic_config, smoke_config
from continuation import ContinuationTable
from pieces import catalogue_hash
from transforms import CANDIDATES, TransformSelector, inverse, transform_mask

FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_config_declares_unforced_frozen():
    for cfg in (smoke_config(), diagnostic_config()):
        data = cfg.to_dict()
        assert data["constructed_prefix_on_eval"] is False
        assert data["scheduled_matches"] is False
        assert data["online_memory_growth"] is False
        assert data["category_hidden"] is True


def test_selector_rule_unchanged():
    sel = TransformSelector()
    sel.note_attempt("rot90")
    sel.note_attempt("rot270")
    sel.observe("rot90", transformed_ok=True, validation_ok=True, acceptable=True)
    assert sel.freeze() == ("rot90",)
    assert sel.as_dict()["coverage"]["rot270"]["insufficient_coverage"] is True
    sel.observe("rot270", transformed_ok=True, validation_ok=True, acceptable=True)
    assert sel.chosen == ("rot90",)


def test_frozen_table_does_not_learn():
    table = ContinuationTable()
    table.freeze()

    class _Env:
        occupied = 100

    assert table.learn_from_success(_Env(), None) == 0


def test_d4_inverse_roundtrip():
    mask = (1 << 3) | (1 << 14) | (1 << 27)
    for name in CANDIDATES:
        assert transform_mask(inverse(name), transform_mask(name, mask)) == mask


def test_family_generator_is_table_blind():
    import family_gen

    source = inspect.getsource(family_gen)
    for token in ("ContinuationTable", "lookup", "remaining_table_match", "continuation"):
        assert token not in source.replace("consults_memory_table", "").replace("is not consulted", ""), token


def test_declare_families_deterministic():
    from family_gen import declare_families

    a = declare_families(3, random.Random(5))
    b = declare_families(3, random.Random(5))
    assert a == b
    assert all(spec["consults_memory_table"] is False for spec in a)
    assert len({tuple(s["type_set"]) for s in a}) == 3


def test_run_triple_rejects_constructed_prefix():
    from experiment import _run_triple

    task = {"task_id": "x", "inventory": {"M": 1}, "constructed_prefix": [("M", 0, 0, 0)]}
    try:
        _run_triple(diagnostic_config(), task, 11, 0, "s", "p", ContinuationTable(), (), [], 0, "w")
    except RuntimeError as exc:
        assert "constructed prefix" in str(exc)
    else:
        raise AssertionError("constructed prefix accepted on evaluation")


def test_source_has_no_shape_labels():
    root = Path(__file__).resolve().parents[1]
    for path in (root / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
