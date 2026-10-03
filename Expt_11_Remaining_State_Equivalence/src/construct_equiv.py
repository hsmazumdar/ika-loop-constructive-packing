"""Construct labeled remaining-state equivalence cases and rejection foils.

Transformed versions of one donor stay in that donor's family partition.
Symmetric remaining states (T(mask) == mask) are excluded. Empty-board cases
are excluded because every isometry leaves mask 0 and exact match already hits.
"""

from __future__ import annotations

import hashlib
import json

from construct import add_counts, counts_dict, counts_tuple, find_alternative_cover, placement_counts, replay_placements
from continuation import ContinuationTable
from pieces import PIECE_TYPES, piece_area
from transforms import CANDIDATES, is_symmetric, transform_mask, transform_suffix


def partition_families(donor_ids: list[str], train_frac: float = 2.0 / 3.0) -> tuple[set[str], set[str]]:
    ids = sorted(donor_ids)
    if len(ids) <= 1:
        return set(ids), set()
    n_train = max(1, min(len(ids) - 1, int(round(len(ids) * train_frac))))
    return set(ids[:n_train]), set(ids[n_train:])


def _task(task_id: str, inventory: dict, meta: dict) -> dict:
    rec = {
        "task_id": task_id,
        "family": meta["donor_task_id"],
        "inventory": inventory,
        "constructed_prefix": meta["constructed_prefix"],
        "donor_task_id": meta["donor_task_id"],
        "donor_seed": meta["donor_seed"],
        "partition": meta["partition"],
        "transform": meta.get("transform"),
        "kind": meta["kind"],
        "cut": meta["cut"],
        "prefix_occupied": meta["prefix_occupied"],
        "suffix_len": meta["suffix_len"],
        "symmetric_excluded": True,
        "descriptors": {
            "types": sum(1 for t in PIECE_TYPES if inventory.get(t)),
            "pieces": sum(inventory.values()),
            "max_type_cells": max(inventory.get(t, 0) * piece_area(t) for t in PIECE_TYPES if inventory),
            "constructed_equivalence": meta["kind"] == "constructed_equiv",
            "foil": meta["kind"].endswith("_foil"),
        },
    }
    rec.update({k: v for k, v in meta.items() if k not in rec})
    return rec


def _id(prefix: str, payload) -> str:
    return prefix + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:12]


def build_equivalence_tasks(donors: list[dict], table: ContinuationTable, train_ids: set[str], config) -> list[dict]:
    tasks = []
    seen = set()
    max_t = int(getattr(config, "max_transforms_per_donor", 4))
    for donor in donors:
        stack = list(donor["stack"])
        inventory = dict(donor["inventory"])
        partition = "train" if donor["task_id"] in train_ids else "test"
        if len(stack) < 3:
            continue
        chosen_t = 0
        for cut in range(1, min(len(stack), 6)):
            prefix = stack[:cut]
            suffix = stack[cut:]
            if not suffix:
                continue
            env = replay_placements(inventory, prefix)
            occupied = env.occupied
            if occupied < int(config.min_prefix_cells) or occupied > int(config.max_prefix_cells):
                continue
            stored_mask = int(env.mask)
            remaining = dict(env.inventory.counts)
            if table.lookup_key(stored_mask, counts_tuple(remaining)) is None:
                continue
            if stored_mask == 0:
                continue
            original_counts = counts_tuple(placement_counts(prefix))
            for name in CANDIDATES:
                if chosen_t >= max_t:
                    break
                if is_symmetric(name, stored_mask):
                    continue
                mapped_suffix = transform_suffix(name, suffix)
                if mapped_suffix is None:
                    continue
                mapped_prefix = transform_suffix(name, prefix)
                if mapped_prefix is None:
                    continue
                t_mask = transform_mask(name, stored_mask)
                if t_mask == stored_mask:
                    continue
                alt = find_alternative_cover(t_mask, original_counts, max_pieces=max(3, cut + 1))
                if alt:
                    constructed_prefix = alt
                    constructed_inv = counts_dict(add_counts(remaining, placement_counts(alt)))
                else:
                    constructed_prefix = mapped_prefix
                    constructed_inv = counts_dict(add_counts(remaining, placement_counts(mapped_prefix)))
                if counts_tuple(constructed_inv) in seen:
                    continue
                probe = replay_placements(constructed_inv, constructed_prefix)
                if int(probe.mask) != t_mask:
                    continue
                if counts_tuple(probe.inventory.counts) != counts_tuple(remaining):
                    continue
                if table.lookup_key(int(probe.mask), counts_tuple(probe.inventory.counts)) is not None:
                    # Exact remaining-state hit: this transform did not evade literal matching.
                    continue
                seen.add(counts_tuple(constructed_inv))
                meta = {
                    "kind": "constructed_equiv",
                    "donor_task_id": donor["task_id"],
                    "donor_seed": donor["seed"],
                    "partition": partition,
                    "transform": name,
                    "cut": cut,
                    "prefix_occupied": occupied,
                    "suffix_len": len(suffix),
                    "constructed_prefix": constructed_prefix,
                    "stored_mask": stored_mask,
                    "target_mask": t_mask,
                    "empty_board_lookup_excluded": True,
                }
                tasks.append(
                    _task(_id("eqv_", [donor["task_id"], name, cut, constructed_inv]), constructed_inv, meta)
                )
                chosen_t += 1
            if chosen_t >= max_t:
                break
    return tasks


def build_foil_tasks(equiv_tasks: list[dict], table: ContinuationTable) -> list[dict]:
    """Similar-looking remaining states that must not reuse the stored continuation."""
    foils = []
    seen = set()
    for task in equiv_tasks:
        remaining_after = replay_placements(task["inventory"], task["constructed_prefix"])
        rem = dict(remaining_after.inventory.counts)
        # Inventory foil: same geometry, one suffix-relevant count removed.
        inv_foil = dict(task["inventory"])
        changed = False
        for t in PIECE_TYPES:
            if rem.get(t, 0) > 0 and inv_foil.get(t, 0) > 0:
                inv_foil[t] = inv_foil[t] - 1
                if inv_foil[t] <= 0:
                    inv_foil.pop(t, None)
                changed = True
                break
        if changed and counts_tuple(inv_foil) not in seen:
            try:
                probe = replay_placements(inv_foil, task["constructed_prefix"])
            except RuntimeError:
                probe = None
            if probe is not None and table.lookup_key(int(probe.mask), counts_tuple(probe.inventory.counts)) is None:
                seen.add(counts_tuple(inv_foil))
                meta = dict(task)
                meta["kind"] = "inventory_foil"
                meta["foil_of"] = task["task_id"]
                foils.append(_task(_id("foilinv_", [task["task_id"], inv_foil]), inv_foil, meta))
        # Geometry foil: drop the last constructed prefix placement so the remaining mask is close but wrong.
        if len(task["constructed_prefix"]) >= 2:
            short = list(task["constructed_prefix"])[:-1]
            try:
                probe = replay_placements(task["inventory"], short)
            except RuntimeError:
                probe = None
            if (
                probe is not None
                and int(probe.mask) != int(task.get("target_mask") or -1)
                and table.lookup_key(int(probe.mask), counts_tuple(probe.inventory.counts)) is None
                and counts_tuple(task["inventory"]) not in seen
            ):
                seen.add(("geo", task["task_id"]))
                meta = dict(task)
                meta["kind"] = "geometry_foil"
                meta["foil_of"] = task["task_id"]
                meta["constructed_prefix"] = short
                foils.append(_task(_id("foilgeo_", [task["task_id"], short]), dict(task["inventory"]), meta))
    return foils
