"""Collect matched-state labels, including legal candidates the current policy did not commit."""

from __future__ import annotations

import json

from diagnostic import list_legal_candidates, primitive_step, remaining_pair
from environment import PackingEnv
from gates import commit_vector, consult_vector
from inventory import Inventory
from solver import Ledger, _execute, make_rng


def _record(config, task, seed, split_name, choice_index, rec, skip, commit, check_cost, env, selected: bool) -> dict:
    remaining_saving = skip["A"] - commit["A"]
    quality_ok = commit["Q"] >= skip["Q"] - config.quality_loss_margin
    effort_ok = remaining_saving > check_cost
    remaining = env.inventory.as_dict()
    return {
        "decision_id": f"{seed}:{task['task_id']}:{split_name}:{choice_index}:{rec['op'].op_id}:sel{int(selected)}",
        "task_id": task["task_id"],
        "seed": seed,
        "split": split_name,
        "choice_index": choice_index,
        "op_id": rec["op"].op_id,
        "depth": rec["op"].depth,
        "composed": rec["composed"],
        "op_size": rec["op_size"],
        "selected_by_current_policy": selected,
        "applicability_passed": rec["useful"],
        "check_cost": check_cost,
        "A_remaining_primitive": skip["A"],
        "A_remaining_after_commit": commit["A"],
        "effort_saving_remaining": remaining_saving,
        "Q_remaining_primitive": skip["Q"],
        "Q_remaining_after_commit": commit["Q"],
        "quality_ok": quality_ok,
        "effort_ok": effort_ok,
        "acceptable_success": effort_ok and quality_ok,
        "occupied_at_choice": env.occupied,
        "remaining_piece_count": sum(remaining.values()),
        "remaining_pieces": json.dumps(remaining, sort_keys=True),
        "actions_used": env.actions_used,
        "undos": env.undos,
        "applicability_score": rec["score"],
        "consult_vector": consult_vector(env.occupied, remaining, env.actions_used, env.undos),
        "commit_vector": commit_vector(
            env.occupied, remaining, env.actions_used, env.undos, rec["op_size"], rec["op"].depth, rec["score"], rec["composed"]
        ),
        "diagnosis_only": True,
    }


def collect_box(config, task, seed, phase, repetition, memory, split_name: str, sample_rng) -> tuple[list[dict], int]:
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    primitive = Ledger()
    consult = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    records = []
    choice_index = 0
    selected_n = 0
    unchosen_n = 0
    learning_replay_a = 0
    max_selected = int(config.max_replays_per_box)
    max_unchosen = int(config.unchosen_samples_per_box)
    while not env.terminal and env.occupied < config.q_min and primitive.A < cap:
        legal, policy, check_cost = list_legal_candidates(
            config, env, memory, seed, task["task_id"], phase, repetition, primitive.decisions + consult.decisions, consult
        )
        to_label = []
        if policy is not None and selected_n < max_selected:
            to_label.append((policy, True))
        others = [rec for rec in legal if rec is not policy]
        sample_rng.shuffle(others)
        if unchosen_n < max_unchosen and others:
            to_label.append((others[0], False))
        for rec, selected in to_label:
            skip, commit, ok, _n_internal = remaining_pair(config, env, select_rng, tabu, rec["site"], cap)
            if not ok:
                continue
            learning_replay_a += int(skip["A"]) + int(commit["A"])
            records.append(_record(config, task, seed, split_name, choice_index, rec, skip, commit, check_cost, env, selected))
            records[-1]["learning_remaining_A"] = int(skip["A"]) + int(commit["A"])
            choice_index += 1
            if selected:
                selected_n += 1
            else:
                unchosen_n += 1
        if policy is not None:
            _execute(env, policy["site"])
            consult.decisions += 1
            continue
        stop, _token = primitive_step(config, env, select_rng, tabu, primitive)
        if stop:
            break
        if env.terminal:
            break
    learning_a = primitive.A + consult.A + learning_replay_a
    return records, learning_a
