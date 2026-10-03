"""LTM-guided piece picking (Phase 2). Nothing here is learned online: weights are read from the frozen LTM.

Mechanism, per step of a trial:
  1. With probability epsilon (default 0.1): explore. Pick one legal placement uniformly (Phase 1 / control style).
  2. Otherwise: group the legal placements by piece type. Weight every legal type t:
         w(t) = single_weight(t) * boost(t)
     single_weight(t) = clip( smoothed lift of t in the LTM , 0.25 , 4.0 )
         smoothed lift = ((n_top + a) / (N_top + 2a)) / ((n_bottom + a) / (N_bottom + 2a)),  a = 1
         (n_top, n_bottom come from the LTM's single_type entries for the default ranking, S2).
     boost(t) = the largest LTM lift_vs_bottom among *winning* pairs/triples C (lift > 1) that adding t completes:
         C contains t, the pieces already placed contain C minus one t, and they do not yet contain C.
         No such combination -> boost 1. Boosts are clipped to [1, 6]. Non-winning combinations are ignored.
     Sample a type with probability w(t) / sum w, then a uniformly random legal placement of that type.
Flat/ablation variants reuse the same two-stage sampling with part of the weights switched off.
"""

from __future__ import annotations

import random
from collections import Counter

from mga.environment import Action, PackingEnv
from mga.pieces import N_CELLS
from trials import trial_seed

DEFAULT_EPSILON = 0.1
SMOOTHING = 1.0
SINGLE_CLIP = (0.25, 4.0)
BOOST_CLIP = (1.0, 6.0)


def smoothed_single_weights(entries, n_top_total, n_bottom_total, smoothing=SMOOTHING, clip=SINGLE_CLIP) -> dict:
    out = {}
    for e in entries:
        ft = (e["n_top"] + smoothing) / (n_top_total + 2 * smoothing)
        fb = (e["n_bottom"] + smoothing) / (n_bottom_total + 2 * smoothing)
        out[e["key"]] = min(max(ft / fb, clip[0]), clip[1])
    return out


def _lift(e, clip):
    lift = e.get("lift_vs_bottom")
    return clip[1] if lift is None else min(max(float(lift), clip[0]), clip[1])


class Policy:
    def __init__(self, name, single_w, pair_idx, tri_idx, epsilon=DEFAULT_EPSILON, use_single=True, use_boost=True):
        self.name = name
        self.single_w = dict(single_w)
        self.pair_idx = pair_idx     # placed type u -> [(t, combo, lift)]
        self.tri_idx = tri_idx       # (u, v) sorted placed types -> [(t, combo, lift)]
        self.epsilon = float(epsilon)
        self.use_single = use_single
        self.use_boost = use_boost

    @classmethod
    def from_ltm(cls, ltm: dict, ranking: str | None = None, epsilon=DEFAULT_EPSILON, smoothing=SMOOTHING,
                 single_clip=SINGLE_CLIP, boost_clip=BOOST_CLIP, name=None):
        ranking = ranking or ltm["default_ranking"]
        body = ltm["ltm"][ranking]
        n_top_total = int(ltm["cutoffs"][ranking]["n_top"])
        n_bottom_total = int(ltm["manifest"]["trials"]) - n_top_total
        single_w = smoothed_single_weights(body["single_type"]["entries"], n_top_total, n_bottom_total, smoothing, single_clip)
        pair_idx: dict = {}
        tri_idx: dict = {}
        for e in body["pair_type"]["entries"]:
            if not e["winning"] or (e.get("lift_vs_bottom") is not None and e["lift_vs_bottom"] <= 1.0):
                continue
            key, lift = tuple(e["key"]), _lift(e, boost_clip)
            for t in set(key):
                rest = list(key)
                rest.remove(t)
                pair_idx.setdefault(rest[0], []).append((t, key, lift))
        for e in body["triple_type"]["entries"]:
            if not e["winning"] or (e.get("lift_vs_bottom") is not None and e["lift_vs_bottom"] <= 1.0):
                continue
            key, lift = tuple(e["key"]), _lift(e, boost_clip)
            for t in set(key):
                rest = list(key)
                rest.remove(t)
                tri_idx.setdefault(tuple(sorted(rest)), []).append((t, key, lift))
        return cls(name or f"ltm_{ranking}", single_w, pair_idx, tri_idx, epsilon)

    def variant(self, name, use_single=True, use_boost=True):
        return Policy(name, self.single_w, self.pair_idx, self.tri_idx, self.epsilon, use_single, use_boost)

    def boosts(self, placed) -> dict:
        """type -> boost (>1) for types that would complete a winning pair/triple given the pieces already placed."""
        out: dict = {}
        if not self.use_boost:
            return out
        present = sorted(t for t, c in placed.items() if c > 0)
        for u in present:
            for t, key, lift in self.pair_idx.get(u, ()):
                if placed.get(t, 0) < key.count(t) and lift > out.get(t, 1.0):
                    out[t] = lift
        for i, u in enumerate(present):
            for v in present[i:]:
                if u == v and placed[u] < 2:
                    continue
                for t, key, lift in self.tri_idx.get((u, v), ()):
                    if placed.get(t, 0) < key.count(t) and lift > out.get(t, 1.0):
                        out[t] = lift
        return out

    def weights(self, types, placed) -> list[float]:
        boost = self.boosts(placed)
        return [(self.single_w.get(t, 1.0) if self.use_single else 1.0) * boost.get(t, 1.0) for t in types]

    def describe(self) -> dict:
        return {"name": self.name, "epsilon": self.epsilon, "use_single": self.use_single, "use_boost": self.use_boost,
                "single_weights": dict(sorted(self.single_w.items())),
                "n_pair_rules": sum(len(v) for v in self.pair_idx.values()),
                "n_triple_rules": sum(len(v) for v in self.tri_idx.values())}


def _result(env, trial_id, tseed, extra) -> dict:
    empty = sum(1 for row in env.cells for cell in row if cell is None)
    s1 = N_CELLS - empty
    if s1 != env.occupied:
        raise AssertionError(f"trial {trial_id}: 100-empty={s1} but env.occupied={env.occupied}")
    attempts = env.placements_count
    out = {
        "trial_id": trial_id, "trial_seed": tseed, "S1": s1, "empty_cells": empty, "attempts": attempts,
        "S2": s1 / attempts if attempts else 0.0, "invalid_attempts": env.invalid_attempts,
        "actions_used": env.actions_used, "termination_reason": env.termination_reason or "no_legal_placement",
        "placements": [(i.piece_type, int(i.rotation), int(i.x), int(i.y)) for i in env.stack],
    }
    out.update(extra)
    return out


def run_guided_trial(seed: int, trial_id: int, policy: Policy) -> dict:
    """Same per-trial seed rule as trials.run_trial, so trial i of a guided arm and of the uniform control share a seed."""
    tseed = trial_seed(seed, trial_id)
    rng = random.Random(tseed)
    env = PackingEnv()
    placed: Counter = Counter()
    explore = guided = boosted = 0
    while not env.terminal:
        legal = env.legal_placements()
        if not legal:
            break
        if rng.random() < policy.epsilon:
            p = rng.choice(legal)
            explore += 1
        else:
            by_type: dict = {}
            for q in legal:
                by_type.setdefault(q.piece_type, []).append(q)
            types = sorted(by_type)
            if policy.use_boost and policy.boosts(placed) and any(t in policy.boosts(placed) for t in types):
                boosted += 1
            t = rng.choices(types, weights=policy.weights(types, placed))[0]
            p = rng.choice(by_type[t])
            guided += 1
        env.step(Action.place_from(p))
        placed[p.piece_type] += 1
    return _result(env, trial_id, tseed, {"n_explore_steps": explore, "n_guided_steps": guided, "n_boosted_steps": boosted})


def run_guided_trials(seed: int, n: int, policy: Policy) -> list[dict]:
    return [run_guided_trial(seed, i, policy) for i in range(n)]