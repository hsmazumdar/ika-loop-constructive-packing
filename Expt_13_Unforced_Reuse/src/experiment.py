"""Store and freeze memory and selection, then evaluate unforced ordinary search."""

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
from construct_equiv import build_equivalence_tasks, partition_families
from continuation import ContinuationTable
from family_gen import declare_families, generate_family_members
from policy_equiv import observe_train_case, solve_equiv
from policy_exact import solve_primitive
from tools.generate_boxes import generate, inventory_key
from transforms import TransformSelector


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
        "hypothesis": (
            "frozen exact and learned-transform memory save effort at preserved quality when "
            "ordinary search reaches reusable states without constructed prefixes"
        ),
        "mechanism": "frozen Expt-11/12",
        "constructed_prefix_on_eval": False,
        "scheduled_matches": False,
        "online_memory_growth": False,
        "category_hidden": True,
        "family_generator_consults_table": False,
        "seeds_are_paired_not_independent_memories": True,
        "does_not_invent_transforms": True,
        "does_not_expand_abstraction": True,
        "A_identity": "primitive_evals + lookup + matching + transformation + validation + learning",
    }


def _row(seed, task, split, condition, out, primitive_ref=None, **extra) -> dict:
    rec = {
        "seed": seed,
        "task_id": task["task_id"],
        "split": split,
        "condition": condition,
        "workload": task.get("workload") or extra.get("workload"),
        "stream_id": extra.pop("stream_id", None),
        "family_id": task.get("family_id"),
        "Q": out["Q"],
        "A": out["A"],
        "acceptable": out["acceptable"],
        "primitive_evals": out.get("primitive_evals") or 0,
        "lookup_cost": out.get("lookup_cost") or 0,
        "matching_cost": out.get("matching_cost") or 0,
        "transformation_cost": out.get("transformation_cost") or 0,
        "validation_cost": out.get("validation_cost") or 0,
        "hits": out.get("hits") or 0,
        "exact_hits": out.get("exact_hits") or 0,
        "equiv_hits": out.get("equiv_hits") or 0,
        "replays": out.get("replays") or 0,
        "validation_fails": out.get("validation_fails") or 0,
        "used_transform": out.get("used_transform"),
        "initial_state_hit": bool(out.get("initial_state_hit")),
        "initial_state_hits": out.get("initial_state_hits") or 0,
        "intermediate_hits": out.get("intermediate_hits") or 0,
        "valid_reuse": bool(out.get("valid_reuse")),
        "first_hit_kind": out.get("first_hit_kind"),
        "first_hit_occupied": out.get("first_hit_occupied"),
        "primitive_evals_before_first_hit": out.get("primitive_evals_before_first_hit"),
        "A_identity_ok": out.get("A_identity_ok"),
        "constructed_prefix_used": bool(task.get("constructed_prefix")),
        "inventory_repeats_store": bool(task.get("inventory_repeats_store")),
    }
    rec.update(extra)
    if primitive_ref is not None:
        rec["A_primitive"] = primitive_ref["A"]
        rec["Q_primitive"] = primitive_ref["Q"]
        rec["effort_saving"] = primitive_ref["A"] - out["A"]
        rec["quality_loss"] = out["Q"] < primitive_ref["Q"] - 1.0
        rec["quality_delta"] = out["Q"] - primitive_ref["Q"]
    else:
        rec["A_primitive"] = out["A"]
        rec["Q_primitive"] = out["Q"]
        rec["effort_saving"] = 0
        rec["quality_loss"] = False
        rec["quality_delta"] = 0.0
    return rec


def interpret(net: bool, present: bool, n_init: int, n_inter: int) -> str:
    if not present:
        return (
            "no valid reuse observed in these streams with this frozen table and exact state "
            "representation; this does not establish how rare recurrence is throughout the environment"
        )
    if n_inter == 0:
        return (
            "all hits were initial-state whole-problem recurrences (the inventory itself repeated); "
            "no reusable intermediate state was reached through autonomous placements in these streams"
            + ("; net saving came from exact whole-problem recall" if net else "")
        )
    if net:
        return "lower total effort at preserved quality, including intermediate hits after autonomous placements"
    return "intermediate reuse occurred but did not produce a net saving at preserved quality"


def _mean(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _summarise(rows, split, condition) -> dict:
    picked = [r for r in rows if r["split"] == split and r["condition"] == condition]
    if not picked:
        return {"n": 0, "split": split, "condition": condition}
    hit_rows = [r for r in picked if r.get("valid_reuse")]
    return {
        "n": len(picked),
        "split": split,
        "condition": condition,
        "workload": picked[0].get("workload"),
        "stream_id": picked[0].get("stream_id"),
        "n_tasks": len({r["task_id"] for r in picked}),
        "n_seeds": len({r["seed"] for r in picked}),
        "mean_A": _mean(picked, "A"),
        "mean_Q": _mean(picked, "Q"),
        "mean_effort_saving": _mean(picked, "effort_saving"),
        "mean_quality_delta": _mean(picked, "quality_delta"),
        "quality_loss_rate": sum(1.0 for r in picked if r["quality_loss"]) / len(picked),
        "n_quality_loss": sum(1 for r in picked if r["quality_loss"]),
        "acceptable_rate": sum(1.0 for r in picked if r["acceptable"]) / len(picked),
        "n_hits": sum(int(r["hits"] or 0) for r in picked),
        "n_exact_hits": sum(int(r["exact_hits"] or 0) for r in picked),
        "n_equiv_hits": sum(int(r["equiv_hits"] or 0) for r in picked),
        "n_initial_hits": sum(int(r["initial_state_hits"] or 0) for r in picked),
        "n_intermediate_hits": sum(int(r["intermediate_hits"] or 0) for r in picked),
        "n_boxes_valid_reuse": sum(1 for r in picked if r.get("valid_reuse")),
        "frac_boxes_valid_reuse": sum(1.0 for r in picked if r.get("valid_reuse")) / len(picked),
        "mean_primitive_before_first_hit": _mean(hit_rows, "primitive_evals_before_first_hit"),
        "mean_lookup": _mean(picked, "lookup_cost"),
        "mean_matching": _mean(picked, "matching_cost"),
        "mean_transformation": _mean(picked, "transformation_cost"),
        "mean_validation": _mean(picked, "validation_cost"),
        "mean_primitive_evals": _mean(picked, "primitive_evals"),
        "n_constructed_prefix": sum(1 for r in picked if r.get("constructed_prefix_used")),
    }


def _across_streams(stream_summaries: list[dict]) -> dict:
    if not stream_summaries:
        return {}
    savings = [s.get("mean_effort_saving") for s in stream_summaries if s.get("mean_effort_saving") is not None]
    fracs = [s.get("frac_boxes_valid_reuse") for s in stream_summaries if s.get("frac_boxes_valid_reuse") is not None]
    qls = [s.get("quality_loss_rate") for s in stream_summaries if s.get("quality_loss_rate") is not None]
    return {
        "n_streams": len(stream_summaries),
        "across_stream_mean_saving": sum(savings) / len(savings) if savings else None,
        "across_stream_min_saving": min(savings) if savings else None,
        "across_stream_max_saving": max(savings) if savings else None,
        "across_stream_mean_reuse_frac": sum(fracs) / len(fracs) if fracs else None,
        "across_stream_mean_quality_loss": sum(qls) / len(qls) if qls else None,
        "streams": stream_summaries,
    }


def _run_triple(config, task, seed, index, split, phase, table, selected, rows, stream_id, workload):
    if task.get("constructed_prefix"):
        raise RuntimeError("evaluation must not use a constructed prefix")
    prim = solve_equiv(
        config, task, seed, phase, index, table, mode="primitive",
        constructed_prefix=None, allow_initial_lookup=True,
    )
    rows.append(_row(seed, task, split, "primitive", prim, stream_id=stream_id, workload=workload))
    for label, mode in (("exact", "exact"), ("learned", "learned")):
        out = solve_equiv(
            config, task, seed, phase, index, table, mode=mode, selected=selected,
            constructed_prefix=None, allow_initial_lookup=True,
        )
        rows.append(_row(seed, task, split, label, out, prim, stream_id=stream_id, workload=workload))


def run_experiment(config: Config) -> dict:
    from tools.generate_boxes import generate as generate_boxes

    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    generate_boxes(
        target=int(config.n_store_independent),
        timeout=600.0,
        seed=int(config.generate_seed),
        out_name="store",
    )
    independent_store = load_json_tasks(ROOT / "data" / "store.json")[: int(config.n_store_independent)]
    if len(independent_store) < int(config.n_store_independent):
        raise RuntimeError(f"independent store {len(independent_store)}")
    for task in independent_store:
        task["workload"] = "store_independent"
        task["constructed_prefix"] = None

    family_rng = random.Random(int(config.generate_seed) + 17)
    family_specs = declare_families(int(config.n_families), family_rng)
    blocked = {inventory_key(t["inventory"]) for t in independent_store}
    family_store = generate_family_members(
        family_specs,
        int(config.n_store_per_family),
        int(config.generate_seed) + 31,
        blocked,
        timeout=600.0,
    )
    (ROOT / "data" / "family_store.json").write_text(
        json.dumps({"tasks": family_store, "specs": family_specs}, indent=2), encoding="utf-8"
    )
    store_tasks = list(independent_store) + list(family_store)
    print(
        f"store independent {len(independent_store)}; family store {len(family_store)}; "
        f"families {len(family_specs)}",
        flush=True,
    )

    table = ContinuationTable()
    rows = []
    donors = []
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"store seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt13-store", index)
            table.learn_from_success(prim["env"], prim["ledger"], config.q_min)
            rec = _row(seed, task, "store", "primitive", prim, workload=task.get("workload"))
            rec["A"] = prim["primitive_evals"] + prim["ledger"].learning_cost
            rec["learning_cost"] = prim["ledger"].learning_cost
            rows.append(rec)
            if prim["acceptable"] and not any(d["task_id"] == task["task_id"] for d in donors):
                donors.append(
                    {
                        "task_id": task["task_id"],
                        "seed": seed,
                        "inventory": dict(task["inventory"]),
                        "stack": list(prim["stack"]),
                    }
                )
    table.freeze()
    if not table.frozen:
        raise RuntimeError("table must be frozen before selection and evaluation")

    train_ids, test_ids = partition_families([d["task_id"] for d in donors], config.train_frac)
    coverage_tasks = build_equivalence_tasks(donors, table, train_ids, config)
    selector = TransformSelector()
    n_coverage_observed = 0
    for task in coverage_tasks:
        if task.get("partition") == "train":
            observe_train_case(task, table, selector)
            n_coverage_observed += 1
    selected = selector.freeze()
    if not selector.frozen:
        raise RuntimeError("selection must be frozen before evaluation")
    print(
        f"coverage-pass cases {n_coverage_observed}; selected {list(selected)} "
        f"before evaluation; table frozen={table.frozen}",
        flush=True,
    )

    stored_keys = {inventory_key(t["inventory"]) for t in store_tasks}
    stream_meta = []
    eval_ids = {"independent_fresh": [], "recurring_family": []}
    for stream_id in range(int(config.n_streams)):
        fresh_name = f"fresh_s{stream_id}"
        generate(
            target=int(config.n_fresh_per_stream),
            timeout=600.0,
            seed=int(config.generate_seed) + 100 + stream_id,
            out_name=fresh_name,
            extra_blocked=[ROOT / "data" / "store.json", ROOT / "data" / "family_store.json"],
        )
        fresh = load_json_tasks(ROOT / "data" / f"{fresh_name}.json")[: int(config.n_fresh_per_stream)]
        if len(fresh) < int(config.n_fresh_per_stream):
            raise RuntimeError(f"stream {stream_id} fresh {len(fresh)}")
        for task in fresh:
            if inventory_key(task["inventory"]) in stored_keys:
                raise RuntimeError(f"fresh inventory collides with store {task['task_id']}")
            task["workload"] = "independent_fresh"
            task["constructed_prefix"] = None
            task["family_id"] = None
        eval_ids["independent_fresh"].extend(t["task_id"] for t in fresh)

        # Stored inventories are not excluded here: filtering on what memory holds would
        # select cases by their relation to the table.
        blocked_eval = {inventory_key(t["inventory"]) for t in fresh}
        family_eval = generate_family_members(
            family_specs,
            int(config.n_eval_per_family),
            int(config.generate_seed) + 200 + stream_id,
            blocked_eval,
            timeout=600.0,
        )
        for task in family_eval:
            if task.get("constructed_prefix"):
                raise RuntimeError("family generator must not attach a constructed prefix")
            task["workload"] = "recurring_family"
            task["inventory_repeats_store"] = inventory_key(task["inventory"]) in stored_keys
        eval_ids["recurring_family"].extend(t["task_id"] for t in family_eval)
        (ROOT / "data" / f"family_eval_s{stream_id}.json").write_text(
            json.dumps({"tasks": family_eval, "specs": family_specs}, indent=2), encoding="utf-8"
        )

        stream_meta.append(
            {
                "stream_id": stream_id,
                "n_fresh": len(fresh),
                "n_family": len(family_eval),
                "fresh_ids": [t["task_id"] for t in fresh],
                "family_ids": [t["task_id"] for t in family_eval],
            }
        )
        for workload, tasks in (("independent_fresh", fresh), ("recurring_family", family_eval)):
            split = f"{workload}_s{stream_id}"
            phase = f"expt13-{workload}-s{stream_id}"
            for seed in config.seeds:
                for index, task in enumerate(tasks):
                    print(
                        f"{split} seed={seed} {index + 1}/{len(tasks)} {task['task_id']}",
                        flush=True,
                    )
                    _run_triple(
                        config, task, seed, index, split, phase, table, selected, rows, stream_id, workload
                    )

    summaries = []
    across = {}
    for workload in ("independent_fresh", "recurring_family"):
        across[workload] = {}
        for cond in ("primitive", "exact", "learned"):
            stream_sums = []
            for stream_id in range(int(config.n_streams)):
                split = f"{workload}_s{stream_id}"
                summary = _summarise(rows, split, cond)
                if summary.get("n"):
                    summaries.append(summary)
                    stream_sums.append(summary)
            across[workload][cond] = _across_streams(stream_sums)

    learned_fresh = across.get("independent_fresh", {}).get("learned") or {}
    learned_family = across.get("recurring_family", {}).get("learned") or {}

    def _success(block: dict) -> dict:
        saving = block.get("across_stream_mean_saving")
        ql = block.get("across_stream_mean_quality_loss")
        reuse = block.get("across_stream_mean_reuse_frac") or 0
        n_inter = sum(int(s.get("n_intermediate_hits") or 0) for s in block.get("streams") or [])
        n_init = sum(int(s.get("n_initial_hits") or 0) for s in block.get("streams") or [])
        present = reuse > 0
        net = saving is not None and saving > 0 and ql is not None and ql <= 0.2 and present
        return {
            "reuse_present": present,
            "n_initial_hits": n_init,
            "n_intermediate_hits": n_inter,
            "net_save_quality_ok": net,
            "autonomous_intermediate_success": bool(net and n_inter > 0),
            "interpretation": interpret(net, present, n_init, n_inter),
        }

    return {
        "store_independent_ids": [t["task_id"] for t in independent_store],
        "family_store_ids": [t["task_id"] for t in family_store],
        "family_specs": family_specs,
        "eval_ids": eval_ids,
        "train_families": sorted(train_ids),
        "test_families": sorted(test_ids),
        "n_keys": len(table.entries),
        "n_overwrites": table.n_overwrites,
        "storage_bytes": table.bytes(),
        "n_initial_keys": table.n_initial_keys(),
        "table_frozen_before_eval": table.frozen,
        "selection_frozen_before_eval": selector.frozen,
        "coverage_pass": {
            "n_constructed_train_cases": n_coverage_observed,
            "n_constructed_total": len(coverage_tasks),
            "used_for_evaluation": False,
            "rule": "T-first coverage pass; same Expt-11 selection rule; not an evaluation workload",
        },
        "selector": selector.as_dict(),
        "stream_meta": stream_meta,
        "summaries": summaries,
        "across_streams": across,
        "learned_fresh": {**learned_fresh, **_success(learned_fresh)},
        "learned_family": {**learned_family, **_success(learned_family)},
        "rows": rows,
        "note": (
            "Evaluation has no constructed prefixes and no scheduled matching states. "
            "Family inventories are generated from a predeclared type-set rule that does not "
            "consult the memory table. Seeds are paired comparisons on identical starts, not "
            "independent learned memories. Results are summarised across independent streams. "
            "The table and selected transforms are frozen before evaluation; there is no online "
            "memory growth. Initial-state hits are reported separately from intermediate hits "
            "after autonomous placements."
        ),
    }
