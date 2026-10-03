"""Teacher solvers. Their cost is a separate ledger from agent evaluation.

The exact-cover search is a reference controller, labeled teacher experience.
It is not the common policy used at test time. Held-out inventories are never
passed to these functions by the corpus builder.
"""

from __future__ import annotations

import random
import time

from mga3.pieces import ALL_PLACEMENTS, FULL_MASK, PIECE_TYPES

BY_CELL: list[list] = [[] for _ in range(100)]
for _placement in ALL_PLACEMENTS:
    _mask = _placement.mask
    while _mask:
        _bit = _mask & -_mask
        _mask ^= _bit
        BY_CELL[_bit.bit_length() - 1].append(_placement)


def exact_cover(inventory: dict[str, int], seed: int, node_cap: int = 40000) -> dict:
    """Depth-first most-constrained search for a complete tiling of one inventory."""
    rng = random.Random(int(seed))
    counts = {t: int(inventory.get(t, 0)) for t in PIECE_TYPES}
    stack = []
    nodes = 0
    best = 0
    started = time.perf_counter()

    def search(mask: int) -> bool:
        nonlocal nodes, best
        filled = mask.bit_count()
        if filled > best:
            best = filled
        if mask == FULL_MASK:
            return True
        if nodes >= node_cap:
            return False
        empty = FULL_MASK ^ mask
        bits = []
        probe = empty
        while probe and len(bits) < 8:
            bit = probe & -probe
            probe ^= bit
            bits.append(bit.bit_length() - 1)
        best_cands = None
        for idx in bits:
            cands = [p for p in BY_CELL[idx] if counts[p.piece_type] > 0 and not (p.mask & mask)]
            if not cands:
                return False
            if best_cands is None or len(cands) < len(best_cands):
                best_cands = cands
                if len(cands) == 1:
                    break
        assert best_cands is not None
        order = list(best_cands)
        rng.shuffle(order)
        for placement in order[:16]:
            nodes += 1
            counts[placement.piece_type] -= 1
            stack.append(placement)
            if search(mask | placement.mask):
                return True
            stack.pop()
            counts[placement.piece_type] += 1
            if nodes >= node_cap:
                return False
        return False

    solved = search(0)
    placements = [
        {
            "type": p.piece_type,
            "rotation": p.rotation,
            "x": p.x,
            "y": p.y,
            "cells": [list(c) for c in p.cells],
        }
        for p in stack
    ] if solved else []
    return {
        "solved": bool(solved),
        "best_filled": int(best if not solved else FULL_MASK.bit_count()),
        "nodes": int(nodes),
        "seconds": time.perf_counter() - started,
        "placements": placements,
        "mask": int(FULL_MASK if solved else 0),
        "solver": "teacher_exact_cover",
    }
