"""Expt-19 driver. Development sets the budget. Validation fresh is the decision set.

Commitment is disabled. Counterfactual replays are diagnostic and are not
part of the recognition cost.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from config import Config
from diagnostic import _finish_reason, primitive_step
from environment import PackingEnv
from inventory import Inventory
from matcher import Budget, Recogniser, absolute_budget, changed_piece_types
from pieces import catalogue_hash
from solver import Ledger, make_rng
from utility import first_translation, normalize_pattern, replay_branch, select_patterns, stage_name

REPO = Path(__file__).resolve().parents[2]
EXPT16 = REPO / "Expt_16_Search_Acquired_Local_Memory"
EXPT17_FROZEN = (
    REPO / "Expt_17_Arrangement_Census" / "results" / "20260930_090000_diagnostic" / "frozen.json"
)
DEVELOPMENT = ("applicability_fresh", "applicability_family")
EVALUATION = ("validation_fresh", "validation_family")


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
        raise RuntimeError("frozen dictionary hash mismatch")
    return [normalize_pattern(item, index) for index, item in enumerate(json.loads(raw.decode("utf-8")))]


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


def trace_primitive(config: Config, task: dict, phase: str, index: int) -> dict:
    cap = int(config.eval_cap)
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    tabu: set = set()
    rng = make_rng(int(config.seed), task["task_id"], phase, index, "select")
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
    return {"Q": float(env.score), "A": int(ledger.A), "acceptable": bool(env.score >= config.q_min), "termination": reason, "snaps": snaps}


def _occupied(env) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for inst in env.stack:
        cells.update(inst.cells)
    return cells


def _remaining(env) -> dict[str, int]:
    return {str(k): int(v) for k, v in env.inventory.counts.items()}


def audited_prefixes(snaps: list[dict], config: Config) -> list[int]:
    """Start, and the first middle prefix. Not chosen by which prefix saved effort."""
    chosen = [0]
    for index, snap in enumerate(snaps):
        name = stage_name(int(snap["occupied"]), int(config.early_below), int(config.middle_below))
        if name == "middle":
            if index != 0:
                chosen.append(index)
            break
    return chosen


def _useful(config: Config, snap: dict, traced: dict, primitive: dict, commit: dict) -> dict:
    replay_ok = (
        primitive["Q"] is not None
        and abs(float(primitive["Q"]) - float(traced["Q"])) < 1e-9
        and int(snap["prefix_A"]) + int(primitive["A"]) == int(traced["A"])
    )
    saving = None
    quality_delta = None
    quality_loss = False
    acceptability_lost = False
    if commit["valid"] and commit["Q"] is not None and primitive["Q"] is not None:
        quality_delta = float(commit["Q"]) - float(primitive["Q"])
        quality_loss = quality_delta < -float(config.quality_loss_margin)
        acceptability_lost = bool(primitive["acceptable"]) and not bool(commit["acceptable"])
        saving = int(primitive["A"]) - int(commit["A"])
    useful = bool(
        replay_ok
        and commit["valid"]
        and saving is not None
        and saving >= int(config.min_saving)
        and not quality_loss
        and not acceptability_lost
    )
    return {
        "replay_ok": replay_ok,
        "valid": bool(commit["valid"]),
        "effort_saving": saving,
        "quality_delta": quality_delta,
        "quality_loss": quality_loss,
        "useful": useful,
        "diagnostic_A": int(primitive["A"]) + int(commit["A"]),
    }


def miss_reason(action: dict, consult: dict | None) -> str:
    if consult is None:
        return "budget_before_state"
    origin = (int(action["origin_x"]), int(action["origin_y"]))
    index = int(action["pattern_index"])
    exposed = {(int(item["pattern_index"]), tuple(item["origin"])) for item in consult["exposed"]}
    if (index, origin) in exposed:
        return "exposed"
    if index in set(consult.get("unchecked") or []):
        return "budget_during_consult"
    if index in set(consult["inventory_rejected"]):
        return "inventory"
    anchors = {tuple(item) for item in consult["anchors"]}
    if not consult["anchor_complete"] and origin not in anchors:
        return "budget_during_anchor"
    if origin not in anchors:
        return "anchor"
    tested = {(int(item["pattern_index"]), tuple(item["origin"])) for item in consult["tested"]}
    if (index, origin) not in tested and (index, origin) not in exposed:
        return "budget_during_consult"
    return "not_exposed"


def recognise_box(config: Config, snaps: list[dict], patterns: list[dict], limit: int) -> tuple[Recogniser, list[dict]]:
    budget = Budget(limit)
    recogniser = Recogniser(patterns, budget)
    if not snaps:
        return recogniser, []
    recogniser.filter_inventory(_remaining(snaps[0]["env"]), None)
    previous = snaps[0]
    consulted = []
    for index, snap in enumerate(snaps):
        if index:
            changed_cells = _occupied(snap["env"]).symmetric_difference(_occupied(previous["env"]))
            recogniser.invalidate(changed_cells)
            recogniser.filter_inventory(_remaining(snap["env"]), changed_piece_types(_remaining(previous["env"]), _remaining(snap["env"])))
            previous = snap
        if recogniser.stopped or recogniser.budget.exhausted:
            break
        consulted.append(recogniser.consult(index, _occupied(snap["env"]), config))
    return recogniser, consulted


def _reference_at(config: Config, task: dict, traced: dict, snap: dict, pattern: dict, prefix: int) -> tuple[dict, int]:
    """One sampled action: the first row-major legal translation at this prefix. Diagnostic only."""
    cost, origin = first_translation(pattern, _occupied(snap["env"]), Counter(_remaining(snap["env"])))
    stage = stage_name(int(snap["occupied"]), int(config.early_below), int(config.middle_below))
    base = {
        "pattern_index": pattern["pattern_index"],
        "n_inventories": pattern["n_inventories"],
        "pieces": pattern["pieces"],
        "prefix": prefix,
        "stage": stage,
        "occupied": snap["occupied"],
        "origin_x": None if origin is None else origin[0],
        "origin_y": None if origin is None else origin[1],
        "legal": origin is not None,
        "useful": False,
        "effort_saving": None,
        "quality_delta": None,
        "replay_ok": False,
        "discovery_checks": cost,
        "diagnostic_A": 0,
    }
    if origin is None:
        return base, cost
    primitive = replay_branch(config, snap, None, None)
    commit = replay_branch(config, snap, pattern, origin)
    judged = _useful(config, snap, traced, primitive, commit)
    base.update(judged)
    return base, cost + int(judged["diagnostic_A"])


def score_box(config: Config, workload: str, index: int, task: dict, traced: dict, patterns: list[dict], reference: list[dict], limit: int) -> tuple[dict, list[dict]]:
    recogniser, consults = recognise_box(config, traced["snaps"], patterns, limit)
    by_prefix = {int(item["prefix"]): item for item in consults}
    targets = audited_prefixes(traced["snaps"], config)
    rows = []
    diagnostic_checks = 0
    diagnostic_a = 0
    for prefix in targets:
        snap = traced["snaps"][prefix]
        for pattern in reference:
            action, spent = _reference_at(config, task, traced, snap, pattern, prefix)
            diagnostic_checks += int(action["discovery_checks"])
            diagnostic_a += int(action["diagnostic_A"])
            if not action["legal"]:
                continue
            consult = by_prefix.get(prefix)
            reason = miss_reason(action, consult)
            rows.append({
                "workload": workload,
                "index": index,
                "task_id": task["task_id"],
                **action,
                "exposed": reason == "exposed",
                "miss_reason": reason,
            })
    useful = [row for row in rows if row["useful"]]
    exposed_useful = [row for row in useful if row["exposed"]]
    oracle = max(useful, key=lambda row: (row["effort_saving"], -row["pattern_index"])) if useful else None
    retained_rows = exposed_useful
    retained = max(retained_rows, key=lambda row: row["effort_saving"])["effort_saving"] if retained_rows else 0
    unlabeled = 0
    labeled = {(int(row["pattern_index"]), int(row["origin_x"]), int(row["origin_y"]), int(row["prefix"])) for row in rows}
    for consult in consults:
        if int(consult["prefix"]) not in set(targets):
            unlabeled += len(consult["exposed"])
            continue
        for item in consult["exposed"]:
            origin = tuple(item["origin"])
            key = (int(item["pattern_index"]), int(origin[0]), int(origin[1]), int(consult["prefix"]))
            if key not in labeled:
                unlabeled += 1
    cost = recogniser.budget.as_dict()
    box = {
        "workload": workload,
        "index": index,
        "task_id": task["task_id"],
        "primitive_A": traced["A"],
        "recognition": cost["spent"],
        "recognition_ratio": (cost["spent"] / traced["A"]) if traced["A"] else None,
        "under_gate": bool(traced["A"] and cost["spent"] < float(config.cheap_fraction) * traced["A"]),
        "budget_exhausted": cost["exhausted"],
        "n_consults": len(consults),
        "n_reference_actions": len(rows),
        "n_useful": len(useful),
        "n_useful_exposed": len(exposed_useful),
        "oracle_saving": 0 if oracle is None else oracle["effort_saving"],
        "oracle_pattern": None if oracle is None else oracle["pattern_index"],
        "oracle_support": None if oracle is None else oracle["n_inventories"],
        "oracle_stage": None if oracle is None else oracle["stage"],
        "retained_saving": retained if oracle is not None else 0,
        "retention": None if oracle is None else (retained / oracle["effort_saving"] if oracle["effort_saving"] else None),
        "unlabeled_exposures": unlabeled,
        **{f"cost_{key}": cost[key] for key in ("inventory", "anchor", "geometry", "cache_create", "cache_invalidate", "lookup")},
        "diagnostic_checks": diagnostic_checks,
        "diagnostic_A": diagnostic_a,
    }
    return box, rows


def _mean(vals) -> float | None:
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _workload_summary(boxes: list[dict], rows: list[dict]) -> dict:
    useful = [row for row in rows if row["useful"]]
    states: dict[tuple, list] = {}
    for row in useful:
        states.setdefault((row["workload"], row["index"], row["prefix"]), []).append(row)
    hits = sum(1 for group in states.values() if any(row["exposed"] for row in group))
    with_ref = [box for box in boxes if box["n_useful"]]
    reasons = Counter(row["miss_reason"] for row in useful)

    def support_block(min_support: int | None, exact: int | None) -> dict:
        if exact is None:
            group = [row for row in useful if int(row["n_inventories"]) >= int(min_support)]
            chosen = [box for box in with_ref if box["oracle_support"] is not None and int(box["oracle_support"]) >= int(min_support)]
        else:
            group = [row for row in useful if int(row["n_inventories"]) == int(exact)]
            chosen = [box for box in with_ref if box["oracle_support"] is not None and int(box["oracle_support"]) == int(exact)]
        return {
            "useful_actions": len(group),
            "exposed_actions": sum(1 for row in group if row["exposed"]),
            "action_recall": (sum(1 for row in group if row["exposed"]) / len(group)) if group else None,
            "n_boxes": len(chosen),
            "mean_retention": _mean([box["retention"] for box in chosen]),
        }

    return {
        "n_boxes": len(boxes),
        "mean_primitive": _mean([box["primitive_A"] for box in boxes]),
        "mean_recognition": _mean([box["recognition"] for box in boxes]),
        "mean_ratio": _mean([box["recognition_ratio"] for box in boxes]),
        "boxes_under_gate": sum(1 for box in boxes if box["under_gate"]),
        "boxes_budget_exhausted": sum(1 for box in boxes if box["budget_exhausted"]),
        "n_boxes_with_reference": len(with_ref),
        "state_recall": (hits / len(states)) if states else None,
        "n_audited_states_with_useful": len(states),
        "action_recall": (sum(1 for row in useful if row["exposed"]) / len(useful)) if useful else None,
        "n_useful_actions": len(useful),
        "mean_retention": _mean([box["retention"] for box in with_ref]),
        "mean_oracle_saving": _mean([box["oracle_saving"] for box in with_ref]),
        "mean_retained_saving": _mean([box["retained_saving"] for box in with_ref]),
        "miss_reasons": dict(reasons),
        "high_support": support_block(3, None),
        "support_two": support_block(None, 2),
        "unlabeled_exposures": sum(box["unlabeled_exposures"] for box in boxes),
        "diagnostic_A": sum(box["diagnostic_A"] for box in boxes),
        "diagnostic_checks": sum(box["diagnostic_checks"] for box in boxes),
    }


def decide(config: Config, fresh: dict) -> dict:
    mean_p = fresh.get("mean_primitive") or 0
    mean_r = fresh.get("mean_recognition") or 0
    ratio = (mean_r / mean_p) if mean_p else None
    cheap = ratio is not None and ratio < float(config.cheap_fraction)
    recall = fresh.get("state_recall")
    retention = fresh.get("mean_retention")
    n_ref = int(fresh.get("n_boxes_with_reference") or 0)
    retains = (
        cheap
        and n_ref >= int(config.min_boxes_with_reference)
        and recall is not None
        and retention is not None
        and recall >= float(config.min_state_recall)
        and retention >= float(config.min_retention)
    )
    if not cheap:
        row = "recognition_expensive"
        text = (
            "Recognition remains expensive relative to primitive effort on the held-out fresh boxes. "
            "Stop this access design."
        )
    elif retains:
        row = "retains_opportunities"
        text = (
            "Cheap recognition retains sampled useful opportunities. The next experiment is a separate "
            "commitment policy. This run did not commit, and it does not establish cheaper solving."
        )
    else:
        row = "misses_opportunities"
        text = (
            "Cheap recognition misses the sampled useful actions. Diagnose anchor coverage before "
            "changing the library. The library and the anchor rule were not changed after this result."
        )
    return {
        "row": row,
        "text": text,
        "fresh_ratio": ratio,
        "cheap": cheap,
        "state_recall": recall,
        "mean_retention": retention,
        "commitment": "disabled",
        "cost_gate": "applied to validation fresh; not used to choose the absolute budget",
    }


def _limit(tasks: list[dict], limit: int | None) -> list[dict]:
    return tasks if limit is None else tasks[: int(limit)]


def run_experiment(config: Config) -> dict:
    frozen = load_frozen(config)
    reference = select_patterns(frozen, config)
    dev_rows = []
    dev_efforts = []
    for name in DEVELOPMENT:
        tasks = _limit(load_manifest(name)["tasks"], config.development_limit)
        for index, task in enumerate(tasks):
            print(f"development {name} {index} {task['task_id']}", flush=True)
            traced = trace_primitive(config, task, f"expt19-development-{name}", index)
            dev_rows.append({"manifest": name, "index": index, "task_id": task["task_id"], "primitive_A": traced["A"]})
            dev_efforts.append(traced["A"])
    budget = absolute_budget(dev_efforts, config.cheap_fraction)
    dev_ids = {row["task_id"] for row in dev_rows}
    # Family validation shares some ids with the development family manifest. Those are not held out.
    excluded = []
    box_rows = []
    action_rows = []
    for name in EVALUATION:
        tasks = load_manifest(name)["tasks"]
        kept = []
        for task in tasks:
            if task["task_id"] in dev_ids:
                excluded.append({"manifest": name, "task_id": task["task_id"]})
                continue
            kept.append(task)
        kept = _limit(kept, config.eval_limit)
        workload = "validation_fresh" if name == "validation_fresh" else "validation_family"
        for index, task in enumerate(kept):
            print(f"eval {workload} {index} {task['task_id']}", flush=True)
            traced = trace_primitive(config, task, f"expt19-eval-{name}", index)
            box, rows = score_box(config, workload, index, task, traced, frozen, reference, budget)
            box_rows.append(box)
            action_rows.extend(rows)
    fresh_boxes = [box for box in box_rows if box["workload"] == "validation_fresh"]
    family_boxes = [box for box in box_rows if box["workload"] == "validation_family"]
    fresh_rows = [row for row in action_rows if row["workload"] == "validation_fresh"]
    family_rows = [row for row in action_rows if row["workload"] == "validation_family"]
    fresh = _workload_summary(fresh_boxes, fresh_rows)
    family = _workload_summary(family_boxes, family_rows)
    return {
        "budget": budget,
        "development_mean_primitive": sum(dev_efforts) / len(dev_efforts),
        "development_n": len(dev_efforts),
        "development_rows": dev_rows,
        "n_frozen": len(frozen),
        "reference_indices": [item["pattern_index"] for item in reference],
        "high_support_indices": [item["pattern_index"] for item in reference if item["n_inventories"] >= config.high_support],
        "excluded_family_ids": excluded,
        "box_rows": box_rows,
        "action_rows": action_rows,
        "fresh": fresh,
        "family": family,
        "decision": decide(config, fresh),
        "catalogue_hash": catalogue_hash(),
    }


def audit_implementation() -> dict:
    return {"catalogue_hash": catalogue_hash(), "commitment": False, "frozen": str(EXPT17_FROZEN)}
