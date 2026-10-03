"""Store exact continuations; test whole-problem repeats, constructed intermediate reuse, and fresh overhead."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import Config
from construct import build_constructed_tasks
from continuation import ContinuationTable
from policy_exact import solve_agent, solve_exact, solve_primitive


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


def generate_splits(config: Config) -> tuple[list[dict], list[dict]]:
    from tools.generate_boxes import generate

    generate(target=int(config.n_store), timeout=600.0, seed=int(config.generate_seed), out_name="store")
    store = load_json_tasks(ROOT / "data" / "store.json")[: int(config.n_store)]
    generate(
        target=int(config.n_fresh),
        timeout=600.0,
        seed=int(config.generate_seed) + 1,
        out_name="fresh",
        extra_blocked=[ROOT / "data" / "store.json"],
    )
    fresh = load_json_tasks(ROOT / "data" / "fresh.json")[: int(config.n_fresh)]
    if len(store) < int(config.n_store) or len(fresh) < int(config.n_fresh):
        raise RuntimeError(f"generated store={len(store)} fresh={len(fresh)}")
    overlap = {t["task_id"] for t in store} & {t["task_id"] for t in fresh}
    if overlap:
        raise RuntimeError(f"store/fresh overlap {overlap}")
    return store, fresh


def audit_implementation() -> dict:
    from continuation import ContinuationTable
    from environment import Action, PackingEnv
    from inventory import Inventory
    from solver import Ledger

    env = PackingEnv(budget=80, inventory=Inventory({"A": 1}))
    table = ContinuationTable()
    ledger = Ledger()
    table.learn_from_success(env, ledger)
    return {
        "hypothesis": "exact subproblem reuse after a nonempty prefix; whole-problem recall is the positive control",
        "not_abstraction": True,
        "not_expt8c_rescue": True,
        "A_identity": "primitive_evals + lookup + validation + learning",
        "catalogue_note": "same A–P catalogue; no Expt-7 libraries",
        "memory_sharing": "one shared ContinuationTable across seeds; frozen before eval",
        "retention": "first write wins; not best-of",
        "constructed_recurrence_labeled": True,
        "natural_recurrence_separate": True,
        "exclude_initial_state_on_constructed": True,
        "require_nonzero_prefix_on_constructed": True,
        "key": "(mask, inventory counts)",
        "empty_store_on_unsuccessful": True,
    }


def _row(seed, task, split, condition, out, primitive_ref=None, **extra) -> dict:
    rec = {
        "seed": seed,
        "task_id": task["task_id"],
        "split": split,
        "condition": condition,
        "Q": out["Q"],
        "A": out["A"],
        "acceptable": out["acceptable"],
        "termination": out["termination"],
        "primitive_evals": out["primitive_evals"],
        "lookup_cost": out["lookup_cost"],
        "validation_cost": out["validation_cost"],
        "learning_cost": out["learning_cost"],
        "reuse_cost": out["reuse_cost"],
        "lookups": out["lookups"],
        "hits": out["hits"],
        "replays": out["replays"],
        "validation_fails": out["validation_fails"],
        "A_identity_ok": out["A_identity_ok"],
        "n_place": out["n_place"],
        "prefix_primitive_evals": out.get("prefix_primitive_evals"),
        "prefix_n_place": out.get("prefix_n_place"),
        "remaining_primitive_evals": out.get("remaining_primitive_evals"),
        "first_hit_occupied": out.get("first_hit_occupied"),
        "first_hit_n_place": out.get("first_hit_n_place"),
        "initial_state_hit": out.get("initial_state_hit"),
        "natural_opportunities": out.get("natural_opportunities") or 0,
        "first_natural_opportunity_n_place": out.get("first_natural_opportunity_n_place"),
        "lookups_before_first_hit": out.get("lookups_before_first_hit"),
        "constructed_prefix_ok": out.get("constructed_prefix_ok"),
        "donor_task_id": task.get("donor_task_id"),
        "cut": task.get("cut"),
        "prefix_occupied": task.get("prefix_occupied"),
        "suffix_len": task.get("suffix_len"),
    }
    rec.update(extra)
    if primitive_ref is not None:
        rec["A_primitive"] = primitive_ref["A"]
        rec["Q_primitive"] = primitive_ref["Q"]
        rec["effort_saving"] = primitive_ref["A"] - out["A"]
        rec["quality_loss"] = out["Q"] < primitive_ref["Q"] - 1.0
        rec["remaining_search_avoided"] = primitive_ref.get("remaining_primitive_evals", primitive_ref.get("primitive_evals", 0)) - (
            out.get("remaining_primitive_evals") or 0
        )
    else:
        rec["A_primitive"] = out["A"]
        rec["Q_primitive"] = out["Q"]
        rec["effort_saving"] = 0
        rec["quality_loss"] = False
        rec["remaining_search_avoided"] = 0
    return rec


def _mean(rows: list[dict], key: str):
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _summarise(rows: list[dict], split: str, condition: str) -> dict:
    picked = [r for r in rows if r["split"] == split and r["condition"] == condition]
    if not picked:
        return {"n": 0, "split": split, "condition": condition}
    hits = sum(int(r["hits"] or 0) for r in picked)
    lookups = sum(int(r["lookups"] or 0) for r in picked)
    return {
        "n": len(picked),
        "split": split,
        "condition": condition,
        "n_boxes": len({r["task_id"] for r in picked}),
        "n_seeds": len({r["seed"] for r in picked}),
        "mean_A": _mean(picked, "A"),
        "mean_Q": _mean(picked, "Q"),
        "mean_effort_saving": _mean(picked, "effort_saving"),
        "mean_remaining_search_avoided": _mean(picked, "remaining_search_avoided"),
        "mean_prefix_primitive": _mean(picked, "prefix_primitive_evals"),
        "mean_prefix_n_place": _mean(picked, "prefix_n_place"),
        "mean_first_hit_occupied": _mean(picked, "first_hit_occupied"),
        "quality_loss_rate": sum(1.0 for r in picked if r["quality_loss"]) / len(picked),
        "acceptable_rate": sum(1.0 for r in picked if r["acceptable"]) / len(picked),
        "hit_rate": None if not lookups else hits / lookups,
        "n_hits": hits,
        "n_lookups": lookups,
        "n_replays": sum(int(r["replays"] or 0) for r in picked),
        "n_validation_fails": sum(int(r["validation_fails"] or 0) for r in picked),
        "n_initial_state_hits": sum(1 for r in picked if r.get("initial_state_hit")),
        "n_nonzero_prefix_hits": sum(
            1 for r in picked if r.get("hits") and not r.get("initial_state_hit") and (r.get("prefix_n_place") or 0) > 0
        ),
        "mean_lookup": _mean(picked, "lookup_cost"),
        "mean_validation": _mean(picked, "validation_cost"),
        "mean_learning": _mean(picked, "learning_cost"),
        "mean_primitive_evals": _mean(picked, "primitive_evals"),
        "mean_reuse_cost": _mean(picked, "reuse_cost"),
        "mean_remaining_primitive": _mean(picked, "remaining_primitive_evals"),
        "n_natural_opportunity_traces": sum(1 for r in picked if int(r.get("natural_opportunities") or 0) > 0),
        "natural_opportunity_rate": sum(1.0 for r in picked if int(r.get("natural_opportunities") or 0) > 0) / len(picked),
    }


def run_experiment(config: Config) -> dict:
    store_tasks, fresh_tasks = generate_splits(config)
    table = ContinuationTable()
    rows = []
    donors = []
    print(f"store {len(store_tasks)} boxes; fresh {len(fresh_tasks)}", flush=True)
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"store primitive seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt10-store", index)
            n_new = table.learn_from_success(prim["env"], prim["ledger"], config.q_min)
            rec = _row(seed, task, "store", "primitive", prim)
            rec["learning_cost"] = prim["ledger"].learning_cost
            rec["reuse_cost"] = prim["lookup_cost"] + prim["validation_cost"] + prim["ledger"].learning_cost
            rec["A"] = prim["primitive_evals"] + rec["reuse_cost"]
            rec["n_keys_added"] = n_new
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
    frozen_n = len(table.entries)
    frozen_bytes = table.bytes()
    n_initial = table.n_initial_keys()
    constructed_tasks = build_constructed_tasks(donors, table, config)
    print(f"constructed {len(constructed_tasks)} labeled intermediate tasks from {len(donors)} donors", flush=True)
    if not constructed_tasks:
        raise RuntimeError("no constructed intermediate tasks; cannot test subproblem reuse")

    primitive_store = {(r["seed"], r["task_id"]): r for r in rows if r["split"] == "store"}
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"recurring exact seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            exact = solve_exact(config, task, seed, "expt10-recurring", index, table, learn=False, allow_initial_lookup=True)
            store_ref = primitive_store[(seed, task["task_id"])]
            rows.append(
                _row(
                    seed,
                    task,
                    "recurring",
                    "exact",
                    exact,
                    {"A": store_ref["primitive_evals"], "Q": store_ref["Q"], "remaining_primitive_evals": store_ref["primitive_evals"]},
                )
            )

        for index, task in enumerate(constructed_tasks):
            print(f"constructed memory-off seed={seed} {index + 1}/{len(constructed_tasks)} {task['task_id']}", flush=True)
            off = solve_agent(
                config,
                task,
                seed,
                "expt10-constructed",
                index,
                table,
                memory=False,
                constructed_prefix=list(task["constructed_prefix"]),
                track_natural_opportunity=False,
            )
            off_row = _row(seed, task, "constructed", "memory_off", off)
            rows.append(off_row)
            print(f"constructed memory-on seed={seed} {index + 1}/{len(constructed_tasks)} {task['task_id']}", flush=True)
            on = solve_agent(
                config,
                task,
                seed,
                "expt10-constructed",
                index,
                table,
                memory=True,
                allow_initial_lookup=False,
                constructed_prefix=list(task["constructed_prefix"]),
            )
            rec = _row(
                seed,
                task,
                "constructed",
                "memory_on",
                on,
                {
                    "A": off["A"],
                    "Q": off["Q"],
                    "remaining_primitive_evals": off.get("remaining_primitive_evals") or 0,
                },
            )
            rec["remaining_search_avoided"] = (off.get("remaining_primitive_evals") or 0) - (
                on.get("remaining_primitive_evals") or 0
            )
            rec["initial_state_hit"] = bool(on.get("initial_state_hit"))
            rows.append(rec)

        for index, task in enumerate(fresh_tasks):
            print(f"fresh primitive seed={seed} {index + 1}/{len(fresh_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(
                config, task, seed, "expt10-fresh", index, table, track_natural_opportunity=True
            )
            rows.append(_row(seed, task, "fresh", "primitive", prim))
            print(f"fresh exact seed={seed} {index + 1}/{len(fresh_tasks)} {task['task_id']}", flush=True)
            exact = solve_exact(config, task, seed, "expt10-fresh", index, table, learn=False, allow_initial_lookup=True)
            rec = _row(seed, task, "fresh", "exact", exact, prim)
            rec["remaining_search_avoided"] = (prim["primitive_evals"]) - (exact["primitive_evals"])
            rows.append(rec)

    summaries = [
        _summarise(rows, "store", "primitive"),
        _summarise(rows, "recurring", "exact"),
        _summarise(rows, "constructed", "memory_off"),
        _summarise(rows, "constructed", "memory_on"),
        _summarise(rows, "fresh", "primitive"),
        _summarise(rows, "fresh", "exact"),
    ]
    recurring = next(s for s in summaries if s["split"] == "recurring")
    constructed_on = next(s for s in summaries if s["split"] == "constructed" and s["condition"] == "memory_on")
    fresh_exact = next(s for s in summaries if s["split"] == "fresh" and s["condition"] == "exact")
    fresh_prim = next(s for s in summaries if s["split"] == "fresh" and s["condition"] == "primitive")
    ql = constructed_on.get("quality_loss_rate")
    constructed_ok = (
        (constructed_on.get("mean_remaining_search_avoided") or 0) > 0
        and ql is not None
        and ql <= 0.2
        and (constructed_on.get("n_nonzero_prefix_hits") or 0) > 0
        and (constructed_on.get("n_initial_state_hits") or 0) == 0
    )
    return {
        "store_ids": [t["task_id"] for t in store_tasks],
        "fresh_ids": [t["task_id"] for t in fresh_tasks],
        "constructed_ids": [t["task_id"] for t in constructed_tasks],
        "constructed_meta": [
            {
                "task_id": t["task_id"],
                "donor_task_id": t["donor_task_id"],
                "donor_seed": t["donor_seed"],
                "cut": t["cut"],
                "prefix_occupied": t["prefix_occupied"],
                "suffix_len": t["suffix_len"],
                "n_alt_prefix": len(t["constructed_prefix"]),
            }
            for t in constructed_tasks
        ],
        "rows": rows,
        "summaries": summaries,
        "n_keys": frozen_n,
        "n_initial_keys": n_initial,
        "n_intermediate_keys": frozen_n - n_initial,
        "storage_bytes": frozen_bytes,
        "n_overwrites": table.n_overwrites,
        "table_frozen": True,
        "memory_sharing": "shared across seeds; first write wins; not per-agent; not best-of",
        "recurrence_hit_rate_recurring": recurring.get("hit_rate"),
        "recurrence_hit_rate_constructed": constructed_on.get("hit_rate"),
        "recurrence_hit_rate_fresh": fresh_exact.get("hit_rate"),
        "natural_intermediate_opportunity_rate": fresh_prim.get("natural_opportunity_rate"),
        "useful_on_recurring": (
            (recurring.get("mean_effort_saving") or 0) > 0
            and recurring.get("quality_loss_rate") is not None
            and recurring.get("quality_loss_rate") <= 0.2
            and (recurring.get("n_hits") or 0) > 0
        ),
        "useful_on_constructed_intermediate": constructed_ok,
        "note": (
            "Exact reuse is memorization. Constructed tasks are labeled: an alternative covering "
            "reaches a stored (mask, inventory) after a nonempty prefix. Natural intermediate "
            "recurrence on fresh primitive traces is reported separately. Fresh completed solves "
            "measure lookup overhead when no stored remaining state matches."
        ),
    }
