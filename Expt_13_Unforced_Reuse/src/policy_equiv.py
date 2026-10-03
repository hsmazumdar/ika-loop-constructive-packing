"""Primitive, exact, supplied-equivalence, and learned-equivalence agents."""

from __future__ import annotations

import time

from continuation import ContinuationTable, replay_suffix, state_key
from diagnostic import _finish_reason, primitive_step
from environment import Action, PackingEnv
from inventory import Inventory
from policy_exact import apply_constructed_prefix
from solver import Ledger, make_rng
from transforms import CANDIDATES, TransformSelector, counts_tuple, inverse, transform_mask, transform_suffix


def _components(ledger: Ledger) -> dict:
    primitive_evals = ledger.primitive_evals
    lookup = ledger.lookup_cost
    matching = ledger.matching_cost
    transformation = ledger.transformation_cost
    validation = ledger.validation_cost
    learning = ledger.learning_cost
    total = primitive_evals + lookup + matching + transformation + validation + learning
    return {
        "primitive_evals": primitive_evals,
        "lookup_cost": lookup,
        "matching_cost": matching,
        "transformation_cost": transformation,
        "validation_cost": validation,
        "learning_cost": learning,
        "A": total,
        "A_identity_ok": total == ledger.A,
        "reuse_cost": lookup + matching + transformation + validation + learning,
    }


def consult_equivalence(env, table: ContinuationTable, ledger, mode: str, selected: tuple[str, ...]) -> dict:
    """Exact probe, then candidate isometries. Validate happens in replay_suffix."""
    ledger.charge("lookup", 1)
    exact = table.lookup(env)
    if exact:
        return {"suffix": exact, "via": "identity", "transform": None, "exact_hit": True}
    if mode == "exact":
        return {"suffix": None, "via": None, "transform": None, "exact_hit": False}
    names = CANDIDATES if mode == "supplied" else selected
    inv = counts_tuple(env.inventory.counts)
    for name in names:
        ledger.charge("matching", 1)
        stored = table.lookup_key(transform_mask(inverse(name), env.mask), inv)
        if stored is None:
            continue
        ledger.charge("transformation", len(stored))
        mapped = transform_suffix(name, stored)
        if mapped is None:
            continue
        return {"suffix": mapped, "via": "equivalence", "transform": name, "exact_hit": False}
    return {"suffix": None, "via": None, "transform": None, "exact_hit": False}


def observe_train_case(task, table: ContinuationTable, selector: TransformSelector) -> None:
    """Experience for selector: try each candidate on the remaining state after the constructed prefix.

    Does not use the generating-transform label as a usefulness label. No-match is not a failure.
    """
    def remaining_env() -> PackingEnv:
        env = PackingEnv(budget=80, inventory=Inventory(dict(task["inventory"])))
        for piece, rotation, x, y in task["constructed_prefix"]:
            env.step(Action.place(piece, rotation, x, y))
        return env

    probe = remaining_env()
    if probe.occupied == 0:
        return
    inv = counts_tuple(probe.inventory.counts)
    for name in CANDIDATES:
        selector.note_attempt(name)
        stored = table.lookup_key(transform_mask(inverse(name), probe.mask), inv)
        if stored is None:
            continue
        mapped = transform_suffix(name, stored)
        if mapped is None:
            selector.observe(name, transformed_ok=True, validation_ok=False, acceptable=False)
            continue
        copy = remaining_env()
        ledger = Ledger()
        result = replay_suffix(copy, mapped, ledger)
        selector.observe(
            name,
            transformed_ok=True,
            validation_ok=bool(result["ok"] and result["n_executed"] > 0),
            acceptable=copy.score >= 75,
        )


def natural_opportunity(env, table: ContinuationTable) -> bool:
    if env.occupied == 0:
        return False
    if table.lookup(env):
        return True
    inv = counts_tuple(env.inventory.counts)
    for name in CANDIDATES:
        if table.lookup_key(transform_mask(inverse(name), env.mask), inv):
            return True
    return False


def solve_equiv(
    config,
    task,
    seed,
    phase,
    repetition,
    table: ContinuationTable | None,
    *,
    mode: str,
    selected: tuple[str, ...] = (),
    constructed_prefix: list[tuple] | None = None,
    allow_initial_lookup: bool = False,
    track_natural_opportunity: bool = False,
) -> dict:
    cap = int(config.eval_cap)
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    reason = "quality"
    lookups = hits = replays = fails = 0
    exact_hits = equiv_hits = 0
    used_transform = None
    n_place = 0
    prefix_primitive_evals = 0
    prefix_n_place = 0
    first_hit_occupied = None
    initial_state_hit = False
    initial_state_hits = 0
    intermediate_hits = 0
    primitive_evals_before_first_hit = None
    natural_opportunities = 0
    constructed_prefix_ok = None

    if constructed_prefix:
        applied = apply_constructed_prefix(config, env, select_rng, tabu, ledger, constructed_prefix)
        prefix_n_place = applied["n_place"]
        prefix_primitive_evals = applied["prefix_primitive_evals"]
        n_place += prefix_n_place
        constructed_prefix_ok = applied["ok"]
        if not applied["ok"]:
            reason = _finish_reason(env, ledger.A, cap, config, "constructed_prefix_failed")
            return _finish(
                config, env, ledger, reason, started, n_place, lookups, hits, replays, fails,
                prefix_primitive_evals, prefix_n_place, first_hit_occupied, initial_state_hit,
                natural_opportunities, constructed_prefix_ok, exact_hits, equiv_hits, used_transform, mode,
                extra={
                    "primitive_evals_before_first_hit": primitive_evals_before_first_hit,
                    "initial_state_hits": initial_state_hits,
                    "intermediate_hits": intermediate_hits,
                    "valid_reuse": False,
                    "first_hit_kind": None,
                },
            )

    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        if mode != "primitive" and table is not None and (env.occupied > 0 or allow_initial_lookup):
            found = consult_equivalence(env, table, ledger, mode, selected)
            lookups += 1
            if found["suffix"]:
                hits += 1
                if found["exact_hit"]:
                    exact_hits += 1
                else:
                    equiv_hits += 1
                    used_transform = found["transform"]
                if env.occupied == 0:
                    initial_state_hit = True
                    initial_state_hits += 1
                else:
                    intermediate_hits += 1
                if first_hit_occupied is None:
                    first_hit_occupied = int(env.occupied)
                    primitive_evals_before_first_hit = int(ledger.primitive_evals)
                result = replay_suffix(env, found["suffix"], ledger)
                if result["ok"] and result["n_executed"] > 0:
                    replays += 1
                    n_place += result["n_executed"]
                    continue
                fails += 1
        stop, token = primitive_step(config, env, select_rng, tabu, ledger)
        if token and token.startswith("PLACE:"):
            n_place += 1
        if track_natural_opportunity and table is not None and natural_opportunity(env, table):
            natural_opportunities += 1
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break

    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return _finish(
        config, env, ledger, reason, started, n_place, lookups, hits, replays, fails,
        prefix_primitive_evals, prefix_n_place, first_hit_occupied, initial_state_hit,
        natural_opportunities, constructed_prefix_ok, exact_hits, equiv_hits, used_transform, mode,
        extra={
            "primitive_evals_before_first_hit": primitive_evals_before_first_hit,
            "initial_state_hits": initial_state_hits,
            "intermediate_hits": intermediate_hits,
            "valid_reuse": replays > 0,
            "first_hit_kind": (
                "initial"
                if first_hit_occupied == 0
                else ("intermediate" if first_hit_occupied is not None else None)
            ),
        },
    )


def _finish(
    config, env, ledger, reason, started, n_place, lookups, hits, replays, fails,
    prefix_primitive_evals, prefix_n_place, first_hit_occupied, initial_state_hit,
    natural_opportunities, constructed_prefix_ok, exact_hits, equiv_hits, used_transform, mode,
    extra: dict | None = None,
) -> dict:
    comps = _components(ledger)
    if constructed_prefix_ok is not None:
        remaining_primitive = ledger.primitive_evals - int(prefix_primitive_evals or 0)
    elif first_hit_occupied is None:
        remaining_primitive = 0
        prefix_primitive_evals = ledger.primitive_evals
        prefix_n_place = n_place
    else:
        remaining_primitive = 0
    rec = {
        "Q": float(env.score),
        "A": comps["A"],
        "acceptable": env.score >= config.q_min,
        "termination": reason,
        "n_place": n_place,
        "occupied": env.occupied,
        "stack": [(p.piece_type, int(p.rotation), int(p.x), int(p.y)) for p in env.stack],
        "env": env,
        "ledger": ledger,
        **comps,
        "lookups": lookups,
        "hits": hits,
        "replays": replays,
        "validation_fails": fails,
        "exact_hits": exact_hits,
        "equiv_hits": equiv_hits,
        "used_transform": used_transform,
        "mode": mode,
        "prefix_primitive_evals": prefix_primitive_evals,
        "prefix_n_place": prefix_n_place,
        "remaining_primitive_evals": remaining_primitive,
        "first_hit_occupied": first_hit_occupied,
        "initial_state_hit": initial_state_hit,
        "natural_opportunities": natural_opportunities,
        "constructed_prefix_ok": constructed_prefix_ok,
        "seconds": time.perf_counter() - started,
        "state_key": state_key(env)[0],
    }
    if extra:
        rec.update(extra)
    return rec
