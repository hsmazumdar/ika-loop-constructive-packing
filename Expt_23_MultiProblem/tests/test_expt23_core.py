import sys, pathlib
import numpy as np
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import polyomino as PM, generator as G, baselines as B
from env import Env

def test_pool_counts_are_one_sided_polyominoes():
    assert [sum(1 for p in PM.POOL if len(p) == n) for n in (3, 4, 5, 6, 7)] == [2, 7, 18, 60, 196]
    assert len(set(PM.LEGACY_POOL_IDX)) == 16

def test_legacy_placement_count_matches_expt01():
    assert Env(G.make_problem("legacy", 0)).N == 3636

def test_generator_deterministic_and_disjoint():
    assert G.make_problem("train", 7) == G.make_problem("train", 7)
    d = G.check_disjoint(300, 60)
    assert d["train_used_test_piece"] == 0
    for sp in ("test_iid", "test_size", "test_piece", "test_both"):
        assert d[sp]["overlap_with_train"] == 0
    assert d["test_size"]["mean_test_pieces"] == 0 and d["test_piece"]["mean_test_pieces"] >= 2
    tr_sizes = {s for s in G.TRAIN_SIZES}
    assert not (set(d["test_size"]["sizes"]) & tr_sizes) and not (set(d["test_both"]["sizes"]) & tr_sizes)

def test_every_catalogue_has_a_large_piece():
    for sp in ("train", "test_iid", "test_size", "test_piece", "test_both"):
        for p in G.problems(sp, 60):
            assert max(len(PM.POOL[i]) for i in p.catalogue) >= 6

@pytest.mark.parametrize("sp", ["train", "test_size", "test_both", "legacy"])
def test_episode_invariants(sp):
    for cap in (14, None):
        p = G.make_problem(sp, 3, budget=cap)
        env = Env(p)
        rng = np.random.default_rng(1)
        for natural in (True, False):
            s = env.new_state()
            seen = set(p.blocked)
            while True:
                c, f = env.candidates(s, natural)
                if c.size == 0:
                    break
                if natural:
                    assert (f["contact"] > 0).all()
                i = int(c[rng.integers(c.size)])
                cells = [int(x) for x in env.CELLS[i] if x < env.HW]
                assert not (set(cells) & seen)           # never overlaps a piece or an obstacle
                assert all(0 <= x < env.HW for x in cells)
                seen |= set(cells)
                env.place(s, i)
            assert s.filled <= env.free_cells
            assert s.filled == len(seen) - len(p.blocked)
            if cap:
                assert s.n <= cap

def test_natural_set_is_never_empty_while_legal_exists():
    p = G.make_problem("train", 2); env = Env(p); rng = np.random.default_rng(3)
    s = env.new_state()
    while not env.done(s):
        leg = env.legal(s)
        c, _ = env.candidates(s, True)
        if leg.size:
            assert c.size > 0
        else:
            break
        env.place(s, int(c[rng.integers(c.size)]))

def test_baselines_reproduce_expt22_legacy_means():
    p = G.make_problem("legacy", 0)
    u = B.evaluate_policy(p, B.run_uniform, 1200, 7_700_000).mean()
    h = B.evaluate_policy(p, B.run_hand, 1200, 7_700_000).mean()
    assert abs(u - 67.319) < 0.5      # Expt 22e: uniform natural 67.319 on 1,200 episodes (different RNG order)
    assert abs(h - 89.617) < 0.5      # Expt 22e: hand rule 89.617

def test_beam_beats_hand_on_sample_problems():
    wins = 0
    for sp in ("train", "test_iid", "test_size", "test_piece"):
        p = G.make_problem(sp, 0); env = Env(p)
        h = B.evaluate_policy(p, B.run_hand, 100, 9_000_000).mean()
        b, _ = B.run_beam(env, width=64)
        wins += b > h
    assert wins == 4

def test_beam_deterministic():
    env = Env(G.make_problem("train", 1))
    assert B.run_beam(env, width=16, seed=5) == B.run_beam(env, width=16, seed=5)

def test_rollout_beam_at_least_hand_mean_and_deterministic():
    p = G.make_problem("train", 1); env = Env(p)
    h = B.evaluate_policy(p, B.run_hand, 100, 9_000_000).mean()
    a = B.run_beam_rollout(env, width=4, per_parent=4, seed=2)
    assert a[0] >= h and a == B.run_beam_rollout(env, width=4, per_parent=4, seed=2)
def test_dev_split_disjoint_from_test_splits():
    dev = {p.spec_hash() for p in G.problems("dev", 200)}
    for sp in ("train", "test_iid", "test_size", "test_piece", "test_both"):
        assert not (dev & {p.spec_hash() for p in G.problems(sp, 200)})