"""Store exact continuations, then compare recurring boxes with fresh boxes."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import Config
from continuation import ContinuationTable
from policy_exact import solve_exact, solve_primitive


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
    from environment import PackingEnv
    from inventory import Inventory
    from solver import Ledger

    env = PackingEnv(budget=80, inventory=Inventory({"A": 1}))
    table = ContinuationTable()
    ledger = Ledger()
    table.learn_from_success(env, ledger)
    return {
        "hypothesis": "exact continuation reuse on (mask, inventory)",
        "not_abstraction": True,
        "not_expt8c_rescue": True,
        "A_identity": "primitive_evals + lookup + validation + learning",
        "catalogue_note": "same A–P catalogue; no Expt-7 libraries",
        "empty_store_on_unsuccessful": True,
        "key": "(mask, inventory counts)",
    }


def _row(seed, task, split, condition, out, primitive_ref=None) -> dict:
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
    }
    if primitive_ref is not None:
        rec["A_primitive"] = primitive_ref["A"]
        rec["Q_primitive"] = primitive_ref["Q"]
        rec["effort_saving"] = primitive_ref["A"] - out["A"]
        rec["quality_loss"] = out["Q"] < primitive_ref["Q"] - 1.0
    else:
        rec["A_primitive"] = out["A"]
        rec["Q_primitive"] = out["Q"]
        rec["effort_saving"] = 0
        rec["quality_loss"] = False
    return rec


def _summarise(rows: list[dict], split: str, condition: str) -> dict:
    picked = [r for r in rows if r["split"] == split and r["condition"] == condition]
    if not picked:
        return {"n": 0, "split": split, "condition": condition}
    hits = sum(int(r["hits"]) for r in picked)
    lookups = sum(int(r["lookups"]) for r in picked)
    return {
        "n": len(picked),
        "split": split,
        "condition": condition,
        "n_boxes": len({r["task_id"] for r in picked}),
        "n_seeds": len({r["seed"] for r in picked}),
        "mean_A": sum(r["A"] for r in picked) / len(picked),
        "mean_Q": sum(r["Q"] for r in picked) / len(picked),
        "mean_effort_saving": sum(r["effort_saving"] for r in picked) / len(picked),
        "quality_loss_rate": sum(1.0 for r in picked if r["quality_loss"]) / len(picked),
        "acceptable_rate": sum(1.0 for r in picked if r["acceptable"]) / len(picked),
        "hit_rate": None if not lookups else hits / lookups,
        "n_hits": hits,
        "n_lookups": lookups,
        "n_replays": sum(int(r["replays"]) for r in picked),
        "n_validation_fails": sum(int(r["validation_fails"]) for r in picked),
        "mean_lookup": sum(r["lookup_cost"] for r in picked) / len(picked),
        "mean_validation": sum(r["validation_cost"] for r in picked) / len(picked),
        "mean_learning": sum(r["learning_cost"] for r in picked) / len(picked),
        "mean_primitive_evals": sum(r["primitive_evals"] for r in picked) / len(picked),
        "mean_reuse_cost": sum(r["reuse_cost"] for r in picked) / len(picked),
    }


def run_experiment(config: Config) -> dict:
    store_tasks, fresh_tasks = generate_splits(config)
    table = ContinuationTable()
    rows = []
    print(f"store {len(store_tasks)} boxes; fresh {len(fresh_tasks)}", flush=True)
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"store primitive seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt9-store", index)
            n_new = table.learn_from_success(prim["env"], prim["ledger"], config.q_min)
            rec = _row(seed, task, "store", "primitive", prim)
            rec["learning_cost"] = prim["ledger"].learning_cost
            rec["reuse_cost"] = prim["lookup_cost"] + prim["validation_cost"] + prim["ledger"].learning_cost
            rec["A"] = prim["primitive_evals"] + rec["reuse_cost"]
            rec["n_keys_added"] = n_new
            rows.append(rec)
    table.freeze()
    frozen_n = len(table.entries)
    frozen_bytes = table.bytes()
    primitive_fresh = {}
    primitive_store = {(r["seed"], r["task_id"]): r for r in rows if r["split"] == "store"}
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"recurring exact seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            exact = solve_exact(config, task, seed, "expt9-recurring", index, table, learn=False)
            store_prim_evals = primitive_store[(seed, task["task_id"])]["primitive_evals"]
            rec = _row(seed, task, "recurring", "exact", exact, {"A": store_prim_evals, "Q": primitive_store[(seed, task["task_id"])]["Q"]})
            rows.append(rec)
        for index, task in enumerate(fresh_tasks):
            print(f"fresh primitive seed={seed} {index + 1}/{len(fresh_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt9-fresh", index)
            primitive_fresh[(seed, task["task_id"])] = prim
            rows.append(_row(seed, task, "fresh", "primitive", prim))
            print(f"fresh exact seed={seed} {index + 1}/{len(fresh_tasks)} {task['task_id']}", flush=True)
            exact = solve_exact(config, task, seed, "expt9-fresh", index, table, learn=False)
            rows.append(_row(seed, task, "fresh", "exact", exact, prim))
    summaries = [
        _summarise(rows, "store", "primitive"),
        _summarise(rows, "recurring", "exact"),
        _summarise(rows, "fresh", "primitive"),
        _summarise(rows, "fresh", "exact"),
    ]
    recurring = next(s for s in summaries if s["split"] == "recurring")
    fresh_exact = next(s for s in summaries if s["split"] == "fresh" and s["condition"] == "exact")
    ql = recurring.get("quality_loss_rate")
    useful = (
        (recurring.get("mean_effort_saving") or 0) > 0
        and ql is not None
        and ql <= 0.2
        and (recurring.get("hit_rate") or 0) > 0
    )
    return {
        "store_ids": [t["task_id"] for t in store_tasks],
        "fresh_ids": [t["task_id"] for t in fresh_tasks],
        "rows": rows,
        "summaries": summaries,
        "n_keys": frozen_n,
        "storage_bytes": frozen_bytes,
        "table_frozen": True,
        "recurrence_hit_rate_recurring": recurring.get("hit_rate"),
        "recurrence_hit_rate_fresh": fresh_exact.get("hit_rate"),
        "useful_on_recurring": useful,
        "proceed_wholebox": False,
        "note": "Exact reuse is memorization. Fresh hits, if any, are accidental identical remaining states, not learned equivalence.",
    }
