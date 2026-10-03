"""Cheap bitmask helpers and cost accounting for placement-level guidance.

Cost model (reported per box, in "units"):
  enum_ops   3636 per call to env.legal_placements(): the environment's own enumeration. Every arm pays it, control included.
  mask_ops   one per bitmask test the strategy itself makes (anchor search, lookahead filtering of the legal list).
  cand_evals one per candidate placement the strategy scores (contact score, lookahead, learned-table weight).
Extra compute of a strategy = mask_ops + cand_evals (what it adds on top of the uniform control). Weight arithmetic over the
<=16 piece types per step is not counted.
"""

from __future__ import annotations

from mga.pieces import ALL_PLACEMENTS, FULL_MASK, N_CELLS, placements_covering

N_ALL = len(ALL_PLACEMENTS)
_COVER: dict[int, tuple] = {}


class Cost:
    __slots__ = ("enum_ops", "mask_ops", "cand_evals", "explore", "boost_steps", "steps")

    def __init__(self) -> None:
        self.enum_ops = self.mask_ops = self.cand_evals = self.explore = self.boost_steps = self.steps = 0

    def as_dict(self) -> dict:
        return {"enum_ops": self.enum_ops, "mask_ops": self.mask_ops, "cand_evals": self.cand_evals,
                "n_explore_steps": self.explore, "n_boost_steps": self.boost_steps}


def cover(index: int) -> tuple:
    c = _COVER.get(index)
    if c is None:
        c = _COVER[index] = placements_covering(index)
    return c


def contact_score(p, occ: int) -> int:
    """Edge contacts of the placement with the wall or with occupied cells (neighbour cells are counted once per cell)."""
    return p.boundary_contacts + (p.neighbor_mask & occ).bit_count()


def dead_cells(legal, occ: int) -> int:
    """Empty cells that no legal placement can ever cover (they stay empty for the rest of the box)."""
    union = 0
    for p in legal:
        union |= p.mask
    return (FULL_MASK & ~union & ~occ).bit_count()


def dead_cells_after(legal, occ: int, cand_mask: int) -> int:
    """Dead cells after also placing a piece with mask `cand_mask`. `legal` is the current legal list."""
    union = 0
    for p in legal:
        if not (p.mask & cand_mask):
            union |= p.mask
    return (FULL_MASK & ~union & ~(occ | cand_mask)).bit_count()


def anchor_pool(occ: int, cost: Cost) -> list:
    """Legal placements covering the first (row-major) empty cell that any legal placement can cover."""
    for idx in range(N_CELLS):
        if (occ >> idx) & 1:
            continue
        cands = cover(idx)
        cost.mask_ops += len(cands)
        pool = [p for p in cands if not (p.mask & occ)]
        if pool:
            return pool
    return []