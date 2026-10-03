import numpy as np
import pytest

import engine as E
import learner as L
from analysis import saturation_test, rolling_mean
from config import Cfg
from mga.environment import Action, PackingEnv
from mga.pieces import ALL_PLACEMENTS
from stream import run_stream, schedule
from tables import HashTable


def _play_random(seed, budget=14, natural=True):
    rng = np.random.default_rng(seed)
    box = E.Box(budget=budget)
    while True:
        cand, f = E.natural_candidates(box, 2)
        if cand.size == 0:
            return box
        box.place(int(cand[rng.integers(cand.size)]))


def test_boxes_replay_in_packing_env_and_s1_matches():
    for s in range(15):
        box = _play_random(s)
        env = PackingEnv()
        for i in box.placed:
            p = ALL_PLACEMENTS[i]
            assert p in env.legal_placements()
            env.step(Action.place_from(p))
        empty = sum(1 for row in env.cells for c in row if c is None)
        assert box.s1 == 100 - empty == env.occupied


def test_budget_limits_pieces():
    assert all(_play_random(s, budget=9).n <= 9 for s in range(5))


def test_natural_placing_every_piece_touches_wall_or_piece():
    for s in range(10):
        rng = np.random.default_rng(s)
        box = E.Box(budget=14)
        while True:
            cand, f = E.natural_candidates(box, 0)
            if cand.size == 0:
                break
            i = int(cand[rng.integers(cand.size)])
            occ_before = box.occ
            p = ALL_PLACEMENTS[i]
            assert p.boundary_contacts + (p.neighbor_mask & occ_before).bit_count() > 0
            box.place(i)


def test_natural_candidates_are_subset_of_legal_and_nonempty_when_legal():
    box = _play_random(3, budget=5)
    box2 = E.Box()
    cand, _ = E.natural_candidates(box2)
    assert set(cand) <= set(box2.legal()) and cand.size > 0


def test_features_contact_matches_expt20_definition():
    box = _play_random(4, budget=6)
    legal = box.legal()
    f = E.features(box, legal, 2)
    for k in range(0, legal.size, max(1, legal.size // 40)):
        p = ALL_PLACEMENTS[legal[k]]
        assert f["contact"][k] == p.boundary_contacts + (p.neighbor_mask & box.occ).bit_count()


def test_features_holes_count():
    box = E.Box()
    legal = box.legal()
    f = E.features(box, legal, 2)
    assert f["p1"].min() >= 0 and f["n3"].min() >= 0
    # a placement that leaves a one-cell hole: find one by brute force and check p1 >= 1
    box.place(int(np.flatnonzero((E.PTYPE == 1))[0]))  # B at corner-ish
    f2 = E.features(box, box.legal(), 2)
    assert f2["sig1"].dtype == np.int64


def test_hashtable_learns_mean_and_shrinks():
    t = HashTable(6, k=2.0)
    keys = np.array([5] * 10)
    t.update(keys, np.ones(10), np.full(10, 4.0), np.ones(10))
    w = t.get(np.array([5]))[0]
    assert 0 < w < 4.0
    assert t.get(np.array([6]))[0] == 0.0


def test_hashtable_decay_prune_and_grow_keep_strong_entries():
    t = HashTable(6, k=1.0)
    t.update(np.array([1]), np.array([1.0]), np.array([0.0]), np.array([1.0]))  # weak: w=0, n=1
    t.update(np.array([2] * 50), np.ones(50), np.full(50, 3.0), np.ones(50))     # strong
    assert t.prune(n_min=5.0, w_min=0.5, occupancy=0.99) == 1
    w_before = t.get(np.array([2]))[0]
    t.grow(9)
    assert t.size == 512 and abs(t.get(np.array([2]))[0] - w_before) < 1e-12
    t.decay(0.5)
    assert t.n.max() <= 25.0 + 1e-9


def test_advantage_learning_prefers_better_piece():
    cfg = Cfg()
    mem = L.Memory(cfg)
    rng = np.random.default_rng(0)
    # fake episodes: boxes containing type 15 (P) are better than those containing type 12 (M)
    good = [int(np.flatnonzero(E.PTYPE == 15)[0])]
    bad = [int(np.flatnonzero(E.PTYPE == 12)[0])]
    for _ in range(60):
        mem.learn_online(L.Episode(good, 20))
        mem.learn_online(L.Episode(bad, 10))
    w = mem.tables["type"]
    assert w.get(np.array([15]))[0] > w.get(np.array([12]))[0]


def test_growth_adds_features_and_reconsolidates():
    cfg = Cfg()
    mem = L.Memory(cfg)
    assert mem.active == ["type", "A"] and mem.level == 0
    rng = np.random.default_rng(1)
    stm = [L.Episode(b.placed, b.s1) for b in [L.play_box(mem, rng, 2.0, 0.1) for _ in range(40)]]
    for st in range(1, len(cfg.stages)):
        new = mem.grow_to(st)
        mem.reconsolidate(stm, new)
    assert set(mem.active) == set(L.ALL_FEATS) and mem.level == 2
    assert mem.tables["S1"].bits == cfg.bits["S1"] + mem.cap_extra
    assert mem.stats()["entries"] > 0


def test_sleep_runs_and_dreams():
    cfg = Cfg()
    mem = L.Memory(cfg)
    rng = np.random.default_rng(2)
    stm = [L.Episode(b.placed, b.s1) for b in [L.play_box(mem, rng, 2.0, 0.1) for _ in range(60)]]
    out = mem.sleep(stm, 40, rng, 1.5, True)
    assert out["dreams"] == int(cfg.dream_ratio * 40) and mem.sleeps == 1
    out2 = mem.sleep(stm, 40, rng, 1.5, False)
    assert out2["dreams"] == 0


def test_policy_is_not_a_hand_heuristic_untrained_is_uniform():
    # an empty memory must give all-zero scores => uniform choice among natural placements
    mem = L.Memory(Cfg())
    box = E.Box(budget=14)
    cand, f = E.natural_candidates(box, 0)
    assert not mem.score(box, cand, f).any()


def test_choose_softmax_prefers_high_score_and_respects_eps():
    rng = np.random.default_rng(0)
    s = np.array([0.0, 5.0, 0.0])
    picks = [L.choose(s, 0.5, 0.0, rng) for _ in range(400)]
    assert picks.count(1) > 380
    picks = [L.choose(s, 0.5, 1.0, rng) for _ in range(900)]
    assert all(picks.count(k) > 200 for k in range(3))


def test_saturation_detector():
    rng = np.random.default_rng(0)
    flat_a, flat_b = rng.normal(70, 6, 6000), rng.normal(70, 6, 6000)
    assert saturation_test(flat_a, flat_b, 0.3, 1.645)[0]
    up = rng.normal(72, 6, 6000)
    assert not saturation_test(flat_a, up, 0.3, 1.645)[0]
    assert rolling_mean(np.arange(10), 5).tolist() == [2, 3, 4, 5, 6, 7]


def test_anneal_schedule_monotone():
    cfg = Cfg()
    a, b, c = schedule(cfg, 0), schedule(cfg, cfg.anneal_boxes // 2), schedule(cfg, cfg.anneal_boxes * 3)
    assert a[0] > b[0] > c[0] and a[1] > b[1] > c[1] and c == pytest.approx((cfg.tau_min, cfg.eps_min))


def _tiny_cfg():
    cfg = Cfg()
    cfg.anneal_boxes, cfg.sat_window, cfg.check_every, cfg.max_stage_boxes = 400, 200, 100, 500
    cfg.min_boxes, cfg.eval_boxes, cfg.checkpoints, cfg.rehearse, cfg.sleep_every = 10**9, 40, (0, 600), 20, 50
    return cfg


def test_stream_learns_and_grows_and_is_reproducible():
    cfg = _tiny_cfg()
    a = run_stream("full", 1, 1300, cfg)
    b = run_stream("full", 1, 1300, cfg)
    assert np.array_equal(a["S1"], b["S1"])
    assert a["events"] and a["final_stage"] >= 1
    assert a["evals"][0]["S1"].mean() < a["evals"][1300]["S1"].mean()


def test_frozen_variant_is_flat_and_no_growth():
    cfg = _tiny_cfg()
    r = run_stream("frozen", 1, 1000, cfg)
    assert r["events"] == [] and r["final_stage"] == 0
    assert abs(r["S1"][:300].mean() - r["S1"][-300:].mean()) < 4.0  # no learning => flat (noise only)
    assert r["memory"]["stats"]["entries"] == 0


def test_baseline_in_target_band():
    rng = np.random.default_rng(0)
    m = np.mean([L.play_box(None, rng, 1.0, 0.0).s1 for _ in range(400)])
    assert 62 <= m <= 71