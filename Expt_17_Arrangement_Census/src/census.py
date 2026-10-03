"""Extract and match small connected arrangements. Read only.

A group is a few pieces already placed in a successful packing. Their cells
must be 4-connected. Absolute position is removed by subtracting the minimum
cell of the group. Frequency inside one trajectory does not increase support.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

from pieces import BOARD_SIZE, is_connected, placed_cells


def relative_pattern(group: list[tuple]) -> tuple | None:
    """Return a translation-normalised key, or None if the group is not a single connected patch."""
    cells: list[tuple[int, int]] = []
    for piece, rotation, x, y in group:
        cells.extend(placed_cells(piece, int(rotation), int(x), int(y)))
    if len(set(cells)) != len(cells):
        return None
    if not is_connected(cells):
        return None
    min_x = min(x for x, _y in cells)
    min_y = min(y for _x, y in cells)
    anchors = tuple(sorted(
        (piece, int(rotation), int(x) - min_x, int(y) - min_y)
        for piece, rotation, x, y in group
    ))
    rel_cells = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
    counts = tuple(sorted(Counter(piece for piece, _r, _x, _y in anchors).items()))
    return anchors, counts, rel_cells


def stage_name(occupied: int, early_below: int, middle_below: int) -> str:
    if occupied < early_below:
        return "early"
    if occupied < middle_below:
        return "middle"
    return "late"


class PatternTable:
    """Support is independent boxes and distinct inventories. The table does not place pieces."""

    def __init__(self) -> None:
        self.patterns: dict[tuple, dict] = {}
        self.extraction_checks = 0
        self.extraction_connected = 0
        self.boxes_seen = 0

    def observe_box(self, seed: int, task_id: str, inventory_key: tuple, stack: list[tuple], config) -> dict:
        self.boxes_seen += 1
        seen: set[tuple] = set()
        checks = 0
        connected = 0
        capped = False
        n = len(stack)
        for size in range(int(config.min_pieces), int(config.max_pieces) + 1):
            if size > n:
                continue
            for combo in combinations(range(n), size):
                if checks >= int(config.max_checks_per_box):
                    capped = True
                    break
                checks += 1
                group = [stack[i] for i in combo]
                key = relative_pattern(group)
                if key is None:
                    continue
                connected += 1
                if key in seen:
                    continue
                seen.add(key)
                rec = self.patterns.get(key)
                if rec is None:
                    anchors, counts, rel_cells = key
                    rec = {
                        "pieces": size,
                        "counts": dict(counts),
                        "anchors": anchors,
                        "cells": rel_cells,
                        "boxes": set(),
                        "inventories": set(),
                    }
                    self.patterns[key] = rec
                rec["boxes"].add((int(seed), str(task_id)))
                rec["inventories"].add(inventory_key)
            if capped:
                break
        self.extraction_checks += checks
        self.extraction_connected += connected
        return {"checks": checks, "connected_groups": connected, "unique_in_box": len(seen), "capped": capped}

    def freeze(self, min_inventories: int) -> list[dict]:
        frozen = []
        for key, rec in self.patterns.items():
            if len(rec["inventories"]) < int(min_inventories):
                continue
            frozen.append({
                "pieces": rec["pieces"],
                "counts": rec["counts"],
                "anchors": rec["anchors"],
                "cells": rec["cells"],
                "n_boxes": len(rec["boxes"]),
                "n_inventories": len(rec["inventories"]),
                "boxes": sorted(f"{seed}:{task}" for seed, task in rec["boxes"]),
            })
        frozen.sort(key=lambda item: (-item["n_inventories"], -item["n_boxes"], item["pieces"], str(item["anchors"])))
        return frozen


def _remaining(inventory: dict, prefix: list[tuple]) -> Counter:
    left: Counter = Counter({str(k): int(v) for k, v in inventory.items() if int(v)})
    for piece, _rotation, _x, _y in prefix:
        left[piece] -= 1
    return left


def _occupied(prefix: list[tuple]) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for piece, rotation, x, y in prefix:
        cells.update(placed_cells(piece, int(rotation), int(x), int(y)))
    return cells


def match_pattern(pattern: dict, occupied: set[tuple[int, int]], remaining: Counter) -> tuple[int, int]:
    """Return (checks, number of translations that fit). Does not modify the board."""
    checks = 1
    for piece, need in pattern["counts"].items():
        if remaining[piece] < int(need):
            return checks, 0
    fits = 0
    cells = pattern["cells"]
    for ox in range(BOARD_SIZE):
        for oy in range(BOARD_SIZE):
            checks += 1
            ok = True
            for dx, dy in cells:
                x, y = ox + dx, oy + dy
                checks += 1
                if x < 0 or y < 0 or x >= BOARD_SIZE or y >= BOARD_SIZE or (x, y) in occupied:
                    ok = False
                    break
            if ok:
                fits += 1
    return checks, fits


def scan_trajectory(stack: list[tuple], inventory: dict, patterns: list[dict], config) -> dict:
    """Legal-fit census along one completed primitive trajectory. No placement is committed."""
    stages = {"early": 0, "middle": 0, "late": 0}
    checks = 0
    events = 0
    patterns_hit: set[int] = set()
    earliest = {"early": None, "middle": None, "late": None}
    for t in range(len(stack) + 1):
        prefix = stack[:t]
        occupied = _occupied(prefix)
        remaining = _remaining(inventory, prefix)
        stage = stage_name(len(occupied), int(config.early_below), int(config.middle_below))
        for index, pattern in enumerate(patterns):
            cost, fits = match_pattern(pattern, occupied, remaining)
            checks += cost
            if fits:
                events += 1
                stages[stage] += 1
                patterns_hit.add(index)
                if earliest[stage] is None:
                    earliest[stage] = t
    return {
        "match_checks": checks,
        "fit_events": events,
        "patterns_with_fit": len(patterns_hit),
        "early_fits": stages["early"],
        "middle_fits": stages["middle"],
        "late_fits": stages["late"],
        "earliest_prefix": earliest,
    }
