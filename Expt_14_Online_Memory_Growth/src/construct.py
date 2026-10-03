"""Construct new inventories that reach a stored intermediate state after a nonempty prefix.

The alternative covering occupies the same cells as a stored prefix, so remaining (mask,
inventory) matches a frozen key. The starting inventory differs, so the empty-board key
does not match. This is labeled constructed recurrence, not natural recurrence, and not
abstraction.
"""

from __future__ import annotations

import hashlib
import json

from environment import Action, PackingEnv
from inventory import Inventory
from pieces import ALL_PLACEMENTS, PIECE_TYPES, piece_area


def counts_tuple(counts: dict[str, int]) -> tuple[int, ...]:
    return tuple(int(counts.get(t, 0)) for t in PIECE_TYPES)


def counts_dict(counts: dict[str, int] | tuple[int, ...]) -> dict[str, int]:
    if isinstance(counts, tuple):
        return {t: int(n) for t, n in zip(PIECE_TYPES, counts) if int(n)}
    return {t: int(counts.get(t, 0)) for t in PIECE_TYPES if int(counts.get(t, 0))}


def add_counts(base: dict[str, int], extra: dict[str, int]) -> dict[str, int]:
    out = {t: int(base.get(t, 0)) for t in PIECE_TYPES}
    for t, n in extra.items():
        out[t] += int(n)
    return out


def placement_counts(placements: list[tuple]) -> dict[str, int]:
    out = {t: 0 for t in PIECE_TYPES}
    for piece, _rotation, _x, _y in placements:
        out[piece] += 1
    return out


def replay_placements(inventory: dict[str, int], placements: list[tuple], budget: int = 80) -> PackingEnv:
    env = PackingEnv(budget=budget, inventory=Inventory(dict(inventory)))
    for piece, rotation, x, y in placements:
        result = env.step(Action.place(piece, rotation, x, y))
        if not result.accepted:
            raise RuntimeError(f"illegal constructed placement {piece} {rotation} {x} {y}")
    return env


def find_alternative_cover(
    prefix_mask: int,
    forbidden_counts: tuple[int, ...],
    *,
    max_pieces: int = 5,
    node_cap: int = 80_000,
) -> list[tuple] | None:
    """Exact cover of prefix_mask by catalogue placements, not the original piece multiset."""
    n_cells = prefix_mask.bit_count()
    if n_cells == 0:
        return None
    covering: list[list] = [[] for _ in range(100)]
    for placement in ALL_PLACEMENTS:
        if not placement.mask or placement.mask & ~prefix_mask:
            continue
        mask = placement.mask
        while mask:
            bit = mask & -mask
            covering[bit.bit_length() - 1].append(placement)
            mask ^= bit
    type_index = {name: index for index, name in enumerate(PIECE_TYPES)}
    found: list[tuple] | None = None
    nodes = 0

    def rec(used: int, counts: list[int], acc: list[tuple]) -> bool:
        nonlocal found, nodes
        nodes += 1
        if found is not None or nodes > node_cap:
            return found is not None
        if used == prefix_mask:
            if tuple(counts) != forbidden_counts:
                found = list(acc)
                return True
            return False
        if len(acc) >= max_pieces:
            return False
        remaining = prefix_mask & ~used
        bit = (remaining & -remaining).bit_length() - 1
        seen = set()
        for placement in covering[bit]:
            if placement.signature in seen:
                continue
            seen.add(placement.signature)
            if placement.mask & used:
                continue
            index = type_index[placement.piece_type]
            counts[index] += 1
            acc.append((placement.piece_type, placement.rotation, placement.x, placement.y))
            if rec(used | placement.mask, counts, acc):
                return True
            acc.pop()
            counts[index] -= 1
        return False

    rec(0, [0] * len(PIECE_TYPES), [])
    return found


def _cut_candidates(stack: list[tuple], min_cells: int, max_cells: int, min_placements: int) -> list[int]:
    env = PackingEnv(budget=80, inventory=Inventory({t: 20 for t in PIECE_TYPES}))
    cuts = []
    for index, rec in enumerate(stack, start=1):
        env.step(Action.place(rec[0], rec[1], rec[2], rec[3]))
        if index < min_placements:
            continue
        if min_cells <= env.occupied <= max_cells:
            cuts.append(index)
    # Prefer a short nonempty prefix so the remaining suffix is the stored subproblem.
    return sorted(cuts, key=lambda k: (0 if k >= 2 else 1, k))


def build_constructed_tasks(donors: list[dict], table, config) -> list[dict]:
    """One constructed inventory per donor packing that admits an alternative prefix covering."""
    tasks = []
    seen_inv = set()
    for donor in donors:
        stack = list(donor["stack"])
        inventory = dict(donor["inventory"])
        if not stack:
            continue
        cuts = _cut_candidates(
            stack,
            int(config.min_prefix_cells),
            int(config.max_prefix_cells),
            int(config.min_prefix_placements),
        )
        chosen = None
        for cut in cuts:
            original = stack[:cut]
            original_counts = counts_tuple(placement_counts(original))
            prefix_env = replay_placements(inventory, original)
            prefix_mask = int(prefix_env.mask)
            remaining = dict(prefix_env.inventory.counts)
            key = (prefix_mask, counts_tuple(remaining))
            if key not in table.entries:
                continue
            if prefix_mask == 0:
                continue
            alt = find_alternative_cover(
                prefix_mask,
                original_counts,
                max_pieces=max(3, cut + 1),
            )
            if not alt:
                continue
            constructed_counts = add_counts(remaining, placement_counts(alt))
            constructed_inv = counts_dict(constructed_counts)
            if counts_tuple(constructed_inv) == counts_tuple(inventory):
                continue
            if counts_tuple(constructed_inv) in seen_inv:
                continue
            empty_key = (0, counts_tuple(constructed_inv))
            if empty_key in table.entries:
                continue
            probe = replay_placements(constructed_inv, alt)
            if int(probe.mask) != prefix_mask:
                continue
            if counts_tuple(probe.inventory.counts) != counts_tuple(remaining):
                continue
            if table.lookup(probe) is None:
                continue
            chosen = {
                "cut": cut,
                "original_prefix": original,
                "alt_prefix": alt,
                "prefix_mask": prefix_mask,
                "prefix_occupied": prefix_env.occupied,
                "remaining": counts_dict(remaining),
                "constructed_inv": constructed_inv,
                "suffix_len": len(stack) - cut,
            }
            break
        if chosen is None:
            continue
        seen_inv.add(counts_tuple(chosen["constructed_inv"]))
        payload = json.dumps(chosen["constructed_inv"], sort_keys=True)
        task_id = "cstr_" + hashlib.sha256(payload.encode()).hexdigest()[:12]
        tasks.append(
            {
                "task_id": task_id,
                "family": "constructed_intermediate",
                "inventory": chosen["constructed_inv"],
                "constructed": True,
                "donor_task_id": donor["task_id"],
                "donor_seed": donor["seed"],
                "cut": chosen["cut"],
                "prefix_occupied": chosen["prefix_occupied"],
                "prefix_cells": chosen["prefix_mask"].bit_count(),
                "original_prefix": chosen["original_prefix"],
                "constructed_prefix": chosen["alt_prefix"],
                "suffix_len": chosen["suffix_len"],
                "descriptors": {
                    "types": sum(1 for t in PIECE_TYPES if chosen["constructed_inv"].get(t)),
                    "pieces": sum(chosen["constructed_inv"].values()),
                    "max_type_cells": max(
                        chosen["constructed_inv"].get(t, 0) * piece_area(t) for t in PIECE_TYPES
                    ),
                    "constructed_recurrence": True,
                },
            }
        )
    return tasks
