"""Expt-17 driver. Acquire a frozen dictionary from successful packings, then count legal fits. No commit."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from census import PatternTable, scan_trajectory
from config import Config
from pieces import PIECE_TYPES, catalogue_hash
from policy_exact import solve_primitive

REPO = Path(__file__).resolve().parents[2]
EXPT16 = REPO / "Expt_16_Search_Acquired_Local_Memory"
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


def _inv_key(inv: dict) -> tuple:
    return tuple(int(inv.get(t, 0)) for t in PIECE_TYPES)


def _sets(config: Config) -> dict:
    store = load_manifest("acquisition_store")["tasks"]
    fresh = load_manifest("applicability_fresh")["tasks"]
    family = load_manifest("applicability_family")["tasks"]
    if config.store_limit is not None:
        store = store[: int(config.store_limit)]
    if config.fresh_limit is not None:
        fresh = fresh[: int(config.fresh_limit)]
        family = family[: int(config.fresh_limit)]
    return {"store": store, "independent_fresh": fresh, "recurring_family": family}


def _support_hist(table: PatternTable) -> dict:
    by_inv = Counter(len(rec["inventories"]) for rec in table.patterns.values())
    by_box = Counter(len(rec["boxes"]) for rec in table.patterns.values())
    return {
        "by_inventories": {str(k): by_inv[k] for k in sorted(by_inv)},
        "by_boxes": {str(k): by_box[k] for k in sorted(by_box)},
    }


def acquire(config: Config, store_tasks: list[dict]) -> dict:
    table = PatternTable()
    rows = []
    started = time.perf_counter()
    primitive_a = 0
    n_excluded = 0
    for seed in config.store_seeds:
        for index, task in enumerate(store_tasks):
            prim = solve_primitive(config, task, int(seed), config.store_phase, index)
            primitive_a += int(prim["A"])
            row = {
                "seed": int(seed),
                "task_id": task["task_id"],
                "store_index": index,
                "Q": prim["Q"],
                "A": prim["A"],
                "acceptable": prim["acceptable"],
                "n_place": prim["n_place"],
                "checks": 0,
                "unique_in_box": 0,
                "capped": False,
            }
            if not prim["acceptable"]:
                n_excluded += 1
                rows.append(row)
                continue
            obs = table.observe_box(int(seed), task["task_id"], _inv_key(task["inventory"]), list(prim["stack"]), config)
            row.update(obs)
            rows.append(row)
    frozen = table.freeze(config.min_inventories)
    return {
        "table": table,
        "frozen": frozen,
        "rows": rows,
        "summary": {
            "n_trajectories": len(rows),
            "n_excluded_unacceptable": n_excluded,
            "n_acceptable": len(rows) - n_excluded,
            "primitive_A_sum": primitive_a,
            "primitive_A_per_trajectory": _mean([r["A"] for r in rows]),
            "extraction_checks": table.extraction_checks,
            "extraction_connected_groups": table.extraction_connected,
            "extraction_per_acceptable_box": _mean([r["checks"] for r in rows if r["acceptable"]]),
            "boxes_capped": sum(1 for r in rows if r["capped"]),
            "n_patterns": len(table.patterns),
            "n_frozen": len(frozen),
            "support": _support_hist(table),
            "frozen_by_pieces": dict(Counter(item["pieces"] for item in frozen)),
            "seconds": time.perf_counter() - started,
        },
    }


def examine(config: Config, sets: dict, frozen: list[dict], store_keys: set) -> dict:
    rows = []
    started = time.perf_counter()
    for workload in WORKLOADS:
        for index, task in enumerate(sets[workload]):
            prim = solve_primitive(
                config,
                task,
                int(config.applicability_seed),
                f"{config.applicability_phase}-{workload}",
                index,
            )
            scan = scan_trajectory(list(prim["stack"]), task["inventory"], frozen, config)
            rows.append({
                "workload": workload,
                "index": index,
                "task_id": task["task_id"],
                "inventory_in_store": _inv_key(task["inventory"]) in store_keys,
                "Q": prim["Q"],
                "A": prim["A"],
                "acceptable": prim["acceptable"],
                "n_place": prim["n_place"],
                **scan,
            })
    summary = {}
    for workload in WORKLOADS:
        group = [row for row in rows if row["workload"] == workload]
        primitive = _mean([row["A"] for row in group])
        matching = _mean([row["match_checks"] for row in group])
        summary[workload] = {
            "n_boxes": len(group),
            "n_inventory_in_store": sum(1 for row in group if row["inventory_in_store"]),
            "primitive_A_per_box": primitive,
            "match_checks_per_box": matching,
            "match_fraction_of_primitive": (matching / primitive) if primitive else None,
            "boxes_with_fit": sum(1 for row in group if row["fit_events"]),
            "boxes_with_early_or_middle_fit": sum(1 for row in group if row["early_fits"] or row["middle_fits"]),
            "fit_events": sum(row["fit_events"] for row in group),
            "early_fits": sum(row["early_fits"] for row in group),
            "middle_fits": sum(row["middle_fits"] for row in group),
            "late_fits": sum(row["late_fits"] for row in group),
            "patterns_with_fit_mean": _mean([row["patterns_with_fit"] for row in group]),
        }
    summary["seconds"] = time.perf_counter() - started
    return {"rows": rows, "summary": summary}


def decide(config: Config, acquired: dict, examined: dict) -> dict:
    fresh = examined["summary"]["independent_fresh"]
    family = examined["summary"]["recurring_family"]
    n_frozen = acquired["summary"]["n_frozen"]
    cheap = fresh["match_fraction_of_primitive"] is not None and fresh["match_fraction_of_primitive"] < config.cheap_fraction
    early = fresh["boxes_with_early_or_middle_fit"] >= config.min_fit_boxes
    any_fit = fresh["boxes_with_fit"] > 0
    if n_frozen == 0:
        row = "no_cross_inventory_recurrence"
        text = "No small arrangement recurred across the predeclared number of distinct training inventories."
    elif not any_fit:
        row = "recurrence_but_no_fit"
        text = "Some arrangements recur across inventories, but none fitted free space on an independent fresh trajectory."
    elif fresh["boxes_with_fit"] > 0 and fresh["boxes_with_early_or_middle_fit"] == 0:
        row = "late_only_not_sufficient"
        text = "Legal fits on independent fresh trajectories were only in the late occupied-cell third."
    elif early and cheap:
        row = "coverage_warrants_later_test"
        text = "Early or middle fits exist on enough fresh boxes, and matching stayed under the predeclared cost fraction. A separate commit diagnostic is not part of this run."
    elif any_fit and not cheap:
        row = "fits_but_not_cheap"
        text = "Legal fits exist, but matching cost is not under the predeclared fraction of primitive effort."
    else:
        row = "coverage_short"
        text = "Recurring arrangements and some fits exist, but not enough early or middle fresh boxes to justify a commit test."
    return {
        "row": row,
        "text": text,
        "n_frozen": n_frozen,
        "fresh_boxes_with_fit": fresh["boxes_with_fit"],
        "fresh_boxes_with_early_or_middle_fit": fresh["boxes_with_early_or_middle_fit"],
        "fresh_match_fraction": fresh["match_fraction_of_primitive"],
        "family_boxes_with_fit": family["boxes_with_fit"],
        "commitment": "not run",
    }


def run_experiment(config: Config) -> dict:
    sets = _sets(config)
    store_keys = {_inv_key(task["inventory"]) for task in load_manifest("acquisition_store")["tasks"]}
    acquired = acquire(config, sets["store"])
    examined = examine(config, sets, acquired["frozen"], store_keys)
    decision = decide(config, acquired, examined)
    return {
        "acquisition_rows": acquired["rows"],
        "box_rows": examined["rows"],
        "frozen": [
            {k: (list(v) if k == "anchors" else v) for k, v in item.items()}
            for item in acquired["frozen"]
        ],
        "acquisition": acquired["summary"],
        "applicability": examined["summary"],
        "decision": decision,
        "catalogue_hash": catalogue_hash(),
    }


def audit_implementation() -> dict:
    return {"catalogue_hash": catalogue_hash(), "manifests": manifest_hashes(), "commitment": False}
