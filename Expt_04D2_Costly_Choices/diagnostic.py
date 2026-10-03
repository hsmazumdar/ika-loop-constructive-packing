"""Diagnostic solves with separated primitive and consultation ledgers.

retrieve_check_then_primitive must not share the evaluation cap with retrieval.
Consultation uses its own RNG streams and must not mutate the board.
"""

from __future__ import annotations

import copy
import json
import time

from environment import Action, PackingEnv
from inventory import Inventory
from pieces import ALL_PLACEMENTS
from primitive_search import primitive_choice
from retrieval import first_legal_site, retrieve, state_features
from solver import Ledger, _execute, make_rng


def a_components(primitive: Ledger, consult: Ledger) -> dict:
    primitive_evals = primitive.primitive_evals
    retrieval_cost = consult.retrieval_cost
    applicability_cost = consult.applicability_cost
    learned_evals = consult.learned_evals
    total = primitive_evals + retrieval_cost + applicability_cost + learned_evals
    return {
        "primitive_evals": primitive_evals,
        "retrieval_cost": retrieval_cost,
        "applicability_cost": applicability_cost,
        "learned_evals": learned_evals,
        "A": total,
        "A_identity_ok": total == (primitive.A + consult.A),
        "consultation_cost": retrieval_cost + applicability_cost + learned_evals,
    }


def _finish_reason(env, primitive_a, cap, config, reason):
    if env.occupied >= config.q_min:
        return "quality"
    if primitive_a >= cap:
        return "eval_cap"
    if env.terminal and reason == "quality":
        return env.termination_reason or "terminal"
    return reason


def primitive_step(config, env, select_rng, tabu, ledger) -> tuple[str | None, str | None]:
    """One primitive PLACE or UNDO. Returns (stop_reason, action_token)."""
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
            return None, f"UNDO:{top.piece_type}:{top.rotation}:{top.x}:{top.y}"
        return "no_progress", None
    tabu.clear()
    placement = ALL_PLACEMENTS[index]
    result = env.step(Action.place(placement.piece_type, placement.rotation, placement.x, placement.y))
    ledger.decisions += 1
    ledger.note_depth(0)
    token = f"PLACE:{placement.piece_type}:{placement.rotation}:{placement.x}:{placement.y}"
    if not result.accepted:
        ledger.failed_attempts += 1
        return "no_progress", token
    ledger.successful_placements += 1
    return None, token


def primitive_remaining(config, env, select_rng, tabu, cap) -> dict:
    ledger = Ledger()
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        stop, _token = primitive_step(config, env, select_rng, tabu, ledger)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return {
        "Q": float(env.score),
        "A": ledger.A,
        "acceptable": env.score >= config.q_min,
        "primitive_evals": ledger.primitive_evals,
        "termination": reason,
        "occupied": env.occupied,
    }


def _applicability(op, features, threshold: float) -> tuple[bool, float]:
    rule = op.applicability
    if rule is None:
        return True, 0.0
    return rule.useful_here(features)


def propose_learned(config, env, memory, seed, task_id, phase, repetition, decisions, consult: Ledger):
    """Retrieve and check. Does not execute, does not touch select_rng, does not mutate env or ops."""
    active = [] if memory is None else memory.active()
    if not active:
        return None, 0
    start_a = consult.A
    retrieve_rng = make_rng(seed, task_id, phase, repetition, f"retrieve-{decisions}")
    features = state_features(env)
    ranked, looked = retrieve(active, features, retrieve_rng, config.retrieval_pool, config.top_k)
    consult.charge("retrieval", looked)
    eligible = []
    for op, _similarity in ranked:
        consult.charge("applicability", 1)
        useful, score = _applicability(op, features, config.applicability_min)
        if (not useful) or score < config.abstention_margin:
            consult.rejected_operations += 1
            continue
        eligible.append((op, score))
    if not eligible:
        consult.abstentions += 1
        return None, consult.A - start_a
    for op, score in eligible:
        site_rng = make_rng(seed, task_id, phase, repetition, f"anchor-{decisions}-{op.op_id}")
        site, examined = first_legal_site(op, env, site_rng, config.anchors)
        consult.charge("learned", examined)
        if site is None:
            consult.failed_attempts += 1
            consult.rejected_operations += 1
            continue
        return {
            "op": op,
            "site": site,
            "score": score,
            "features": list(features),
            "check_cost": consult.A - start_a,
            "composed": op.depth > 1,
            "op_size": len(op.steps),
            "op_types": [step["type"] for step in op.steps],
        }, consult.A - start_a
    consult.fallbacks += 1
    return None, consult.A - start_a


def _snapshot_decision(env, features) -> dict:
    remaining = env.inventory.as_dict()
    n_comp, max_comp = 0, 0
    if len(features) >= 40:
        n_comp = int(round(float(features[-3]) * 100.0))
        max_comp = int(round(float(features[-2]) * 100.0))
    return {
        "occupied": env.occupied,
        "remaining_pieces": remaining,
        "remaining_piece_count": sum(remaining.values()),
        "empty_components": n_comp,
        "largest_empty_region": max_comp,
        "border_empty_frac": float(features[-1]) if features else None,
        "board_mask": int(env.mask),
        "actions_used": env.actions_used,
        "undos": env.undos,
    }


def solve_diagnostic(config, task, seed, phase, repetition, memory, mode: str) -> dict:
    """mode: primitive | retrieve_check_then_primitive | normal_reuse

    retrieve_check stopping uses only primitive evaluations, so consultation
    cannot truncate the primitive trajectory. normal_reuse stops on total A.
    """
    cap = int(config.eval_cap)
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    primitive = Ledger()
    consult = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    reason = "quality"
    bypassed = 0
    proposals = 0
    trace: list[str] = []
    while not env.terminal and env.occupied < config.q_min:
        if mode == "normal_reuse" and (primitive.A + consult.A) >= cap:
            reason = "eval_cap"
            break
        if mode != "normal_reuse" and primitive.A >= cap:
            reason = "eval_cap"
            break
        proposal = None
        if mode != "primitive" and memory is not None:
            proposal, _cost = propose_learned(
                config, env, memory, seed, task["task_id"], phase, repetition, primitive.decisions + consult.decisions, consult
            )
            if proposal is not None:
                proposals += 1
        acted = False
        if mode == "normal_reuse" and proposal is not None:
            ok, placed, n_internal = _execute(env, proposal["site"])
            consult.internal_execution += n_internal
            consult.decisions += 1
            consult.note_depth(proposal["op"].depth)
            token = "LEARNED:" + ",".join(f"{p['type']}:{p['rotation']}:{p['x']}:{p['y']}" for p in placed)
            trace.append(token)
            if ok:
                consult.successful_placements += len(placed)
                acted = True
                bypassed += 1
        if not acted:
            stop, token = primitive_step(config, env, select_rng, tabu, primitive)
            if token:
                trace.append(token)
            if stop:
                reason = stop
                break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    parts = a_components(primitive, consult)
    reason = _finish_reason(env, primitive.A if mode != "normal_reuse" else parts["A"], cap, config, reason)
    elapsed = time.perf_counter() - started
    return {
        "task_id": task["task_id"],
        "mode": mode,
        "Q": float(env.score),
        "A": parts["A"],
        "acceptable": env.score >= config.q_min,
        "effort_saving_definition": "A_primitive - A_agent (positive = fewer evaluations)",
        "primitive_evals": parts["primitive_evals"],
        "learned_evals": parts["learned_evals"],
        "retrieval_cost": parts["retrieval_cost"],
        "applicability_cost": parts["applicability_cost"],
        "consultation_cost": parts["consultation_cost"],
        "A_identity_ok": parts["A_identity_ok"],
        "rejected_operations": consult.rejected_operations,
        "internal_execution": consult.internal_execution,
        "abstentions": consult.abstentions,
        "decisions": primitive.decisions + consult.decisions,
        "bypassed_primitive_decisions": bypassed,
        "library_proposals": proposals,
        "added_option_only": mode == "retrieve_check_then_primitive",
        "primitive_trace": "|".join(trace),
        "elapsed_s": elapsed,
        "termination": reason,
        "library_size": 0 if memory is None else len(memory.active()),
        "memory_bytes": 0 if memory is None else memory.bytes_used(),
    }


def counterfactual_replays(config, task, seed, phase, repetition, memory, split_name: str) -> list[dict]:
    """Matched-state remaining-solves. Diagnosis only."""
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    primitive = Ledger()
    consult = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    records = []
    choice_index = 0
    while not env.terminal and env.occupied < config.q_min and primitive.A < cap and len(records) < config.max_replays_per_box:
        proposal, check_cost = propose_learned(
            config, env, memory, seed, task["task_id"], phase, repetition, primitive.decisions + consult.decisions, consult
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
                remaining_saving = skip["A"] - commit["A"]
                quality_ok = commit["Q"] >= skip["Q"] - config.quality_loss_margin
                effort_ok = remaining_saving > check_cost
                snap = _snapshot_decision(env, proposal["features"])
                decision_id = f"{seed}:{task['task_id']}:{split_name}:{choice_index}:occ{env.occupied}:{proposal['op'].op_id}"
                records.append(
                    {
                        "decision_id": decision_id,
                        "task_id": task["task_id"],
                        "seed": seed,
                        "split": split_name,
                        "choice_index": choice_index,
                        "op_id": proposal["op"].op_id,
                        "depth": proposal["op"].depth,
                        "composed": proposal["composed"],
                        "op_size": proposal["op_size"],
                        "op_types": json.dumps(proposal["op_types"]),
                        "check_cost": check_cost,
                        "retrieval_and_check_cost": check_cost,
                        "prefix_primitive_A": primitive.A,
                        "A_remaining_primitive": skip["A"],
                        "A_remaining_after_commit": commit["A"],
                        "effort_saving_remaining": remaining_saving,
                        "Q_remaining_primitive": skip["Q"],
                        "Q_remaining_after_commit": commit["Q"],
                        "quality_difference": commit["Q"] - skip["Q"],
                        "quality_ok": quality_ok,
                        "effort_ok": effort_ok,
                        "acceptable_success": effort_ok and quality_ok,
                        "occupied_at_choice": snap["occupied"],
                        "remaining_piece_count": snap["remaining_piece_count"],
                        "remaining_pieces": json.dumps(snap["remaining_pieces"], sort_keys=True),
                        "empty_components": snap["empty_components"],
                        "largest_empty_region": snap["largest_empty_region"],
                        "border_empty_frac": snap["border_empty_frac"],
                        "board_mask": snap["board_mask"],
                        "features": json.dumps(proposal["features"]),
                        "internal_execution": n_internal,
                        "diagnosis_only": True,
                    }
                )
                choice_index += 1
                _execute(env, proposal["site"])
                consult.internal_execution += n_internal
                consult.decisions += 1
                consult.note_depth(proposal["op"].depth)
                continue
        stop, _token = primitive_step(config, env, select_rng, tabu, primitive)
        if stop:
            break
        if env.terminal:
            break
    return records
