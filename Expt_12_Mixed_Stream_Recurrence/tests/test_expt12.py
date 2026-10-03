"""Expt-12 tests. Frozen Expt-11 mechanism; mixed streams; coverage stats."""

from __future__ import annotations

import random

from config import QUALITY_LOSS_MARGIN
from continuation import ContinuationTable
from mix_stream import compose_stream, realized_rate
from pieces import catalogue_hash
from transforms import CANDIDATES, TransformSelector, inverse, remaining_table_match, transform_mask

FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_selector_coverage_and_rule():
    sel = TransformSelector()
    sel.note_attempt("rot90")
    sel.note_attempt("rot270")
    sel.observe("rot90", transformed_ok=True, validation_ok=True, acceptable=True)
    chosen = sel.freeze()
    assert "rot90" in chosen
    assert "rot270" not in chosen
    payload = sel.as_dict()
    assert payload["coverage"]["rot270"]["attempts"] == 1
    assert payload["coverage"]["rot270"]["compatible"] == 0
    assert payload["coverage"]["rot270"]["insufficient_coverage"] is True


def test_d4_inverse_roundtrip():
    mask = (1 << 3) | (1 << 14) | (1 << 27)
    for name in CANDIDATES:
        assert transform_mask(inverse(name), transform_mask(name, mask)) == mask


def test_compose_stream_zero_and_one():
    exact = [{"task_id": "e1", "kind": "exact_recurrence"}]
    xform = [{"task_id": "t1", "kind": "valid_transform", "constructed_prefix": [("M", 0, 0, 0)]}]
    nomatch = [{"task_id": "n1", "kind": "no_match", "constructed_prefix": [("M", 0, 0, 0)]}]
    fresh = [{"task_id": "f1", "kind": "fresh"}]
    pools = {
        "exact_recurrence": exact,
        "valid_transform": xform,
        "no_match": nomatch,
        "fresh": fresh,
    }
    zero = compose_stream(pools, 0.0, 8, random.Random(1))
    assert realized_rate(zero) == 0.0
    assert all(t["hidden_kind"] in ("no_match", "fresh") for t in zero)
    one = compose_stream(pools, 1.0, 8, random.Random(2))
    assert realized_rate(one) == 1.0
    assert all(t["hidden_kind"] in ("exact_recurrence", "valid_transform") for t in one)


def test_remaining_match_none_on_empty_table():
    table = ContinuationTable()
    assert remaining_table_match(0, (0,) * 16, table) is None


def test_source_has_no_shape_labels():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for path in (root / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
