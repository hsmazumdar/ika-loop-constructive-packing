"""Census invariants: translation, connectivity, one-box support, no placement."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from census import PatternTable, match_pattern, relative_pattern, scan_trajectory, stage_name
from config import diagnostic_config
from pieces import placed_cells

ROOT = Path(__file__).resolve().parents[1]


def _pair_at(origin_x: int, origin_y: int) -> list[tuple]:
    return [("M", 0, origin_x, origin_y), ("M", 0, origin_x, origin_y + 4)]


def test_translation_only_removes_absolute_position():
    a = relative_pattern(_pair_at(0, 0))
    b = relative_pattern(_pair_at(3, 2))
    assert a is not None and a == b
    anchors = a[0]
    assert min(x for _p, _r, x, _y in anchors) == 0
    assert min(y for _p, _r, _x, y in anchors) == 0


def test_disconnected_group_is_not_a_pattern():
    far = [("M", 0, 0, 0), ("M", 0, 6, 6)]
    cells_a = set(placed_cells("M", 0, 0, 0))
    cells_b = set(placed_cells("M", 0, 6, 6))
    assert cells_a.isdisjoint(cells_b)
    assert relative_pattern(far) is None


def test_adjacent_group_need_not_be_rectangular():
    # Vertical M and a second M shifted aside so the union is an L, not a filled rectangle.
    group = [("M", 0, 0, 0), ("M", 0, 1, 3)]
    key = relative_pattern(group)
    assert key is not None
    _anchors, _counts, cells = key
    width = max(x for x, _y in cells) - min(x for x, _y in cells) + 1
    height = max(y for _x, y in cells) - min(y for _x, y in cells) + 1
    assert width * height > len(cells)


def test_one_trajectory_counts_once_and_inventories_are_distinct():
    table = PatternTable()

    class Cfg:
        min_pieces = 2
        max_pieces = 2
        max_checks_per_box = 100

    stack = _pair_at(0, 0) + _pair_at(2, 0)
    table.observe_box(11, "same", ("inv",), stack, Cfg)
    table.observe_box(22, "same", ("inv",), stack, Cfg)
    table.observe_box(11, "other", ("other",), _pair_at(0, 0), Cfg)
    key = relative_pattern(_pair_at(0, 0))
    rec = table.patterns[key]
    assert len(rec["boxes"]) == 3
    assert len(rec["inventories"]) == 2
    frozen = table.freeze(2)
    assert any(item["n_inventories"] >= 2 for item in frozen)
    assert table.freeze(3) == []


def test_match_bills_and_does_not_require_an_enclosed_cavity():
    key = relative_pattern(_pair_at(0, 0))
    pattern = {"counts": dict(key[1]), "cells": key[2]}
    checks, fits = match_pattern(pattern, set(), Counter({"M": 4}))
    assert fits > 0
    assert checks > 1
    # Occupied cells elsewhere still leave a translation.
    blocked = set(placed_cells("M", 0, 0, 0))
    _checks, fits_partial = match_pattern(pattern, blocked, Counter({"M": 4}))
    assert fits_partial > 0
    assert stage_name(0, 34, 67) == "early"
    assert stage_name(40, 34, 67) == "middle"
    assert stage_name(80, 34, 67) == "late"


def test_scan_does_not_place():
    key = relative_pattern(_pair_at(0, 0))
    pattern = {"counts": dict(key[1]), "cells": key[2], "pieces": 2}

    class Cfg:
        early_below = 34
        middle_below = 67

    stack = [("O", 0, 8, 8)]
    before = list(stack)
    scan = scan_trajectory(stack, {"M": 2, "O": 1}, [pattern], Cfg)
    assert stack == before
    assert scan["early_fits"] >= 1
    assert scan["match_checks"] > 0


def test_config_declares_the_census_limits():
    data = diagnostic_config().to_dict()
    assert data["commitment"] is False
    assert data["rotations_or_reflections"] is False
    assert data["rectangular_outline_required"] is False
    assert data["large_pieces_first"] is False
    assert data["min_pieces"] == 2 and data["max_pieces"] == 3
    assert data["max_checks_per_box"] == 4000
    assert data["min_inventories"] == 2
    assert data["cheap_fraction"] == 0.10


def test_sources_do_not_place_a_stored_group():
    src = ROOT / "src"
    for path in src.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "env.step" not in text
        assert "replay_suffix" not in text
        assert ".sort(key=lambda" not in text or "n_inventories" in text
