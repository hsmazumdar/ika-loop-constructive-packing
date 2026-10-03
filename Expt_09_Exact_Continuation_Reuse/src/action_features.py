"""Inexpensive pre-commitment features of one legal placement. No remaining-solve."""

from __future__ import annotations

from pieces import PIECE_TYPES
from ranker import RANK_NAMES, rank_vector

ACTION_EXTRA = (
    "rotation",
    "anchor_x",
    "anchor_y",
    "centroid_x",
    "centroid_y",
    "bbox_w",
    "bbox_h",
    "contact_frac",
    "empty_adj_frac",
    "boundary_frac",
    "local_fill",
    "n_cells",
)
ACTION_NAMES = RANK_NAMES + ACTION_EXTRA


def placement_geometry(site: list[dict]) -> dict:
    cells = [tuple(c) for step in site for c in step["cells"]]
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    first = [tuple(c) for c in site[0]["cells"]]
    ax = min(x for x, _ in first)
    ay = min(y for _, y in first)
    return {
        "cells": cells,
        "n_cells": len(cells),
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "anchor_x": ax,
        "anchor_y": ay,
        "centroid_x": sum(xs) / len(xs),
        "centroid_y": sum(ys) / len(ys),
        "bbox_w": max_x - min_x + 1,
        "bbox_h": max_y - min_y + 1,
    }


def local_free_space(env, geo: dict) -> tuple[list[float], int]:
    """Contact, empty adjacency, boundary, and fill in the bbox expanded by 1. Counts inspected cells."""
    occupied = set()
    mask = env.mask
    for i in range(100):
        if (mask >> i) & 1:
            occupied.add((i % 10, i // 10))
    placed = set(geo["cells"])
    checks = 0
    contact = empty_adj = boundary = 0
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    seen_adj = set()
    for x, y in placed:
        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy
            if (nx, ny) in placed:
                continue
            if not (0 <= nx < 10 and 0 <= ny < 10):
                boundary += 1
                continue
            if (nx, ny) in seen_adj:
                continue
            seen_adj.add((nx, ny))
            checks += 1
            if (nx, ny) in occupied:
                contact += 1
            else:
                empty_adj += 1
    x0 = max(0, geo["min_x"] - 1)
    x1 = min(9, geo["max_x"] + 1)
    y0 = max(0, geo["min_y"] - 1)
    y1 = min(9, geo["max_y"] + 1)
    local_n = filled = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) in placed:
                continue
            checks += 1
            local_n += 1
            if (x, y) in occupied:
                filled += 1
    denom_adj = max(1, contact + empty_adj + boundary)
    return [
        contact / denom_adj,
        empty_adj / denom_adj,
        boundary / max(1, 4 * geo["n_cells"]),
        (filled / local_n) if local_n else 0.0,
        geo["n_cells"] / 20.0,
    ], checks


def infer_rotation(site: list[dict]) -> int:
    """Rotation index of the first step relative to the operation's stored first-step cells, if provided on the rec."""
    return int(site[0].get("rotation", 0) or 0) % 4


def action_vector(occupied, remaining: dict, actions_used, undos, op, score, op_area, site, env, rotation: int) -> tuple[list[float], int]:
    context = rank_vector(
        occupied, remaining, actions_used, undos, len(op.steps), op.depth, score, op.depth > 1, op_area
    )
    geo = placement_geometry(site)
    local, checks = local_free_space(env, geo)
    extra = [
        float(rotation) / 3.0,
        geo["anchor_x"] / 9.0,
        geo["anchor_y"] / 9.0,
        geo["centroid_x"] / 9.0,
        geo["centroid_y"] / 9.0,
        geo["bbox_w"] / 10.0,
        geo["bbox_h"] / 10.0,
        *local,
    ]
    return context + extra, checks


def context_vector(occupied, remaining: dict, actions_used, undos, op, score, op_area) -> list[float]:
    return rank_vector(
        occupied, remaining, actions_used, undos, len(op.steps), op.depth, score, op.depth > 1, op_area
    )


def unused_piece_types() -> tuple[str, ...]:
    return PIECE_TYPES
