"""Reference policies for Expt 23 (REFERENCE ONLY: none of these is ever used inside a learner).

uniform_natural : uniform among the action set (natural placements by default)
hand_rule       : the Expt 21-22 rule, argmax of contact - 3 p1 - n3 + 2 area + U(0, 0.5)
beam_search     : width-B beam over afterstates, ranked by a hand-written shaping score (reference upper bound, not optimal)
"""
from __future__ import annotations

import time

import numpy as np

from env import Env, Problem


def run_uniform(env: Env, rng, natural=True) -> int:
    s = env.new_state()
    while True:
        c, _ = env.candidates(s, natural)
        if c.size == 0:
            break
        env.place(s, int(c[rng.integers(c.size)]))
    return s.filled


def run_hand(env: Env, rng, natural=True) -> int:
    s = env.new_state()
    while True:
        c, f = env.candidates(s, natural)
        if c.size == 0:
            break
        sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * env.AREA[c] + rng.random(c.size) * 0.5
        env.place(s, int(c[int(np.argmax(sc))]))
    return s.filled


def shaping(env: Env, s, w_hole=2.0, w_notch=0.5) -> float:
    gh, gn = env.global_holes_notches(s)
    return s.filled - w_hole * gh - w_notch * gn


def run_beam(env: Env, width=8, natural=True, expand_cap=24, seed=0, w_hole=2.0, w_notch=0.5) -> tuple[int, int]:
    """Beam search. At each depth every beam state is expanded by its `expand_cap` best children (hand score + noise),
    all children are ranked by `shaping` and the best `width` distinct boards are kept. Returns (best S1 found, nodes)."""
    rng = np.random.default_rng(seed)
    beam = [env.new_state()]
    best, nodes = 0, 0
    while beam:
        kids, seen = [], set()
        for s in beam:
            c, f = env.candidates(s, natural)
            if c.size == 0:
                best = max(best, s.filled)
                continue
            sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * env.AREA[c] + rng.random(c.size) * 0.01
            top = c[np.argsort(-sc)[:expand_cap]]
            for i in top:
                t = s.copy()
                env.place(t, int(i))
                key = t.occ.tobytes()
                if key in seen:
                    continue
                seen.add(key)
                nodes += 1
                kids.append((shaping(env, t, w_hole, w_notch) + rng.random() * 1e-3, t))
        kids.sort(key=lambda z: -z[0])
        beam = [t for _, t in kids[:width]]
        for t in beam:
            best = max(best, t.filled)
    return best, nodes


def evaluate_policy(prob: Problem, fn, n_eps: int, seed0: int, natural=True) -> np.ndarray:
    env = Env(prob)
    return np.array([fn(env, np.random.default_rng((seed0, j)), natural) for j in range(n_eps)], np.int32)

def _rollout_hand(env: Env, s, rng, natural=True) -> int:
    s = s.copy()
    while True:
        c, f = env.candidates(s, natural)
        if c.size == 0:
            break
        sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * env.AREA[c] + rng.random(c.size) * 0.5
        env.place(s, int(c[int(np.argmax(sc))]))
    return s.filled


def run_beam_rollout(env: Env, width=8, per_parent=6, n_roll=2, natural=True, seed=0) -> tuple[int, int]:
    """Stronger REFERENCE: beam whose states are ranked by the best of `n_roll` hand-rule rollouts (children per parent
    = 3 * per_parent by hand score). Returns (best S1 found, rollouts used). Never used inside a learner."""
    rng = np.random.default_rng(seed)
    beam = [env.new_state()]
    best, calls = 0, 0
    while beam:
        kids, seen = [], set()
        for s in beam:
            c, f = env.candidates(s, natural)
            if c.size == 0:
                best = max(best, s.filled)
                continue
            sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * env.AREA[c] + rng.random(c.size) * 0.5
            for i in c[np.argsort(-sc)[:per_parent * 3]]:
                t = s.copy()
                env.place(t, int(i))
                key = t.occ.tobytes()
                if key in seen:
                    continue
                seen.add(key)
                v = max(_rollout_hand(env, t, rng, natural) for _ in range(n_roll))
                calls += n_roll
                best = max(best, v)
                kids.append((v + rng.random() * 1e-3, t))
        kids.sort(key=lambda z: -z[0])
        beam = [t for _, t in kids[:width]]
    return best, calls

def run_hand_w(env: Env, rng, natural=True, w=(1.0, -3.0, -1.0, 2.0)) -> int:
    """Parametrised hand rule (contact, p1, n3, area weights) + U(0, 0.5) noise. w=(1,-3,-1,2) is the Expt 21-22 rule. REFERENCE ONLY."""
    s = env.new_state()
    while True:
        c, f = env.candidates(s, natural)
        if c.size == 0:
            break
        sc = w[0] * f["contact"] + w[1] * f["p1"] + w[2] * f["n3"] + w[3] * env.AREA[c] + rng.random(c.size) * 0.5
        env.place(s, int(c[int(np.argmax(sc))]))
    return s.filled


def cem_tune_hand(problems, natural=True, seed=0, pop=24, elites=8, iters=6, n_prob=12, n_eps=20, w0=(1.0, -3.0, -1.0, 2.0), sd0=1.5):
    """Cross-entropy-method tuning of the 4 hand-rule weights on TRAIN problems. Fitness = mean S1/free_cells with common random numbers.
    REFERENCE ONLY (never inside a learner). Returns dict(w=..., history=[...])."""
    rng = np.random.default_rng(seed)
    envs = {}
    mu, sd = np.array(w0, float), np.full(4, sd0)
    hist = []
    for it in range(iters):
        idx = rng.choice(len(problems), n_prob, replace=False)
        for i in idx:
            if i not in envs:
                envs[i] = Env(problems[i])
        cands = np.vstack([mu] + [mu + sd * rng.standard_normal(4) for _ in range(pop - 1)])
        fit = np.zeros(pop)
        for k, w in enumerate(cands):
            tot = 0.0
            for i in idx:
                e = envs[i]
                for j in range(n_eps):
                    tot += run_hand_w(e, np.random.default_rng((seed, it, int(i), j)), natural, tuple(w)) / max(e.free_cells, 1)
            fit[k] = tot / (len(idx) * n_eps)
        order = np.argsort(-fit)[:elites]
        mu, sd = cands[order].mean(axis=0), np.maximum(cands[order].std(axis=0), 0.15)
        hist.append({"iter": it, "best_fit": float(fit[order[0]]), "mean_fit": float(fit.mean()), "mu": mu.tolist()})
    return {"w": mu.tolist(), "history": hist}