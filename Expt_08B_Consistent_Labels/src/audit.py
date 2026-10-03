"""Instrumented ranked solve. Frozen artifacts only. Remaining-solves are diagnostic."""

from __future__ import annotations

from diagnostic import a_components, primitive_step, remaining_pair, _finish_reason
from enumerate_ops import action_key
from environment import PackingEnv
from inventory import Inventory
from ranker import rank_vector
from retrieval import first_legal_site, state_features
from snapshot import remaining_cap, state_fingerprint
from solver import Ledger, _execute, make_rng


def _ops_by_id(memory) -> dict:
    return {op.op_id: op for op in memory.active()}


def solve_primitive_traced(config, task, seed, phase, repetition) -> dict:
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    primitive = Ledger()
    consult = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    trace = []
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and primitive.A < cap:
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
    reason = _finish_reason(env, parts["A"], cap, config, reason)
    return {
        "task_id": task["task_id"],
        "condition": "primitive",
        "Q": float(env.score),
        "A": parts["A"],
        "primitive_evals": parts["primitive_evals"],
        "consultation_cost": 0,
        "A_identity_ok": parts["A_identity_ok"],
        "primitive_trace": "|".join(trace),
        "termination": reason,
    }


def solve_ranked_audit(
    config,
    task,
    seed,
    phase,
    repetition,
    memory,
    index,
    benefit_model,
    quality_model,
    k: int,
    consult_budget: int,
    diagnostic_ledger: dict,
    replay_cache: dict,
    collect_counterfactuals: bool = True,
) -> dict:
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    primitive = Ledger()
    consult = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    ops = _ops_by_id(memory)
    decisions = []
    ranker_rows = []
    cf_rows = []
    trace = []
    reason = "quality"
    bypassed = 0
    first_exhaustion = None
    consult_attempts = 0
    step = 0
    while not env.terminal and env.occupied < config.q_min:
        if (primitive.A + consult.A) >= cap:
            reason = "eval_cap"
            break
        remaining = env.inventory.as_dict()
        fp = state_fingerprint(env, primitive.A, select_rng.getstate())
        rec = {
            "seed": seed,
            "task_id": task["task_id"],
            "step": step,
            "occupied": env.occupied,
            "prefix_primitive_A": primitive.A,
            "consult_A_before": consult.A,
            "budget_remaining": max(0, int(consult_budget) - consult.A),
            "fingerprint": fp,
            "consulted": False,
            "budget_exhausted": consult.A >= int(consult_budget),
            "committed": False,
            "primitive_token": None,
            "shortlist": [],
        }
        acted = False
        if consult.A < int(consult_budget):
            consult_attempts += 1
            rec["consulted"] = True
            posted, probes, checks = index.query(remaining, env.occupied)
            consult.charge("index", probes)
            consult.charge("applicability", checks)
            shortlist = posted[: int(k)]
            rec["n_posted"] = len(posted)
            rec["index_probes"] = probes
            rec["compat_checks"] = checks
            feats = state_features(env)
            scored = []
            pending = []
            remaining_check = max(1, int(config.anchors))
            for entry in shortlist:
                op = ops.get(entry.op_id)
                if op is None:
                    continue
                _useful, score = (op.applicability.useful_here(feats) if op.applicability else (True, 0.0))
                consult.charge("ranking", 1)
                vec = rank_vector(
                    env.occupied, remaining, env.actions_used, env.undos, len(op.steps), op.depth, score, op.depth > 1, entry.area
                )
                pred_save = benefit_model.predict(vec)
                p_ok = quality_model.probability(vec, op.op_id)
                reject_quality = p_ok < quality_model.threshold
                reject_saving = pred_save <= remaining_check
                admit = (not reject_quality) and (not reject_saving)
                if not admit:
                    consult.abstentions += 1
                site_rng = make_rng(seed, task["task_id"], phase, repetition, f"anchor-{primitive.decisions}-{op.op_id}")
                site, examined = first_legal_site(op, env, site_rng, config.anchors)
                akey = action_key(site) if site is not None else None
                row = {
                    "seed": seed,
                    "task_id": task["task_id"],
                    "step": step,
                    "occupied": env.occupied,
                    "fingerprint": fp,
                    "op_id": op.op_id,
                    "definition_hash": entry.definition_hash,
                    "pred_saving": pred_save,
                    "p_quality_ok": p_ok,
                    "quality_threshold": quality_model.threshold,
                    "remaining_check_cost": remaining_check,
                    "reject_quality": reject_quality,
                    "reject_saving": reject_saving,
                    "ranker_admit": admit,
                    "placement_found": site is not None,
                    "placement_examined": examined,
                    "action_key": akey,
                    "committed": False,
                    "diagnosis_only": False,
                }
                rec["shortlist"].append(op.op_id)
                ranker_rows.append(row)
                pending.append((op, entry, admit, site, examined, akey, row))
                if admit:
                    scored.append((-pred_save, entry.definition_hash, op, site, examined, row))
            if collect_counterfactuals:
                for op, entry, admit, site, _examined, akey, _row in pending:
                    if site is None:
                        continue
                    cf = _counterfactual(config, env, select_rng, tabu, primitive.A, site, akey, replay_cache, diagnostic_ledger)
                    cf.update(
                        {
                            "seed": seed,
                            "task_id": task["task_id"],
                            "step": step,
                            "op_id": op.op_id,
                            "definition_hash": entry.definition_hash,
                            "action_key": akey,
                            "ranker_admit": admit,
                            "fingerprint": fp,
                            "diagnosis_only": True,
                            "cache_hit": cf.pop("cache_hit", False),
                        }
                    )
                    cf_rows.append(cf)
            scored.sort()
            for _neg, _h, op, site, examined, row in scored:
                if consult.A >= int(consult_budget):
                    if first_exhaustion is None:
                        first_exhaustion = step
                    break
                consult.charge("learned", examined)
                if site is None:
                    consult.rejected_operations += 1
                    continue
                ok, placed, n_internal = _execute(env, site)
                consult.internal_execution += n_internal
                consult.decisions += 1
                consult.note_depth(op.depth)
                if ok:
                    consult.successful_placements += len(placed)
                    acted = True
                    bypassed += 1
                    row["committed"] = True
                    rec["committed"] = True
                    rec["committed_op_id"] = op.op_id
                    rec["committed_action_key"] = row["action_key"]
                    trace.append("LEARNED:" + row["action_key"])
                    break
                consult.rejected_operations += 1
        else:
            rec["budget_exhausted"] = True
            if first_exhaustion is None:
                first_exhaustion = step
        if not acted:
            stop, token = primitive_step(config, env, select_rng, tabu, primitive)
            if token:
                trace.append(token)
                rec["primitive_token"] = token
            if stop:
                reason = stop
                decisions.append(rec)
                break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            decisions.append(rec)
            break
        decisions.append(rec)
        step += 1
    parts = a_components(primitive, consult)
    reason = _finish_reason(env, parts["A"], cap, config, reason)
    return {
        "task_id": task["task_id"],
        "condition": "indexed_ranked",
        "Q": float(env.score),
        "A": parts["A"],
        "primitive_evals": parts["primitive_evals"],
        "learned_evals": parts["learned_evals"],
        "applicability_cost": parts["applicability_cost"],
        "index_cost": parts["index_cost"],
        "ranking_cost": parts["ranking_cost"],
        "consultation_cost": parts["consultation_cost"],
        "gate_cost": parts["gate_cost"],
        "retrieval_cost": parts["retrieval_cost"],
        "A_identity_ok": parts["A_identity_ok"],
        "bypassed_primitive_decisions": bypassed,
        "consult_attempts": consult_attempts,
        "n_commitments": bypassed,
        "first_budget_exhaustion_step": first_exhaustion,
        "primitive_trace": "|".join(trace),
        "termination": reason,
        "decisions": decisions,
        "ranker_rows": ranker_rows,
        "counterfactuals": cf_rows,
        "seed": seed,
    }


def _counterfactual(config, env, select_rng, tabu, prefix_a, site, akey, cache: dict, ledger: dict) -> dict:
    rem_cap = remaining_cap(int(config.eval_cap), prefix_a)
    key = (state_fingerprint(env, prefix_a, select_rng.getstate()), akey, rem_cap)
    if key in cache:
        ledger["cache_hits"] = ledger.get("cache_hits", 0) + 1
        copied = dict(cache[key])
        copied["cache_hit"] = True
        return copied
    skip, commit, ok, n_internal = remaining_pair(config, env, select_rng, tabu, site, rem_cap)
    ledger["commit_rollouts"] = ledger.get("commit_rollouts", 0) + 1
    ledger["skip_rollouts"] = ledger.get("skip_rollouts", 0) + 1
    if ok:
        ledger["skip_A"] = ledger.get("skip_A", 0) + int(skip["A"])
        ledger["commit_A"] = ledger.get("commit_A", 0) + int(commit["A"])
        remaining_saving = skip["A"] - commit["A"]
        quality_ok = commit["Q"] >= skip["Q"] - config.quality_loss_margin
        payload = {
            "ok": True,
            "A_skip": skip["A"],
            "A_commit": commit["A"],
            "remaining_saving": remaining_saving,
            "Q_skip": skip["Q"],
            "Q_commit": commit["Q"],
            "quality_ok": quality_ok,
            "beneficial_free": quality_ok and remaining_saving > 0,
            "internal_execution": n_internal,
            "cache_hit": False,
        }
    else:
        payload = {"ok": False, "beneficial_free": False, "quality_ok": False, "remaining_saving": None, "cache_hit": False}
    cache[key] = payload
    return dict(payload)
