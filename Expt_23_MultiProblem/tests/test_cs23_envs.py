import sys, pathlib, time
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import cs2_programs as C2, cs3_tiles as C3

def test_cs3_scramble_solvable_and_deterministic():
    a, b = C3.make_task("train", 5), C3.make_task("train", 5)
    assert a == b
    t = C3.make_task("test_iid", 1)
    d = C3.optimal_length(t)
    assert d is not None and d <= t["scramble_depth"]

def test_cs3_astar_matches_bfs_on_small():
    for i in range(10):
        t = C3.make_task("train", i)
        L, _ = C3.astar(t["start"], t["R"], t["C"], 200_000)
        assert L == C3.optimal_length(t)

def test_cs3_splits_boards():
    assert {(C3.make_task("train", i)["R"], C3.make_task("train", i)["C"]) for i in range(30)} <= set(C3.TRAIN_BOARDS)
    assert {(C3.make_task("test_size", i)["R"], C3.make_task("test_size", i)["C"]) for i in range(60)} <= set(C3.TEST_BOARDS)
    assert not set(C3.TRAIN_BOARDS) & set(C3.TEST_BOARDS)

def test_cs3_depth_split():
    assert max(C3.make_task("train", i)["scramble_depth"] for i in range(50)) <= 30
    assert min(C3.make_task("test_deep", i)["scramble_depth"] for i in range(50)) >= 31

def test_cs2_task_valid_and_deterministic():
    for sp in ("train", "test_iid", "test_comp", "test_deep", "test_const"):
        t = C2.make_task(sp, 3)
        assert t == C2.make_task(sp, 3)
        assert C2.solves(t["prog"], t)

def test_cs2_composition_split_disjoint():
    train = {tuple(p[0] for p in C2.make_task("train", i)["prog"]) for i in range(300)}
    comp = {tuple(p[0] for p in C2.make_task("test_comp", i)["prog"]) for i in range(100)}
    assert not (train & comp)
    assert all(C2._is_held_comp(c) for c in comp) and not any(C2._is_held_comp(c) for c in train)

def test_cs2_const_and_depth_split():
    assert all(p[1] in C2.UNSEEN_CONSTS or p[1] == 0 for i in range(40) for p in C2.make_task("test_const", i)["prog"])
    assert all(p[1] in C2.TRAIN_CONSTS or p[1] == 0 for i in range(40) for p in C2.make_task("train", i)["prog"])
    assert min(C2.make_task("test_deep", i)["depth"] for i in range(40)) >= 4

def test_cs2_enumeration_solves_short_programs():
    ok = 0
    for i in range(20):
        t = C2.make_task("train", i)
        pr, n = C2.enumerate_solver(t, 200_000)
        ok += pr is not None
    assert ok >= 18