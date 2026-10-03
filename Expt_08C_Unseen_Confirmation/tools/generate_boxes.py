"""Generate fresh inventories, disjoint from prior experiment splits."""

from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pieces import ALL_PLACEMENTS, BOARD_SIZE, FULL_MASK, PIECE_TYPES, Placement, piece_area  # noqa: E402

BY_CELL: list[list[Placement]] = [[] for _ in range(BOARD_SIZE * BOARD_SIZE)]
for _placement in ALL_PLACEMENTS:
    mask = _placement.mask
    while mask:
        bit = mask & -mask
        mask ^= bit
        BY_CELL[bit.bit_length() - 1].append(_placement)

BLOCKED_PATHS = [
    ROOT / "data" / "train.json",
    ROOT / "data" / "development.json",
    ROOT.parent / "Expt_04_Emergent_Hierarchical_Abstraction" / "data" / "test.json",
    ROOT.parent / "Expt_04B_Selective_Reuse" / "data" / "test.json",
    ROOT.parent / "Expt_04C_Confirm_Reusable_Knowledge" / "data" / "test.json",
    ROOT.parent / "Expt_04C_Confirm_Reusable_Knowledge" / "data" / "train.json",
    ROOT.parent / "Expt_04D_Where_Reuse_Loses_Advantage" / "data" / "development.json",
    ROOT.parent / "Expt_04D2_Costly_Choices" / "data" / "fresh.json",
    ROOT.parent / "Expt_05_Consult_and_Commit_Gates" / "data" / "eval.json",
    ROOT.parent / "Expt_05_Consult_and_Commit_Gates" / "data" / "train.json",
    ROOT.parent / "Expt_05_Consult_and_Commit_Gates" / "data" / "development.json",
    ROOT.parent / "Expt_06_Frozen_Library_Opportunity" / "data" / "eval.json",
    ROOT.parent / "Expt_06_Frozen_Library_Opportunity" / "data" / "smoke.json",
    ROOT.parent / "Expt_06_Frozen_Library_Opportunity" / "data" / "train.json",
    ROOT.parent / "Expt_06_Frozen_Library_Opportunity" / "data" / "development.json",
    ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "eval.json",
    ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "train.json",
    ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "development.json",
]


def all_prior_task_files() -> list[Path]:
    """Every JSON file that already lists packing tasks. New boxes must miss all of them."""
    skip = {".venv", "results", "__pycache__", "node_modules"}
    found = []
    for path in ROOT.parent.rglob("*.json"):
        if skip.intersection(path.parts):
            continue
        if path.resolve() == (ROOT / "data" / "unseen.json").resolve() and path.exists():
            found.append(path)
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        tasks = payload.get("tasks") if isinstance(payload, dict) else None
        if isinstance(tasks, list) and tasks and isinstance(tasks[0], dict) and "inventory" in tasks[0]:
            found.append(path)
    return found


def inventory_key(counts: dict[str, int]) -> tuple[int, ...]:
    return tuple(int(counts.get(t, 0)) for t in PIECE_TYPES)


def load_tasks(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return list(json.loads(path.read_text(encoding="utf-8")).get("tasks") or [])


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


def _blocked(extra: list[Path] | None = None) -> set[tuple[int, ...]]:
    blocked = set()
    paths = list(BLOCKED_PATHS) + list(extra or [])
    for rel in paths:
        for task in load_tasks(Path(rel)):
            counts = {t: 0 for t in PIECE_TYPES}
            counts.update({k: int(v) for k, v in task["inventory"].items()})
            blocked.add(inventory_key(counts))
    return blocked


def generate(
    target: int = 24,
    timeout: float = 180.0,
    seed: int = 2026092962,
    out_name: str = "eval",
    extra_blocked: list[Path] | None = None,
) -> dict:
    rng = random.Random(seed)
    extra = list(extra_blocked or []) + all_prior_task_files()
    blocked = _blocked(extra)
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
        key = inventory_key(counts)
        if key in blocked or key in found:
            continue
        task_id = "inv_" + hashlib.sha256(json.dumps(counts, sort_keys=True).encode()).hexdigest()[:12]
        found[key] = {"task_id": task_id, "counts": counts}
    tasks = []
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
    (ROOT / "data" / f"{out_name}.json").write_text(json.dumps({"tasks": tasks}, indent=2), encoding="utf-8")
    manifest = {
        "unique": len(tasks),
        "target": target,
        "attempts": attempts,
        "status": "OK" if len(tasks) >= target else "PARTIAL",
        "seed": seed,
        "out_name": out_name,
        "task_ids": [t["task_id"] for t in tasks],
    }
    (ROOT / "data" / f"{out_name}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "eval"
    if kind == "smoke":
        print(json.dumps(generate(target=4, seed=2026092971, out_name="smoke")))
    else:
        extra = [ROOT / "data" / "smoke.json"]
        print(json.dumps(generate(target=16, seed=2026092972, out_name="eval", extra_blocked=extra)))
