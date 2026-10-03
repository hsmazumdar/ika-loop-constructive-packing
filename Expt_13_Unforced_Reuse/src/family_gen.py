"""Recurring-family inventories declared before evaluation.

A family is a frozen catalogue type-set. Variants are independent packings
restricted to that type-set; counts may differ. This generator does not import
or consult the memory table.
"""

from __future__ import annotations

import hashlib
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pieces import PIECE_TYPES
from tools.generate_boxes import counts_ok, inventory_key, pack_one, task_from_counts

GENERATOR_RULE = (
    "independent catalogue packings restricted to a frozen type-set; "
    "inventory counts may differ; the memory table is not consulted"
)


def declare_families(n_families: int, rng: random.Random) -> list[dict]:
    specs = []
    seen: set[tuple[str, ...]] = set()
    guard = 0
    while len(specs) < n_families and guard < n_families * 50:
        guard += 1
        k = rng.randint(4, 7)
        types = tuple(sorted(rng.sample(list(PIECE_TYPES), k=k)))
        if types in seen:
            continue
        seen.add(types)
        fam_id = "fam_" + hashlib.sha256(",".join(types).encode()).hexdigest()[:12]
        specs.append(
            {
                "family_id": fam_id,
                "type_set": list(types),
                "rule": GENERATOR_RULE,
                "consults_memory_table": False,
            }
        )
    if len(specs) < n_families:
        raise RuntimeError(f"declared {len(specs)} families, wanted {n_families}")
    return specs


def inventories_for_types(
    type_set: list[str],
    n: int,
    rng: random.Random,
    blocked: set[tuple[int, ...]],
    deadline: float,
    family_id: str,
) -> list[dict]:
    found: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    while len(found) < n and time.perf_counter() < deadline:
        solved = pack_one(rng, min(deadline, time.perf_counter() + 2.0), 40, 8000, set(type_set))
        if not solved:
            continue
        counts = {t: 0 for t in PIECE_TYPES}
        for rec in solved:
            counts[rec["type"]] += 1
        if not counts_ok(counts):
            continue
        key = inventory_key(counts)
        if key in blocked or key in seen:
            continue
        seen.add(key)
        task = task_from_counts(counts, family=family_id)
        task["family_id"] = family_id
        task["type_set"] = list(type_set)
        task["constructed_prefix"] = None
        task["workload"] = "recurring_family"
        found.append(task)
    if len(found) < n:
        raise RuntimeError(f"family {family_id} produced {len(found)} inventories, wanted {n}")
    return found


def generate_family_members(
    specs: list[dict],
    n_each: int,
    seed: int,
    blocked: set[tuple[int, ...]],
    timeout: float = 180.0,
) -> list[dict]:
    rng = random.Random(int(seed))
    deadline = time.perf_counter() + timeout
    out = []
    used = set(blocked)
    for spec in specs:
        tasks = inventories_for_types(
            spec["type_set"], n_each, rng, used, deadline, spec["family_id"]
        )
        for task in tasks:
            used.add(inventory_key(task["inventory"]))
            out.append(task)
    return out
