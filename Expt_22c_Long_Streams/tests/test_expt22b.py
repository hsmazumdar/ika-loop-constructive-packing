import numpy as np

import engine as E
import feat as F
from agent import Agent, Library
from config import VARIANTS, Cfg
from learner_ref import hand_ref, uniform_ref
from mga.environment import Action, PackingEnv
from mga.pieces import ALL_PLACEMENTS
from meta import BOUNDS, Meta
from net import MLP
from stream import run_stream


def _tiny():
    c = Cfg()
    c.eval_boxes, c.epoch, c.probe_boxes, c.grow_min_box, c.grow_every_epochs = 30, 200, 15, 400, 1
    c.checkpoints = (0,)
    return c


def test_default_lambda_is_monte_carlo_and_variants_exist():
    assert Cfg().h0["lam"] == 1.0
    for v in ("full", "no_meta", "no_sleep", "no_dream", "no_concepts", "td095", "badinit_meta", "badinit_fixed", "frozen"):
        assert v in VARIANTS


def test_features_shape_and_natural_only():
    box = E.Box(budget=14)
    cand, X, sig = F.step_features(box, 14)
    assert X.shape == (cand.size, F.D) and sig.shape == cand.shape
    assert np.allclose(X[:, :16].sum(1), 1.0)
    for i in cand[:: max(1, cand.size // 30)]:
        p = ALL_PLACEMENTS[i]
        assert p.boundary_contacts + (p.neighbor_mask & box.occ).bit_count() > 0


def test_agent_boxes_replay_in_packing_env():
    ag = Agent(_tiny(), VARIANTS["full"], 0)
    for s in range(6):
        box, ep = ag.play(np.random.default_rng(s), 1.0, 0.1, 14)
        env = PackingEnv()
        for i in box.placed:
            assert ALL_PLACEMENTS[i] in env.legal_placements()
            env.step(Action.place_from(ALL_PLACEMENTS[i]))
        assert box.s1 == env.occupied == 100 - sum(1 for r in env.cells for c in r if c is None)
        assert box.n <= 14 and ep.X.shape[0] == box.n


def test_untrained_policy_is_near_uniform_baseline():
    ag = Agent(_tiny(), VARIANTS["frozen"], 0)
    m = np.mean([ag.play(np.random.default_rng(s), 1.0, 0.0, 14, record=False)[0].s1 for s in range(200)])
    assert 60 <= m <= 72


def test_mlp_learns_and_widening_preserves_function():
    rng = np.random.default_rng(0)
    net = MLP(5, 16, rng)
    X = rng.standard_normal((512, 5)).astype(np.float32)
    y = (X[:, 0] * 2 - X[:, 1]).astype(np.float32)
    w = np.ones(512, np.float32)
    l0 = net.step(X, y, w, 1e-2)
    for _ in range(300):
        l = net.step(X, y, w, 1e-2)
    assert l < 0.2 * l0
    assert np.allclose(net.forward(X), net.widen(32, rng).forward(X), atol=1e-4)


def test_lambda_returns():
    ag = Agent(_tiny(), VARIANTS["full"], 0)
    _, ep = ag.play(np.random.default_rng(1), 1.0, 0.1, 14)
    X, K, M, W, L, fin = ag._pack([ep])
    G, V = ag._targets(X, M, L, fin, 1.0)
    assert np.allclose(G[0, : L[0]], (fin[0] - 70.0) / 10.0)
    G0, V0 = ag._targets(X, M, L, fin, 0.0)
    assert np.isclose(G0[0, L[0] - 1], (fin[0] - 70.0) / 10.0)
    assert np.allclose(G0[0, : L[0] - 1], V[0, 1: L[0]])


def test_sleep_dreams_and_updates_slow_weights():
    cfg = _tiny()
    ag = Agent(cfg, VARIANTS["full"], 0)
    rng = np.random.default_rng(0)
    for _ in range(40):
        ag.remember(ag.play(rng, 1.5, 0.1, 14)[1])
    before = ag.slow.p["W1"].copy()
    st = ag.sleep(True, 14)
    assert st["n_dream"] > 0 and ag.sleeps == 1 and not np.allclose(before, ag.slow.p["W1"])
    ag2 = Agent(cfg, VARIANTS["no_dream"], 0)
    for _ in range(40):
        ag2.remember(ag2.play(rng, 1.5, 0.1, 14)[1])
    assert ag2.sleep(False, 14)["n_dream"] == 0


def test_no_sleep_evaluates_the_learning_net_not_a_frozen_one():
    ag = Agent(_tiny(), VARIANTS["no_sleep"], 0)
    assert ag.memory_net() is ag.fast
    assert Agent(_tiny(), VARIANTS["full"], 0).memory_net() is not None


def test_concept_library_promotes_only_significant_patterns():
    lib = Library()
    rng = np.random.default_rng(0)
    keys = np.concatenate([np.full(200, 11), np.full(200, 22), rng.integers(1000, 1100, 200)])
    resid = np.concatenate([np.full(200, 2.0) + rng.normal(0, .5, 200), rng.normal(0, .5, 200), rng.normal(0, 1, 200)])
    lib.observe(keys, resid)
    assert lib.promote(Cfg()) == 1 and lib.keys[0] == 11 and lib.val[0] > 0
    assert lib.lookup(np.array([11, 22]))[1] == 0


def test_meta_moves_within_bounds_logs_reasons_and_off_switch():
    cfg = _tiny()
    ag = Agent(cfg, VARIANTS["full"], 0)
    meta = Meta(cfg, True)
    for k, probe in enumerate([70, 71, 72, 72.05, 72.05, 72.0, 72.0, 72.02] * 4):
        meta.end_epoch(ag, (k + 1) * 1000, probe, [{"loss_first": 1.0, "loss_last": 0.5, "l_new": 1, "l_old": 1, "n_concepts": 0}])
    assert meta.events and all(e["reason"] for e in meta.events)
    for k, (lo, hi) in BOUNDS.items():
        assert lo <= ag.h[k] <= hi
    off, ag2 = Meta(cfg, False), Agent(cfg, VARIANTS["no_meta"], 0)
    off.end_epoch(ag2, 1000, 70, []); off.end_epoch(ag2, 2000, 71, [])
    assert off.events == [] and ag2.h == {**cfg.h0}


def test_capacity_test_widens_only_when_validated():
    cfg = _tiny()
    ag = Agent(cfg, VARIANTS["full"], 0)
    rng = np.random.default_rng(0)
    for _ in range(420):
        ag.remember(ag.play(rng, 1.5, 0.1, 14)[1])
    cfg.grow_test_steps = 20
    r = ag.capacity_test()
    assert r["tested"] and r["to"] == 128 and ag.hidden == (128 if r["grow"] else 64)


def test_stream_reproducible_frozen_flat_and_fixed_has_no_events():
    cfg = _tiny()
    a, b = run_stream("full", 3, cfg, 450), run_stream("full", 3, cfg, 450)
    assert np.array_equal(a["S1"], b["S1"])
    assert run_stream("frozen", 3, cfg, 450)["events"] == []
    assert run_stream("no_meta", 1, cfg, 450)["events"] == []


def test_references_run():
    cfg = _tiny()
    assert 60 < uniform_ref(cfg, 14, 40)["S1"].mean() < 75
    assert hand_ref(cfg, 14, 40).mean() > uniform_ref(cfg, 14, 40)["S1"].mean()