"""Single-intervention oracle and frozen-policy comparison for one library–box pair."""

from __future__ import annotations

import json

from diagnostic import solve_gated
from enumerate_ops import enumerate_legal, inventory_compatible
from gates import commit_vector, consult_vector
from library_io import definition_hash
from retrieval import state_features
from snapshot import primitive_remaining, remaining_cap, restore_rng, run_primitive_snapshots
from solver import _execute, make_rng


def select_free_oracle(candidate_rows: list[dict], prim_a: float, prim_q: float, margin: float) -> dict | None:
    """Minimum whole-box A among quality-ok candidates. Prefer primitive on an effort tie."""
    selected = None
    for row in candidate_rows:
        if not row.get("quality_vs_primitive_box"):
            continue
        if float(row["Q_commit"]) < float(prim_q) - float(margin):
            continue
        a_box = float(row["A_box_candidate"])
        if a_box > float(prim_a):
            continue
        if a_box == float(prim_a):
            continue
        key = (a_box, int(row["state_index"]), str(row["action_key"]))
        if selected is None or key < (float(selected["A_box_candidate"]), int(selected["state_index"]), str(selected["action_key"])):
            selected = row
    return selected


def _suffix(config, snap, cap):
    env = snap["env"].clone()
    rng = make_rng(0, "x", "y", 0, "select")
    restore_rng(rng, snap["rng_state"])
    tabu = set(snap["tabu"])
    return primitive_remaining(config, env, rng, tabu, cap, want_trace=True)


def diagnose_pair(config, task, seed, box_index, bundle: dict, diagnostic_ledger: dict) -> dict:
    memory = bundle["memory"]
    consult_gate = bundle["consult_gate"]
    commit_gate = bundle["commit_gate"]
    lib_hash = bundle["library_hash"]
    cap = int(config.eval_cap)
    prim = run_primitive_snapshots(config, task, seed, "expt6", box_index)
    diagnostic_ledger["primitive_boxes"] = diagnostic_ledger.get("primitive_boxes", 0) + 1
    frozen = solve_gated(
        config, task, seed, "expt6", box_index, memory, "both_gates", consult_gate, commit_gate
    )
    frozen["A_identity_ok"] = bool(frozen.get("A_identity_ok"))
    c_box = 0
    chooser = int(config.chooser_cost)
    candidate_rows = []
    state_rows = []
    incomplete_any = False
    skip_identity_ok = True
    n_composed_active = sum(1 for op in memory.active() if op.depth > 1)
    n_composed_legal = 0
    for snap in prim["snapshots"]:
        rem_cap = remaining_cap(cap, snap["prefix_A"])
        skip = _suffix(config, snap, rem_cap)
        diagnostic_ledger["skip_A"] = diagnostic_ledger.get("skip_A", 0) + int(skip["A"])
        diagnostic_ledger["skip_rollouts"] = diagnostic_ledger.get("skip_rollouts", 0) + 1
        expected_a = int(prim["A"]) - int(snap["prefix_A"])
        snap_ok = abs(int(skip["A"]) - expected_a) == 0 and abs(float(skip["Q"]) - float(prim["Q"])) < 1e-9
        skip_identity_ok = skip_identity_ok and snap_ok
        remaining = snap["env"].inventory.as_dict()
        active = memory.active()
        c_box += len(active)
        feats = state_features(snap["env"])
        consult_vec = consult_vector(snap["occupied"], remaining, snap["actions_used"], snap["undos"])
        consult_would = consult_gate.admit(consult_vec)
        diagnostic_ledger["gate_probes"] = diagnostic_ledger.get("gate_probes", 0) + 1
        n_compat = 0
        n_legal_ops = 0
        n_legal_actions = 0
        n_beneficial = 0
        state_incomplete = False
        for op in active:
            c_box += 1
            if not inventory_compatible(op, snap["env"]):
                continue
            n_compat += 1
            enum = enumerate_legal(op, snap["env"], config.max_candidates_per_state)
            c_box += int(enum["examined"])
            if enum["incomplete"]:
                state_incomplete = True
                incomplete_any = True
            if enum["n_legal"] <= 0:
                continue
            n_legal_ops += 1
            if op.depth > 1:
                n_composed_legal += 1
            n_legal_actions += enum["n_legal"]
            _useful, score = (op.applicability.useful_here(feats) if op.applicability else (True, 0.0))
            commit_vec = commit_vector(
                snap["occupied"], remaining, snap["actions_used"], snap["undos"], len(op.steps), op.depth, score, op.depth > 1
            )
            commit_would = commit_gate.admit(commit_vec, op.op_id)
            for place in enum["placements"]:
                env_c = snap["env"].clone()
                rng_c = make_rng(0, "x", "y", 0, "select")
                restore_rng(rng_c, snap["rng_state"])
                ok, _placed, n_internal = _execute(env_c, place["site"])
                if not ok:
                    continue
                commit = primitive_remaining(config, env_c, rng_c, set(snap["tabu"]), rem_cap, want_trace=False)
                diagnostic_ledger["commit_A"] = diagnostic_ledger.get("commit_A", 0) + int(commit["A"])
                diagnostic_ledger["commit_rollouts"] = diagnostic_ledger.get("commit_rollouts", 0) + 1
                remaining_saving = skip["A"] - commit["A"]
                qdiff = commit["Q"] - skip["Q"]
                quality_ok = qdiff >= -config.quality_loss_margin
                beneficial_free = quality_ok and remaining_saving > 0
                validation = 1
                a_box = snap["prefix_A"] + commit["A"] + validation
                quality_vs_prim = commit["Q"] >= prim["Q"] - config.quality_loss_margin
                row = {
                    "seed": seed,
                    "task_id": task["task_id"],
                    "library_hash": lib_hash,
                    "state_index": snap["state_index"],
                    "occupancy_target": snap["occupancy_target"],
                    "occupied": snap["occupied"],
                    "prefix_A": snap["prefix_A"],
                    "op_id": op.op_id,
                    "definition_hash": definition_hash(op),
                    "depth": op.depth,
                    "composed": op.depth > 1,
                    "action_key": place["action_key"],
                    "A_skip_remaining": skip["A"],
                    "A_commit_remaining": commit["A"],
                    "remaining_saving": remaining_saving,
                    "Q_skip": skip["Q"],
                    "Q_commit": commit["Q"],
                    "quality_difference": qdiff,
                    "quality_ok": quality_ok,
                    "beneficial_free": beneficial_free,
                    "quality_vs_primitive_box": quality_vs_prim,
                    "A_box_candidate": a_box,
                    "internal_execution": n_internal,
                    "mandatory_validation": validation,
                    "skip_termination": skip["termination"],
                    "commit_termination": commit["termination"],
                    "skip_identity_ok": snap_ok,
                    "enumeration_incomplete": enum["incomplete"],
                    "consult_gate_would_admit": consult_would,
                    "commit_gate_would_admit": commit_would,
                    "gate_would_select": consult_would and commit_would,
                    "diagnosis_only": True,
                }
                candidate_rows.append(row)
                if beneficial_free:
                    n_beneficial += 1
        state_rows.append(
            {
                "seed": seed,
                "task_id": task["task_id"],
                "library_hash": lib_hash,
                "state_index": snap["state_index"],
                "occupancy_target": snap["occupancy_target"],
                "occupied": snap["occupied"],
                "prefix_A": snap["prefix_A"],
                "fingerprint": snap["fingerprint"],
                "n_active": len(active),
                "n_inventory_compatible": n_compat,
                "n_ops_with_legal_placement": n_legal_ops,
                "n_legal_actions": n_legal_actions,
                "n_beneficial_free": n_beneficial,
                "consult_gate_would_admit": consult_would,
                "incomplete": state_incomplete,
                "skip_identity_ok": snap_ok,
                "skip_A": skip["A"],
                "skip_Q": skip["Q"],
                "expected_skip_A": expected_a,
            }
        )
    c_box += chooser
    selected = select_free_oracle(candidate_rows, prim["A"], prim["Q"], config.quality_loss_margin)
    overlap = 1 if selected is not None else 0
    c_box_charged = max(0, c_box - overlap)
    a_free = prim["A"] if selected is None else selected["A_box_candidate"]
    q_free = prim["Q"] if selected is None else selected["Q_commit"]
    a_scan = a_free + c_box_charged
    found_opportunity = any(r["beneficial_free"] for r in candidate_rows)
    if found_opportunity:
        has_opportunity = True
    elif incomplete_any:
        has_opportunity = None
    else:
        has_opportunity = False
    box_row = {
        "seed": seed,
        "task_id": task["task_id"],
        "library_hash": lib_hash,
        "library_reconstructed": True,
        "Q_primitive": prim["Q"],
        "A_primitive": prim["A"],
        "termination_primitive": prim["termination"],
        "Q_both_gates": frozen["Q"],
        "A_both_gates": frozen["A"],
        "gate_cost_both": frozen.get("gate_cost") or 0,
        "consultation_both": frozen.get("consultation_cost") or 0,
        "A_identity_ok_both": frozen.get("A_identity_ok"),
        "Q_oracle_free": q_free,
        "A_oracle_free": a_free,
        "saving_oracle_free": prim["A"] - a_free,
        "Q_oracle_scan": q_free,
        "A_oracle_scan": a_scan,
        "saving_oracle_scan": prim["A"] - a_scan,
        "C_box": c_box,
        "C_box_charged": c_box_charged,
        "chooser_cost": chooser,
        "validation_overlap_subtracted": overlap,
        "intervention_op_id": None if selected is None else selected["op_id"],
        "intervention_definition_hash": None if selected is None else selected["definition_hash"],
        "intervention_state_index": None if selected is None else selected["state_index"],
        "intervention_occupancy": None if selected is None else selected["occupied"],
        "n_snapshots": len(prim["snapshots"]),
        "n_candidates": len(candidate_rows),
        "n_beneficial_free": sum(1 for r in candidate_rows if r["beneficial_free"]),
        "has_opportunity": has_opportunity,
        "oracle_complete": not incomplete_any,
        "oracle_kind": "sampled_candidate_oracle" if incomplete_any else "exhaustive",
        "cap_hit_primitive": prim["termination"] == "eval_cap",
        "cap_hit_frozen": frozen.get("termination") == "eval_cap",
        "unreachable_occupancy": json.dumps(prim["unreachable_occupancy"]),
        "n_composed_active": n_composed_active,
        "n_composed_legal": n_composed_legal,
        "quality_ok_oracle_free": q_free >= prim["Q"] - config.quality_loss_margin,
        "Q_ge_75_primitive": prim["Q"] >= config.q_min,
        "Q_ge_75_oracle_free": q_free >= config.q_min,
        "Q_ge_75_both": frozen["Q"] >= config.q_min,
        "skip_identity_ok": skip_identity_ok,
        "A_identity_ok_primitive": True,
    }
    diagnostic_ledger["C_box_sum"] = diagnostic_ledger.get("C_box_sum", 0) + c_box
    diagnostic_ledger["incomplete_pairs"] = diagnostic_ledger.get("incomplete_pairs", 0) + int(incomplete_any)
    return {"box": box_row, "states": state_rows, "candidates": candidate_rows, "frozen": frozen, "primitive": prim}
