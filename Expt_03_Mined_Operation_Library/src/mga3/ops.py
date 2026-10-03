"""Canonical operations. Rotations are allowed. Reflections are not."""

from __future__ import annotations

import hashlib
import json

from mga3.pieces import PIECES, is_connected, orientation


def _rot_point(x: int, y: int, k: int) -> tuple[int, int]:
    for _ in range(k % 4):
        x, y = -y, x
    return x, y


def rotate_steps(steps: list[dict], k: int) -> list[dict]:
    rotated = []
    for step in steps:
        rotated.append(
            {
                "type": step["type"],
                "cells": [_rot_point(int(x), int(y), k) for x, y in step["cells"]],
            }
        )
    flat = [c for step in rotated for c in step["cells"]]
    min_x = min(x for x, _ in flat)
    min_y = min(y for _, y in flat)
    out = []
    for step in rotated:
        cells = tuple(sorted((x - min_x, y - min_y) for x, y in step["cells"]))
        out.append({"type": step["type"], "cells": cells})
    return out


def steps_from_absolute(placements: list[dict]) -> list[dict]:
    flat = [tuple(c) for p in placements for c in p["cells"]]
    min_x = min(x for x, _ in flat)
    min_y = min(y for _, y in flat)
    steps = []
    for p in placements:
        cells = tuple(sorted((int(x) - min_x, int(y) - min_y) for x, y in p["cells"]))
        steps.append({"type": p["type"], "cells": cells})
    return steps


def canonical_form(steps: list[dict]) -> tuple[list[dict], int, str]:
    best: str | None = None
    best_steps: list[dict] | None = None
    best_k = 0
    for k in range(4):
        turned = rotate_steps(steps, k)
        payload = json.dumps(turned, separators=(",", ":"))
        if best is None or payload < best:
            best = payload
            best_steps = turned
            best_k = k
    assert best is not None and best_steps is not None
    return best_steps, best_k, best


def operation_id(canonical: str) -> str:
    return "op_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def inventory_demand(steps: list[dict]) -> dict[str, int]:
    demand: dict[str, int] = {}
    for step in steps:
        demand[step["type"]] = demand.get(step["type"], 0) + 1
    return demand


def footprint_cells(steps: list[dict]) -> list[tuple[int, int]]:
    return [tuple(c) for step in steps for c in step["cells"]]


def rectangle_geometry(steps: list[dict]) -> dict:
    cells = footprint_cells(steps)
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    width = max(xs) - min(xs) + 1
    height = max(ys) - min(ys) + 1
    unique = len(set(cells))
    filled = unique == len(cells) and unique == width * height
    rectangular = bool(filled and width >= 2 and height >= 2 and len(steps) >= 2)
    return {
        "width": width,
        "height": height,
        "area": unique,
        "filled": filled,
        "rectangular": rectangular,
    }


def connected_steps(steps: list[dict]) -> bool:
    cells = footprint_cells(steps)
    if len(cells) != len(set(cells)):
        return False
    return is_connected(cells)


def placement_params(piece_type: str, abs_cells: list[tuple[int, int]] | tuple) -> tuple[int, int, int] | None:
    rel = tuple(sorted(tuple(c) for c in abs_cells))
    min_x = min(x for x, _ in rel)
    min_y = min(y for _, y in rel)
    norm = tuple(sorted((x - min_x, y - min_y) for x, y in rel))
    for k in range(4):
        if orientation(PIECES[piece_type], k) == norm:
            return k, min_x, min_y
    return None


def translate_steps(steps: list[dict], ox: int, oy: int) -> list[dict]:
    out = []
    for step in steps:
        cells = tuple(sorted((x + ox, y + oy) for x, y in step["cells"]))
        out.append({"type": step["type"], "cells": cells})
    return out


def reflected_canonical(steps: list[dict]) -> str:
    """Left-right reflection, used only to show it is not in the rotation set."""
    flat_x = [x for step in steps for x, _ in step["cells"]]
    max_x = max(flat_x)
    reflected = []
    for step in steps:
        cells = tuple(sorted((max_x - x, y) for x, y in step["cells"]))
        reflected.append({"type": step["type"], "cells": cells})
    _, _, text = canonical_form(reflected)
    return text
