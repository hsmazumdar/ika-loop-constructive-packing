"""Gated solves. Consultation and commitment are separate, billed decisions."""

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
    gate_cost = consult.gate_cost
    total = primitive_evals + retrieval_cost + applicability_cost + learned_evals + gate_cost
    return {
        "primitive_evals": primitive_evals,
        "retrieval_cost": retrieval_cost,
        "applicability_cost": applicability_cost,
        "learned_evals": learned_evals,
        "gate_cost": gate_cost,
        "A": total,
        "A_identity_ok": total == (primitive.A + consult.A),
        "consultation_cost": retrieval_cost + applicability_cost + learned_evals,
    }


def _finish_reason(env, used_a, cap, config, reason):
    if env.occupied >= config.q_min:
        return "quality"
    if used_a >= cap:
        return "eval_cap"
    if env.terminal and reason == "quality":
        return env.termination_reason or "terminal"
    return reason


def primitive_step(config, env, select_rng, tabu, ledger) -> tuple[str | None, str | None]:
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
    return {"Q": float(env.score), "A": ledger.A, "acceptable": env.score >= config.q_min, "termination": reason}


def _applicability(op, features, threshold: float) -> tuple[bool, float]:
    rule = op.applicability
    if rule is None:
        return True, 0.0
    return rule.useful_here(features)


def list_legal_candidates(config, env, memory, seed, task_id, phase, repetition, decisions, consult: Ledger) -> tuple[list[dict], dict | None, int]:
    """Return legal sites. Policy choice is the first applicability-passing legal op."""
    active = [] if memory is None else memory.active()
    if not active:
        return [], None, 0
    start_a = consult.A
    retrieve_rng = make_rng(seed, task_id, phase, repetition, f"retrieve-{decisions}")
    features = state_features(env)
    ranked, looked = retrieve(active, features, retrieve_rng, config.retrieval_pool, config.top_k)
    consult.charge("retrieval", looked)
    legal = []
    policy = None
    for op, _similarity in ranked:
        consult.charge("applicability", 1)
        useful, score = _applicability(op, features, config.applicability_min)
        site_rng = make_rng(seed, task_id, phase, repetition, f"anchor-{decisions}-{op.op_id}")
        site, examined = first_legal_site(op, env, site_rng, config.anchors)
        consult.charge("learned", examined)
        if site is None:
            consult.failed_attempts += 1
            consult.rejected_operations += 1
            continue
        rec = {
            "op": op,
            "site": site,
            "score": score,
            "useful": useful and score >= config.abstention_margin,
            "features": list(features),
            "composed": op.depth > 1,
            "op_size": len(op.steps),
            "op_types": [step["type"] for step in op.steps],
        }
        legal.append(rec)
        if rec["useful"] and policy is None:
            policy = rec
        if not rec["useful"]:
            consult.rejected_operations += 1
    if policy is None and not legal:
        consult.abstentions += 1
    check_cost = consult.A - start_a
    for rec in legal:
        rec["check_cost"] = check_cost
    return legal, policy, check_cost


def propose_learned(config, env, memory, seed, task_id, phase, repetition, decisions, consult: Ledger):
    legal, policy, check_cost = list_legal_candidates(
        config, env, memory, seed, task_id, phase, repetition, decisions, consult
    )
    if policy is None:
        return None, check_cost
    return policy, check_cost


def remaining_pair(config, env, select_rng, tabu, site, cap) -> tuple[dict, dict, bool, int]:
    env_skip = env.clone()
    env_commit = env.clone()
    rng_skip = copy.copy(select_rng)
    rng_commit = copy.copy(select_rng)
    tabu_skip = set(tabu)
    tabu_commit = set(tabu)
    ok, _placed, n_internal = _execute(env_commit, site)
    if not ok:
        return {}, {}, False, 0
    skip = primitive_remaining(config, env_skip, rng_skip, tabu_skip, cap)
    commit = primitive_remaining(config, env_commit, rng_commit, tabu_commit, cap)
    return skip, commit, True, n_internal


def solve_gated(config, task, seed, phase, repetition, memory, condition: str, consult_gate=None, commit_gate=None) -> dict:
    """Agent solve. primitive / current_selective / consult_gate_only / commit_gate_only / both_gates.

    Normal reuse and gated agents stop on total A. Gate checks are billed.
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
    consult_skips = 0
    commit_skips = 0
    consult_asks = 0
    commit_asks = 0
    use_memory = condition != "primitive" and memory is not None
    use_consult_gate = condition in ("consult_gate_only", "both_gates") and consult_gate is not None
    use_commit_gate = condition in ("commit_gate_only", "both_gates") and commit_gate is not None
    while not env.terminal and env.occupied < config.q_min:
        if (primitive.A + consult.A) >= cap:
            reason = "eval_cap"
            break
        remaining = env.inventory.as_dict()
        acted = False
        may_consult = use_memory
        if use_consult_gate and use_memory:
            from gates import consult_vector

            consult.charge("gate", 1)
            consult_asks += 1
            vec = consult_vector(env.occupied, remaining, env.actions_used, env.undos)
            may_consult = consult_gate.admit(vec)
            if not may_consult:
                consult_skips += 1
        proposal = None
        if may_consult:
            proposal, _cost = propose_learned(
                config, env, memory, seed, task["task_id"], phase, repetition, primitive.decisions + consult.decisions, consult
            )
            if proposal is not None:
                proposals += 1
                if use_commit_gate:
                    from gates import commit_vector

                    consult.charge("gate", 1)
                    commit_asks += 1
                    vec = commit_vector(
                        env.occupied,
                        remaining,
                        env.actions_used,
                        env.undos,
                        proposal["op_size"],
                        proposal["op"].depth,
                        proposal["score"],
                        proposal["composed"],
                    )
                    if not commit_gate.admit(vec, proposal["op"].op_id):
                        commit_skips += 1
                        proposal = None
        if proposal is not None:
            ok, placed, n_internal = _execute(env, proposal["site"])
            consult.internal_execution += n_internal
            consult.decisions += 1
            consult.note_depth(proposal["op"].depth)
            if ok:
                consult.successful_placements += len(placed)
                acted = True
                bypassed += 1
        if not acted:
            stop, _token = primitive_step(config, env, select_rng, tabu, primitive)
            if stop:
                reason = stop
                break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    parts = a_components(primitive, consult)
    reason = _finish_reason(env, parts["A"], cap, config, reason)
    return {
        "task_id": task["task_id"],
        "condition": condition,
        "Q": float(env.score),
        "A": parts["A"],
        "acceptable": env.score >= config.q_min,
        "effort_saving_definition": "A_primitive - A_agent (positive = fewer evaluations)",
        "primitive_evals": parts["primitive_evals"],
        "learned_evals": parts["learned_evals"],
        "retrieval_cost": parts["retrieval_cost"],
        "applicability_cost": parts["applicability_cost"],
        "gate_cost": parts["gate_cost"],
        "consultation_cost": parts["consultation_cost"],
        "A_identity_ok": parts["A_identity_ok"],
        "rejected_operations": consult.rejected_operations,
        "internal_execution": consult.internal_execution,
        "abstentions": consult.abstentions,
        "decisions": primitive.decisions + consult.decisions,
        "bypassed_primitive_decisions": bypassed,
        "library_proposals": proposals,
        "consult_gate_asks": consult_asks,
        "consult_gate_skips": consult_skips,
        "commit_gate_asks": commit_asks,
        "commit_gate_skips": commit_skips,
        "elapsed_s": time.perf_counter() - started,
        "termination": reason,
        "library_size": 0 if memory is None else len(memory.active()),
        "memory_bytes": 0 if memory is None else memory.bytes_used(),
    }
