"""Continuous-learning agent: STM episodes -> sleep (replay + dream) -> LTM tables -> softmax placement policy.

What is learned (all from outcomes, nothing hand-coded in the policy):
  score(candidate) = sum of LTM table weights over the active features of that candidate
  features: type (piece type), A (oriented piece x contact count x 1-cell holes x dead-end notches),
            pair (piece type x types already in the box), S1 (oriented piece x 3x3-style ring occupancy),
            trip (piece type x last two types placed), S2 (S1 context x second-ring occupied count).
  learning target per placement: advantage = (cells added from this step to the end of the box) - (running mean of
  that quantity at the same step index); each table learns the shrunk mean residual of the advantage.
The policy is softmax(score / tau) mixed with eps uniform, over *natural* placements only.
"""

from __future__ import annotations

import pickle

import numpy as np

import engine as E
from config import Cfg
from tables import HashTable

ALL_FEATS = ("type", "A", "pair", "S1", "trip", "S2")


class Episode:
    __slots__ = ("placed", "s1")

    def __init__(self, placed: list, s1: int) -> None:
        self.placed, self.s1 = list(placed), int(s1)


class Exp:
    """A batch of learning experiences (one per placement step) with the keys of every feature."""

    def __init__(self) -> None:
        self.t, self.G = [], []
        self.single = {k: [] for k in ("type", "A", "S1", "S2")}
        self.pk, self.po, self.pf = [], [], []
        self.tk, self.to = [], []
        self.n = 0

    def add(self, placed: list, s1_final: int, t0: int = 0) -> None:
        box = E.Box()
        cum = 0
        areas = [int(E.AREA[i]) for i in placed]
        total = sum(areas)
        for t, i in enumerate(placed):
            if t >= t0:
                f = E.features(box, np.array([i]), 2)
                typ = int(E.PTYPE[i])
                self.t.append(t)
                self.G.append(total - cum)
                self.single["type"].append(typ)
                self.single["A"].append(a_key(int(E.ORIENT[i]), int(f["contact"][0]), int(f["p1"][0]), int(f["n3"][0])))
                self.single["S1"].append(int(f["sig1"][0]))
                self.single["S2"].append(int(f["sig2"][0]))
                us = sorted(set(box.types))
                for u in us:
                    self.pk.append(min(typ, u) * 16 + max(typ, u))
                    self.po.append(self.n)
                    self.pf.append(1.0 / len(us))
                if box.n >= 2:
                    self.tk.append(trip_key(typ, box.types[-1], box.types[-2]))
                    self.to.append(self.n)
                self.n += 1
            box.place(i)
            cum += areas[t]

    def arrays(self) -> dict:
        return {"t": np.array(self.t, dtype=np.int64), "G": np.array(self.G, dtype=float),
                "single": {k: np.array(v, dtype=np.int64) for k, v in self.single.items()},
                "pk": np.array(self.pk, dtype=np.int64), "po": np.array(self.po, dtype=np.int64),
                "pf": np.array(self.pf), "tk": np.array(self.tk, dtype=np.int64),
                "to": np.array(self.to, dtype=np.int64), "n": self.n}


def a_key(orient, contact, p1, n3):
    return ((orient * 12 + min(contact, 11)) * 4 + min(p1, 3)) * 4 + min(n3, 3)


def trip_key(a, b, c):
    a, b, c = sorted((a, b, c))
    return (a * 16 + b) * 16 + c


class Memory:
    def __init__(self, cfg: Cfg) -> None:
        self.cfg = cfg
        self.tables: dict[str, HashTable] = {}
        self.active: list[str] = []
        self.stage = -1
        self.cap_extra = 0
        self.stm_mult = 1.0
        self.dream_mult = 1.0
        self.base = np.zeros(cfg.budget + 2)
        self.base_n = np.zeros(cfg.budget + 2)
        self.sleeps = 0
        self.grow_to(0)

    # ---- structure -------------------------------------------------------------------------------------------
    @property
    def level(self) -> int:
        return 2 if "S2" in self.active else (1 if "S1" in self.active else 0)

    def grow_to(self, stage: int) -> list[str]:
        name, feats, extra, stm_m, dream_m = self.cfg.stages[stage]
        self.stage = stage
        self.cap_extra += extra
        self.stm_mult, self.dream_mult = stm_m, dream_m
        new = []
        for f in feats:
            if f not in self.active:
                self.active.append(f)
                new.append(f)
        for f in self.active:
            bits = self.cfg.bits[f] + self.cap_extra
            if f in self.tables:
                self.tables[f].grow(bits)
            else:
                self.tables[f] = HashTable(bits, self.cfg.shrink_k)
        return new

    # ---- scoring -----------------------------------------------------------------------------------------------
    def _type_scores(self, box: E.Box) -> np.ndarray:
        out = np.zeros(E.N_TYPES)
        if "pair" in self.active and box.types:
            us = sorted(set(box.types))
            keys = np.array([[min(t, u) * 16 + max(t, u) for u in us] for t in range(E.N_TYPES)], dtype=np.int64)
            out += self.tables["pair"].get(keys.ravel()).reshape(keys.shape).mean(axis=1)
        if "trip" in self.active and box.n >= 2:
            a, b = box.types[-1], box.types[-2]
            keys = np.array([trip_key(t, a, b) for t in range(E.N_TYPES)], dtype=np.int64)
            out += self.tables["trip"].get(keys)
        return out

    def score(self, box: E.Box, cand: np.ndarray, f: dict) -> np.ndarray:
        s = np.zeros(cand.size)
        act = self.active
        if "type" in act:
            s += self.tables["type"].get(E.PTYPE[cand])
        if "A" in act:
            s += self.tables["A"].get(((E.ORIENT[cand] * 12 + np.minimum(f["contact"], 11)) * 4
                                       + np.minimum(f["p1"], 3)) * 4 + np.minimum(f["n3"], 3))
        if "S1" in act:
            s += self.tables["S1"].get(f["sig1"])
        if "S2" in act:
            s += self.tables["S2"].get(f["sig2"])
        if "pair" in act or "trip" in act:
            s += self._type_scores(box)[E.PTYPE[cand]]
        return s

    # ---- learning ----------------------------------------------------------------------------------------------
    def apply(self, x: dict, weight: float, count: bool, only: list[str] | None = None) -> None:
        if x["n"] == 0:
            return
        n = x["n"]
        pred = np.zeros(n)
        for name in self.active:
            tb = self.tables[name]
            if name in ("type", "A", "S1", "S2"):
                pred += tb.get(x["single"][name])
            elif name == "pair" and x["pk"].size:
                pred += np.bincount(x["po"], weights=tb.get(x["pk"]) * x["pf"], minlength=n)
            elif name == "trip" and x["tk"].size:
                pred += np.bincount(x["to"], weights=tb.get(x["tk"]), minlength=n)
        adv = x["G"] - self.base[x["t"]]
        e = (adv - pred) / len(self.active)
        for name in (only or self.active):
            tb = self.tables[name]
            if name in ("type", "A", "S1", "S2"):
                tb.update(x["single"][name], np.full(n, weight), e, np.full(n, weight if count else 0.0))
            elif name == "pair" and x["pk"].size:
                f = x["pf"] * weight
                tb.update(x["pk"], f, e[x["po"]], f if count else np.zeros_like(f))
            elif name == "trip" and x["tk"].size:
                f = np.full(x["tk"].size, weight)
                tb.update(x["tk"], f, e[x["to"]], f if count else np.zeros_like(f))

    def update_base(self, eps: list[Episode]) -> None:
        for ep in eps:
            cum = 0
            total = sum(int(E.AREA[i]) for i in ep.placed)
            for t, i in enumerate(ep.placed):
                g = total - cum
                self.base_n[t] += 1
                self.base[t] += max(1.0 / self.base_n[t], self.cfg.bl_rate) * (g - self.base[t])
                cum += int(E.AREA[i])

    def learn_online(self, ep: Episode) -> None:
        x = Exp()
        x.add(ep.placed, ep.s1)
        self.apply(x.arrays(), 1.0, True)
        self.update_base([ep])

    def sleep(self, stm: list[Episode], n_new: int, rng: np.random.Generator, tau: float, dream: bool) -> dict:
        cfg = self.cfg
        new = stm[-n_new:]
        old = stm[:-n_new] if len(stm) > n_new else []
        reh = [old[j] for j in rng.choice(len(old), min(cfg.rehearse, len(old)), replace=False)] if old else []
        xn, xr, xd = Exp(), Exp(), Exp()
        for ep in new:
            xn.add(ep.placed, ep.s1)
        for ep in reh:
            xr.add(ep.placed, ep.s1)
        n_dream = 0
        if dream:
            for _ in range(int(cfg.dream_ratio * self.dream_mult * n_new)):
                ep = stm[int(rng.integers(len(stm)))]
                cut = int(rng.integers(0, len(ep.placed)))
                box = play_box(self, rng, tau * cfg.dream_tau_mult, cfg.dream_eps, prefix=ep.placed[:cut])
                xd.add(box.placed, box.s1, t0=cut)
                n_dream += 1
        an, ar, ad = xn.arrays(), xr.arrays(), xd.arrays()
        for epoch in range(cfg.epochs):
            first = epoch == 0
            self.apply(an, 1.0, first)
            self.apply(ar, 0.5, False)
            self.apply(ad, cfg.dream_w, first)
        self.update_base(new)
        pruned = 0
        for tb in self.tables.values():
            tb.decay(cfg.decay)
            pruned += tb.prune(cfg.prune_n, cfg.prune_w, cfg.prune_occupancy)
        self.sleeps += 1
        return {"dreams": n_dream, "replayed": len(new) + len(reh), "pruned": pruned}

    def reconsolidate(self, stm: list[Episode], new_feats: list[str]) -> None:
        """After growth: fill the new tables from the whole STM so they start informed."""
        if not new_feats:
            return
        x = Exp()
        for ep in stm:
            x.add(ep.placed, ep.s1)
        a = x.arrays()
        for _ in range(self.cfg.epochs):
            self.apply(a, 1.0, _ == 0, only=new_feats)

    # ---- introspection -------------------------------------------------------------------------------------------
    def stats(self) -> dict:
        d = {k: t.stats() for k, t in self.tables.items()}
        return {"entries": int(sum(v["entries"] for v in d.values())), "slots": int(sum(v["size"] for v in d.values())),
                "per_table": d, "stage": self.stage, "active": list(self.active), "sleeps": self.sleeps}

    def summary(self) -> dict:
        from mga.pieces import PIECE_TYPES
        out = {"stats": self.stats(), "base": self.base.tolist()}
        tb = self.tables["type"]
        out["type_weights"] = {PIECE_TYPES[k]: float(tb.get(np.array([k]))[0]) for k in range(E.N_TYPES)}
        if "pair" in self.tables:
            t = self.tables["pair"]
            used = np.flatnonzero(t.keys >= 0)
            order = used[np.argsort(-t.w[used])]
            dec = lambda k: PIECE_TYPES[int(k) // 16] + "+" + PIECE_TYPES[int(k) % 16]
            out["pair_top"] = [(dec(t.keys[i]), float(t.w[i]), float(t.n[i])) for i in order[:10] if t.n[i] >= 5]
            out["pair_bottom"] = [(dec(t.keys[i]), float(t.w[i]), float(t.n[i])) for i in order[::-1][:10] if t.n[i] >= 5]
        return out

    def dump(self, path) -> None:
        with open(path, "wb") as fh:
            pickle.dump({"cfg": self.cfg.as_dict(), "stage": self.stage, "active": self.active,
                         "tables": {k: {"bits": t.bits, "keys": t.keys, "w": t.w, "n": t.n} for k, t in self.tables.items()},
                         "base": self.base}, fh)


def choose(s: np.ndarray, tau: float, eps: float, rng: np.random.Generator) -> int:
    n = s.size
    if n == 1:
        return 0
    if not s.any():
        return int(rng.integers(n))
    z = s / tau
    z -= z.max()
    p = np.exp(z)
    p /= p.sum()
    if eps > 0:
        p = (1 - eps) * p + eps / n
    return int(np.searchsorted(np.cumsum(p), rng.random() * 0.999999999))


def play_box(mem: Memory | None, rng: np.random.Generator, tau: float, eps: float, prefix: list | None = None,
             budget: int | None = None) -> E.Box:
    cfg = mem.cfg if mem is not None else Cfg()
    box = E.Box(budget=budget or cfg.budget)
    for i in prefix or ():
        box.place(i)
    lvl = mem.level if mem is not None else 0
    while True:
        cand, f = E.natural_candidates(box, lvl)
        if cand.size == 0:
            return box
        s = mem.score(box, cand, f) if mem is not None else np.zeros(cand.size)
        box.place(int(cand[choose(s, tau, eps, rng)]))


def hand_box(rng: np.random.Generator, budget: int, w_area: float = 2.0) -> E.Box:
    """Reference ONLY (never used by the learner): a hand-written contact/hole/area heuristic under the same handicap."""
    box = E.Box(budget=budget)
    while True:
        cand, f = E.natural_candidates(box, 0)
        if cand.size == 0:
            return box
        sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + w_area * E.AREA[cand] + rng.random(cand.size) * 0.5
        box.place(int(cand[int(np.argmax(sc))]))