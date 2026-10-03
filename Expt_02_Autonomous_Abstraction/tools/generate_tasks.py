"""Offline inventory generator.

Witnesses are stored under validation_only and are not imported by the agent.
If the time limit hits before the target counts, partial data is saved and
duplicate inventories are not used to fill the quota.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mga2.pieces import (  # noqa: E402
    ALL_PLACEMENTS,
    BOARD_SIZE,
    FULL_MASK,
    PIECE_TYPES,
    Placement,
    piece_area,
)

BY_CELL: list[list[Placement]] = [[] for _ in range(BOARD_SIZE * BOARD_SIZE)]
for _placement in ALL_PLACEMENTS:
    bit = 0
    mask = _placement.mask
    while mask:
        b = mask & -mask
        mask ^= b
        BY_CELL[b.bit_length() - 1].append(_placement)


def _inventory_key(counts: dict[str, int]) -> tuple[int, ...]:
    return tuple(counts[t] for t in PIECE_TYPES)


def _ok_inventory(counts: dict[str, int], min_types: int, max_cells: int) -> bool:
    types = 0
    for t in PIECE_TYPES:
        cells = counts[t] * piece_area(t)
        if counts[t]:
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
        best: list[Placement] | None = None
        empty = FULL_MASK ^ mask
        # Most-constrained among a sample of empty cells, then one exact pass if needed.
        bits = []
        probe = empty
        while probe and len(bits) < 8:
            bit = probe & -probe
            probe ^= bit
            bits.append(bit.bit_length() - 1)
        if not bits:
            return False
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
        assert best is not None
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
    return [
        {"type": p.piece_type, "rotation": p.rotation, "x": p.x, "y": p.y}
        for p in stack
    ]


def _counts_from(placements: list[dict]) -> dict[str, int]:
    counts = {t: 0 for t in PIECE_TYPES}
    for rec in placements:
        counts[rec["type"]] += 1
    return counts


def generate(config: dict, root: Path = ROOT) -> dict:
    gen = config.get("generation", {})
    timeout = float(gen.get("timeout_seconds", 180))
    min_types = int(gen.get("min_types", 4))
    max_cells = int(gen.get("max_cells_per_type", 40))
    targets = {
        "train": int(gen.get("train", 24)),
        "development": int(gen.get("development", 8)),
        "test": int(gen.get("test", 12)),
    }
    need = sum(targets.values())
    seed = int(gen.get("seed", 20260929))
    rng = random.Random(seed)
    deadline = time.perf_counter() + timeout
    found: dict[tuple[int, ...], dict] = {}
    attempts = 0
    while len(found) < need and time.perf_counter() < deadline:
        attempts += 1
        # Each attempt gets a slice of the remaining time and a node budget.
        slice_deadline = min(deadline, time.perf_counter() + 2.0)
        solved = _solve_one(rng, slice_deadline, max_cells, node_cap=8000)
        if not solved:
            continue
        counts = _counts_from(solved)
        if not _ok_inventory(counts, min_types, max_cells):
            continue
        key = _inventory_key(counts)
        if key in found:
            continue
        task_id = "inv_" + hashlib.sha256(json.dumps(counts, sort_keys=True).encode()).hexdigest()[:12]
        found[key] = {"task_id": task_id, "counts": counts, "placements": solved}
    keys = sorted(found)
    splits = {}
    cursor = 0
    for name in ("train", "development", "test"):
        take = keys[cursor : cursor + targets[name]]
        cursor += len(take)
        splits[name] = take
    runtime = root / "data" / "runtime"
    witnesses = root / "validation_only" / "witnesses"
    runtime.mkdir(parents=True, exist_ok=True)
    witnesses.mkdir(parents=True, exist_ok=True)
    manifest = {"splits": {}, "attempts": attempts, "unique": len(found), "targets": targets, "partial": len(found) < need}
    for name, key_list in splits.items():
        tasks = []
        for key in key_list:
            item = found[key]
            counts = item["counts"]
            descriptors = {
                "types": sum(1 for t in PIECE_TYPES if counts[t]),
                "pieces": sum(counts.values()),
                "max_type_cells": max(counts[t] * piece_area(t) for t in PIECE_TYPES),
            }
            tasks.append(
                {
                    "task_id": item["task_id"],
                    "family": "inventory_tasks",
                    "inventory": {t: counts[t] for t in PIECE_TYPES if counts[t]},
                    "descriptors": descriptors,
                }
            )
            (witnesses / f"{item['task_id']}.json").write_text(
                json.dumps(
                    {
                        "task_id": item["task_id"],
                        "inventory": {t: counts[t] for t in PIECE_TYPES if counts[t]},
                        "placements": item["placements"],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        (runtime / f"{name}.json").write_text(json.dumps({"tasks": tasks}, indent=2), encoding="utf-8")
        manifest["splits"][name] = [t["task_id"] for t in tasks]
    raw = json.dumps(manifest["splits"], sort_keys=True).encode()
    manifest["dataset_hash"] = hashlib.sha256(raw).hexdigest()
    manifest["status"] = "OK" if not manifest["partial"] else "PARTIAL"
    (runtime / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    manifest = generate(config)
    print(json.dumps({"status": manifest["status"], "unique": manifest["unique"], "splits": {k: len(v) for k, v in manifest["splits"].items()}}))


if __name__ == "__main__":
    main()
