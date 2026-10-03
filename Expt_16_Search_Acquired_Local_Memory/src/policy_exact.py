"""Primitive solve and exact-continuation solve. No operation library."""

from __future__ import annotations

import time

from continuation import ContinuationTable, replay_suffix
from diagnostic import _finish_reason, primitive_step
from environment import Action, PackingEnv
from inventory import Inventory
from primitive_search import primitive_choice
from solver import Ledger, make_rng


def _components(ledger: Ledger) -> dict:
    primitive_evals = ledger.primitive_evals
    lookup = ledger.lookup_cost
    validation = ledger.validation_cost
    learning = ledger.learning_cost
    total = primitive_evals + lookup + validation + learning
    return {
        "primitive_evals": primitive_evals,
        "lookup_cost": lookup,
        "validation_cost": validation,
        "learning_cost": learning,
        "A": total,
        "A_identity_ok": total == ledger.A,
        "reuse_cost": lookup + validation + learning,
    }


def apply_constructed_prefix(config, env, select_rng, tabu, ledger, prefix: list[tuple]) -> dict:
    """Bill one primitive scan per constructed placement, then commit the constructed covering.

    The scan is real candidate evaluation. The committed placement is the labeled constructed
    prefix, not necessarily the scan's argmax. Memory-on and memory-off share this path so they
    draw the same RNG stream through the prefix.
    """
    prefix_primitive = 0
    n_place = 0
    for piece, rotation, x, y in prefix:
        if env.terminal:
            return {"ok": False, "n_place": n_place, "prefix_primitive_evals": prefix_primitive}
        _found, evaluated, failed = primitive_choice(
            env, select_rng, config.scan, config.score_area, config.score_contact, config.score_boundary, tabu
        )
        ledger.charge("primitive", evaluated)
        ledger.failed_attempts += failed
        prefix_primitive += evaluated
        result = env.step(Action.place(piece, rotation, x, y))
        if not result.accepted:
            return {"ok": False, "n_place": n_place, "prefix_primitive_evals": prefix_primitive}
        ledger.decisions += 1
        ledger.successful_placements += 1
        n_place += 1
    return {"ok": True, "n_place": n_place, "prefix_primitive_evals": prefix_primitive}


def solve_agent(
    config,
    task,
    seed,
    phase,
    repetition,
    table: ContinuationTable | None,
    *,
    memory: bool,
    allow_initial_lookup: bool = True,
    constructed_prefix: list[tuple] | None = None,
    learn: bool = False,
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
    n_place = 0
    prefix_primitive_evals = 0
    prefix_n_place = 0
    first_hit_occupied = None
    first_hit_n_place = None
    primitive_at_first_hit = None
    initial_state_hit = False
    natural_opportunities = 0
    first_natural_opportunity_n_place = None
    lookups_before_first_hit = 0
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
                config,
                env,
                ledger,
                reason,
                started,
                n_place,
                lookups,
                hits,
                replays,
                fails,
                prefix_primitive_evals,
                prefix_n_place,
                None,
                None,
                None,
                False,
                0,
                None,
                0,
                constructed_prefix_ok,
            )

    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        if memory and table is not None and (env.occupied > 0 or allow_initial_lookup):
            ledger.charge("lookup", 1)
            lookups += 1
            if first_hit_occupied is None:
                lookups_before_first_hit += 1
            suffix = table.lookup(env)
            if suffix:
                hits += 1
                if first_hit_occupied is None:
                    first_hit_occupied = int(env.occupied)
                    first_hit_n_place = n_place
                    primitive_at_first_hit = ledger.primitive_evals
                    initial_state_hit = env.occupied == 0
                    if constructed_prefix is None:
                        prefix_primitive_evals = ledger.primitive_evals
                        prefix_n_place = n_place
                result = replay_suffix(env, suffix, ledger)
                if result["ok"] and result["n_executed"] > 0:
                    replays += 1
                    n_place += result["n_executed"]
                    continue
                fails += 1
        stop, token = primitive_step(config, env, select_rng, tabu, ledger)
        if token and token.startswith("PLACE:"):
            n_place += 1
        if track_natural_opportunity and table is not None and env.occupied > 0 and table.lookup(env):
            natural_opportunities += 1
            if first_natural_opportunity_n_place is None:
                first_natural_opportunity_n_place = n_place
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break

    if learn and env.score >= config.q_min and table is not None:
        table.learn_from_success(env, ledger)
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return _finish(
        config,
        env,
        ledger,
        reason,
        started,
        n_place,
        lookups,
        hits,
        replays,
        fails,
        prefix_primitive_evals,
        prefix_n_place,
        first_hit_occupied,
        first_hit_n_place,
        primitive_at_first_hit,
        initial_state_hit,
        natural_opportunities,
        first_natural_opportunity_n_place,
        lookups_before_first_hit,
        constructed_prefix_ok,
    )


def _finish(
    config,
    env,
    ledger,
    reason,
    started,
    n_place,
    lookups,
    hits,
    replays,
    fails,
    prefix_primitive_evals,
    prefix_n_place,
    first_hit_occupied,
    first_hit_n_place,
    primitive_at_first_hit,
    initial_state_hit,
    natural_opportunities,
    first_natural_opportunity_n_place,
    lookups_before_first_hit,
    constructed_prefix_ok,
) -> dict:
    comps = _components(ledger)
    if constructed_prefix_ok is not None:
        remaining_primitive = ledger.primitive_evals - int(prefix_primitive_evals or 0)
    elif first_hit_occupied is None:
        remaining_primitive = 0
        prefix_primitive_evals = ledger.primitive_evals
        prefix_n_place = n_place
    else:
        remaining_primitive = ledger.primitive_evals - int(primitive_at_first_hit or 0)
    return {
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
        "prefix_primitive_evals": prefix_primitive_evals,
        "prefix_n_place": prefix_n_place,
        "remaining_primitive_evals": remaining_primitive,
        "first_hit_occupied": first_hit_occupied,
        "first_hit_n_place": first_hit_n_place,
        "initial_state_hit": initial_state_hit,
        "natural_opportunities": natural_opportunities,
        "first_natural_opportunity_n_place": first_natural_opportunity_n_place,
        "lookups_before_first_hit": lookups_before_first_hit,
        "constructed_prefix_ok": constructed_prefix_ok,
        "seconds": time.perf_counter() - started,
    }


def solve_primitive(config, task, seed, phase, repetition, table=None, *, track_natural_opportunity: bool = False) -> dict:
    return solve_agent(
        config,
        task,
        seed,
        phase,
        repetition,
        table,
        memory=False,
        learn=False,
        track_natural_opportunity=track_natural_opportunity,
    )


def solve_exact(
    config,
    task,
    seed,
    phase,
    repetition,
    table: ContinuationTable,
    *,
    learn: bool,
    allow_initial_lookup: bool = True,
) -> dict:
    return solve_agent(
        config,
        task,
        seed,
        phase,
        repetition,
        table,
        memory=True,
        allow_initial_lookup=allow_initial_lookup,
        learn=learn,
    )
