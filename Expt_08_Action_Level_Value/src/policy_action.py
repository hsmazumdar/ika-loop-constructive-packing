"""Action-level ranked reuse. Used only after validation supports a useful subset."""

from __future__ import annotations

import time

from action_features import action_vector
from collect import _rotation_of_site
from diagnostic import _finish_reason, a_components, primitive_step
from enumerate_ops import enumerate_legal
from environment import PackingEnv
from inventory import Inventory
from predictors import remaining_check_cost, would_accept
from retrieval import first_legal_site, state_features
from solver import Ledger, _execute, make_rng


def solve_action_ranked(config, task, seed, phase, repetition, memory, index, benefit_model, quality_model, k, consult_budget, n_placements) -> dict:
    cap = int(config.eval_cap)
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    primitive = Ledger()
    consult = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    ops = {op.op_id: op for op in memory.active()}
    reason = "quality"
    bypassed = 0
    remaining_check = remaining_check_cost(config.anchors)
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
            feats = state_features(env)
            scored = []
            for entry in shortlist:
                op = ops.get(entry.op_id)
                if op is None:
                    continue
                _u, score = (op.applicability.useful_here(feats) if op.applicability else (True, 0.0))
                candidates = []
                if int(n_placements) <= 1:
                    site_rng = make_rng(seed, task["task_id"], phase, repetition, f"anchor-{primitive.decisions}-{op.op_id}")
                    site, examined = first_legal_site(op, env, site_rng, config.anchors)
                    if site is not None:
                        candidates.append((site, examined, _rotation_of_site(op, site)))
                    consult.charge("learned", examined)
                else:
                    enum = enumerate_legal(op, env, int(n_placements))
                    consult.charge("learned", int(enum["examined"]))
                    for rec in enum["placements"][: int(n_placements)]:
                        candidates.append((rec["site"], 1, int(rec["rotation"])))
                for site, examined, rotation in candidates:
                    vec, feat_checks = action_vector(
                        env.occupied, remaining, env.actions_used, env.undos, op, score, entry.area, site, env, rotation
                    )
                    consult.charge("ranking", 1 + feat_checks)
                    pred = benefit_model.predict(vec)
                    p_ok = quality_model.probability(vec, op.op_id)
                    if would_accept(pred, p_ok, quality_model.threshold, remaining_check):
                        scored.append((-pred, entry.definition_hash, op, site, examined))
                    else:
                        consult.abstentions += 1
            scored.sort()
            for _neg, _h, op, site, examined in scored:
                if consult.A >= int(consult_budget):
                    break
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
        "condition": "action_ranked",
        "Q": float(env.score),
        "A": parts["A"],
        "primitive_evals": parts["primitive_evals"],
        "consultation_cost": parts["consultation_cost"],
        "ranking_cost": parts["ranking_cost"],
        "learned_evals": parts["learned_evals"],
        "index_cost": parts["index_cost"],
        "A_identity_ok": parts["A_identity_ok"],
        "bypassed_primitive_decisions": bypassed,
        "termination": reason,
        "elapsed_s": time.perf_counter() - started,
    }
