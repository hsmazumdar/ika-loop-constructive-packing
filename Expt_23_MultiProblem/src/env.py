"""Variable-board, variable-catalogue packing environment (Expt 23, case study 1).

A Problem fixes: board H x W, blocked (obstacle) cells, a catalogue (indices into polyomino.POOL) and a piece budget
(14 in the capped condition, None = uncapped). The agent chooses piece AND placement at every step (unlimited supply).
S1 = number of non-obstacle cells covered at the end of the episode.
Natural placing (default) restricts the action set to legal placements that touch the wall, an obstacle or a placed piece.
The engine contains NO decision rule; contact / p1 / n3 are returned as raw features (as in Expt 21-22).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

import polyomino as PM


@dataclass(frozen=True)
class Problem:
    pid: str
    split: str
    H: int
    W: int
    blocked: tuple
    catalogue: tuple
    budget: int | None

    def spec(self) -> tuple:
        return (self.H, self.W, tuple(sorted(self.blocked)), tuple(sorted(self.catalogue)))

    def spec_hash(self) -> str:
        return hashlib.sha1(repr(self.spec()).encode()).hexdigest()[:12]

    def with_budget(self, budget):
        return Problem(self.pid, self.split, self.H, self.W, self.blocked, self.catalogue, budget)


class State:
    __slots__ = ("occ", "n", "filled")

    def __init__(self, occ, n=0, filled=0):
        self.occ, self.n, self.filled = occ, n, filled

    def copy(self):
        return State(self.occ.copy(), self.n, self.filled)


class Env:
    def __init__(self, prob: Problem) -> None:
        self.prob = prob
        H, W = prob.H, prob.W
        HW = H * W
        self.HW, self.PAD, self.WALL = HW, HW, HW + 1
        blocked = set(prob.blocked)
        cells_l, ring_l, cpn_l, bound_l, slot_l, ori_l = [], [], [], [], [], []
        oid = 0
        for slot, pidx in enumerate(prob.catalogue):
            for ori in PM.orientations(PM.POOL[pidx]):
                w, h = max(x for x, _ in ori) + 1, max(y for _, y in ori) + 1
                own0 = set(ori)
                ring0 = sorted({(x + dx, y + dy) for x, y in own0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - own0)
                for ty in range(H - h + 1):
                    for tx in range(W - w + 1):
                        cells = [(x + tx, y + ty) for x, y in ori]
                        ids = [y * W + x for x, y in cells]
                        if blocked and any(i in blocked for i in ids):
                            continue
                        own = set(cells)
                        ring = [(x + tx, y + ty) for x, y in ring0]
                        inb = [(x, y) for x, y in ring if 0 <= x < W and 0 <= y < H]
                        bound = sum(1 for x, y in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                                    if not (0 <= x + dx < W and 0 <= y + dy < H))
                        cpn = [sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in own) for x, y in inb]
                        cells_l.append(ids)
                        ring_l.append([y * W + x for x, y in inb])
                        cpn_l.append(cpn)
                        bound_l.append(bound)
                        slot_l.append(slot)
                        ori_l.append(oid)
                oid += 1
        n = len(cells_l)
        self.N = n
        L = max(len(c) for c in cells_l) if n else 1
        R = max(len(r) for r in ring_l) if n else 1
        self.CELLS = np.full((n, L), self.PAD, np.int32)
        self.RING = np.full((n, R), self.PAD, np.int32)
        self.CPN = np.zeros((n, R), np.int16)
        for k in range(n):
            self.CELLS[k, :len(cells_l[k])] = cells_l[k]
            self.RING[k, :len(ring_l[k])] = ring_l[k]
            self.CPN[k, :len(cpn_l[k])] = cpn_l[k]
        self.RING_OK = self.RING < HW
        self.BOUND = np.array(bound_l, np.int16)
        self.SLOT = np.array(slot_l, np.int16)
        self.ORIENT = np.array(ori_l, np.int32)
        self.AREA = (self.CELLS < HW).sum(axis=1).astype(np.int16)
        nb = np.full((HW, 4), self.WALL, np.int32)
        for i in range(HW):
            x, y = i % W, i // W
            for d, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    nb[i, d] = (y + dy) * W + x + dx
        self.NB = nb
        self.free_cells = HW - len(blocked)
        self.max_area = int(self.AREA.max()) if n else 0

    # ---- state -----------------------------------------------------------------------------------------------
    def new_state(self) -> State:
        occ = np.zeros(self.HW + 2, bool)
        occ[self.WALL] = True
        for b in self.prob.blocked:
            occ[b] = True
        return State(occ)

    def done(self, s: State) -> bool:
        return self.prob.budget is not None and s.n >= self.prob.budget

    def legal(self, s: State) -> np.ndarray:
        if self.done(s) or self.N == 0:
            return np.empty(0, np.int64)
        return np.flatnonzero(~s.occ[self.CELLS].any(axis=1))

    def place(self, s: State, i: int) -> None:
        c = self.CELLS[i]
        s.occ[c[c < self.HW]] = True
        s.n += 1
        s.filled += int(self.AREA[i])

    def blocked_neighbours(self, s: State) -> np.ndarray:
        bn = np.zeros(self.HW + 2, np.int16)
        bn[:self.HW] = s.occ[self.NB].sum(axis=1)
        return bn

    def features(self, s: State, cand: np.ndarray, bn=None) -> dict:
        """Raw per-candidate quantities (inputs, never rules): contact, p1 (new 1-cell holes), n3 (new 3-sided notches)."""
        ring = self.RING[cand]
        ok = self.RING_OK[cand]
        occr = s.occ[ring] & ok
        er = (~s.occ[ring]) & ok
        if bn is None:
            bn = self.blocked_neighbours(s)
        bl = bn[ring] + self.CPN[cand]
        return {"contact": self.BOUND[cand] + occr.sum(axis=1), "p1": (er & (bl >= 4)).sum(axis=1),
                "n3": (er & (bl == 3)).sum(axis=1)}

    def candidates(self, s: State, natural: bool = True):
        """Action set. natural=True: legal placements touching wall/obstacle/piece. Returns (cand, feats) or (empty, None)."""
        legal = self.legal(s)
        if legal.size == 0:
            return legal, None
        f = self.features(s, legal)
        if not natural:
            return legal, f
        nat = f["contact"] > 0
        if nat.all():
            return legal, f
        return legal[nat], {k: v[nat] for k, v in f.items()}

    def global_holes_notches(self, s: State):
        bn = self.blocked_neighbours(s)[:self.HW]
        emp = ~s.occ[:self.HW]
        return int((emp & (bn >= 4)).sum()), int((emp & (bn == 3)).sum())