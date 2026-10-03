"""Unified guided-trial runner. One Spec describes a variant; run_trial executes it headless.

Step logic (every step, after env.legal_placements()):
  1. explore: with probability eps pick a uniformly random legal placement (ignores everything below).
  2. candidate pool: all legal placements, or (anchor=True) only those covering the first empty cell (row-major) that some
     legal placement can cover ("bottom-left anchoring"; cells no piece can cover are skipped and stay empty).
  3. type choice (type_mode):
       placement_uniform  no type choice; candidates = the whole pool (control-style)
       flat               piece type uniformly among the types present in the pool
       size               weight area**alpha
       ltm                weight (single_lift**alpha if use_single) * (boost**beta if use_boost); hard_priority: if any
                          type would complete a winning LTM pair/triple, choose only among those
       online             softmax / Thompson weights over types from the running mean S1 of boxes containing the type
  4. placement choice among the chosen type's candidates (select):
       random   uniform
       contact  maximum edge contact with wall/occupied cells, random tie-break
       table    weight learned_lift(type, rotation, x, y)**gamma (top-25% placement frequency vs the rest)
       look     one-step lookahead: sample K candidates, evaluate dead cells after placing (empty cells that no legal
                placement can cover), pick min dead, tie-break max contact, then random
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import asdict, dataclass, field

from mga.environment import Action, PackingEnv
from mga.pieces import PIECES, N_CELLS
from phases.policy import Policy
from stronger.engine import N_ALL, Cost, anchor_pool, contact_score, dead_cells_after
from trials import trial_seed


@dataclass(frozen=True)
class Spec:
    name: str
    family: str
    eps: float = 0.1
    type_mode: str = "ltm"            # placement_uniform | flat | size | ltm | online
    ltm: str = "S2_frozen"
    alpha: float = 1.0                # exponent on single-type weight (or on area for type_mode=size)
    beta: float = 1.0                 # exponent on boost
    use_single: bool = True
    use_boost: bool = True
    hard_priority: bool = False
    boost_max: float = 6.0
    anchor: bool = False
    select: str = "random"            # random | contact | table | look
    K: int = 8
    table: str = ""
    gamma: float = 1.0
    online: str = "softmax"           # softmax | thompson (type_mode == online)
    tau: float = 1.0
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


class Online:
    """Bandit-style type weights from the running mean S1 of boxes that contain the type (credit = final S1 of the box)."""

    def __init__(self, prior: float = 20.0, sd0: float = 4.0) -> None:
        self.n = 0; self.s = 0.0; self.s2 = 0.0
        self.nw: Counter = Counter(); self.sw: Counter = Counter()
        self.prior = prior; self.sd0 = sd0

    def effect(self, t: str) -> tuple[float, float]:
        nwt = self.nw[t]; n_wo = self.n - nwt
        if nwt == 0 or n_wo == 0:
            return 0.0, self.sd0
        m_w = self.sw[t] / nwt
        m_wo = (self.s - self.sw[t]) / n_wo
        sd = math.sqrt(max(self.s2 / self.n - (self.s / self.n) ** 2, 1e-6))
        shrink = nwt / (nwt + self.prior)
        return (m_w - m_wo) * shrink, sd * math.sqrt(1.0 / nwt + 1.0 / n_wo)

    def weights(self, types, rng, mode: str, tau: float) -> list[float]:
        out = []
        for t in types:
            e, se = self.effect(t)
            x = rng.gauss(e, se) if mode == "thompson" else e
            out.append(math.exp(max(min(x / tau, 30.0), -30.0)))
        return out

    def update(self, s1: float, types_present) -> None:
        self.n += 1; self.s += s1; self.s2 += s1 * s1
        for t in types_present:
            self.nw[t] += 1; self.sw[t] += s1


class Context:
    """Frozen knowledge shared by all variants: LTMs (as dicts) and placement tables. Built per process."""

    def __init__(self, ltms: dict, tables: dict) -> None:
        self.ltms = ltms
        self.tables = tables
        self._pol: dict = {}

    def policy(self, name: str, boost_max: float) -> Policy:
        key = (name, boost_max)
        if key not in self._pol:
            self._pol[key] = Policy.from_ltm(self.ltms[name], boost_clip=(1.0, boost_max))
        return self._pol[key]


def _choose_type(spec: Spec, ctx: Context, types, placed, rng, cost: Cost, online: Online | None):
    if spec.type_mode == "flat":
        return rng.choice(types)
    if spec.type_mode == "size":
        return rng.choices(types, weights=[len(PIECES[t]) ** spec.alpha for t in types])[0]
    if spec.type_mode == "online":
        return rng.choices(types, weights=online.weights(types, rng, spec.online, spec.tau))[0]
    pol = ctx.policy(spec.ltm, spec.boost_max)
    boost = pol.boosts(placed) if spec.use_boost else {}
    avail = {t: boost[t] for t in types if t in boost}
    if avail:
        cost.boost_steps += 1
    if spec.hard_priority and avail:
        cand = sorted(avail)
        return rng.choices(cand, weights=[avail[t] ** spec.beta for t in cand])[0]
    w = []
    for t in types:
        x = (pol.single_w.get(t, 1.0) ** spec.alpha) if spec.use_single else 1.0
        if t in avail:
            x *= avail[t] ** spec.beta
        w.append(x)
    return rng.choices(types, weights=w)[0]


def _choose_placement(spec: Spec, ctx: Context, cands, legal, occ, rng, cost: Cost):
    if spec.select == "random":
        return rng.choice(cands)      # same RNG use as trials.run_trial, so eps=0 placement_uniform reproduces the control exactly
    if len(cands) == 1:
        return cands[0]
    if spec.select == "contact":
        cost.cand_evals += len(cands)
        return max(cands, key=lambda p: (contact_score(p, occ), rng.random()))
    if spec.select == "table":
        tab = ctx.tables[spec.table]
        cost.cand_evals += len(cands)
        w = [tab.get(p.signature, 1.0) ** spec.gamma for p in cands]
        return rng.choices(cands, weights=w)[0]
    if spec.select == "look":
        pool = cands if len(cands) <= spec.K else rng.sample(cands, spec.K)
        best, best_key = None, None
        for p in pool:
            cost.cand_evals += 1
            cost.mask_ops += len(legal)
            key = (dead_cells_after(legal, occ, p.mask), -contact_score(p, occ), rng.random())
            if best_key is None or key < best_key:
                best, best_key = p, key
        return best
    raise ValueError(spec.select)


def run_trial(seed: int, trial_id: int, spec: Spec, ctx: Context, online: Online | None = None) -> dict:
    tseed = trial_seed(seed, trial_id)
    rng = random.Random(tseed)
    env = PackingEnv()
    placed: Counter = Counter()
    cost = Cost()
    while not env.terminal:
        legal = env.legal_placements()
        cost.enum_ops += N_ALL
        if not legal:
            break
        occ = env.mask
        if spec.eps > 0 and rng.random() < spec.eps:
            p = rng.choice(legal)
            cost.explore += 1
        else:
            pool = anchor_pool(occ, cost) if spec.anchor else legal
            if not pool:
                pool = legal
            if spec.type_mode == "placement_uniform":
                cands = pool
            else:
                by_type: dict = {}
                for q in pool:
                    by_type.setdefault(q.piece_type, []).append(q)
                types = sorted(by_type)
                t = _choose_type(spec, ctx, types, placed, rng, cost, online)
                cands = by_type[t]
            p = _choose_placement(spec, ctx, cands, legal, occ, rng, cost)
        env.step(Action.place_from(p))
        placed[p.piece_type] += 1
    empty = sum(1 for row in env.cells for cell in row if cell is None)
    s1 = N_CELLS - empty
    assert s1 == env.occupied
    att = env.placements_count
    if online is not None:
        online.update(s1, list(placed))
    return {"trial_id": trial_id, "S1": s1, "attempts": att, "S2": s1 / att if att else 0.0, "n_P": placed.get("P", 0),
            **cost.as_dict()}


def run_online_arm(seed: int, ids, spec: Spec, ctx: Context) -> list[dict]:
    on = Online()
    return [run_trial(seed, i, spec, ctx, on) for i in ids]