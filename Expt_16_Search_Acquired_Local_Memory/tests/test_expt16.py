"""Expt-16 tests. Bounded search outcomes, snapshots, entry table, read-only matching, branching."""

from __future__ import annotations

from acquire import AcquiredMemory, area_feasible, branch, load_manifest, observe, region_snapshots, search_region, validate_filling
from config import diagnostic_config, smoke_config
from pieces import catalogue_hash


def _rect(x0, y0, w, h):
    return [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)]


def test_catalogue():
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_config_declares_scope():
    d = diagnostic_config().to_dict()
    assert d["partial_fillings"] is False and d["transformations"] is False and d["learned_gate"] is False
    assert "unknown" in " ".join(d["search_outcomes"])


def test_area_feasible():
    assert area_feasible(8, {4: 2})
    assert not area_feasible(8, {5: 3})
    assert area_feasible(9, {4: 1, 5: 1})
    assert not area_feasible(11, {4: 3, 5: 0, 7: 0})


def test_search_found_impossible_and_budget():
    found = search_region(_rect(0, 0, 2, 4), {"M": 2}, 20000)
    assert found["status"] == "found" and len(found["placements"]) == 2
    impossible = search_region(_rect(0, 0, 2, 4), {"A": 3}, 20000)
    assert impossible["status"] == "impossible"
    tight = search_region(_rect(0, 0, 4, 5), {t: 2 for t in "ABCDEFGHIJKL"}, 3)
    assert tight["status"] in ("found", "budget_exhausted")
    assert tight["status"] != "impossible"


def test_budget_stop_is_never_impossible():
    region = _rect(0, 0, 4, 5)
    inv = {t: 1 for t in "ABCDEFGHIJKL"}
    small = search_region(region, inv, 5)
    big = search_region(region, inv, 10**6)
    if big["status"] == "found":
        assert small["status"] in ("found", "budget_exhausted")


def test_snapshots_and_validation():
    stack = [("M", 0, 0, 0), ("M", 0, 0, 1)]
    snaps, cost = region_snapshots({"M": 4}, stack, 8, 20)
    assert cost > 0
    for s in snaps:
        assert 8 <= len(s["region"]) <= 20
    ok, vcost = validate_filling({"M": 2}, [], _rect(0, 0, 2, 4), search_region(_rect(0, 0, 2, 4), {"M": 2}, 1000)["placements"])
    assert ok and vcost == 2


def test_entry_table_keeps_multisets_and_alternatives():
    mem = AcquiredMemory()
    region = _rect(0, 0, 2, 4)
    p = search_region(region, {"M": 2}, 1000)["placements"]
    assert mem.add(region, p, "a", 5)["outcome"] == "written"
    assert mem.add(_rect(5, 5, 2, 4), [(q[0], q[1], q[2] + 5, q[3] + 5) for q in p], "b", 5)["outcome"] == "duplicate"
    mem.freeze()
    geo, compat, lcost, checks = mem.lookup_all(_rect(3, 2, 2, 4), {"M": 2, "A": 9})
    assert geo and len(compat) == 1 and lcost == 1 and checks == 1
    geo, compat, _, _ = mem.lookup_all(_rect(3, 2, 2, 4), {"M": 1})
    assert geo and compat == []


def test_manifests_hash_checked():
    store = load_manifest("acquisition_store")
    assert len(store["tasks"]) == 16
    assert len(load_manifest("applicability_fresh")["tasks"]) == 60
    assert len(load_manifest("validation_family")["tasks"]) == 60


def test_primitive_branch_reproduces_trajectory():
    config = smoke_config()
    task = load_manifest("applicability_fresh")["tasks"][0]
    mem = AcquiredMemory()
    for x0, y0, w, h in ((0, 0, 2, 4), (0, 0, 4, 2), (0, 0, 3, 3)):
        r = _rect(x0, y0, w, h)
        res = search_region(r, {t: 3 for t in "ABCDEFGHIJKLMNOP"}, 20000)
        if res["status"] == "found":
            mem.add(r, res["placements"], "t", res["evals"])
    mem.freeze()
    obs = observe(config, task, 11, "test", 0, mem)
    for snap in obs["snapshots"][:2]:
        base = branch(config, snap, None)
        assert abs(base["Q"] - obs["Q"]) < 1e-9
        assert snap["prefix_A"] + base["A_rest"] == obs["A"]
