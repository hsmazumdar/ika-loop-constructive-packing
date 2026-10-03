"""Diagnostic solves. Counterfactual remaining-solves are training/diagnosis only."""

from __future__ import annotations

import copy
import json
import time

from environment import Action, PackingEnv
from inventory import Inventory
from pieces import ALL_PLACEMENTS, placed_cells
from primitive_search import primitive_choice
from retrieval import first_legal_site, retrieve, state_features
from solver import Ledger, _execute, make_rng


def _finish_reason(env, ledger, cap, config, reason):
    if env.occupied >= config.q_min:
        return "quality"
    if ledger.A >= cap:
        return "eval_cap"
    if env.terminal and reason == "quality":
        return env.termination_reason or "terminal"
    return reason


def primitive_step(config, env, select_rng, tabu, ledger, cap) -> str | None:
    """One primitive PLACE or UNDO. Returns a stop reason or None to continue."""
    features = state_features(env)
    index = None
    for _attempt in range(4):
        found, evaluated, failed = primitive_choice(
            env, select_rng, config.scan, config.score_area, config.score_contact, config.score_boundary, tabu
        )
        ledger.charge("primitive", evaluated)
        ledger.failed_attempts += failed
        if found is not None:
            index = found
            break
    if index is None:
        found, evaluated, failed = primitive_choice(
            env, select_rng, 10**6, config.score_area, config.score_contact, config.score_boundary, tabu
        )
        ledger.charge("primitive", evaluated)
        ledger.failed_attempts += failed
        index = found
    if index is None:
        if env.stack and env.undos < config.undo_budget and env.actions_used < env.budget and not env.terminal:
            top = env.stack[-1]
            tabu.add((top.piece_type, top.rotation, top.x, top.y))
            env.step(Action.undo())
            return None
        return "no_progress"
    tabu.clear()
    placement = ALL_PLACEMENTS[index]
    result = env.step(Action.place(placement.piece_type, placement.rotation, placement.x, placement.y))
    ledger.decisions += 1
    ledger.note_depth(0)
    if not result.accepted:
        ledger.failed_attempts += 1
        return "no_progress"
    ledger.successful_placements += 1
    return None


def primitive_remaining(config, env, select_rng, tabu, cap) -> dict:
    ledger = Ledger()
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        stop = primitive_step(config, env, select_rng, tabu, ledger, cap)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    reason = _finish_reason(env, ledger, cap, config, reason)
    return {
        "Q": float(env.score),
        "A": ledger.A,
        "acceptable": env.score >= config.q_min,
        "primitive_evals": ledger.primitive_evals,
        "internal_execution": ledger.internal_execution,
        "termination": reason,
        "occupied": env.occupied,
    }


def propose_learned(config, env, memory, seed, task_id, phase, repetition, decisions, ledger, cap, learn: bool):
    """Retrieve, check applicability, find a legal site. Does not execute."""
    active = [] if memory is None else memory.active()
    if not active or ledger.A >= cap:
        return None, 0
    start_a = ledger.A
    retrieve_rng = make_rng(seed, task_id, phase, repetition, f"retrieve-{decisions}")
    features = state_features(env)
    ranked, looked = retrieve(active, features, retrieve_rng, config.retrieval_pool, config.top_k)
    ledger.charge("retrieval", looked)
    eligible = []
    for op, _similarity in ranked:
        if ledger.A >= cap:
            break
        ledger.charge("applicability", 1)
        rule = op.ensure_rule(len(features), config.applicability_min)
        useful, score = rule.useful_here(features)
        if (not useful) or score < config.abstention_margin:
            ledger.rejected_operations += 1
            continue
        eligible.append((op, score))
    if not eligible:
        ledger.abstentions += 1
        return None, ledger.A - start_a
    for op, score in eligible:
        if ledger.A >= cap:
            break
        site_rng = make_rng(seed, task_id, phase, repetition, f"anchor-{decisions}-{op.op_id}")
        site, examined = first_legal_site(op, env, site_rng, config.anchors)
        ledger.charge("learned", examined)
        if site is None:
            ledger.failed_attempts += 1
            ledger.rejected_operations += 1
            continue
        return {
            "op": op,
            "site": site,
            "score": score,
            "features": list(features),
            "check_cost": ledger.A - start_a,
            "composed": op.depth > 1,
        }, ledger.A - start_a
    ledger.fallbacks += 1
    return None, ledger.A - start_a


def solve_diagnostic(config, task, seed, phase, repetition, memory, mode: str) -> dict:
    """mode: primitive | retrieve_check_then_primitive | normal_reuse"""
    cap = int(config.eval_cap)
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    reason = "quality"
    bypassed = 0
    proposals = 0
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        proposal = None
        check_cost = 0
        if mode != "primitive" and memory is not None:
            proposal, check_cost = propose_learned(
                config, env, memory, seed, task["task_id"], phase, repetition, ledger.decisions, ledger, cap, False
            )
            if proposal is not None:
                proposals += 1
        acted = False
        if mode == "normal_reuse" and proposal is not None:
            ok, placed, n_internal = _execute(env, proposal["site"])
            ledger.internal_execution += n_internal
            ledger.decisions += 1
            ledger.note_depth(proposal["op"].depth)
            if ok:
                ledger.successful_placements += len(placed)
                acted = True
                bypassed += 1
        if not acted:
            stop = primitive_step(config, env, select_rng, tabu, ledger, cap)
            if stop:
                reason = stop
                break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    reason = _finish_reason(env, ledger, cap, config, reason)
    elapsed = time.perf_counter() - started
    return {
        "task_id": task["task_id"],
        "mode": mode,
        "Q": float(env.score),
        "A": ledger.A,
        "acceptable": env.score >= config.q_min,
        "effort_saving_definition": "A_primitive - A_agent (positive = fewer evaluations)",
        "primitive_evals": ledger.primitive_evals,
        "learned_evals": ledger.learned_evals,
        "retrieval_cost": ledger.retrieval_cost,
        "applicability_cost": ledger.applicability_cost,
        "rejected_operations": ledger.rejected_operations,
        "internal_execution": ledger.internal_execution,
        "abstentions": ledger.abstentions,
        "decisions": ledger.decisions,
        "bypassed_primitive_decisions": bypassed,
        "library_proposals": proposals,
        "added_option_only": mode == "retrieve_check_then_primitive",
        "elapsed_s": elapsed,
        "termination": reason,
        "library_size": 0 if memory is None else len(memory.active()),
        "memory_bytes": 0 if memory is None else memory.bytes_used(),
    }


def counterfactual_replays(config, task, seed, phase, repetition, memory) -> list[dict]:
    """At each would-commit proposal, compare remaining primitive solves with/without the op.

    Both futures are diagnosis only. The live walk commits the operation (normal reuse)
    so later operations can also be tested. A deployed agent must not see both outcomes.
    """
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    records = []
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap and len(records) < config.max_replays_per_box:
        proposal, check_cost = propose_learned(
            config, env, memory, seed, task["task_id"], phase, repetition, ledger.decisions, ledger, cap, False
        )
        if proposal is not None:
            env_skip = env.clone()
            env_commit = env.clone()
            rng_skip = copy.copy(select_rng)
            rng_commit = copy.copy(select_rng)
            tabu_skip = set(tabu)
            tabu_commit = set(tabu)
            ok, _placed, n_internal = _execute(env_commit, proposal["site"])
            if ok:
                skip = primitive_remaining(config, env_skip, rng_skip, tabu_skip, cap)
                commit = primitive_remaining(config, env_commit, rng_commit, tabu_commit, cap)
                commit_A = commit["A"]
                remaining_saving = skip["A"] - commit_A
                records.append(
                    {
                        "task_id": task["task_id"],
                        "seed": seed,
                        "op_id": proposal["op"].op_id,
                        "depth": proposal["op"].depth,
                        "composed": proposal["composed"],
                        "check_cost": check_cost,
                        "prefix_A": ledger.A,
                        "A_remaining_primitive": skip["A"],
                        "A_remaining_after_commit": commit_A,
                        "effort_saving_remaining": remaining_saving,
                        "Q_remaining_primitive": skip["Q"],
                        "Q_remaining_after_commit": commit["Q"],
                        "quality_difference": commit["Q"] - skip["Q"],
                        "occupied_at_choice": env.occupied,
                        "features": json.dumps(proposal["features"]),
                        "helps_effort": remaining_saving > check_cost,
                        "helps_quality": commit["Q"] >= skip["Q"] - config.quality_loss_margin,
                        "internal_execution": n_internal,
                        "diagnosis_only": True,
                    }
                )
                _execute(env, proposal["site"])
                ledger.internal_execution += n_internal
                ledger.decisions += 1
                ledger.note_depth(proposal["op"].depth)
                ledger.successful_placements += n_internal
                continue
        stop = primitive_step(config, env, select_rng, tabu, ledger, cap)
        if stop:
            break
        if env.terminal:
            break
    return records
