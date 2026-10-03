"""Read-only legal placement enumeration. Does not consume the primitive RNG."""

from __future__ import annotations

import json

from miner import rotate_steps
from retrieval import _SHAPE_INDEX, macro_fits, translate_steps


def leaf_demand(op) -> dict[str, int]:
    demand: dict[str, int] = {}
    for step in op.steps:
        demand[step["type"]] = demand.get(step["type"], 0) + 1
    return demand


def inventory_compatible(op, env) -> bool:
    return env.inventory.fits_multiset(leaf_demand(op))


def action_key(placed: list[dict]) -> str:
    payload = [(s["type"], [list(c) for c in s["cells"]]) for s in placed]
    return json.dumps(payload, separators=(",", ":"))


def enumerate_legal(op, env, max_candidates: int) -> dict:
    """All distinct legal placements, or a deterministic prefix if capped."""
    examined = 0
    legal = []
    seen: set[str] = set()
    if not inventory_compatible(op, env):
        return {"compatible": False, "n_legal": 0, "examined": 0, "incomplete": False, "placements": []}
    for k in range(4):
        turned = rotate_steps(op.steps, k)
        first = turned[0]
        cells = [tuple(c) for c in first["cells"]]
        min_x = min(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        norm = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
        anchors = list(_SHAPE_INDEX.get((first["type"], norm), []))
        anchors.sort(key=lambda p: (p.y, p.x, p.rotation))
        for placement in anchors:
            examined += 1
            ox = placement.x - min_x
            oy = placement.y - min_y
            placed = translate_steps(turned, ox, oy)
            key = action_key(placed)
            if key in seen:
                continue
            if not macro_fits(env, placed):
                continue
            seen.add(key)
            legal.append({"rotation": k, "ox": ox, "oy": oy, "site": placed, "action_key": key})
    legal.sort(key=lambda rec: rec["action_key"])
    incomplete = len(legal) > int(max_candidates)
    if incomplete:
        legal = legal[: int(max_candidates)]
    return {
        "compatible": True,
        "n_legal": len(legal),
        "n_legal_uncapped": len(seen),
        "examined": examined,
        "incomplete": incomplete,
        "placements": legal,
    }
