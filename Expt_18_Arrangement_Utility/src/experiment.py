"""Expt-18 driver. Sample Expt-17 legal placements and replay paired continuations."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

from config import Config
from diagnostic import _finish_reason, primitive_step
from environment import PackingEnv
from inventory import Inventory
from pieces import catalogue_hash
from solver import Ledger, make_rng
from utility import (
    box_opportunity,
    decide,
    earliest_in_stage,
    normalize_pattern,
    replay_branch,
    sample_indices,
    select_patterns,
)

REPO = Path(__file__).resolve().parents[2]
EXPT16 = REPO / "Expt_16_Search_Acquired_Local_Memory"
EXPT17_FROZEN = (
    REPO / "Expt_17_Arrangement_Census" / "results" / "20260930_090000_diagnostic" / "frozen.json"
)
WORKLOADS = ("independent_fresh", "recurring_family")


def manifest_hashes() -> dict[str, str]:
    out = {}
    for line in (EXPT16 / "manifests" / "MANIFEST_HASHES.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            out[name.strip()] = digest
    return out


def load_manifest(name: str) -> dict:
    path = EXPT16 / "manifests" / f"{name}.json"
    raw = path.read_bytes()
    expect = manifest_hashes().get(f"{name}.json")
    got = hashlib.sha256(raw).hexdigest()
    if expect != got:
        raise RuntimeError(f"manifest hash mismatch for {name}.json")
    return json.loads(raw.decode("utf-8"))


def load_frozen(config: Config) -> list[dict]:
    raw = EXPT17_FROZEN.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != config.frozen_sha256:
        raise RuntimeError("Expt-17 frozen dictionary hash does not match the predeclared digest")
    patterns = [normalize_pattern(item, index) for index, item in enumerate(json.loads(raw.decode("utf-8")))]
    return patterns


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (json.dumps(v) if isinstance(v, (list, dict, tuple)) else v) for k, v in row.items()})


def _mean(vals) -> float | None:
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _median(vals) -> float | None:
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    if len(vals) % 2:
        return float(vals[mid])
    return (vals[mid - 1] + vals[mid]) / 2


def trace_primitive(config: Config, task: dict, phase: str, index: int) -> dict:
    """Ordinary primitive trajectory. A snapshot is taken at every prefix, including the empty board."""
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    rng = make_rng(int(config.applicability_seed), task["task_id"], phase, index, "select")
    snaps = []

    def snap(open_prefix: bool) -> None:
        snaps.append({
            "env": env.clone(),
            "rng_state": rng.getstate(),
            "tabu": set(tabu),
            "prefix_A": int(ledger.A),
            "occupied": int(env.occupied),
            "n_place": len(env.stack),
            "open_prefix": open_prefix,
        })

    snap(True)
    reason = "quality"
    entered = False
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        entered = True
        stop, _token = primitive_step(config, env, rng, tabu, ledger)
        ended = bool(stop) or env.terminal or env.occupied >= config.q_min or ledger.A >= cap
        snap(not ended)
        if stop:
            reason = stop
            break
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
        if ended:
            break
    if not entered:
        snaps[0]["open_prefix"] = False
    reason = _finish_reason(env, ledger.A, cap, config, reason)
    return {
        "Q": float(env.score),
        "A": int(ledger.A),
        "acceptable": bool(env.score >= config.q_min),
        "termination": reason,
        "snaps": snaps,
    }


def _candidate_row(config: Config, workload: str, index: int, task: dict, pattern: dict, stage: str, snap: dict, origin, primitive: dict, commit: dict, traced: dict) -> dict:
    replay_ok = (
        commit is not None
        and primitive["Q"] is not None
        and abs(primitive["Q"] - traced["Q"]) < 1e-9
        and int(snap["prefix_A"]) + int(primitive["A"]) == int(traced["A"])
    )
    valid = bool(commit["valid"]) if commit else False
    quality_delta = None
    quality_loss = False
    acceptability_lost = False
    effort_saving = None
    if valid and primitive["Q"] is not None and commit["Q"] is not None:
        quality_delta = float(commit["Q"]) - float(primitive["Q"])
        quality_loss = quality_delta < -float(config.quality_loss_margin)
        acceptability_lost = bool(primitive["acceptable"]) and not bool(commit["acceptable"])
        effort_saving = int(primitive["A"]) - int(commit["A"])
    benefit = bool(
        replay_ok
        and valid
        and effort_saving is not None
        and effort_saving > 0
        and not quality_loss
        and not acceptability_lost
    )
    return {
        "workload": workload,
        "index": index,
        "task_id": task["task_id"],
        "pattern_index": pattern["pattern_index"],
        "pieces": pattern["pieces"],
        "n_inventories": pattern["n_inventories"],
        "stage": stage,
        "occupied": snap["occupied"],
        "n_place": snap["n_place"],
        "prefix_A": snap["prefix_A"],
        "origin_x": origin[0],
        "origin_y": origin[1],
        "Q_primitive": primitive["Q"],
        "A_rest_primitive": primitive["A"],
        "acceptable_primitive": primitive["acceptable"],
        "Q_commit": commit["Q"],
        "A_rest_commit": commit["A"],
        "validation_checks": commit["validation"],
        "acceptable_commit": commit["acceptable"],
        "valid": valid,
        "replay_ok": replay_ok,
        "effort_saving": effort_saving,
        "quality_delta": quality_delta,
        "quality_loss": quality_loss,
        "acceptability_lost": acceptability_lost,
        "quality_preserving_benefit": benefit,
        "termination_primitive": primitive["termination"],
        "termination_commit": commit["termination"],
    }


def _stats(rows: list[dict]) -> dict:
    def block(group: list[dict]) -> dict:
        if not group:
            return {"n": 0}
        savings = [row["effort_saving"] for row in group]
        return {
            "n": len(group),
            "mean_effort_saving": _mean(savings),
            "median_effort_saving": _median(savings),
            "mean_quality_delta": _mean([row["quality_delta"] for row in group]),
            "n_quality_loss": sum(1 for row in group if row["quality_loss"]),
            "n_positive_saving": sum(1 for row in group if row["effort_saving"] is not None and row["effort_saving"] > 0),
        }

    valid = [row for row in rows if row["valid"] and row["replay_ok"]]
    return {
        "n_rows": len(rows),
        "n_invalid": sum(1 for row in rows if not row["valid"]),
        "n_replay_failed": sum(1 for row in rows if not row["replay_ok"]),
        "valid_replayed": block(valid),
        "quality_preserving": block([row for row in rows if row["quality_preserving_benefit"]]),
        "note": "Candidate-level averages. Do not add them across prefixes of the same box.",
    }


def run_experiment(config: Config) -> dict:
    frozen = load_frozen(config)
    patterns = select_patterns(frozen, config)
    fresh_tasks = load_manifest("applicability_fresh")["tasks"]
    family_tasks = load_manifest("applicability_family")["tasks"]
    fresh_n = config.fresh_sample_boxes if config.fresh_sample_boxes_override is None else config.fresh_sample_boxes_override
    family_n = config.family_sample_boxes if config.family_sample_boxes_override is None else config.family_sample_boxes_override
    chosen = {
        "independent_fresh": sample_indices(len(fresh_tasks), config.fresh_stride, fresh_n),
        "recurring_family": sample_indices(len(family_tasks), config.family_stride, family_n),
    }
    tasks = {"independent_fresh": fresh_tasks, "recurring_family": family_tasks}
    sample = {
        "pattern_indices": [item["pattern_index"] for item in patterns],
        "high_support_indices": [item["pattern_index"] for item in patterns if item["n_inventories"] >= config.high_support],
        "boxes": chosen,
        "stages": list(config.stages),
    }
    rows: list[dict] = []
    discovery = 0
    counterfactual_a = 0
    started = time.perf_counter()
    for workload in WORKLOADS:
        phase = f"{config.applicability_phase}-{workload}"
        for index in chosen[workload]:
            task = tasks[workload][index]
            print(f"{workload} box {index} {task['task_id']}", flush=True)
            traced = trace_primitive(config, task, phase, index)
            for pattern in patterns:
                for stage in config.stages:
                    cost, snap, origin = earliest_in_stage(traced["snaps"], pattern, stage, config)
                    discovery += cost
                    if snap is None:
                        continue
                    primitive = replay_branch(config, snap, None, None)
                    commit = replay_branch(config, snap, pattern, origin)
                    counterfactual_a += int(primitive["A"]) + int(commit["A"])
                    rows.append(_candidate_row(config, workload, index, task, pattern, stage, snap, origin, primitive, commit, traced))
    by_box: dict[tuple, list] = {}
    for row in rows:
        by_box.setdefault((row["workload"], row["index"]), []).append(row)
    box_rows = []
    for workload in WORKLOADS:
        for index in chosen[workload]:
            task = tasks[workload][index]
            opp = box_opportunity(by_box.get((workload, index), []), config)
            box_rows.append({
                "workload": workload,
                "index": index,
                "task_id": task["task_id"],
                **opp,
            })
    fresh_boxes = [box for box in box_rows if box["workload"] == "independent_fresh"]
    family_boxes = [box for box in box_rows if box["workload"] == "recurring_family"]
    n_replay_failed = sum(1 for row in rows if not row["replay_ok"])
    decision = decide(config, fresh_boxes, family_boxes, len(rows), n_replay_failed)
    return {
        "sample": sample,
        "n_frozen": len(frozen),
        "candidate_rows": rows,
        "box_rows": box_rows,
        "candidates": {
            "independent_fresh": _stats([row for row in rows if row["workload"] == "independent_fresh"]),
            "recurring_family": _stats([row for row in rows if row["workload"] == "recurring_family"]),
        },
        "diagnostic_cost": {
            "discovery_checks": discovery,
            "counterfactual_A": counterfactual_a,
            "seconds": time.perf_counter() - started,
            "role": "diagnostic only; not a deployable matcher and not a relaxation of the Expt-17 cost gate",
        },
        "decision": decision,
        "catalogue_hash": catalogue_hash(),
    }


def audit_implementation() -> dict:
    return {
        "catalogue_hash": catalogue_hash(),
        "frozen": str(EXPT17_FROZEN),
        "commitment_policy": False,
    }
