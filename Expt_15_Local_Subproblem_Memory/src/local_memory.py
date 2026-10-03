"""Local subproblem memory: how to fill a bounded free region with a specified piece multiset.

An entry records the region's free-cell geometry (translation-normalised), the consumed piece
multiset, relative placements, and measured acquisition cost. An entry matches when the region
geometry is identical and its multiset is available; the rest of the board and the unused
inventory may differ. No transformations, no hierarchy, no learned gate.

Region detection here is an engineered flood fill over free cells. It is billed and is not
learned decomposition.
"""

from __future__ import annotations

from environment import Action, PackingEnv
from inventory import Inventory
from pieces import ALL_PLACEMENTS, BOARD_SIZE, FULL_MASK, NEIGHBORS, PIECE_TYPES, bit_for, cell_coords, placed_cells

_COVER: list[list[int]] = [[] for _ in range(BOARD_SIZE * BOARD_SIZE)]
for _i, _p in enumerate(ALL_PLACEMENTS):
    _m = _p.mask
    while _m:
        _b = _m & -_m
        _m ^= _b
        _COVER[_b.bit_length() - 1].append(_i)


def mask_cells(mask: int) -> list[tuple[int, int]]:
    out = []
    m = int(mask)
    while m:
        b = m & -m
        m ^= b
        out.append(cell_coords(b.bit_length() - 1))
    return out


def geometry_key(cells) -> tuple:
    """Translation-normalised free-cell geometry."""
    cells = list(cells)
    ox = min(x for x, _ in cells)
    oy = min(y for _, y in cells)
    return tuple(sorted((x - ox, y - oy) for x, y in cells))


def region_origin(cells) -> tuple[int, int]:
    cells = list(cells)
    return min(x for x, _ in cells), min(y for _, y in cells)


def counts_key(counts: dict[str, int]) -> tuple[int, ...]:
    return tuple(int(counts.get(t, 0)) for t in PIECE_TYPES)


def _flood(start: tuple[int, int], occupied_mask: int, limit: int, seen: set) -> tuple[list[tuple[int, int]], int, bool]:
    """Flood free cells from start. Stops once size exceeds limit. Returns (cells, visited, bounded)."""
    stack = [start]
    comp = []
    visited = 0
    local = {start}
    while stack:
        x, y = stack.pop()
        visited += 1
        comp.append((x, y))
        if len(comp) > limit:
            seen.update(local)
            return comp, visited, False
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
                continue
            if occupied_mask & bit_for(nx, ny):
                continue
            if (nx, ny) in local:
                continue
            local.add((nx, ny))
            stack.append((nx, ny))
    seen.update(local)
    return comp, visited, True


def regions_near(occupied_mask: int, placed: list[tuple[int, int]], min_size: int, max_size: int) -> tuple[list[list[tuple[int, int]]], int]:
    """Bounded free components adjacent to the last placement. Cost = free cells visited."""
    seeds = []
    for x, y in placed:
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and not (occupied_mask & bit_for(nx, ny)):
                seeds.append((nx, ny))
    seen: set = set()
    out = []
    cost = 0
    for s in seeds:
        if s in seen:
            continue
        comp, visited, bounded = _flood(s, occupied_mask, max_size, seen)
        cost += visited
        if bounded and min_size <= len(comp) <= max_size:
            out.append(comp)
    return out, cost


def all_regions(occupied_mask: int, min_size: int, max_size: int) -> tuple[list[list[tuple[int, int]]], int]:
    seen: set = set()
    out = []
    cost = 0
    free = FULL_MASK ^ int(occupied_mask)
    for cell in mask_cells(free):
        if cell in seen:
            continue
        comp, visited, bounded = _flood(cell, occupied_mask, max_size, seen)
        cost += visited
        if bounded and min_size <= len(comp) <= max_size:
            out.append(comp)
    return out, cost


class LocalMemory:
    def __init__(self) -> None:
        self.by_geometry: dict[tuple, list[dict]] = {}
        self.n_entries = 0
        self.n_duplicate = 0
        self.frozen = False
        self.growth: list[int] = []

    def add(self, region_cells, placements: list[tuple], source: str, acquisition_cost: int) -> int:
        """First write per (geometry, multiset). Returns insertion cost (1 probe + 1 if written)."""
        if self.frozen:
            return 0
        geo = geometry_key(region_cells)
        ox, oy = region_origin(region_cells)
        counts: dict[str, int] = {}
        rel = []
        for piece, rotation, x, y in placements:
            counts[piece] = counts.get(piece, 0) + 1
            rel.append((piece, int(rotation), int(x) - ox, int(y) - oy))
        ck = counts_key(counts)
        bucket = self.by_geometry.setdefault(geo, [])
        if any(e["counts_key"] == ck for e in bucket):
            self.n_duplicate += 1
            return 1
        bucket.append(
            {
                "counts": counts,
                "counts_key": ck,
                "placements": rel,
                "source": source,
                "acquisition_cost": int(acquisition_cost),
                "n_cells": len(geo),
            }
        )
        self.n_entries += 1
        return 2

    def lookup(self, region_cells, available: dict[str, int]) -> tuple[dict | None, int, int]:
        """Returns (entry, lookup_cost, availability_checks). First stored available entry wins."""
        bucket = self.by_geometry.get(geometry_key(region_cells))
        if not bucket:
            return None, 1, 0
        checks = 0
        for entry in bucket:
            checks += 1
            if all(int(available.get(t, 0)) >= n for t, n in entry["counts"].items()):
                return entry, 1, checks
        return None, 1, checks

    def freeze(self) -> None:
        self.frozen = True

    def n_geometries(self) -> int:
        return len(self.by_geometry)

    def bytes(self) -> int:
        return sum(16 + 8 * e["n_cells"] + 16 * len(e["placements"]) for b in self.by_geometry.values() for e in b)


def place_entry(env: PackingEnv, region_cells, entry: dict, ledger) -> dict:
    """Validate each translated placement, then commit. Stops before any illegal PLACE."""
    ox, oy = region_origin(region_cells)
    region = set(region_cells)
    executed = 0
    for piece, rotation, dx, dy in entry["placements"]:
        ledger.charge("validation", 1)
        cells = placed_cells(piece, rotation, dx + ox, dy + oy)
        if not env.inventory.can_take(piece) or any(c not in region for c in cells) or not env._can_place_cells(cells):
            return {"ok": False, "executed": executed}
        if env.terminal:
            return {"ok": False, "executed": executed}
        env.step(Action.place(piece, rotation, dx + ox, dy + oy))
        executed += 1
    return {"ok": True, "executed": executed}


def solve_region(region_cells, budget: dict[str, int], node_cap: int = 20000) -> tuple[list[tuple] | None, int]:
    """Exact cover of the region using only the budget. Cost = candidate placements examined.

    Deterministic depth-first search over the first uncovered cell. This is the region-level
    search that local memory is meant to replace.
    """
    region_mask = 0
    for x, y in region_cells:
        region_mask |= bit_for(x, y)
    counts = {t: int(budget.get(t, 0)) for t in PIECE_TYPES}
    stack: list[int] = []
    evals = 0

    def first_free(mask: int) -> int | None:
        rest = region_mask & ~mask
        if not rest:
            return None
        b = rest & -rest
        return b.bit_length() - 1

    def search(mask: int) -> bool:
        nonlocal evals
        idx = first_free(mask)
        if idx is None:
            return True
        for pi in _COVER[idx]:
            if evals >= node_cap:
                return False
            evals += 1
            p = ALL_PLACEMENTS[pi]
            if counts[p.piece_type] <= 0:
                continue
            if p.mask & ~region_mask or p.mask & mask:
                continue
            counts[p.piece_type] -= 1
            stack.append(pi)
            if search(mask | p.mask):
                return True
            stack.pop()
            counts[p.piece_type] += 1
        return False

    ok = search(0)
    if not ok:
        return None, evals
    return [(ALL_PLACEMENTS[i].piece_type, ALL_PLACEMENTS[i].rotation, ALL_PLACEMENTS[i].x, ALL_PLACEMENTS[i].y) for i in stack], evals


def extract_entries(inventory: dict, stack: list[tuple], min_size: int, max_size: int, census: dict | None = None) -> tuple[list[dict], int]:
    """From a completed trajectory, find bounded free regions later filled exactly by pieces inside them.

    Cost = free cells visited by detection + one check per (region, later placement).
    census, if given, accumulates n_regions, n_with_inside_piece, covered_cells, region_cells,
    n_exact, and placements_left_hist (placements remaining when each region first appeared).
    """
    env = PackingEnv(budget=10**6, inventory=Inventory(dict(inventory)))
    masks = []
    cell_sets = []
    for piece, rotation, x, y in stack:
        cells = placed_cells(piece, rotation, x, y)
        cell_sets.append(set(cells))
        m = 0
        for cx, cy in cells:
            m |= bit_for(cx, cy)
        masks.append(m)
    found: list[dict] = []
    seen_regions: set = set()
    cost = 0
    occupied = 0
    for t in range(len(stack) + 1):
        if t > 0:
            occupied |= masks[t - 1]
        regions, c = all_regions(occupied, min_size, max_size)
        cost += c
        for comp in regions:
            key = tuple(sorted(comp))
            if key in seen_regions:
                continue
            seen_regions.add(key)
            region = set(comp)
            inside = []
            covered = set()
            for j in range(t, len(stack)):
                cost += 1
                if cell_sets[j] <= region:
                    inside.append(stack[j])
                    covered |= cell_sets[j]
            if census is not None:
                census["n_regions"] = census.get("n_regions", 0) + 1
                census["n_with_inside_piece"] = census.get("n_with_inside_piece", 0) + (1 if inside else 0)
                census["covered_cells"] = census.get("covered_cells", 0) + len(covered)
                census["region_cells"] = census.get("region_cells", 0) + len(region)
                census["n_exact"] = census.get("n_exact", 0) + (1 if covered == region and inside else 0)
                hist = census.setdefault("placements_left_hist", {})
                left = str(len(stack) - t)
                hist[left] = hist.get(left, 0) + 1
            if covered == region and inside:
                found.append({"region": sorted(comp), "placements": inside, "t": t})
    del env
    return found, cost
