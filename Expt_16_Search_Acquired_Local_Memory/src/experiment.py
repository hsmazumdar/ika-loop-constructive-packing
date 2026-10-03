"""Expt-16 driver: acquire by bounded offline search, freeze, match read-only, diagnose consequences."""

from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path

from acquire import AcquiredMemory, branch, load_manifest, manifest_hashes, observe, region_snapshots, search_region, validate_filling
from config import Config
from pieces import PIECE_TYPES, catalogue_hash
from policy_exact import solve_primitive

ROOT = Path(__file__).resolve().parents[1]
WORKLOADS = ("independent_fresh", "recurring_family")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict, tuple)) else v) for k, v in r.items()})


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _median(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    m = len(vals) // 2
    return vals[m] if len(vals) % 2 else (vals[m - 1] + vals[m]) / 2


def audit_implementation() -> dict:
    return {"catalogue_hash": catalogue_hash(), "manifests": manifest_hashes()}


def _sets(config: Config) -> dict:
    store = load_manifest("acquisition_store")
    fresh = load_manifest("applicability_fresh")["tasks"]
    family = load_manifest("applicability_family")["tasks"]
    store_tasks = store["tasks"]
    if config.manifest_set == "smoke":
        store_tasks = store_tasks[:2]
        fresh = fresh[:3]
        family = family[:3]
    return {"store": store_tasks, "independent_fresh": fresh, "recurring_family": family}


def _inv_key(inv: dict) -> tuple:
    return tuple(int(inv.get(t, 0)) for t in PIECE_TYPES)


def _unused_at_end(inventory: dict, stack: list[tuple]) -> dict:
    left = {t: int(inventory.get(t, 0)) for t in PIECE_TYPES}
    for p in stack:
        left[p[0]] -= 1
    return left


# ---------------------------------------------------------------- acquisition

def acquire(config: Config, store_tasks: list[dict]) -> dict:
    memory = AcquiredMemory()
    rows = []
    costs = {"detection": 0, "search": 0, "validation": 0, "insertion": 0}
    n_traj = n_excluded = 0
    started = time.perf_counter()
    for seed in config.store_seeds:
        for index, task in enumerate(store_tasks):
            prim = solve_primitive(config, task, seed, config.store_phase, index)
            n_traj += 1
            if config.store_acceptable_only and not prim["acceptable"]:
                n_excluded += 1
                continue
            stack = list(prim["stack"])
            snaps, dcost = region_snapshots(task["inventory"], stack, int(config.region_min_cells), int(config.region_max_cells))
            costs["detection"] += dcost
            unused = _unused_at_end(task["inventory"], stack)
            for k, snap in enumerate(snaps):
                res = search_region(snap["region"], snap["remaining"], int(config.search_budget))
                costs["search"] += res["evals"]
                row = {
                    "seed": seed, "task_id": task["task_id"], "store_index": index, "snapshot": k,
                    "t": snap["t"], "placements_left": snap["placements_left"], "size": len(snap["region"]),
                    "status": res["status"], "search_evals": res["evals"],
                    "remaining_pieces": sum(snap["remaining"].values()),
                    "valid": None, "validation_cost": 0, "insertion": None, "insertion_cost": 0,
                    "uses_only_end_unused": None, "multiset": None,
                }
                if res["status"] == "found":
                    ok, vcost = validate_filling(task["inventory"], stack[: snap["t"]], snap["region"], res["placements"])
                    costs["validation"] += vcost
                    row["valid"] = ok
                    row["validation_cost"] = vcost
                    need = Counter(p[0] for p in res["placements"])
                    row["multiset"] = dict(sorted(need.items()))
                    row["uses_only_end_unused"] = all(unused.get(t, 0) >= n for t, n in need.items())
                    if ok:
                        ins = memory.add(snap["region"], res["placements"], f"{seed}:{task['task_id']}:{snap['t']}", res["evals"])
                        costs["insertion"] += ins["cost"]
                        row["insertion"] = ins["outcome"]
                        row["insertion_cost"] = ins["cost"]
                rows.append(row)
    memory.freeze()
    n = len(rows)
    status = Counter(r["status"] for r in rows)
    by_size: dict[int, Counter] = {}
    by_left: dict[int, Counter] = {}
    for r in rows:
        by_size.setdefault(r["size"], Counter())[r["status"]] += 1
        by_left.setdefault(r["placements_left"], Counter())[r["status"]] += 1
    found = [r for r in rows if r["status"] == "found"]
    return {
        "memory": memory,
        "rows": rows,
        "summary": {
            "n_trajectories": n_traj,
            "n_excluded_unacceptable": n_excluded,
            "n_snapshots": n,
            "status": dict(status),
            "fill_rate": status.get("found", 0) / n if n else None,
            "n_valid": sum(1 for r in found if r["valid"]),
            "n_uses_only_end_unused": sum(1 for r in found if r["uses_only_end_unused"]),
            "by_size": {str(k): dict(v) for k, v in sorted(by_size.items())},
            "by_placements_left": {str(k): dict(v) for k, v in sorted(by_left.items())},
            "search_evals_found": {"mean": _mean([r["search_evals"] for r in found]), "median": _median([r["search_evals"] for r in found]),
                                   "max": max([r["search_evals"] for r in found], default=None)},
            "n_impossible_by_area": sum(1 for r in rows if r["status"] == "impossible" and r["search_evals"] == 1),
            "search_evals_impossible": {"mean": _mean([r["search_evals"] for r in rows if r["status"] == "impossible"]),
                                        "median": _median([r["search_evals"] for r in rows if r["status"] == "impossible"])},
            "costs": costs,
            "insertion_outcomes": dict(Counter(r["insertion"] for r in found if r["insertion"])),
            "n_entries": memory.n_entries,
            "n_geometries": memory.n_geometries(),
            "n_entries_with_alternatives": sum(1 for b in memory.by_geometry.values() for e in b if len(e["alternatives"]) > 1),
            "geometries_with_multiple_multisets": sum(1 for b in memory.by_geometry.values() if len(b) > 1),
            "seconds": time.perf_counter() - started,
        },
    }


# ---------------------------------------------------------------- applicability and counterfactuals

def applicability(config: Config, sets: dict, memory: AcquiredMemory, store_keys: set) -> dict:
    boxes = []
    snaps_by_box = {}
    for workload in WORKLOADS:
        for index, task in enumerate(sets[workload]):
            obs = observe(config, task, int(config.applicability_seed), f"{config.applicability_phase}-{workload}", index, memory)
            snaps = obs.pop("snapshots")
            key = (workload, index)
            snaps_by_box[key] = (task, obs, snaps)
            boxes.append({
                "workload": workload, "index": index, "task_id": task["task_id"], "stream_id": task.get("stream_id"),
                "inventory_in_store": _inv_key(task["inventory"]) in store_keys,
                "Q": obs["Q"], "A": obs["A"], "acceptable": obs["acceptable"], "seconds": obs["seconds"],
                "regions": obs["regions"], "detection": obs["detection"], "lookup": obs["lookup"], "availability": obs["availability"],
                "geometry_matches": obs["geometry_matches"], "compatible_matches": obs["compatible_matches"],
            })
    summary = {}
    for workload in WORKLOADS:
        g = [b for b in boxes if b["workload"] == workload]
        summary[workload] = {
            "n_boxes": len(g),
            "n_inventory_in_store": sum(1 for b in g if b["inventory_in_store"]),
            "regions_per_box": _mean([b["regions"] for b in g]),
            "detection_per_box": _mean([b["detection"] for b in g]),
            "lookup_per_box": _mean([b["lookup"] for b in g]),
            "availability_per_box": _mean([b["availability"] for b in g]),
            "detector_lookup_total": sum(b["detection"] + b["lookup"] + b["availability"] for b in g),
            "primitive_A_per_box": _mean([b["A"] for b in g]),
            "geometry_matches": sum(b["geometry_matches"] for b in g),
            "compatible_matches": sum(b["compatible_matches"] for b in g),
            "boxes_with_geometry_match": sum(1 for b in g if b["geometry_matches"]),
            "boxes_with_compatible_match": sum(1 for b in g if b["compatible_matches"]),
            "boxes_with_compatible_match_new_inventory": sum(1 for b in g if b["compatible_matches"] and not b["inventory_in_store"]),
        }
    return {"boxes": boxes, "snaps_by_box": snaps_by_box, "summary": summary}


def counterfactuals(config: Config, snaps_by_box: dict) -> list[dict]:
    rows = []
    for (workload, index), (task, obs, snaps) in snaps_by_box.items():
        for m, snap in enumerate(snaps):
            base = branch(config, snap, None)
            reproduces = abs(base["Q"] - obs["Q"]) < 1e-9 and snap["prefix_A"] + base["A_rest"] == obs["A"]
            for e_rank, entry in enumerate(snap["entries"]):
                com = branch(config, snap, entry)
                rows.append({
                    "workload": workload, "index": index, "task_id": task["task_id"], "match": m, "first_match": m == 0,
                    "entry_rank": e_rank, "first_entry": e_rank == 0, "n_compatible": snap["n_compatible"],
                    "region_size": len(snap["region"]), "occupied_at_match": snap["occupied"], "prefix_A": snap["prefix_A"],
                    "multiset": dict(sorted(entry["counts"].items())), "entry_sources": len(entry["sources"]),
                    "Q_primitive": base["Q"], "A_rest_primitive": base["A_rest"], "acceptable_primitive": base["acceptable"],
                    "Q_commit": com["Q"], "A_rest_commit": com["A_rest"], "acceptable_commit": com["acceptable"], "valid": com["valid"],
                    "effort_saving": base["A_rest"] - com["A_rest"],
                    "quality_delta": (com["Q"] - base["Q"]) if com["Q"] is not None else None,
                    "quality_loss": com["Q"] is None or com["Q"] < base["Q"] - float(config.quality_loss_margin),
                    "quality_gain": com["Q"] is not None and com["Q"] > base["Q"] + float(config.quality_loss_margin),
                    "acceptability_lost": bool(base["acceptable"]) and not bool(com["acceptable"]),
                    "primitive_branch_reproduces_trajectory": reproduces if e_rank == 0 else None,
                })
    return rows


def _cf_summary(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    return {
        "n": len(rows),
        "n_boxes": len({(r["workload"], r["index"]) for r in rows}),
        "n_valid": sum(1 for r in rows if r["valid"]),
        "mean_effort_saving": _mean([r["effort_saving"] for r in rows]),
        "median_effort_saving": _median([r["effort_saving"] for r in rows]),
        "n_positive": sum(1 for r in rows if r["effort_saving"] > 0),
        "n_negative": sum(1 for r in rows if r["effort_saving"] < 0),
        "mean_quality_delta": _mean([r["quality_delta"] for r in rows]),
        "n_quality_loss": sum(1 for r in rows if r["quality_loss"]),
        "n_quality_gain": sum(1 for r in rows if r["quality_gain"]),
        "quality_loss_rate": sum(1 for r in rows if r["quality_loss"]) / len(rows),
        "n_acceptability_lost": sum(1 for r in rows if r["acceptability_lost"]),
        "mean_region_size": _mean([r["region_size"] for r in rows]),
    }


IMPLICATIONS = {
    "few_fillings": "These late regions may be poor acquisition targets.",
    "no_recurrence": "Representation or coverage remains the problem.",
    "commitment_harms": "Piece allocation and safe decomposition remain unresolved.",
    "saves_and_preserves": "Test a deployable commitment rule and acquisition payback on the validation manifests.",
}


def decide(config: Config, acq: dict, app: dict | None, cf: dict | None) -> dict:
    """All rows whose predeclared condition holds, in table order; the first is primary."""
    s = acq["summary"]
    boxes_compat = sum(v["boxes_with_compatible_match"] for v in (app or {}).get("summary", {}).values()) if app else 0
    rows = []
    if s["n_entries"] == 0 or (s["fill_rate"] or 0) < float(config.few_fill_rate):
        rows.append("few_fillings")
    if s["n_entries"] > 0 and boxes_compat < int(config.min_recur_boxes):
        rows.append("no_recurrence")
    primary_cf = (cf or {}).get("first_match_first_entry") or {}
    if boxes_compat >= int(config.min_recur_boxes) and primary_cf.get("n"):
        harms = (
            primary_cf["quality_loss_rate"] > float(config.harm_quality_loss_rate)
            or (primary_cf["mean_quality_delta"] or 0.0) < float(config.harm_mean_quality_delta)
            or (primary_cf["mean_effort_saving"] or 0) <= 0
            or (primary_cf["median_effort_saving"] or 0) <= 0
        )
        rows.append("commitment_harms" if harms else "saves_and_preserves")
    return {
        "row": rows[0],
        "rows": rows,
        "implication": IMPLICATIONS[rows[0]],
        "implications": {r: IMPLICATIONS[r] for r in rows},
        "few_fillings": "few_fillings" in rows,
        "boxes_with_compatible_match": boxes_compat,
        "counterfactuals_below_recurrence_threshold": bool(primary_cf.get("n")) and boxes_compat < int(config.min_recur_boxes),
    }


def run_experiment(config: Config) -> dict:
    sets = _sets(config)
    print(f"store tasks {len(sets['store'])} x seeds {len(config.store_seeds)}", flush=True)
    acq = acquire(config, sets["store"])
    s = acq["summary"]
    print(f"snapshots {s['n_snapshots']} status {s['status']} entries {s['n_entries']} geometries {s['n_geometries']}", flush=True)
    store_keys = {_inv_key(t["inventory"]) for t in sets["store"]}
    app = None
    cf_rows: list[dict] = []
    cf = None
    stopped = None
    if acq["memory"].n_entries == 0:
        stopped = "no entries acquired; applicability not run"
    else:
        app = applicability(config, sets, acq["memory"], store_keys)
        n_compat = sum(v["compatible_matches"] for v in app["summary"].values())
        print(f"applicability {json.dumps({w: (v['geometry_matches'], v['compatible_matches']) for w, v in app['summary'].items()})}", flush=True)
        if n_compat == 0:
            stopped = "no compatible matches; stopped before counterfactuals"
        else:
            cf_rows = counterfactuals(config, app["snaps_by_box"])
            first = [r for r in cf_rows if r["first_match"] and r["first_entry"]]
            cf = {
                "first_match_first_entry": _cf_summary(first),
                "all_first_entries": _cf_summary([r for r in cf_rows if r["first_entry"]]),
                "all": _cf_summary(cf_rows),
                "by_workload_first": {w: _cf_summary([r for r in first if r["workload"] == w]) for w in WORKLOADS},
                "primitive_branch_reproduces": sum(1 for r in cf_rows if r["primitive_branch_reproduces_trajectory"]),
                "primitive_branch_checked": sum(1 for r in cf_rows if r["primitive_branch_reproduces_trajectory"] is not None),
            }
    decision = decide(config, acq, app, cf)
    return {
        "acquisition": s,
        "entries": acq["memory"].to_json(),
        "acquisition_rows": acq["rows"],
        "applicability": app["summary"] if app else None,
        "box_rows": app["boxes"] if app else [],
        "counterfactual_rows": cf_rows,
        "counterfactuals": cf,
        "stopped": stopped,
        "decision": decision,
        "deployment": "not run: a deployed policy is tested only after the decision row saves_and_preserves",
    }
