"""Primitive solve and exact-continuation solve. No operation library."""

from __future__ import annotations

import time

from continuation import ContinuationTable, replay_suffix, state_key
from diagnostic import _finish_reason, primitive_step
from environment import PackingEnv
from inventory import Inventory
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


def solve_primitive(config, task, seed, phase, repetition) -> dict:
    cap = int(config.eval_cap)
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    reason = "quality"
    n_place = 0
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        stop, token = primitive_step(config, env, select_rng, tabu, ledger)
        if token and token.startswith("PLACE:"):
            n_place += 1
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    comps = _components(ledger)
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
        "lookups": 0,
        "hits": 0,
        "replays": 0,
        "validation_fails": 0,
        "seconds": time.perf_counter() - started,
    }


def solve_exact(config, task, seed, phase, repetition, table: ContinuationTable, *, learn: bool) -> dict:
    cap = int(config.eval_cap)
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    reason = "quality"
    lookups = hits = replays = fails = 0
    n_place = 0
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        ledger.charge("lookup", 1)
        lookups += 1
        suffix = table.lookup(env)
        if suffix:
            hits += 1
            result = replay_suffix(env, suffix, ledger)
            if result["ok"] and result["n_executed"] > 0:
                replays += 1
                n_place += result["n_executed"]
                continue
            fails += 1
        stop, token = primitive_step(config, env, select_rng, tabu, ledger)
        if token and token.startswith("PLACE:"):
            n_place += 1
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    if learn and env.score >= config.q_min:
        table.learn_from_success(env, ledger)
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    comps = _components(ledger)
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
        "seconds": time.perf_counter() - started,
    }
