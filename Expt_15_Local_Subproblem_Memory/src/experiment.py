"""Expt-15: local subproblem memory.

Test 1: constructed independent regions with assigned budgets (experimental aid).
Test 2: ordinary packing with naturally occurring regions and shared inventory.
Both memories are built in a store phase and frozen before evaluation.
"""

from __future__ import annotations

import csv
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import Config
from continuation import ContinuationTable
from family_gen import declare_families, generate_family_members, sample_family_stream
from local_memory import LocalMemory, counts_key, geometry_key, solve_region
from policy_equiv import solve_equiv
from policy_exact import solve_primitive
from policy_local import grow_local_from_stack, solve_decomposed, solve_local
from region_gen import carve_region, embed_region, fill_from
from tools.generate_boxes import _blocked, all_prior_task_files, counts_ok, generate, inventory_key, task_from_counts

T1_CONDITIONS = ("primitive_whole", "exact_whole", "primitive_decomposed", "local_decomposed")
T2_CONDITIONS = ("primitive", "exact_whole", "local")
WORKLOADS = ("independent_fresh", "recurring_family")


def load_json_tasks(path: Path) -> list[dict]:
    return list(json.loads(path.read_text(encoding="utf-8"))["tasks"])


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    serialised = [{k: v for k, v in row.items() if k not in ("env", "ledger", "stack", "region_stack")} for row in rows]
    fields: list[str] = []
    for row in serialised:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in serialised:
            writer.writerow({key: row.get(key) for key in fields})


def audit_implementation() -> dict:
    return {
        "hypothesis": "a local region-filling memory creates cross-problem matches that remain beneficial after completing the whole box",
        "test1": "constructed independent regions with assigned budgets; region supplied as experimental aid",
        "test2": "ordinary packing; engineered billed region detector; shared inventory; no gate",
        "local_match_rule": "identical translation-normalised geometry; multiset available",
        "transformations": False,
        "hierarchy": False,
        "learned_gate": False,
        "memories_frozen_before_eval": True,
        "A_identity": "primitive_evals (incl. region search) + detection + lookup + availability + validation + insertion",
    }


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _median(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def _row(test, task, condition, seed, index, out, ref, **extra) -> dict:
    rec = {
        "test": test,
        "task_id": task["task_id"],
        "kind": task.get("kind"),
        "workload": task.get("workload"),
        "stream_id": extra.pop("stream_id", None),
        "family_id": task.get("family_id"),
        "region_id": task.get("region_id"),
        "seed": seed,
        "index": index,
        "condition": condition,
        "Q": out["Q"],
        "A": out["A"],
        "acceptable": out["acceptable"],
        "A_identity_ok": out.get("A_identity_ok"),
        "primitive_evals": out.get("primitive_evals") or 0,
        "region_search_evals": out.get("region_search_evals") or 0,
        "detection_cost": out.get("detection_cost") or 0,
        "lookup_cost": out.get("lookup_cost") or 0,
        "availability_cost": out.get("availability_cost") or 0,
        "validation_cost": out.get("validation_cost") or 0,
        "insertion_cost": out.get("insertion_cost") or 0,
        "local_hits": out.get("local_hits") or 0,
        "local_lookups": out.get("local_lookups") or 0,
        "regions_detected": out.get("regions_detected") or 0,
        "local_cells_filled": out.get("local_cells_filled") or 0,
        "hit_sizes": json.dumps(out.get("hit_sizes") or []),
        "region_via": out.get("region_via"),
        "region_filled": out.get("region_filled"),
        "exact_hits": out.get("hits") if condition == "exact_whole" else 0,
        "exact_initial_hits": out.get("initial_state_hits") if condition == "exact_whole" else 0,
        "exact_intermediate_hits": out.get("intermediate_hits") if condition == "exact_whole" else 0,
        "validation_fails": out.get("validation_fails") or 0,
        "primitive_before_first_hit": out.get("primitive_before_first_hit"),
        "first_hit_occupied": out.get("first_hit_occupied"),
        "seconds": out.get("seconds"),
        "inventory_in_store": extra.pop("inventory_in_store", False),
    }
    rec.update(extra)
    if ref is None:
        rec.update({"A_ref": out["A"], "Q_ref": out["Q"], "effort_saving": 0, "quality_delta": 0.0, "quality_loss": False,
                    "acceptability_lost": False})
    else:
        rec["A_ref"] = ref["A"]
        rec["Q_ref"] = ref["Q"]
        rec["effort_saving"] = int(ref["A"]) - int(out["A"])
        rec["quality_delta"] = float(out["Q"]) - float(ref["Q"])
        rec["quality_loss"] = float(out["Q"]) < float(ref["Q"]) - 1.0
        rec["acceptability_lost"] = bool(ref["acceptable"]) and not bool(out["acceptable"])
    used_local = int(rec["local_hits"]) > 0
    rec["used_local"] = used_local
    rec["allocation_failure"] = used_local and (rec["quality_loss"] or rec["acceptability_lost"])
    return rec


# ---------------------------------------------------------------- Test 1

def build_test1(config: Config) -> dict:
    rng = random.Random(int(config.generate_seed) + 500)
    blocked = _blocked(all_prior_task_files())
    deadline = time.perf_counter() + 900.0
    library: list[dict] = []
    controls: list[dict] = []
    sources: list[dict] = []
    seen: set = set()
    want_regions = int(config.t1_n_library) + int(config.t1_n_control)
    while len(library) + len(controls) < want_regions and time.perf_counter() < deadline:
        tiling = fill_from(0, rng, min(deadline, time.perf_counter() + 2.0))
        if not tiling:
            continue
        counts = {}
        for rec in tiling:
            counts[rec[0]] = counts.get(rec[0], 0) + 1
        full = {t: counts.get(t, 0) for t in counts}
        if not counts_ok(full) or inventory_key(full) in blocked:
            continue
        k = rng.randint(int(config.t1_k_min), int(config.t1_k_max))
        reg = carve_region(tiling, rng, k, int(config.region_min_cells), int(config.region_max_cells))
        if reg is None:
            continue
        gk = (geometry_key(reg["cells"]), counts_key(reg["budget"]))
        if gk in seen:
            continue
        seen.add(gk)
        if len(library) < int(config.t1_n_library):
            src = task_from_counts(full, family="t1_source")
            src["workload"] = "t1_source"
            sources.append(src)
            library.append({"region_id": f"R{len(library):02d}", "cells": reg["cells"], "budget": reg["budget"],
                            "geometry": list(geometry_key(reg["cells"])), "source_task_id": src["task_id"],
                            "n_pieces": k})
        else:
            controls.append({"region_id": f"C{len(controls):02d}", "cells": reg["cells"], "budget": reg["budget"],
                             "geometry": list(geometry_key(reg["cells"])), "n_pieces": k})
    if len(library) < int(config.t1_n_library) or len(controls) < int(config.t1_n_control):
        raise RuntimeError(f"test1 library {len(library)} controls {len(controls)}")

    used = set(blocked) | {inventory_key(s["inventory"]) for s in sources}
    tasks: list[dict] = []

    def embed(spec: dict, kind: str, n: int) -> None:
        geo = tuple(tuple(c) for c in spec["geometry"])
        made = 0
        tries = 0
        while made < n and tries < 60 and time.perf_counter() < deadline + 300:
            tries += 1
            out = embed_region(geo, spec["budget"], rng, time.perf_counter() + 20.0)
            if out is None:
                continue
            full = {t: v for t, v in out["counts"].items() if v}
            if not counts_ok(full):
                continue
            key = inventory_key(full)
            if key in used:
                continue
            used.add(key)
            task = task_from_counts(full, family="t1_eval")
            task.update({"kind": kind, "region_id": spec["region_id"], "region_cells": out["region_cells"],
                         "region_budget": dict(spec["budget"]), "workload": f"t1_{kind}"})
            tasks.append(task)
            made += 1
        if made < n:
            raise RuntimeError(f"could not embed {spec['region_id']}")

    for spec in library:
        embed(spec, "matched", int(config.t1_n_embed_per_region))
    for spec in controls:
        embed(spec, "control", 1)
    return {"library": library, "controls": controls, "sources": sources, "tasks": tasks}


def run_test1(config: Config) -> dict:
    built = build_test1(config)
    (ROOT / "data" / "test1.json").write_text(json.dumps(built, indent=2, default=list), encoding="utf-8")
    local = LocalMemory()
    acquisition = []
    for spec in built["library"]:
        placements, evals = solve_region([tuple(c) for c in spec["cells"]], spec["budget"], int(config.region_node_cap))
        ins = 0
        if placements is not None:
            ins = local.add([tuple(c) for c in spec["cells"]], placements, spec["region_id"], evals)
        acquisition.append({"region_id": spec["region_id"], "search_evals": evals, "insertion": ins,
                            "solved": placements is not None})
        local.growth.append(local.n_entries)
    local.freeze()
    exact = ContinuationTable()
    for seed in config.t1_seeds:
        for index, task in enumerate(built["sources"]):
            prim = solve_primitive(config, task, seed, "expt15-t1-store", index)
            exact.learn_from_success(prim["env"], prim["ledger"], config.q_min)
    exact.freeze()
    print(f"test1 library {len(built['library'])} controls {len(built['controls'])} eval boxes {len(built['tasks'])}; "
          f"local entries {local.n_entries}; exact keys {len(exact.entries)}", flush=True)

    rows = []
    phase = "expt15-t1"
    for seed in config.t1_seeds:
        for index, task in enumerate(built["tasks"]):
            print(f"t1 seed={seed} {index + 1}/{len(built['tasks'])} {task['kind']} {task['task_id']}", flush=True)
            pw = solve_local(config, task, seed, phase, index, None)
            rows.append(_row("t1", task, "primitive_whole", seed, index, pw, None))
            ew = solve_equiv(config, task, seed, phase, index, exact, mode="exact", allow_initial_lookup=True)
            rows.append(_row("t1", task, "exact_whole", seed, index, ew, pw))
            pd = solve_decomposed(config, task, seed, phase, index, None)
            rows.append(_row("t1", task, "primitive_decomposed", seed, index, pd, pw))
            ld = solve_decomposed(config, task, seed, phase, index, local)
            rec = _row("t1", task, "local_decomposed", seed, index, ld, pd)
            rec["saving_vs_primitive_whole"] = int(pw["A"]) - int(ld["A"])
            rec["quality_loss_vs_primitive_whole"] = float(ld["Q"]) < float(pw["Q"]) - 1.0
            rec["region_search_avoided"] = int(pd.get("region_search_evals") or 0) - int(ld.get("region_search_evals") or 0)
            rows.append(rec)

    summaries = []
    for kind in ("matched", "control"):
        for cond in T1_CONDITIONS:
            g = [r for r in rows if r["kind"] == kind and r["condition"] == cond]
            if not g:
                continue
            summaries.append({
                "kind": kind,
                "condition": cond,
                "n": len(g),
                "n_tasks": len({r["task_id"] for r in g}),
                "reference": {"primitive_whole": None, "exact_whole": "primitive_whole",
                              "primitive_decomposed": "primitive_whole", "local_decomposed": "primitive_decomposed"}[cond],
                "mean_A": _mean([r["A"] for r in g]),
                "mean_Q": _mean([r["Q"] for r in g]),
                "mean_effort_saving": _mean([r["effort_saving"] for r in g]),
                "mean_saving_vs_primitive_whole": _mean([r.get("saving_vs_primitive_whole") for r in g]),
                "median_saving_vs_primitive_whole": _median([r.get("saving_vs_primitive_whole") for r in g]),
                "n_positive_vs_primitive_whole": sum(1 for r in g if (r.get("saving_vs_primitive_whole") or 0) > 0) if cond == "local_decomposed" else None,
                "n_negative_vs_primitive_whole": sum(1 for r in g if (r.get("saving_vs_primitive_whole") or 0) < 0) if cond == "local_decomposed" else None,
                "per_seed_saving_vs_primitive_whole": {
                    str(s): _mean([r.get("saving_vs_primitive_whole") for r in g if int(r["seed"]) == int(s)]) for s in config.t1_seeds
                } if cond == "local_decomposed" else None,
                "n_quality_loss_vs_primitive_whole": sum(1 for r in g if r.get("quality_loss_vs_primitive_whole")) if cond == "local_decomposed" else None,
                "mean_region_search_evals": _mean([r["region_search_evals"] for r in g]),
                "mean_region_search_avoided": _mean([r.get("region_search_avoided") for r in g]),
                "n_local_hits": sum(int(r["local_hits"]) for r in g),
                "n_exact_hits": sum(int(r["exact_hits"] or 0) for r in g),
                "n_validation_fails": sum(int(r["validation_fails"]) for r in g),
                "n_quality_loss": sum(1 for r in g if r["quality_loss"]),
                "n_allocation_failure": sum(1 for r in g if r["allocation_failure"]),
                "acceptable_rate": _mean([1.0 if r["acceptable"] else 0.0 for r in g]),
                "region_filled_rate": _mean([1.0 if r.get("region_filled") else 0.0 for r in g]) if "decomposed" in cond else None,
                "mean_lookup": _mean([r["lookup_cost"] for r in g]),
                "mean_validation": _mean([r["validation_cost"] for r in g]),
                "mean_seconds": _mean([r["seconds"] for r in g]),
            })
    return {
        "library": built["library"],
        "controls": built["controls"],
        "n_eval_tasks": len(built["tasks"]),
        "acquisition": acquisition,
        "local_entries": local.n_entries,
        "local_geometries": local.n_geometries(),
        "local_bytes": local.bytes(),
        "exact_keys": len(exact.entries),
        "summaries": summaries,
        "rows": rows,
    }


# ---------------------------------------------------------------- Test 2

def run_test2(config: Config) -> dict:
    generate(target=int(config.n_store_independent), timeout=600.0, seed=int(config.generate_seed), out_name="store")
    independent = load_json_tasks(ROOT / "data" / "store.json")[: int(config.n_store_independent)]
    for task in independent:
        task["workload"] = "store_independent"
        task["constructed_prefix"] = None
    specs = declare_families(int(config.n_families), random.Random(int(config.generate_seed) + 17))
    blocked = {inventory_key(t["inventory"]) for t in independent}
    family_store = generate_family_members(specs, int(config.n_store_per_family), int(config.generate_seed) + 31, blocked, timeout=600.0)
    (ROOT / "data" / "family_store.json").write_text(json.dumps({"tasks": family_store, "specs": specs}, indent=2), encoding="utf-8")
    store_tasks = independent + family_store
    store_keys = {inventory_key(t["inventory"]) for t in store_tasks}

    streams: dict[tuple[str, int], list[dict]] = {}
    for sid, _seed in enumerate(config.stream_seeds):
        name = f"fresh_s{sid}"
        generate(target=int(config.n_per_stream), timeout=600.0, seed=int(config.generate_seed) + 100 + sid, out_name=name,
                 extra_blocked=[ROOT / "data" / "store.json", ROOT / "data" / "family_store.json"])
        fresh = load_json_tasks(ROOT / "data" / f"{name}.json")[: int(config.n_per_stream)]
        if len(fresh) < int(config.n_per_stream):
            raise RuntimeError(f"stream {sid} fresh {len(fresh)}")
        for t in fresh:
            t["workload"] = "independent_fresh"
            t["constructed_prefix"] = None
        fam = sample_family_stream(specs, int(config.n_per_stream), int(config.generate_seed) + 200 + sid)
        (ROOT / "data" / f"family_stream_s{sid}.json").write_text(json.dumps({"tasks": fam}, indent=2), encoding="utf-8")
        streams[("independent_fresh", sid)] = fresh
        streams[("recurring_family", sid)] = fam

    exact = ContinuationTable()
    local = LocalMemory()
    acq = {"extraction_cost": 0, "insertion_cost": 0, "n_found": 0, "store_primitive_evals": 0}
    census: dict = {}
    for seed in config.store_seeds:
        for index, task in enumerate(store_tasks):
            print(f"t2 store seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt15-t2-store", index)
            acq["store_primitive_evals"] += int(prim["primitive_evals"])
            exact.learn_from_success(prim["env"], prim["ledger"], config.q_min)
            if prim["acceptable"]:
                g = grow_local_from_stack(local, task["inventory"], list(prim["stack"]), config, f"store:{seed}:{task['task_id']}", census)
                for k in ("extraction_cost", "insertion_cost", "n_found"):
                    acq[k] += g[k]
            local.growth.append(local.n_entries)
    exact.freeze()
    local.freeze()
    print(f"t2 exact keys {len(exact.entries)}; local entries {local.n_entries} in {local.n_geometries()} geometries", flush=True)

    rows = []
    for (workload, sid), tasks in streams.items():
        seed = int(config.stream_seeds[sid])
        phase = f"expt15-t2-{workload}-s{sid}"
        for index, task in enumerate(tasks):
            print(f"t2 {workload} s{sid} {index + 1}/{len(tasks)} {task['task_id']}", flush=True)
            in_store = inventory_key(task["inventory"]) in store_keys
            prim = solve_local(config, task, seed, phase, index, None)
            rows.append(_row("t2", task, "primitive", seed, index, prim, None, stream_id=sid, inventory_in_store=in_store))
            ex = solve_equiv(config, task, seed, phase, index, exact, mode="exact", allow_initial_lookup=True)
            rows.append(_row("t2", task, "exact_whole", seed, index, ex, prim, stream_id=sid, inventory_in_store=in_store))
            lo = solve_local(config, task, seed, phase, index, local)
            rows.append(_row("t2", task, "local", seed, index, lo, prim, stream_id=sid, inventory_in_store=in_store))

    n_eval_boxes = sum(len(t) for t in streams.values())
    summaries = {}
    for workload in WORKLOADS:
        summaries[workload] = {}
        for cond in T2_CONDITIONS:
            g = [r for r in rows if r["workload"] == workload and r["condition"] == cond]
            if not g:
                continue
            per_stream = []
            for sid in range(config.n_streams):
                s = [r for r in g if r["stream_id"] == sid]
                if s:
                    per_stream.append({"stream_id": sid, "n": len(s), "cumulative_saving": sum(r["effort_saving"] for r in s),
                                       "n_local_hits": sum(int(r["local_hits"]) for r in s),
                                       "n_boxes_local": sum(1 for r in s if r["used_local"])})
            unseen = [r for r in g if not r["inventory_in_store"]]
            hit_boxes = [r for r in g if r["used_local"]]
            summaries[workload][cond] = {
                "n": len(g),
                "n_streams": len(per_stream),
                "mean_cumulative_saving": _mean([p["cumulative_saving"] for p in per_stream]),
                "min_cumulative_saving": min((p["cumulative_saving"] for p in per_stream), default=None),
                "max_cumulative_saving": max((p["cumulative_saving"] for p in per_stream), default=None),
                "mean_per_box_saving": _mean([r["effort_saving"] for r in g]),
                "mean_A": _mean([r["A"] for r in g]),
                "mean_Q": _mean([r["Q"] for r in g]),
                "n_quality_loss": sum(1 for r in g if r["quality_loss"]),
                "n_acceptability_lost": sum(1 for r in g if r["acceptability_lost"]),
                "n_allocation_failure": sum(1 for r in g if r["allocation_failure"]),
                "n_validation_fails": sum(int(r["validation_fails"]) for r in g),
                "n_local_hits": sum(int(r["local_hits"]) for r in g),
                "n_boxes_local": len(hit_boxes),
                "frac_boxes_local": len(hit_boxes) / len(g),
                "n_local_hits_unseen_inventory": sum(int(r["local_hits"]) for r in unseen),
                "n_boxes_local_unseen_inventory": sum(1 for r in unseen if r["used_local"]),
                "n_unseen_inventory": len(unseen),
                "n_exact_hits": sum(int(r["exact_hits"] or 0) for r in g),
                "n_exact_initial": sum(int(r["exact_initial_hits"] or 0) for r in g),
                "n_exact_intermediate": sum(int(r["exact_intermediate_hits"] or 0) for r in g),
                "mean_regions_detected": _mean([r["regions_detected"] for r in g]),
                "mean_detection": _mean([r["detection_cost"] for r in g]),
                "mean_lookup": _mean([r["lookup_cost"] for r in g]),
                "mean_availability": _mean([r["availability_cost"] for r in g]),
                "mean_validation": _mean([r["validation_cost"] for r in g]),
                "mean_primitive_before_first_hit": _mean([r["primitive_before_first_hit"] for r in hit_boxes]),
                "mean_quality_delta_hit_boxes": _mean([r["quality_delta"] for r in hit_boxes]),
                "mean_saving_hit_boxes": _mean([r["effort_saving"] for r in hit_boxes]),
                "mean_saving_no_hit_boxes": _mean([r["effort_saving"] for r in g if not r["used_local"]]),
                "mean_hit_size": _mean([s for r in hit_boxes for s in json.loads(r["hit_sizes"])]),
                "mean_seconds": _mean([r["seconds"] for r in g]),
                "streams": per_stream,
            }
    return {
        "store_ids": [t["task_id"] for t in store_tasks],
        "family_specs": specs,
        "exact_keys": len(exact.entries),
        "local_entries": local.n_entries,
        "local_geometries": local.n_geometries(),
        "local_duplicates": local.n_duplicate,
        "local_bytes": local.bytes(),
        "local_growth": local.growth,
        "acquisition": acq,
        "store_region_census": census,
        "acquisition_per_eval_box": (acq["extraction_cost"] + acq["insertion_cost"]) / n_eval_boxes if n_eval_boxes else None,
        "n_eval_boxes": n_eval_boxes,
        "summaries": summaries,
        "rows": rows,
    }


def run_experiment(config: Config) -> dict:
    (ROOT / "data").mkdir(exist_ok=True)
    t1 = run_test1(config)
    t2 = run_test2(config)
    rows = t1.pop("rows") + t2.pop("rows")
    return {
        "test1": t1,
        "test2": t2,
        "rows": rows,
        "note": (
            "Test 1 supplies independent regions and budgets as an experimental aid; it is not learned "
            "decomposition. Test 2 uses an engineered flood-fill detector next to each placement, billed per "
            "free cell visited; it is not autonomous abstraction. Local entries match on identical "
            "translation-normalised geometry with the multiset available; no transformations, hierarchy, or "
            "learned gate. Memories are frozen before evaluation; store-phase acquisition is reported "
            "separately. Constructed opportunities (Test 1) are never pooled with naturally encountered ones (Test 2)."
        ),
    }
