"""Online exact-memory growth with chronological evaluation.

Store phase builds one base table, then freezes it. Each independent stream gets its own
growing copy. Every box is solved by primitive, frozen exact, and growing exact using only the
memory available before that box. The growing agent's completed solve is inserted afterwards and
insertion is billed to that box.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import Config
from continuation import ContinuationTable
from family_gen import declare_families, generate_family_members, sample_family_stream
from policy_equiv import solve_equiv
from policy_exact import solve_primitive
from tools.generate_boxes import generate, inventory_key

CONDITIONS = ("primitive", "frozen_exact", "growing_exact")
WORKLOADS = ("independent_fresh", "recurring_family")


def load_json_tasks(path: Path) -> list[dict]:
    return list(json.loads(path.read_text(encoding="utf-8"))["tasks"])


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    serialised = [{k: v for k, v in row.items() if k not in ("env", "ledger")} for row in rows]
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
        "hypothesis": "online exact-memory growth creates useful future matches the frozen table lacked",
        "conditions": list(CONDITIONS),
        "retrieval": "exact (mask, inventory) identity",
        "transformation_matching_in_primary": False,
        "first_write_wins": True,
        "per_stream_memory_copy": True,
        "solve_before_insert": True,
        "insertion_billed": True,
        "future_tasks_chosen_by_memory": False,
        "constructed_prefix_on_eval": False,
        "A_identity": "primitive_evals + lookup + validation + insertion",
    }


def _row(task, workload, stream_id, seed, index, condition, out, prim, extra) -> dict:
    A = int(out["A"]) + int(extra.get("insertion_cost") or 0)
    rec = {
        "workload": workload,
        "stream_id": stream_id,
        "seed": seed,
        "index": index,
        "task_id": task["task_id"],
        "family_id": task.get("family_id"),
        "condition": condition,
        "Q": out["Q"],
        "A": A,
        "A_solve": out["A"],
        "acceptable": out["acceptable"],
        "primitive_evals": out.get("primitive_evals") or 0,
        "lookup_cost": out.get("lookup_cost") or 0,
        "validation_cost": out.get("validation_cost") or 0,
        "matching_cost": out.get("matching_cost") or 0,
        "hits": out.get("hits") or 0,
        "replays": out.get("replays") or 0,
        "validation_fails": out.get("validation_fails") or 0,
        "initial_state_hits": out.get("initial_state_hits") or 0,
        "intermediate_hits": out.get("intermediate_hits") or 0,
        "valid_reuse": bool(out.get("valid_reuse")),
        "first_hit_kind": out.get("first_hit_kind"),
        "first_hit_occupied": out.get("first_hit_occupied"),
        "primitive_evals_before_first_hit": out.get("primitive_evals_before_first_hit"),
        "A_identity_ok": out.get("A_identity_ok"),
    }
    rec.update(extra)
    if prim is None:
        rec["A_primitive"] = A
        rec["Q_primitive"] = out["Q"]
        rec["effort_saving"] = 0
        rec["quality_delta"] = 0.0
        rec["quality_loss"] = False
    else:
        rec["A_primitive"] = prim["A"]
        rec["Q_primitive"] = prim["Q"]
        rec["effort_saving"] = int(prim["A"]) - A
        rec["quality_delta"] = float(out["Q"]) - float(prim["Q"])
        rec["quality_loss"] = float(out["Q"]) < float(prim["Q"]) - 1.0
    return rec


def _hit_sources(table: ContinuationTable, keys: list) -> list[str]:
    return ["grown" if table.source_of(k) != "store" else "store" for k in keys]


def run_stream(config, base: ContinuationTable, tasks, workload, stream_id, seed, store_keys) -> list[dict]:
    frozen = base.copy(frozen=True)
    growing = base.copy(frozen=False)
    seen_in_stream: set = set()
    rows = []
    phase = f"expt14-{workload}-s{stream_id}"
    for index, task in enumerate(tasks):
        if task.get("constructed_prefix"):
            raise RuntimeError("evaluation must not use a constructed prefix")
        inv_key = inventory_key(task["inventory"])
        in_store = inv_key in store_keys
        seen_earlier = inv_key in seen_in_stream
        flags = {
            "inventory_in_store": in_store,
            "inventory_seen_earlier_in_stream": seen_earlier,
            "inventory_never_encountered": not in_store and not seen_earlier,
        }
        print(f"{workload} s{stream_id} {index + 1}/{len(tasks)} {task['task_id']}", flush=True)
        prim = solve_equiv(config, task, seed, phase, index, None, mode="primitive", allow_initial_lookup=True)
        rows.append(_row(task, workload, stream_id, seed, index, "primitive", prim, None,
                         {**flags, "insertion_cost": 0, "keys_before": None, "keys_after": None}))

        fro = solve_equiv(config, task, seed, phase, index, frozen, mode="exact", allow_initial_lookup=True)
        src = _hit_sources(frozen, fro.get("hit_keys") or [])
        rows.append(_row(task, workload, stream_id, seed, index, "frozen_exact", fro, prim,
                         {**flags, "insertion_cost": 0, "keys_before": len(frozen.entries),
                          "keys_after": len(frozen.entries), "hits_from_store": src.count("store"),
                          "hits_from_grown": src.count("grown"),
                          "first_hit_source": src[0] if src else None}))

        keys_before = len(growing.entries)
        gro = solve_equiv(config, task, seed, phase, index, growing, mode="exact", allow_initial_lookup=True)
        src = _hit_sources(growing, gro.get("hit_keys") or [])
        ins = growing.grow_from_success(gro["env"], config.q_min, source=f"s{stream_id}:{index}")
        rows.append(_row(task, workload, stream_id, seed, index, "growing_exact", gro, prim,
                         {**flags, "insertion_cost": ins["cost"], "keys_probed": ins["probed"],
                          "keys_written": ins["written"], "insert_collisions": ins["collisions"],
                          "keys_before": keys_before, "keys_after": len(growing.entries),
                          "hits_from_store": src.count("store"), "hits_from_grown": src.count("grown"),
                          "first_hit_source": src[0] if src else None}))
        seen_in_stream.add(inv_key)
    return rows


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _stream_summary(rows, workload, stream_id, condition, n_base_keys) -> dict:
    g = [r for r in rows if r["workload"] == workload and r["stream_id"] == stream_id and r["condition"] == condition]
    g.sort(key=lambda r: r["index"])
    if not g:
        return {}
    n = len(g)
    third = max(1, n // 3)
    new = [r for r in g if r["inventory_never_encountered"]]
    rep = [r for r in g if not r["inventory_never_encountered"]]
    reuse = [r for r in g if r["valid_reuse"]]
    return {
        "workload": workload,
        "stream_id": stream_id,
        "condition": condition,
        "n": n,
        "cumulative_saving": sum(r["effort_saving"] for r in g),
        "mean_saving": _mean([r["effort_saving"] for r in g]),
        "early_mean_saving": _mean([r["effort_saving"] for r in g[:third]]),
        "late_mean_saving": _mean([r["effort_saving"] for r in g[-third:]]),
        "mean_A": _mean([r["A"] for r in g]),
        "mean_Q": _mean([r["Q"] for r in g]),
        "mean_quality_delta": _mean([r["quality_delta"] for r in g]),
        "n_quality_loss": sum(1 for r in g if r["quality_loss"]),
        "n_validation_fails": sum(int(r["validation_fails"]) for r in g),
        "n_initial_hits": sum(int(r["initial_state_hits"]) for r in g),
        "n_intermediate_hits": sum(int(r["intermediate_hits"]) for r in g),
        "n_hits_from_grown": sum(int(r.get("hits_from_grown") or 0) for r in g),
        "n_boxes_valid_reuse": len(reuse),
        "frac_boxes_valid_reuse": len(reuse) / n,
        "mean_primitive_before_first_hit": _mean([r["primitive_evals_before_first_hit"] for r in reuse]),
        "mean_lookup": _mean([r["lookup_cost"] for r in g]),
        "mean_insertion": _mean([r.get("insertion_cost") or 0 for r in g]),
        "n_never_encountered": len(new),
        "n_repeated": len(rep),
        "cumulative_saving_never_encountered": sum(r["effort_saving"] for r in new),
        "mean_saving_never_encountered": _mean([r["effort_saving"] for r in new]),
        "n_quality_loss_never_encountered": sum(1 for r in new if r["quality_loss"]),
        "n_intermediate_hits_never_encountered": sum(int(r["intermediate_hits"]) for r in new),
        "n_reuse_never_encountered": sum(1 for r in new if r["valid_reuse"]),
        "cumulative_saving_repeated": sum(r["effort_saving"] for r in rep),
        "n_reuse_repeated": sum(1 for r in rep if r["valid_reuse"]),
        "keys_start": n_base_keys,
        "keys_end": g[-1].get("keys_after") if condition == "growing_exact" else n_base_keys,
        "keys_curve": [r.get("keys_after") for r in g] if condition == "growing_exact" else None,
    }


def _across(stream_sums: list[dict]) -> dict:
    if not stream_sums:
        return {}

    def col(key):
        return [s.get(key) for s in stream_sums if s.get(key) is not None]

    cum = col("cumulative_saving")
    early = col("early_mean_saving")
    late = col("late_mean_saving")
    growth = [
        (s["keys_end"] / s["keys_start"]) for s in stream_sums if s.get("keys_start") and s.get("keys_end") is not None
    ]
    return {
        "n_streams": len(stream_sums),
        "mean_cumulative_saving": _mean(cum),
        "min_cumulative_saving": min(cum) if cum else None,
        "max_cumulative_saving": max(cum) if cum else None,
        "mean_per_box_saving": _mean(col("mean_saving")),
        "mean_early_saving": _mean(early),
        "mean_late_saving": _mean(late),
        "n_streams_late_gt_early": sum(1 for s in stream_sums if (s.get("late_mean_saving") or 0) > (s.get("early_mean_saving") or 0)),
        "total_initial_hits": sum(col("n_initial_hits")),
        "total_intermediate_hits": sum(col("n_intermediate_hits")),
        "total_hits_from_grown": sum(col("n_hits_from_grown")),
        "total_quality_loss": sum(col("n_quality_loss")),
        "total_validation_fails": sum(col("n_validation_fails")),
        "total_never_encountered": sum(col("n_never_encountered")),
        "total_repeated": sum(col("n_repeated")),
        "mean_saving_never_encountered": _mean(col("mean_saving_never_encountered")),
        "sum_saving_never_encountered": sum(col("cumulative_saving_never_encountered")),
        "total_intermediate_hits_never_encountered": sum(col("n_intermediate_hits_never_encountered")),
        "total_reuse_never_encountered": sum(col("n_reuse_never_encountered")),
        "total_quality_loss_never_encountered": sum(col("n_quality_loss_never_encountered")),
        "total_reuse_repeated": sum(col("n_reuse_repeated")),
        "sum_saving_repeated": sum(col("cumulative_saving_repeated")),
        "mean_frac_boxes_valid_reuse": _mean(col("frac_boxes_valid_reuse")),
        "mean_key_growth_factor": _mean(growth),
        "mean_insertion_per_box": _mean(col("mean_insertion")),
        "streams": stream_sums,
    }


def decide(growing: dict, config: Config) -> dict:
    inter_new = int(growing.get("total_intermediate_hits_never_encountered") or 0)
    n_new = int(growing.get("total_never_encountered") or 0)
    ql_new = int(growing.get("total_quality_loss_never_encountered") or 0)
    repay = (growing.get("sum_saving_never_encountered") or 0) > 0 and (n_new == 0 or ql_new / n_new <= 0.2)
    reuse_new = int(growing.get("total_reuse_never_encountered") or 0)
    reuse_rep = int(growing.get("total_reuse_repeated") or 0)
    growth = growing.get("mean_key_growth_factor") or 1.0
    substantial = growth >= float(config.growth_substantial_factor)
    a = inter_new > 0 and repay
    b = not a and reuse_new == 0 and reuse_rep > 0
    c = not a and substantial
    if a:
        outcome = "A: intermediate hits emerged on never-encountered inventories and repaid their costs; accumulated experience addresses the coverage problem"
    elif b:
        outcome = "B: gains confined to repeated inventories; the demonstrated capability remains whole-problem recall"
    elif reuse_new == 0 and reuse_rep == 0:
        outcome = "no reuse of any kind in this workload"
    else:
        outcome = "reuse on never-encountered inventories occurred but did not repay its costs at preserved quality"
    return {
        "intermediate_hits_never_encountered": inter_new,
        "reuse_never_encountered": reuse_new,
        "reuse_repeated": reuse_rep,
        "repays_on_never_encountered": repay,
        "mean_key_growth_factor": growth,
        "growth_substantial": substantial,
        "outcome_A": a,
        "outcome_B": b,
        "outcome_C_stop_expanding_exact_table": c,
        "outcome": outcome,
        "outcome_C_text": (
            "memory grew substantially without useful intermediate hits: stop expanding the exact-state "
            "table and investigate a representation that can reuse smaller subproblems"
            if c
            else None
        ),
    }


def run_experiment(config: Config) -> dict:
    generate(target=int(config.n_store_independent), timeout=600.0, seed=int(config.generate_seed), out_name="store")
    independent_store = load_json_tasks(ROOT / "data" / "store.json")[: int(config.n_store_independent)]
    if len(independent_store) < int(config.n_store_independent):
        raise RuntimeError(f"independent store {len(independent_store)}")
    for task in independent_store:
        task["workload"] = "store_independent"
        task["constructed_prefix"] = None

    family_specs = declare_families(int(config.n_families), random.Random(int(config.generate_seed) + 17))
    blocked = {inventory_key(t["inventory"]) for t in independent_store}
    family_store = generate_family_members(
        family_specs, int(config.n_store_per_family), int(config.generate_seed) + 31, blocked, timeout=600.0
    )
    (ROOT / "data" / "family_store.json").write_text(
        json.dumps({"tasks": family_store, "specs": family_specs}, indent=2), encoding="utf-8"
    )
    store_tasks = list(independent_store) + list(family_store)
    store_keys = {inventory_key(t["inventory"]) for t in store_tasks}

    streams: dict[tuple[str, int], list[dict]] = {}
    for stream_id, _seed in enumerate(config.stream_seeds):
        name = f"fresh_s{stream_id}"
        generate(
            target=int(config.n_per_stream),
            timeout=600.0,
            seed=int(config.generate_seed) + 100 + stream_id,
            out_name=name,
            extra_blocked=[ROOT / "data" / "store.json", ROOT / "data" / "family_store.json"],
        )
        fresh = load_json_tasks(ROOT / "data" / f"{name}.json")[: int(config.n_per_stream)]
        if len(fresh) < int(config.n_per_stream):
            raise RuntimeError(f"stream {stream_id} fresh {len(fresh)}")
        for task in fresh:
            task["workload"] = "independent_fresh"
            task["constructed_prefix"] = None
        family = sample_family_stream(
            family_specs, int(config.n_per_stream), int(config.generate_seed) + 200 + stream_id
        )
        (ROOT / "data" / f"family_stream_s{stream_id}.json").write_text(
            json.dumps({"tasks": family, "specs": family_specs}, indent=2), encoding="utf-8"
        )
        streams[("independent_fresh", stream_id)] = fresh
        streams[("recurring_family", stream_id)] = family
    print(f"streams declared before evaluation: {len(streams)}", flush=True)

    base = ContinuationTable()
    rows = []
    for seed in config.store_seeds:
        for index, task in enumerate(store_tasks):
            print(f"store seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt14-store", index)
            base.learn_from_success(prim["env"], prim["ledger"], config.q_min)
    base.freeze()
    n_base = len(base.entries)
    print(f"base table {n_base} keys, frozen", flush=True)

    for (workload, stream_id), tasks in streams.items():
        seed = int(config.stream_seeds[stream_id])
        rows += run_stream(config, base, tasks, workload, stream_id, seed, store_keys)

    across: dict = {}
    decisions: dict = {}
    for workload in WORKLOADS:
        across[workload] = {}
        for cond in CONDITIONS:
            sums = [
                _stream_summary(rows, workload, s, cond, n_base) for s in range(config.n_streams)
            ]
            across[workload][cond] = _across([s for s in sums if s])
        decisions[workload] = decide(across[workload]["growing_exact"], config)

    return {
        "store_independent_ids": [t["task_id"] for t in independent_store],
        "family_store_ids": [t["task_id"] for t in family_store],
        "family_specs": family_specs,
        "stream_task_ids": {f"{w}_s{s}": [t["task_id"] for t in ts] for (w, s), ts in streams.items()},
        "n_base_keys": n_base,
        "n_base_initial_keys": base.n_initial_keys(),
        "across": across,
        "decisions": decisions,
        "rows": rows,
        "note": (
            "Each box is solved with only the memory available before it. Growing memory inserts the "
            "growing agent's completed solve afterwards (first write wins) and bills insertion to that "
            "box. Each stream has its own memory copy starting from the same frozen base table. Streams "
            "are declared before evaluation; no task is chosen by checking memory. Retrieval is exact "
            "state identity; transformation matching is excluded. Initial-state and intermediate hits "
            "are reported separately. Streams, not seeds, are the independent units."
        ),
    }
