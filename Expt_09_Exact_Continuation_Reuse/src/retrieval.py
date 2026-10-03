"""Bounded retrieval and legal-site search. Neutral features only."""

from __future__ import annotations

import math
import random

from pieces import ALL_PLACEMENTS, PIECE_TYPES, Placement

from memory import LearnedOperation


def state_features(env) -> tuple[float, ...]:
    counts = [float(env.inventory.counts.get(name, 0)) for name in PIECE_TYPES]
    total = sum(counts) or 1.0
    hist = [c / total for c in counts]
    occupancy = env.occupied / 100.0
    rows = []
    cols = [0] * 10
    border_empty = 0
    border = 0
    for y in range(10):
        row = 0
        for x in range(10):
            filled = (env.mask >> (y * 10 + x)) & 1
            row += filled
            cols[x] += filled
            if x == 0 or y == 0 or x == 9 or y == 9:
                border += 1
                if not filled:
                    border_empty += 1
        rows.append(row / 10.0)
    col_fill = [c / 10.0 for c in cols]
    n_comp, max_comp = _empty_summary(env.mask)
    return tuple(hist + [occupancy] + rows + col_fill + [n_comp / 100.0, max_comp / 100.0, border_empty / border])


def _empty_summary(mask: int) -> tuple[int, int]:
    remaining = ((1 << 100) - 1) ^ (mask & ((1 << 100) - 1))
    n_comp = 0
    max_comp = 0
    while remaining:
        start = (remaining & -remaining).bit_length() - 1
        stack = [start]
        remaining &= ~(1 << start)
        size = 0
        while stack:
            idx = stack.pop()
            size += 1
            x, y = idx % 10, idx // 10
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= 10 or ny >= 10:
                    continue
                bit = 1 << (ny * 10 + nx)
                if remaining & bit:
                    remaining &= ~bit
                    stack.append(ny * 10 + nx)
        n_comp += 1
        if size > max_comp:
            max_comp = size
    return n_comp, max_comp


def cosine(left, right) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = ll = rr = 0.0
    for a, b in zip(left, right):
        dot += a * b
        ll += a * a
        rr += b * b
    if ll <= 0.0 or rr <= 0.0:
        return 0.0
    return dot / math.sqrt(ll * rr)


_SHAPE_INDEX: dict[tuple, list[Placement]] = {}
for _placement in ALL_PLACEMENTS:
    _norm = tuple(sorted((x - _placement.x, y - _placement.y) for x, y in _placement.cells))
    _SHAPE_INDEX.setdefault((_placement.piece_type, _norm), []).append(_placement)


def retrieve(ops: list[LearnedOperation], features, rng: random.Random, pool: int, top_k: int):
    if not ops:
        return [], 0
    chosen = list(ops)
    if len(chosen) > pool:
        rng.shuffle(chosen)
        chosen = chosen[:pool]
    scored = [(op, cosine(features, op.context)) for op in chosen]
    scored.sort(key=lambda item: (-item[1], -item[0].utility, item[0].op_id))
    return scored[:top_k], len(chosen)


def macro_fits(env, steps: list[dict]) -> bool:
    mask = env.mask
    counts = dict(env.inventory.counts)
    for step in steps:
        bit = 0
        for x, y in step["cells"]:
            if x < 0 or y < 0 or x >= 10 or y >= 10:
                return False
            b = 1 << (y * 10 + x)
            if bit & b or mask & b:
                return False
            bit |= b
        if counts.get(step["type"], 0) <= 0:
            return False
        counts[step["type"]] -= 1
        mask |= bit
    return True


def translate_steps(steps: list[dict], ox: int, oy: int) -> list[dict]:
    out = []
    for step in steps:
        cells = tuple(sorted((x + ox, y + oy) for x, y in step["cells"]))
        out.append({"type": step["type"], "cells": cells})
    return out


def first_legal_site(op: LearnedOperation, env, rng: random.Random, anchor_cap: int) -> tuple[list[dict] | None, int]:
    from miner import rotate_steps

    examined = 0
    order = list(range(4))
    rng.shuffle(order)
    for k in order:
        turned = rotate_steps(op.steps, k)
        first = turned[0]
        cells = [tuple(c) for c in first["cells"]]
        min_x = min(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        norm = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
        anchors = list(_SHAPE_INDEX.get((first["type"], norm), []))
        rng.shuffle(anchors)
        for placement in anchors:
            if examined >= anchor_cap:
                return None, examined
            examined += 1
            ox = placement.x - min_x
            oy = placement.y - min_y
            placed = translate_steps(turned, ox, oy)
            if macro_fits(env, placed):
                return placed, examined
    return None, examined
