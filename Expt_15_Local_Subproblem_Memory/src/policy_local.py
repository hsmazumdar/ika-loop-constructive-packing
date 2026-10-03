"""Agents for Expt-15.

Test 1 (constructed, aided): the region and its budget are supplied. The region is filled first
(local memory hit, else region search), then the rest of the box by the primitive policy.

Test 2 (natural): ordinary primitive packing. After each placement the local agent runs an
engineered, billed detector for bounded free regions next to that placement, looks each one up by
geometry, and commits the first stored filling whose multiset is available. There is no gate:
commitment is justified only by geometry and availability, and downstream consequences are measured.

A = primitive_evals (including region search) + detection + lookup + availability checks + validation + insertion.
"""

from __future__ import annotations

import time

from diagnostic import _finish_reason, primitive_step
from environment import Action, PackingEnv
from inventory import Inventory
from local_memory import LocalMemory, place_entry, regions_near, solve_region
from pieces import placed_cells
from solver import Ledger, make_rng


def _pack(env, ledger, config, reason, started, stats) -> dict:
    detection = ledger.index_cost
    availability = ledger.matching_cost
    total = (
        ledger.primitive_evals + detection + ledger.lookup_cost + availability
        + ledger.validation_cost + ledger.learning_cost
    )
    return {
        "Q": float(env.score),
        "A": total,
        "A_identity_ok": total == ledger.A,
        "acceptable": env.score >= config.q_min,
        "termination": reason,
        "occupied": env.occupied,
        "primitive_evals": ledger.primitive_evals,
        "detection_cost": detection,
        "lookup_cost": ledger.lookup_cost,
        "availability_cost": availability,
        "validation_cost": ledger.validation_cost,
        "insertion_cost": ledger.learning_cost,
        "seconds": time.perf_counter() - started,
        "stack": [(p.piece_type, int(p.rotation), int(p.x), int(p.y)) for p in env.stack],
        "env": env,
        **stats,
    }


def _primitive_rest(config, env, select_rng, tabu, ledger, cap) -> str:
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        stop, _ = primitive_step(config, env, select_rng, tabu, ledger)
        if stop:
            return stop
        if env.terminal:
            return env.termination_reason or "terminal"
    return reason


def solve_decomposed(config, task, seed, phase, repetition, memory: LocalMemory | None) -> dict:
    started = time.perf_counter()
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    region = [tuple(c) for c in task["region_cells"]]
    budget = dict(task["region_budget"])
    stats = {"local_hits": 0, "local_lookups": 0, "validation_fails": 0, "region_search_evals": 0,
             "region_filled": False, "region_via": None}
    filled = False
    if memory is not None:
        entry, lcost, checks = memory.lookup(region, budget)
        ledger.charge("lookup", lcost)
        ledger.charge("matching", checks)
        stats["local_lookups"] += 1
        if entry is not None:
            result = place_entry(env, region, entry, ledger)
            if result["ok"]:
                stats["local_hits"] += 1
                stats["region_via"] = "memory"
                filled = True
            else:
                stats["validation_fails"] += 1
                while len(env.stack) > 0 and result["executed"] > 0:
                    env.step(Action.undo())
                    result["executed"] -= 1
    if not filled:
        placements, evals = solve_region(region, budget, node_cap=int(config.region_node_cap))
        ledger.charge("primitive", evals)
        stats["region_search_evals"] = evals
        if placements is not None:
            for piece, rotation, x, y in placements:
                env.step(Action.place(piece, rotation, x, y))
            filled = True
            stats["region_via"] = "search"
    stats["region_filled"] = filled
    stats["region_stack"] = [(p.piece_type, int(p.rotation), int(p.x), int(p.y)) for p in env.stack]
    reason = _primitive_rest(config, env, select_rng, tabu, ledger, cap)
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return _pack(env, ledger, config, reason, started, stats)


def solve_local(config, task, seed, phase, repetition, memory: LocalMemory | None) -> dict:
    """Ordinary packing. memory=None gives the primitive agent on the same RNG stream."""
    started = time.perf_counter()
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    stats = {
        "local_hits": 0, "local_lookups": 0, "regions_detected": 0, "validation_fails": 0,
        "local_cells_filled": 0, "primitive_before_first_hit": None, "first_hit_occupied": None,
        "hit_sizes": [],
    }
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        before = len(env.stack)
        stop, token = primitive_step(config, env, select_rng, tabu, ledger)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
        if memory is None or len(env.stack) <= before or env.occupied >= config.q_min:
            continue
        top = env.stack[-1]
        queue = [list(top.cells)]
        while queue and env.occupied < config.q_min and not env.terminal:
            placed = queue.pop()
            regions, dcost = regions_near(env.mask, placed, int(config.region_min_cells), int(config.region_max_cells))
            ledger.charge("index", dcost)
            stats["regions_detected"] += len(regions)
            for region in regions:
                if env.occupied >= config.q_min or env.terminal:
                    break
                if any(env.mask & (1 << (y * 10 + x)) for x, y in region):
                    continue
                entry, lcost, checks = memory.lookup(region, env.inventory.counts)
                ledger.charge("lookup", lcost)
                ledger.charge("matching", checks)
                stats["local_lookups"] += 1
                if entry is None:
                    continue
                prim_before = ledger.primitive_evals
                occ_before = env.occupied
                n_before = len(env.stack)
                result = place_entry(env, region, entry, ledger)
                if not result["ok"]:
                    stats["validation_fails"] += 1
                    continue
                stats["local_hits"] += 1
                stats["local_cells_filled"] += len(region)
                stats["hit_sizes"].append(len(region))
                if stats["first_hit_occupied"] is None:
                    stats["first_hit_occupied"] = occ_before
                    stats["primitive_before_first_hit"] = prim_before
                for inst in env.stack[n_before:]:
                    queue.append(list(inst.cells))
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return _pack(env, ledger, config, reason, started, stats)


def grow_local_from_stack(memory: LocalMemory, inventory: dict, stack: list[tuple], config, source: str, census: dict | None = None) -> dict:
    from local_memory import extract_entries

    found, cost = extract_entries(inventory, stack, int(config.region_min_cells), int(config.region_max_cells), census)
    ins = 0
    for rec in found:
        ins += memory.add(rec["region"], rec["placements"], source, acquisition_cost=0)
    return {"n_found": len(found), "extraction_cost": cost, "insertion_cost": ins}


def region_cells_of(placements: list[tuple]) -> list[tuple[int, int]]:
    out = []
    for piece, rotation, x, y in placements:
        out.extend(placed_cells(piece, rotation, x, y))
    return sorted(out)
