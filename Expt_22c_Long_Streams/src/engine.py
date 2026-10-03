"""Fast numpy/bitmask engine for Expt-21 (same 10x10 box and 16-piece catalogue as Expt-1/20).

A *box* is one fresh 10x10 box. The box's handicap (the subset of piece types on offer) is part of the box, so the
same box id gives the same box to every policy (paired comparisons). Placements come from
mga.pieces.ALL_PLACEMENTS (canonical placements); every placement made here is replayable in
mga.environment.PackingEnv (tests do this).

Cell index = y*10+x. Padded arrays: index 100 = PAD (never occupied), index 101 = WALL (always occupied).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_E1 = Path(__file__).resolve().parents[2] / 'Expt_01_10x10_Packing' / 'code'
if str(_E1) not in sys.path:
    sys.path.insert(0, str(_E1))

from mga.pieces import ALL_PLACEMENTS, PIECE_TYPES

M64 = (1 << 64) - 1
N_PL = len(ALL_PLACEMENTS)
PAD, WALL = 100, 101
N_TYPES = len(PIECE_TYPES)
NONE_T = N_TYPES
TYPE_ID = {t: i for i, t in enumerate(PIECE_TYPES)}

PTYPE = np.array([TYPE_ID[p.piece_type] for p in ALL_PLACEMENTS], dtype=np.int64)
AREA = np.array([p.area for p in ALL_PLACEMENTS], dtype=np.int64)
BOUND = np.array([p.boundary_contacts for p in ALL_PLACEMENTS], dtype=np.int64)
LO = np.array([p.mask & M64 for p in ALL_PLACEMENTS], dtype=np.uint64)
HI = np.array([p.mask >> 64 for p in ALL_PLACEMENTS], dtype=np.uint64)
MASKS = [p.mask for p in ALL_PLACEMENTS]

_ORIENT_ID: dict[tuple, int] = {}
ORIENT = np.zeros(N_PL, dtype=np.int64)
for _k, _p in enumerate(ALL_PLACEMENTS):
    ORIENT[_k] = _ORIENT_ID.setdefault((_p.piece_type, _p.rotation), len(_ORIENT_ID))
N_ORIENT = len(_ORIENT_ID)


def _nbrs(i: int) -> list[int]:
    x, y = i % 10, i // 10
    out = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        out.append(ny * 10 + nx if 0 <= nx < 10 and 0 <= ny < 10 else WALL)
    return out


NB = np.array([_nbrs(i) for i in range(100)], dtype=np.int64)

_RR, _R2 = 0, 0
_ring_f, _ring2, _cpn, _cells = [], [], [], []
for _p in ALL_PLACEMENTS:
    own = {(x, y) for x, y in _p.cells}
    ring = sorted({(x + dx, y + dy) for x, y in own for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - own,
                  key=lambda c: (c[1], c[0]))
    ring_set = set(ring)
    ring2 = sorted({(x + dx, y + dy) for x, y in ring for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
                   - own - ring_set, key=lambda c: (c[1], c[0]))
    ring2 = [c for c in ring2 if 0 <= c[0] < 10 and 0 <= c[1] < 10]

    def idx(c):
        return c[1] * 10 + c[0] if 0 <= c[0] < 10 and 0 <= c[1] < 10 else WALL

    _ring_f.append([idx(c) for c in ring])
    _cpn.append([sum(1 for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)) if n in own)
                 for c in ring])
    _ring2.append([idx(c) for c in ring2])
    _cells.append(sorted(idx(c) for c in own))
_RR = max(len(r) for r in _ring_f)
_R2 = max(len(r) for r in _ring2)
RINGF = np.full((N_PL, _RR), PAD, dtype=np.int64)
CPN = np.zeros((N_PL, _RR), dtype=np.int64)
RING2 = np.full((N_PL, _R2), PAD, dtype=np.int64)
CELLS = np.full((N_PL, 7), PAD, dtype=np.int64)
for _k in range(N_PL):
    RINGF[_k, :len(_ring_f[_k])] = _ring_f[_k]
    CPN[_k, :len(_cpn[_k])] = _cpn[_k]
    RING2[_k, :len(_ring2[_k])] = _ring2[_k]
    CELLS[_k, :len(_cells[_k])] = _cells[_k]
IN_BOARD = RINGF < 100
BITW = (1 << np.arange(_RR, dtype=np.int64))
BITW2 = (1 << np.arange(_R2, dtype=np.int64))
BITW2 = (1 << np.arange(_R2, dtype=np.int64))


class Box:
    __slots__ = ("occ", "lo", "hi", "occ_arr", "placed", "types", "n", "allowed", "blocked", "budget")

    def __init__(self, allowed: np.ndarray | None = None, blocked: int = 0, budget: int = 10_000) -> None:
        """blocked = bitmask of obstacle cells (occupied from the start, never counted in S1); budget = max pieces."""
        self.occ = int(blocked)
        self.blocked = int(blocked)
        self.budget = int(budget)
        self.lo = np.uint64(self.occ & M64)
        self.hi = np.uint64(self.occ >> 64)
        self.occ_arr = np.zeros(102, dtype=bool)
        self.occ_arr[WALL] = True
        for i in range(100):
            if (self.occ >> i) & 1:
                self.occ_arr[i] = True
        self.placed: list[int] = []
        self.types: list[int] = []
        self.n = 0
        self.allowed = np.ones(N_TYPES, dtype=bool) if allowed is None else allowed

    @property
    def s1(self) -> int:
        """S1 = 100 - empty cells, where obstacle cells count as empty (they can never be filled)."""
        return (self.occ & ~self.blocked).bit_count()

    def legal(self) -> np.ndarray:
        if self.n >= self.budget:
            return np.empty(0, dtype=np.int64)
        idx = np.flatnonzero(((LO & self.lo) == 0) & ((HI & self.hi) == 0))
        return idx[self.allowed[PTYPE[idx]]]

    def place(self, i: int) -> None:
        self.occ |= MASKS[i]
        self.lo = np.uint64(self.occ & M64)
        self.hi = np.uint64(self.occ >> 64)
        self.occ_arr[CELLS[i][CELLS[i] < 100]] = True
        self.placed.append(int(i))
        self.types.append(int(PTYPE[i]))
        self.n += 1

    def copy(self) -> "Box":
        b = Box.__new__(Box)
        b.occ, b.lo, b.hi = self.occ, self.lo, self.hi
        b.occ_arr = self.occ_arr.copy()
        b.placed = list(self.placed)
        b.types = list(self.types)
        b.n = self.n
        b.allowed = self.allowed
        b.blocked, b.budget = self.blocked, self.budget
        return b

    def blocked_neighbours(self) -> np.ndarray:
        bn = np.zeros(102, dtype=np.int64)
        bn[:100] = self.occ_arr[NB].sum(axis=1)
        return bn


def features(box: Box, cand: np.ndarray, level: int = 2) -> dict:
    """Per-candidate local features, read from the board. They are inputs whose weights are learned, never rules.

    contact  edges touching the wall or occupied cells (wall edges + distinct occupied neighbour cells)
    p1       empty neighbour cells that become fully enclosed (4 blocked sides): 1-cell holes
    n3       empty neighbour cells left with 3 blocked sides (dead-end notches)
    sig1     (oriented piece, occupancy bits of the ring of neighbour cells, walls count as occupied)
    sig2     sig1 plus the occupancy bits of the second ring (distance-2 cells): a 5x5-style neighbourhood
    """
    ring = RINGF[cand]
    occr = box.occ_arr[ring]
    inb = IN_BOARD[cand]
    contact = BOUND[cand] + (occr & inb).sum(axis=1)
    empty_r = (~occr) & inb
    bl = box.blocked_neighbours()[ring] + CPN[cand]
    out = {"contact": contact, "p1": (empty_r & (bl >= 4)).sum(axis=1), "n3": (empty_r & (bl == 3)).sum(axis=1)}
    if level >= 1:
        out["sig1"] = ORIENT[cand] * (1 << _RR) + (occr * BITW).sum(axis=1)
        if level >= 2:
            out["sig2"] = out["sig1"] * 17 + box.occ_arr[RING2[cand]].sum(axis=1)
    return out


def natural_candidates(box: Box, level: int = 2):
    """Natural placing: legal placements (of the offered types) that touch the wall or an already placed piece.

    There is no row-major anchor and no preference among them; skipping layers means floating in open space,
    which is excluded. A legal placement with no contact can always be slid until it touches, so if any legal
    placement exists, a natural one exists.
    """
    legal = box.legal()
    if legal.size == 0:
        return legal, None
    f = features(box, legal, level)
    nat = f["contact"] > 0
    if nat.all():
        return legal, f
    cand = legal[nat]
    return cand, {k: v[nat] for k, v in f.items()}