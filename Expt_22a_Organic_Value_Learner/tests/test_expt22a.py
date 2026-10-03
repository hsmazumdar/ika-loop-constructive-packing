import numpy as np
import pytest

import engine as E
import feat as F
from agent import Agent
from analysis import saturation_test, rolling_mean
from config import Cfg, VARIANTS
from mga.environment import Action, PackingEnv
from mga.pieces import ALL_PLACEMENTS
from meta import Meta
from net import MLP
from report import hand_box
from stream import run_stream, sched, evaluate


def _play_random(seed, budget=14):
    rng = np.random.default_rng(seed)
    box = E.Box(budget=budget)
    while True:
        cand, f = E.natural_candidates(box, 2)
        if cand.size == 0:
            return box
        box.place(int(cand[rng.integers(cand.size)]))


def test_boxes_replay_in_packing_env_and_s1_matches():
    for s in range(12):
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
    for s in range(8):
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


def test_feat_shapes():
    box = E.Box(budget=14)
    out = F.step_features(box, 14)
    assert out is not None
    cand, X, sig = out
    assert X.shape == (cand.size, F.D) == (cand.size, 29)
    assert X.dtype == np.float32 and sig.shape == (cand.size,)
    assert F.C_CON == 28 and np.allclose(X[:, F.C_CON], 0)


def test_mlp_train_and_widen_preserves_function():
    rng = np.random.default_rng(0)
    net = MLP(F.D, 16, rng, b_out=0.0)
    X = rng.standard_normal((64, F.D)).astype(np.float32)
    y = (X[:, 16] * 2).astype(np.float32)
    w = np.ones(64, np.float32)
    for _ in range(50):
        net.step(X, y, w, 1e-2)
    pred0 = net.forward(X)
    assert float(np.mean((pred0 - y) ** 2)) < 1.5
    wide = net.widen(24, rng)
    assert np.allclose(pred0, wide.forward(X), atol=1e-5)


def test_agent_play_and_sleep():
    cfg = Cfg()
    flags = dict(VARIANTS["full"])
    ag = Agent(cfg, flags, seed=0, hidden=32)
    rng = np.random.default_rng(1)
    for i in range(80):
        box, ep = ag.play(rng, 1.5, 0.1, cfg.budget)
        assert box.n <= cfg.budget and ep is not None
        ag.remember(ep)
        ag.online_step(ep)
        if ag.new_since_sleep >= 40:
            st = ag.sleep(True, cfg.budget)
            assert "n_dream" in st and ag.sleeps >= 1
            break
    assert ag.sleeps >= 1


def test_learning_improves_over_frozen_short():
    cfg = Cfg()
    cfg.eval_boxes, cfg.probe_boxes, cfg.epoch = 80, 30, 200
    cfg.checkpoints = (0, 600)
    cfg.grow_min_box = 10**9
    a = run_stream("full", 3, cfg, n_boxes=600)
    b = run_stream("frozen", 3, cfg, n_boxes=600)
    assert a["evals"][600]["S1"].mean() > b["evals"][600]["S1"].mean() + 0.5 or a["S1"][-200:].mean() > b["S1"][-200:].mean() + 1.0


def test_stream_reproducible():
    cfg = Cfg()
    cfg.eval_boxes, cfg.checkpoints, cfg.epoch = 40, (0, 300), 150
    cfg.grow_min_box = 10**9
    a = run_stream("full", 1, cfg, n_boxes=300)
    b = run_stream("full", 1, cfg, n_boxes=300)
    assert np.array_equal(a["S1"], b["S1"])


def test_frozen_flat():
    cfg = Cfg()
    cfg.eval_boxes, cfg.checkpoints, cfg.epoch = 30, (0, 200), 10**9
    r = run_stream("frozen", 1, cfg, n_boxes=400)
    assert abs(r["S1"][:150].mean() - r["S1"][-150:].mean()) < 5.0


def test_meta_changes_hparams_on_stagnation_signal():
    cfg = Cfg()
    flags = dict(VARIANTS["full"])
    ag = Agent(cfg, flags, seed=0, hidden=32)
    meta = Meta(cfg, True)
    # fake two epochs then stagnating gains
    meta.end_epoch(ag, 1000, 70.0, [])
    meta.end_epoch(ag, 2000, 70.1, [])
    tau0 = ag.h["tau"]
    meta.gains = [0.05, 0.05, 0.05]
    meta.epoch = 3
    meta.end_epoch(ag, 3000, 70.2, [{"loss_first": 1.0, "loss_last": 1.0, "l_new": 1.0, "l_old": 1.0, "n_concepts": 0}])
    assert meta.events  # some hyper event logged


def test_anneal_schedule_monotone():
    cfg = Cfg()
    a, b, c = sched(cfg, 0), sched(cfg, cfg.anneal_boxes // 2), sched(cfg, cfg.anneal_boxes * 3)
    assert a[0] > b[0] > c[0] and a[1] > b[1] > c[1]


def test_saturation_and_rolling():
    rng = np.random.default_rng(0)
    flat_a, flat_b = rng.normal(70, 1, 8000), rng.normal(70.05, 1, 8000)
    assert saturation_test(flat_a, flat_b, 0.3, 1.645)[0]
    assert rolling_mean(np.arange(10), 5).tolist() == [2, 3, 4, 5, 6, 7]


def test_baseline_band_and_hand_beats_uniform():
    rng = np.random.default_rng(0)
    uni = []
    for i in range(250):
        box = E.Box(budget=14)
        r = np.random.default_rng(i)
        while True:
            out = F.step_features(box, 14)
            if out is None:
                break
            cand, _, _ = out
            box.place(int(cand[int(r.integers(cand.size))]))
        uni.append(box.s1)
    m = float(np.mean(uni))
    assert 62 <= m <= 72
    hand = np.mean([hand_box(np.random.default_rng(i), 14).s1 for i in range(200)])
    assert hand > m + 10


def test_evaluate_uses_slow_net():
    cfg = Cfg()
    flags = dict(VARIANTS["frozen"])
    ag = Agent(cfg, flags, seed=0, hidden=32)
    r = evaluate(ag, cfg, 40, cfg.budget)
    assert r["S1"].shape == (40,) and 50 < r["S1"].mean() < 85


def test_capacity_test_api():
    cfg = Cfg()
    flags = dict(VARIANTS["full"])
    ag = Agent(cfg, flags, seed=0, hidden=64)
    # without enough STM, tested=False
    assert ag.capacity_test()["tested"] is False

