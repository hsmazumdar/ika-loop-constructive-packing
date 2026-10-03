"""Constructed independent regions with assigned piece budgets (Test 1 experimental aid).

A region is carved from a random full tiling as the union of k edge-adjacent pieces. An
evaluation box embeds that region geometry and budget at a random translation and tiles the rest
of the board independently, so the whole inventory is new. Supplying the region and its budget
is an experimental aid, not learned decomposition.
"""

from __future__ import annotations

import random
import time

from pieces import ALL_PLACEMENTS, BOARD_SIZE, FULL_MASK, NEIGHBORS, PIECE_TYPES, bit_for, piece_area

_BY_CELL: list[list] = [[] for _ in range(BOARD_SIZE * BOARD_SIZE)]
for _p in ALL_PLACEMENTS:
    _m = _p.mask
    while _m:
        _b = _m & -_m
        _m ^= _b
        _BY_CELL[_b.bit_length() - 1].append(_p)


def fill_from(start_mask: int, rng: random.Random, deadline: float, start_counts: dict[str, int] | None = None,
              max_cells: int = 40, node_cap: int = 8000) -> list | None:
    active = set(rng.sample(list(PIECE_TYPES), k=rng.randint(4, 7)))
    counts = {t: 0 for t in PIECE_TYPES}
    for t, n in (start_counts or {}).items():
        counts[t] += int(n)
    out: list = []
    nodes = 0

    def search(mask: int) -> bool:
        nonlocal nodes
        if mask == FULL_MASK:
            return True
        if time.perf_counter() >= deadline or nodes >= node_cap:
            return False
        empty = FULL_MASK ^ mask
        bits = []
        probe = empty
        while probe and len(bits) < 8:
            b = probe & -probe
            probe ^= b
            bits.append(b.bit_length() - 1)
        best = None
        for idx in bits:
            cands = [
                p for p in _BY_CELL[idx]
                if p.piece_type in active and not (p.mask & mask)
                and counts[p.piece_type] * piece_area(p.piece_type) + p.area <= max_cells
            ]
            if not cands:
                return False
            if best is None or len(cands) < len(best):
                best = cands
                if len(cands) == 1:
                    break
        order = list(best)
        rng.shuffle(order)
        for p in order[:8]:
            nodes += 1
            counts[p.piece_type] += 1
            out.append(p)
            if search(mask | p.mask):
                return True
            out.pop()
            counts[p.piece_type] -= 1
            if time.perf_counter() >= deadline or nodes >= node_cap:
                return False
        return False

    if not search(int(start_mask)):
        return None
    return [(p.piece_type, p.rotation, p.x, p.y, p.cells) for p in out]


def _adjacent(a_cells, b_cells) -> bool:
    b = set(b_cells)
    for x, y in a_cells:
        for dx, dy in NEIGHBORS:
            if (x + dx, y + dy) in b:
                return True
    return False


def carve_region(tiling: list, rng: random.Random, k: int, min_cells: int, max_cells: int) -> dict | None:
    for _ in range(40):
        chosen = [rng.randrange(len(tiling))]
        while len(chosen) < k:
            options = [
                i for i in range(len(tiling))
                if i not in chosen and any(_adjacent(tiling[i][4], tiling[j][4]) for j in chosen)
            ]
            if not options:
                break
            chosen.append(rng.choice(options))
        if len(chosen) < k:
            continue
        cells = [c for i in chosen for c in tiling[i][4]]
        if not (min_cells <= len(cells) <= max_cells):
            continue
        counts: dict[str, int] = {}
        for i in chosen:
            counts[tiling[i][0]] = counts.get(tiling[i][0], 0) + 1
        return {
            "cells": sorted(cells),
            "placements": [tiling[i][:4] for i in chosen],
            "budget": counts,
        }
    return None


def embed_region(geo: tuple, budget: dict[str, int], rng: random.Random, deadline: float) -> dict | None:
    w = max(x for x, _ in geo) + 1
    h = max(y for _, y in geo) + 1
    for _ in range(30):
        if time.perf_counter() >= deadline:
            return None
        ox = rng.randrange(0, BOARD_SIZE - w + 1)
        oy = rng.randrange(0, BOARD_SIZE - h + 1)
        cells = [(x + ox, y + oy) for x, y in geo]
        mask = 0
        for x, y in cells:
            mask |= bit_for(x, y)
        rest = fill_from(mask, rng, min(deadline, time.perf_counter() + 2.0), start_counts=budget)
        if rest is None:
            continue
        counts = {t: 0 for t in PIECE_TYPES}
        for t, n in budget.items():
            counts[t] += n
        for rec in rest:
            counts[rec[0]] += 1
        return {"region_cells": sorted(cells), "counts": counts, "rest": [r[:4] for r in rest]}
    return None
