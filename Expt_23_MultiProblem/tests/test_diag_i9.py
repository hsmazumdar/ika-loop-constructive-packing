"""Brief tests for src/diag_i9.py on tiny budgets (a few dozen episodes, 2 problems x 1 rep). Single process, one core."""
import sys, json, pathlib, copy
SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import numpy as np
import diag_i9 as D
import variants as V
import learner_full as LF
import meta as M
import run_e_streams as E


def tiny_unit(suite, arm, variant="std", seed=1, n_ep=36, **kw):
    u = D._u(suite, arm, variant, seed, n_ep=n_ep, **kw)
    u["h_over"] = dict(u["h_over"]); u["h_over"].setdefault("sleep_every", 30)
    return u


def test_unit_lists():
    n = {s: len(D.units(s)) for s in ("D1", "D2", "D2L", "D3", "D4")}
    assert n == {"D1": 8, "D2": 8, "D2L": 8, "D3": 8, "D4": 8}, n
    names = [D.unit_name(u) for s in n for u in D.units(s)]
    assert len(names) == len(set(names))


def test_extras_profile():
    u = D._u("D1", "F", "std", 1, extras="full")
    assert len(D.extras_for(u, 5000, False, (5000, 10000, 20000))) == 11   # fast x 5 taus + slow x 4 taus (slow 0.25 is the main evaluation) + 2 noconc
    assert list(D.extras_for(u, 1000, False, (5000, 10000, 20000))) == ["fast_t0.25"]
    ul = D._u("D2", "F_w64", "std", 1, extras="light")
    assert len(D.extras_for(ul, 20000, True, (5000, 10000, 20000))) == 1 + 4


def test_tiny_D1_unit_models_restore_and_reeval(tmp_path):
    orig = (V.make, LF.FullAgent, dict(M.BOUNDS), dict(E.ARMS), E.evaluate, E.N_REP)
    u = tiny_unit("D1", "F", extras="full", models="all")
    name, st = D.run_unit(u, tmp_path, tiny=True)
    assert st == "done", st
    assert (V.make, LF.FullAgent, dict(M.BOUNDS), dict(E.ARMS), E.evaluate, E.N_REP) == orig      # everything restored
    j = json.load(open(tmp_path / "D1" / f"{name}.json"))
    assert set(j["diag"]["extras"]) == {"0", "36"} and "fast_t0.25" in j["diag"]["extras"]["36"]
    assert (tmp_path / "D1" / f"{name}.csv").exists()
    npz = tmp_path / "models" / f"{name}_ck36.npz"
    assert npz.exists() and (tmp_path / "models" / f"{name}_ck0.npz").exists()
    # re-evaluation of the saved model reproduces the stored standard evaluation exactly (slow net, tau 0.25)
    ag = D.load_model(npz)
    res = D.eval_multi(ag, "std", "capped_nat", 1, {"slow_t0.25": ("slow", 0.25, True)}, ("test_iid",), 2, 1)
    assert res["slow_t0.25"]["test_iid"]["S1"] == j["evals"]["36"]["test_iid"]["S1"]
    # a second call skips
    assert D.run_unit(u, tmp_path, tiny=True)[1] == "exists"


def test_width64_and_sleep_pin(tmp_path):
    u = tiny_unit("D2", "F_w64", arm_kw=dict(hidden=64))
    name, st = D.run_unit(u, tmp_path, tiny=True); assert st == "done"
    z = np.load(tmp_path / "models" / f"{name}_ck36.npz")
    assert z["fast_W1"].shape == (257, 64) and z["slow_W3"].shape == (64, 1)
    u3 = D._u("D3", "F_s1000", "std", 1, n_ep=36, h_over=dict(sleep_every=1000), bounds=dict(sleep_every=(1000, 1000)))
    name3, st3 = D.run_unit(u3, tmp_path, tiny=True); assert st3 == "done"
    j = json.load(open(tmp_path / "D3" / f"{name3}.json"))
    assert j["diag"]["h_at_ckpt"]["36"]["sleep_every"] == 1000 and j["diag"]["h_at_ckpt"]["36"]["sleeps"] == 0
    assert M.BOUNDS["sleep_every"] == (100, 400)
    # pinned bounds really hold the interval inside the meta-controller
    old = dict(M.BOUNDS)
    try:
        M.BOUNDS["sleep_every"] = (1000, 1000)
        class Cfg: grow_min_box = 10 ** 9; grow_every_epochs = 10 ** 9
        m = M.Meta(Cfg, True); h = dict(sleep_every=1000, tau=1.0)
        m._set(h, "sleep_every", 1000 * 0.8, "x", 1, 0.0); m._set(h, "sleep_every", 1000 * 1.1, "x", 1, 0.0)
        assert h["sleep_every"] == 1000
    finally:
        M.BOUNDS.clear(); M.BOUNDS.update(old)


def test_legacy_unit(tmp_path):
    u = tiny_unit("D2L", "F", variant="legacy", n_ep=24, legacy=True)
    name, st = D.run_unit(u, tmp_path, tiny=True); assert st == "done"
    j = json.load(open(tmp_path / "D2L" / f"{name}.json"))
    ev = j["evals"]["24"]
    assert list(ev) == ["test_iid"] and set(ev["test_iid"]["free"]) == {100}       # the 10x10 legacy board, no obstacles
    assert V.make("std", "train", 5, "capped_nat").H != 10 or V.make("std", "train", 5, "capped_nat").pid != "legacy_10x10_A-P"