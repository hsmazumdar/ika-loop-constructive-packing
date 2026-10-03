"""Expt-16: search-acquired local memory.

Acquisition replays frozen store trajectories, records every bounded free region at first
appearance (board and remaining inventory at that moment), and searches offline for an exact
filling using only pieces available then. The store trajectory is never changed.

Search outcomes: found; impossible (search exhausted without a filling); budget_exhausted
(feasibility unknown). A budget stop is never labelled impossible.

Applicability is read-only. Counterfactuals branch from the same saved state (board, inventory,
RNG state, tabu) and are diagnostic work, not information available to an agent.
"""

from __future__ import annotations

import hashlib
import random
import time
from pathlib import Path

from diagnostic import _finish_reason, primitive_step
from environment import Action, PackingEnv
from inventory import Inventory
from local_memory import _COVER, counts_key, geometry_key, region_origin, regions_near
from pieces import ALL_PLACEMENTS, PIECE_TYPES, PIECES, bit_for, placed_cells
from solver import Ledger, make_rng

ROOT = Path(__file__).resolve().parents[1]
SIZE = {t: len(PIECES[t]) for t in PIECE_TYPES}


def manifest_hashes() -> dict[str, str]:
    out = {}
    for line in (ROOT / "manifests" / "MANIFEST_HASHES.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            out[name.strip()] = h
    return out


def load_manifest(name: str) -> dict:
    import json

    path = ROOT / "manifests" / f"{name}.json"
    expected = manifest_hashes()[path.name]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"manifest {path.name} hash mismatch")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- bounded exact search

def area_feasible(n: int, by_size: dict[int, int]) -> bool:
    """Can n cells be written as a sum of available piece sizes? Sound necessary condition."""
    sizes = sorted(by_size)
    if n == 0:
        return True

    def rec(i: int, rest: int) -> bool:
        if rest == 0:
            return True
        if i == len(sizes):
            return False
        s = sizes[i]
        for k in range(min(by_size[s], rest // s), -1, -1):
            if rec(i + 1, rest - k * s):
                return True
        return False

    return rec(0, n)


def search_region(region_cells, available: dict[str, int], budget: int) -> dict:
    """Exact cover of the region from the available multiset.

    Cost = candidate placements examined + one area check per node. Returns status in
    {found, impossible, budget_exhausted}; impossible only when the search space was exhausted.
    """
    region_mask = 0
    for x, y in region_cells:
        region_mask |= bit_for(x, y)
    counts = {t: int(available.get(t, 0)) for t in PIECE_TYPES}
    by_size: dict[int, int] = {}
    for t, n in counts.items():
        if n > 0:
            by_size[SIZE[t]] = by_size.get(SIZE[t], 0) + n
    n_cells = len(list(region_cells))
    evals = 0
    stack: list[int] = []
    out_of_budget = False

    def search(mask: int, left: int) -> bool:
        nonlocal evals, out_of_budget
        rest = region_mask & ~mask
        if not rest:
            return True
        evals += 1
        if not area_feasible(left, by_size):
            return False
        idx = (rest & -rest).bit_length() - 1
        for pi in _COVER[idx]:
            if evals >= budget:
                out_of_budget = True
                return False
            evals += 1
            p = ALL_PLACEMENTS[pi]
            if counts[p.piece_type] <= 0 or p.mask & ~region_mask or p.mask & mask:
                continue
            s = SIZE[p.piece_type]
            counts[p.piece_type] -= 1
            by_size[s] -= 1
            stack.append(pi)
            if search(mask | p.mask, left - s):
                return True
            stack.pop()
            counts[p.piece_type] += 1
            by_size[s] += 1
            if out_of_budget:
                return False
        return False

    ok = search(0, n_cells)
    if ok:
        placements = [(ALL_PLACEMENTS[i].piece_type, ALL_PLACEMENTS[i].rotation, ALL_PLACEMENTS[i].x, ALL_PLACEMENTS[i].y) for i in stack]
        return {"status": "found", "placements": placements, "evals": evals}
    return {"status": "budget_exhausted" if out_of_budget else "impossible", "placements": None, "evals": evals}


# ---------------------------------------------------------------- snapshots from a trajectory

def region_snapshots(inventory: dict, stack: list[tuple], lo: int, hi: int) -> tuple[list[dict], int]:
    """Replay a completed stack; after each placement run the Expt-15 detector next to it.

    Returns first appearances of bounded regions with the board and remaining inventory at that
    moment, and the detector cost (free cells visited).
    """
    remaining = {t: int(inventory.get(t, 0)) for t in PIECE_TYPES}
    occupied = 0
    seen: set = set()
    snaps = []
    cost = 0
    for t, (piece, rotation, x, y) in enumerate(stack, start=1):
        cells = placed_cells(piece, rotation, x, y)
        for c in cells:
            occupied |= bit_for(*c)
        remaining[piece] -= 1
        regions, c = regions_near(occupied, list(cells), lo, hi)
        cost += c
        for comp in regions:
            key = tuple(sorted(comp))
            if key in seen:
                continue
            seen.add(key)
            snaps.append({
                "t": t,
                "placements_left": len(stack) - t,
                "occupied_mask": occupied,
                "remaining": dict(remaining),
                "region": sorted(comp),
            })
    return snaps, cost


def validate_filling(inventory: dict, stack_prefix: list[tuple], region, placements) -> tuple[bool, int]:
    """Rebuild the saved board and check each filling placement is legal, in-region, and in stock."""
    env = PackingEnv(budget=10**6, inventory=Inventory(dict(inventory)))
    for p in stack_prefix:
        env.step(Action.place(*p))
    region_set = set(tuple(c) for c in region)
    cost = 0
    covered = set()
    for piece, rotation, x, y in placements:
        cost += 1
        cells = placed_cells(piece, rotation, x, y)
        if not env.inventory.can_take(piece) or any(c not in region_set for c in cells) or not env._can_place_cells(cells):
            return False, cost
        env.step(Action.place(piece, rotation, x, y))
        covered |= set(cells)
    return covered == region_set, cost


# ---------------------------------------------------------------- acquired entry table

class AcquiredMemory:
    """Entries keyed by (geometry, consumed multiset). Alternative placements for a key are recorded."""

    def __init__(self) -> None:
        self.by_geometry: dict[tuple, list[dict]] = {}
        self.n_entries = 0
        self.frozen = False

    def add(self, region, placements, source: str, search_evals: int) -> dict:
        if self.frozen:
            raise RuntimeError("frozen")
        geo = geometry_key(region)
        ox, oy = region_origin(region)
        counts: dict[str, int] = {}
        rel = []
        for piece, rotation, x, y in placements:
            counts[piece] = counts.get(piece, 0) + 1
            rel.append((piece, int(rotation), int(x) - ox, int(y) - oy))
        rel = sorted(rel)
        ck = counts_key(counts)
        bucket = self.by_geometry.setdefault(geo, [])
        for e in bucket:
            if e["counts_key"] == ck:
                e["sources"].append(source)
                if rel not in e["alternatives"]:
                    e["alternatives"].append(rel)
                    return {"cost": 2, "outcome": "alternative_placement"}
                return {"cost": 1, "outcome": "duplicate"}
        bucket.append({
            "geometry": geo,
            "counts": counts,
            "counts_key": ck,
            "placements": rel,
            "alternatives": [rel],
            "sources": [source],
            "search_evals": int(search_evals),
            "n_cells": len(geo),
        })
        self.n_entries += 1
        return {"cost": 2, "outcome": "written"}

    def freeze(self) -> None:
        self.frozen = True

    def lookup_all(self, region, available: dict[str, int]) -> tuple[bool, list[dict], int, int]:
        """Read-only. Returns (geometry_match, compatible entries in stored order, lookup cost, checks)."""
        bucket = self.by_geometry.get(geometry_key(region))
        if not bucket:
            return False, [], 1, 0
        compatible = []
        for e in bucket:
            if all(int(available.get(t, 0)) >= n for t, n in e["counts"].items()):
                compatible.append(e)
        return True, compatible, 1, len(bucket)

    def n_geometries(self) -> int:
        return len(self.by_geometry)

    def to_json(self) -> list[dict]:
        return [
            {k: (list(v) if isinstance(v, tuple) else v) for k, v in e.items() if k != "counts_key"}
            for b in self.by_geometry.values() for e in b
        ]


# ---------------------------------------------------------------- fresh trajectories, read-only

def observe(config, task, seed, phase, index, memory: AcquiredMemory) -> dict:
    """Primitive trajectory unchanged. Detector and read-only lookup billed separately.

    At every region with a compatible entry, the full state is saved for counterfactuals.
    """
    started = time.perf_counter()
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    rng = make_rng(seed, task["task_id"], phase, index, "select")
    stats = {"detection": 0, "lookup": 0, "availability": 0, "regions": 0, "geometry_matches": 0,
             "compatible_matches": 0, "snapshots": []}
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        before = len(env.stack)
        stop, _ = primitive_step(config, env, rng, tabu, ledger)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
        if len(env.stack) <= before or env.occupied >= config.q_min:
            continue
        regions, dcost = regions_near(env.mask, list(env.stack[-1].cells), int(config.region_min_cells), int(config.region_max_cells))
        stats["detection"] += dcost
        stats["regions"] += len(regions)
        for region in regions:
            geo_match, compatible, lcost, checks = memory.lookup_all(region, env.inventory.counts)
            stats["lookup"] += lcost
            stats["availability"] += checks
            if geo_match:
                stats["geometry_matches"] += 1
            if compatible:
                stats["compatible_matches"] += 1
                stats["snapshots"].append({
                    "env": env.clone(),
                    "rng_state": rng.getstate(),
                    "tabu": set(tabu),
                    "prefix_A": ledger.A,
                    "occupied": env.occupied,
                    "region": region,
                    "entries": compatible[: int(config.max_entries_per_match)],
                    "n_compatible": len(compatible),
                })
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return {
        "Q": float(env.score),
        "A": ledger.A,
        "acceptable": env.score >= config.q_min,
        "termination": reason,
        "seconds": time.perf_counter() - started,
        **stats,
    }


def branch(config, snap: dict, entry: dict | None) -> dict:
    """From the saved state: optionally commit the entry (validated per placement), then primitive."""
    env = snap["env"].clone()
    rng = random.Random()
    rng.setstate(snap["rng_state"])
    tabu = set(snap["tabu"])
    ledger = Ledger()
    cap = int(config.eval_cap) - int(snap["prefix_A"])
    committed = False
    if entry is not None:
        ox, oy = region_origin(snap["region"])
        region = set(tuple(c) for c in snap["region"])
        ok = True
        for piece, rotation, dx, dy in entry["placements"]:
            ledger.charge("validation", 1)
            cells = placed_cells(piece, rotation, dx + ox, dy + oy)
            if env.terminal or not env.inventory.can_take(piece) or any(c not in region for c in cells) or not env._can_place_cells(cells):
                ok = False
                break
            env.step(Action.place(piece, rotation, dx + ox, dy + oy))
        committed = ok
        if not ok:
            return {"Q": None, "A_rest": ledger.A, "valid": False, "acceptable": False, "termination": "validation_fail"}
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        stop, _ = primitive_step(config, env, rng, tabu, ledger)
        if stop:
            reason = stop
            break
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return {
        "Q": float(env.score),
        "A_rest": ledger.A,
        "valid": True if entry is None else committed,
        "acceptable": env.score >= config.q_min,
        "termination": reason,
    }
