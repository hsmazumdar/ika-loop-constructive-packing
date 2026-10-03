"""Primitive trajectory snapshots. Occupancy schedule is coverage, not a context rule."""

from __future__ import annotations

import copy
import hashlib
import json

from diagnostic import _finish_reason, primitive_step
from environment import PackingEnv
from inventory import Inventory
from solver import Ledger, make_rng


def state_fingerprint(env, prefix_a: int, rng_state) -> str:
    payload = {
        "mask": int(env.mask),
        "inventory": env.inventory.as_dict(),
        "occupied": env.occupied,
        "actions_used": env.actions_used,
        "undos": env.undos,
        "prefix_A": int(prefix_a),
        "rng": repr(rng_state),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def restore_rng(select_rng, rng_state) -> None:
    select_rng.setstate(rng_state)


def primitive_remaining(config, env, select_rng, tabu, cap, *, want_trace: bool = False) -> dict:
    ledger = Ledger()
    reason = "quality"
    trace = []
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        stop, token = primitive_step(config, env, select_rng, tabu, ledger)
        if token:
            trace.append(token)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    out = {
        "Q": float(env.score),
        "A": ledger.A,
        "acceptable": env.score >= config.q_min,
        "termination": reason,
        "primitive_evals": ledger.primitive_evals,
        "occupied": env.occupied,
    }
    if want_trace:
        out["trace"] = "|".join(trace)
    return out


def run_primitive_snapshots(config, task, seed, phase, repetition) -> dict:
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    raw = []
    trace = []
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        raw.append(
            {
                "occupied": env.occupied,
                "env": env.clone(),
                "rng_state": select_rng.getstate(),
                "tabu": set(tabu),
                "prefix_A": ledger.A,
                "actions_used": env.actions_used,
                "undos": env.undos,
                "fingerprint": state_fingerprint(env, ledger.A, select_rng.getstate()),
            }
        )
        stop, token = primitive_step(config, env, select_rng, tabu, ledger)
        if token:
            trace.append(token)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    picked = _pick_schedule(raw, config.occupancy_schedule, config.max_states_per_box)
    reached = {s["occupancy_target"] for s in picked}
    return {
        "Q": float(env.score),
        "A": ledger.A,
        "acceptable": env.score >= config.q_min,
        "termination": reason,
        "primitive_evals": ledger.A,
        "trace": "|".join(trace),
        "snapshots": picked,
        "n_decisions": len(raw),
        "unreachable_occupancy": [int(t) for t in config.occupancy_schedule if t not in reached],
    }


def _pick_schedule(raw: list[dict], schedule, max_states: int) -> list[dict]:
    picked = []
    used = set()
    for threshold in schedule:
        found = None
        for item in raw:
            if item["occupied"] >= threshold and item["fingerprint"] not in used:
                found = item
                break
        if found is None:
            continue
        used.add(found["fingerprint"])
        rec = dict(found)
        rec["state_index"] = len(picked)
        rec["occupancy_target"] = threshold
        rec["reachable"] = True
        picked.append(rec)
        if len(picked) >= max_states:
            break
    return picked


def remaining_cap(eval_cap: int, prefix_a: int) -> int:
    return max(0, int(eval_cap) - int(prefix_a))
