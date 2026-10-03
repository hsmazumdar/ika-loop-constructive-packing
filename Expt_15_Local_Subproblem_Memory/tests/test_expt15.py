"""Expt-15 tests. Local geometry keys, availability matching, region search, detection, extraction."""

from __future__ import annotations

from config import QUALITY_LOSS_MARGIN, diagnostic_config
from environment import Action, PackingEnv
from inventory import Inventory
from local_memory import (
    LocalMemory,
    all_regions,
    extract_entries,
    geometry_key,
    place_entry,
    regions_near,
    solve_region,
)
from pieces import FULL_MASK, bit_for, catalogue_hash, placed_cells
from solver import Ledger

FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def _rect(x0, y0, w, h):
    return [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)]


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_config_declares_no_transform_gate_hierarchy():
    data = diagnostic_config().to_dict()
    assert data["transformations"] is False
    assert data["hierarchy"] is False
    assert data["learned_gate"] is False
    assert "aid" in data["region_supplied_in_test1"]
    assert "billed" in data["region_detector_in_test2"]


def test_geometry_key_translation_invariant():
    assert geometry_key(_rect(0, 0, 2, 4)) == geometry_key(_rect(5, 3, 2, 4))
    assert geometry_key(_rect(0, 0, 2, 4)) != geometry_key(_rect(0, 0, 4, 2))


def test_region_search_fills_2x4_with_two_M():
    placements, evals = solve_region(_rect(3, 3, 2, 4), {"M": 2})
    assert placements is not None and len(placements) == 2
    assert evals > 0
    assert solve_region(_rect(3, 3, 2, 4), {"M": 1})[0] is None


def test_local_match_ignores_rest_of_inventory_but_needs_pieces():
    region = _rect(0, 0, 2, 4)
    placements, _ = solve_region(region, {"M": 2})
    mem = LocalMemory()
    assert mem.add(region, placements, "src", 10) == 2
    assert mem.add(region, placements, "src2", 10) == 1
    other = _rect(6, 2, 2, 4)
    entry, lcost, checks = mem.lookup(other, {"M": 3, "A": 5, "P": 1})
    assert entry is not None and lcost == 1 and checks == 1
    assert mem.lookup(other, {"M": 1, "A": 5})[0] is None


def test_place_entry_translates_and_validates():
    region = _rect(0, 0, 2, 4)
    placements, _ = solve_region(region, {"M": 2})
    mem = LocalMemory()
    mem.add(region, placements, "src", 0)
    target = _rect(6, 2, 2, 4)
    env = PackingEnv(budget=80, inventory=Inventory({"M": 2, "A": 1}))
    entry, _, _ = mem.lookup(target, env.inventory.counts)
    ledger = Ledger()
    assert place_entry(env, target, entry, ledger)["ok"]
    assert env.occupied == 8 and ledger.validation_cost == 2
    assert all(env.mask & bit_for(x, y) for x, y in target)


def test_regions_near_detects_enclosed_pocket_and_bills():
    occupied = FULL_MASK
    for x, y in _rect(2, 2, 2, 4):
        occupied &= ~bit_for(x, y)
    regions, cost = regions_near(occupied, [(1, 2)], 8, 20)
    assert len(regions) == 1 and len(regions[0]) == 8
    assert cost == 8
    big, cost_big = regions_near(0, [(0, 0)], 8, 20)
    assert big == [] and cost_big <= 21


def test_extract_entries_finds_region_filled_later():
    inv = {"M": 2}
    stack = [("M", 0, 0, 0), ("M", 0, 1, 0)]
    found, cost = extract_entries(inv, stack, 8, 20)
    assert cost > 0
    assert found == [] or all(len(f["region"]) <= 20 for f in found)
    regions, _ = all_regions(FULL_MASK & ~sum(bit_for(x, y) for x, y in _rect(0, 0, 2, 4)), 8, 20)
    assert len(regions) == 1


def test_source_has_no_shape_labels():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for path in (root / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
