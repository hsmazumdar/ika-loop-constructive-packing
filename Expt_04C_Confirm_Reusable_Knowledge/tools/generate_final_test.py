"""Generate 100 unique final-test inventories, disjoint from train and development.

Witnesses stay under validation_only/. The solver is not imported by the agent.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pieces import ALL_PLACEMENTS, BOARD_SIZE, FULL_MASK, PIECE_TYPES, Placement, piece_area  # noqa: E402

BY_CELL: list[list[Placement]] = [[] for _ in range(BOARD_SIZE * BOARD_SIZE)]
for _placement in ALL_PLACEMENTS:
    mask = _placement.mask
    while mask:
        bit = mask & -mask
        mask ^= bit
        BY_CELL[bit.bit_length() - 1].append(_placement)


def _inventory_key(counts: dict[str, int]) -> tuple[int, ...]:
    return tuple(int(counts.get(t, 0)) for t in PIECE_TYPES)


def _ok(counts: dict[str, int], min_types: int = 4, max_cells: int = 40) -> bool:
    types = 0
    for t in PIECE_TYPES:
        cells = counts.get(t, 0) * piece_area(t)
        if counts.get(t, 0):
            types += 1
        if cells > max_cells:
            return False
    return types >= min_types


def _solve_one(rng: random.Random, deadline: float, max_cells: int, node_cap: int) -> list[dict] | None:
    active = set(rng.sample(list(PIECE_TYPES), k=rng.randint(4, 7)))
    counts = {t: 0 for t in PIECE_TYPES}
    stack: list[Placement] = []
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
            bit = probe & -probe
            probe ^= bit
            bits.append(bit.bit_length() - 1)
        if not bits:
            return False
        best = None
        for idx in bits:
            cands = [
                p
                for p in BY_CELL[idx]
                if p.piece_type in active
                and not (p.mask & mask)
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
        for placement in order[:8]:
            nodes += 1
            counts[placement.piece_type] += 1
            stack.append(placement)
            if search(mask | placement.mask):
                return True
            stack.pop()
            counts[placement.piece_type] -= 1
            if time.perf_counter() >= deadline or nodes >= node_cap:
                return False
        return False

    if not search(0):
        return None
    return [{"type": p.piece_type, "rotation": p.rotation, "x": p.x, "y": p.y} for p in stack]


def _blocked() -> set[tuple[int, ...]]:
    blocked = set()
    for name in ("train", "development"):
        path = ROOT / "data" / f"{name}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        for task in payload["tasks"]:
            counts = {t: 0 for t in PIECE_TYPES}
            counts.update({k: int(v) for k, v in task["inventory"].items()})
            blocked.add(_inventory_key(counts))
    return blocked


def generate(target: int = 100, timeout: float = 180.0, seed: int = 20260929) -> dict:
    rng = random.Random(seed)
    blocked = _blocked()
    found: dict[tuple[int, ...], dict] = {}
    deadline = time.perf_counter() + timeout
    attempts = 0
    while len(found) < target and time.perf_counter() < deadline:
        attempts += 1
        solved = _solve_one(rng, min(deadline, time.perf_counter() + 2.0), 40, 8000)
        if not solved:
            continue
        counts = {t: 0 for t in PIECE_TYPES}
        for rec in solved:
            counts[rec["type"]] += 1
        if not _ok(counts):
            continue
        key = _inventory_key(counts)
        if key in blocked or key in found:
            continue
        task_id = "inv_" + hashlib.sha256(json.dumps(counts, sort_keys=True).encode()).hexdigest()[:12]
        found[key] = {"task_id": task_id, "counts": counts, "placements": solved}
    tasks = []
    witnesses = ROOT / "validation_only" / "witnesses"
    witnesses.mkdir(parents=True, exist_ok=True)
    for item in found.values():
        counts = item["counts"]
        inventory = {t: counts[t] for t in PIECE_TYPES if counts[t]}
        tasks.append(
            {
                "task_id": item["task_id"],
                "family": "inventory_tasks",
                "inventory": inventory,
                "descriptors": {
                    "types": sum(1 for t in PIECE_TYPES if counts[t]),
                    "pieces": sum(counts.values()),
                    "max_type_cells": max(counts[t] * piece_area(t) for t in PIECE_TYPES),
                },
            }
        )
        (witnesses / f"{item['task_id']}.json").write_text(
            json.dumps({"task_id": item["task_id"], "inventory": inventory, "placements": item["placements"]}, indent=2),
            encoding="utf-8",
        )
    (ROOT / "data" / "test.json").write_text(json.dumps({"tasks": tasks}, indent=2), encoding="utf-8")
    manifest = {
        "unique": len(tasks),
        "target": target,
        "attempts": attempts,
        "partial": len(tasks) < target,
        "status": "OK" if len(tasks) >= target else "PARTIAL",
        "ids": [t["task_id"] for t in tasks],
    }
    (ROOT / "data" / "test_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(generate()))
