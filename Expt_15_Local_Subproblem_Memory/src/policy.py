"""Indexed shortlist policy. Libraries frozen. No remaining-solve futures at deploy time."""

from __future__ import annotations

import time

from diagnostic import a_components, primitive_step, _finish_reason
from environment import PackingEnv
from index import LibraryIndex
from inventory import Inventory
from ranker import rank_vector
from retrieval import first_legal_site, state_features
from solver import Ledger, _execute, make_rng


def _ops_by_id(memory) -> dict:
    return {op.op_id: op for op in memory.active()}


def solve_indexed(
    config,
    task,
    seed,
    phase,
    repetition,
    memory,
    index: LibraryIndex,
    *,
    ranked: bool,
    k: int,
    consult_budget: int,
    benefit_model=None,
    quality_model=None,
) -> dict:
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
    shortlist_n = 0
    abstain_n = 0
    budget_hits = 0
    ops = _ops_by_id(memory)
    while not env.terminal and env.occupied < config.q_min:
        if (primitive.A + consult.A) >= cap:
            reason = "eval_cap"
            break
        acted = False
        if consult.A < int(consult_budget):
            remaining = env.inventory.as_dict()
            posted, probes, checks = index.query(remaining, env.occupied)
            consult.charge("index", probes)
            consult.charge("applicability", checks)
            shortlist = posted[: int(k)]
            shortlist_n += len(shortlist)
            feats = state_features(env)
            scored = []
            for entry in shortlist:
                op = ops.get(entry.op_id)
                if op is None:
                    continue
                useful, score = (op.applicability.useful_here(feats) if op.applicability else (True, 0.0))
                if ranked and benefit_model is not None and quality_model is not None:
                    consult.charge("ranking", 1)
                    vec = rank_vector(
                        env.occupied,
                        remaining,
                        env.actions_used,
                        env.undos,
                        len(op.steps),
                        op.depth,
                        score,
                        op.depth > 1,
                        entry.area,
                    )
                    pred_save = benefit_model.predict(vec)
                    p_ok = quality_model.probability(vec, op.op_id)
                    remaining_check = max(1, int(config.anchors))
                    if p_ok < quality_model.threshold or pred_save <= remaining_check:
                        abstain_n += 1
                        consult.abstentions += 1
                        continue
                    scored.append(( -pred_save, entry.definition_hash, op, score))
                else:
                    scored.append((0, entry.definition_hash, op, score))
            scored.sort()
            for _key, _h, op, score in scored:
                if consult.A >= int(consult_budget):
                    budget_hits += 1
                    break
                site_rng = make_rng(seed, task["task_id"], phase, repetition, f"anchor-{primitive.decisions}-{op.op_id}")
                site, examined = first_legal_site(op, env, site_rng, config.anchors)
                consult.charge("learned", examined)
                if site is None:
                    consult.rejected_operations += 1
                    continue
                proposals += 1
                ok, placed, n_internal = _execute(env, site)
                consult.internal_execution += n_internal
                consult.decisions += 1
                consult.note_depth(op.depth)
                if ok:
                    consult.successful_placements += len(placed)
                    acted = True
                    bypassed += 1
                    break
                consult.rejected_operations += 1
        else:
            budget_hits += 1
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
        "condition": "indexed_ranked" if ranked else "indexed_retrieval",
        "Q": float(env.score),
        "A": parts["A"],
        "acceptable": env.score >= config.q_min,
        "effort_saving_definition": "A_primitive - A_agent (positive = fewer evaluations)",
        "primitive_evals": parts["primitive_evals"],
        "learned_evals": parts["learned_evals"],
        "retrieval_cost": parts["retrieval_cost"],
        "applicability_cost": parts["applicability_cost"],
        "gate_cost": parts["gate_cost"],
        "index_cost": parts["index_cost"],
        "ranking_cost": parts["ranking_cost"],
        "consultation_cost": parts["consultation_cost"],
        "A_identity_ok": parts["A_identity_ok"],
        "rejected_operations": consult.rejected_operations,
        "internal_execution": consult.internal_execution,
        "abstentions": consult.abstentions,
        "decisions": primitive.decisions + consult.decisions,
        "bypassed_primitive_decisions": bypassed,
        "library_proposals": proposals,
        "shortlist_ops": shortlist_n,
        "ranker_abstentions": abstain_n,
        "consult_budget": int(consult_budget),
        "k_shortlist": int(k),
        "budget_exhaustions": budget_hits,
        "elapsed_s": time.perf_counter() - started,
        "termination": reason,
        "library_size": len(memory.active()),
        "memory_bytes": memory.bytes_used(),
        "index_bytes": index.n_bytes,
    }
