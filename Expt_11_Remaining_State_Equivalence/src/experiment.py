"""Store exact continuations; evaluate primitive, exact, supplied, and learned equivalence."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import Config
from construct_equiv import build_equivalence_tasks, build_foil_tasks, partition_families
from continuation import ContinuationTable
from policy_equiv import observe_train_case, solve_equiv
from policy_exact import solve_exact, solve_primitive
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
    return {
        "hypothesis": "declared remaining-state isometries can transform a stored continuation",
        "not_inventing_transforms": True,
        "not_general_abstraction": True,
        "engineered_and_learned_reported_separately": True,
        "A_identity": "primitive_evals + lookup + matching + transformation + validation + learning",
        "memory_sharing": "one shared ContinuationTable; first write wins",
        "symmetric_states_excluded": True,
        "family_split": "transformed versions of a donor stay in that donor's partition",
        "foils": "inventory change and near-miss geometry must reject reuse",
        "natural_frequency_separate": True,
        "candidates": ["rot90", "rot180", "rot270", "refl_x", "refl_y", "refl_d", "refl_ad"],
    }


def _row(seed, task, split, condition, out, primitive_ref=None, **extra) -> dict:
    rec = {
        "seed": seed,
        "task_id": task["task_id"],
        "split": split,
        "condition": condition,
        "family": task.get("family") or task.get("donor_task_id") or task["task_id"],
        "partition": task.get("partition"),
        "kind": task.get("kind"),
        "transform_label": task.get("transform"),
        "Q": out["Q"],
        "A": out["A"],
        "acceptable": out["acceptable"],
        "termination": out["termination"],
        "primitive_evals": out["primitive_evals"],
        "lookup_cost": out.get("lookup_cost") or 0,
        "matching_cost": out.get("matching_cost") or 0,
        "transformation_cost": out.get("transformation_cost") or 0,
        "validation_cost": out.get("validation_cost") or 0,
        "learning_cost": out.get("learning_cost") or 0,
        "reuse_cost": out.get("reuse_cost") or 0,
        "lookups": out.get("lookups") or 0,
        "hits": out.get("hits") or 0,
        "exact_hits": out.get("exact_hits") or 0,
        "equiv_hits": out.get("equiv_hits") or 0,
        "replays": out.get("replays") or 0,
        "validation_fails": out.get("validation_fails") or 0,
        "used_transform": out.get("used_transform"),
        "A_identity_ok": out.get("A_identity_ok"),
        "n_place": out.get("n_place"),
        "prefix_primitive_evals": out.get("prefix_primitive_evals"),
        "prefix_n_place": out.get("prefix_n_place"),
        "remaining_primitive_evals": out.get("remaining_primitive_evals"),
        "first_hit_occupied": out.get("first_hit_occupied"),
        "initial_state_hit": out.get("initial_state_hit"),
        "natural_opportunities": out.get("natural_opportunities") or 0,
        "donor_task_id": task.get("donor_task_id"),
        "cut": task.get("cut"),
    }
    rec.update(extra)
    if primitive_ref is not None:
        rec["A_primitive"] = primitive_ref["A"]
        rec["Q_primitive"] = primitive_ref["Q"]
        rec["effort_saving"] = primitive_ref["A"] - out["A"]
        rec["quality_loss"] = out["Q"] < primitive_ref["Q"] - 1.0
        rec["remaining_search_avoided"] = (primitive_ref.get("remaining_primitive_evals") or 0) - (
            out.get("remaining_primitive_evals") or 0
        )
    else:
        rec["A_primitive"] = out["A"]
        rec["Q_primitive"] = out["Q"]
        rec["effort_saving"] = 0
        rec["quality_loss"] = False
        rec["remaining_search_avoided"] = 0
    return rec


def _mean(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _summarise(rows, split, condition) -> dict:
    picked = [r for r in rows if r["split"] == split and r["condition"] == condition]
    if not picked:
        return {"n": 0, "split": split, "condition": condition}
    lookups = sum(int(r["lookups"] or 0) for r in picked)
    hits = sum(int(r["hits"] or 0) for r in picked)
    return {
        "n": len(picked),
        "split": split,
        "condition": condition,
        "n_boxes": len({r["task_id"] for r in picked}),
        "mean_A": _mean(picked, "A"),
        "mean_Q": _mean(picked, "Q"),
        "mean_effort_saving": _mean(picked, "effort_saving"),
        "mean_remaining_search_avoided": _mean(picked, "remaining_search_avoided"),
        "mean_prefix_primitive": _mean(picked, "prefix_primitive_evals"),
        "quality_loss_rate": sum(1.0 for r in picked if r["quality_loss"]) / len(picked),
        "n_quality_loss": sum(1 for r in picked if r["quality_loss"]),
        "acceptable_rate": sum(1.0 for r in picked if r["acceptable"]) / len(picked),
        "hit_rate": None if not lookups else hits / lookups,
        "n_hits": hits,
        "n_lookups": lookups,
        "n_exact_hits": sum(int(r["exact_hits"] or 0) for r in picked),
        "n_equiv_hits": sum(int(r["equiv_hits"] or 0) for r in picked),
        "n_replays": sum(int(r["replays"] or 0) for r in picked),
        "n_validation_fails": sum(int(r["validation_fails"] or 0) for r in picked),
        "n_initial_state_hits": sum(1 for r in picked if r.get("initial_state_hit")),
        "mean_lookup": _mean(picked, "lookup_cost"),
        "mean_matching": _mean(picked, "matching_cost"),
        "mean_transformation": _mean(picked, "transformation_cost"),
        "mean_validation": _mean(picked, "validation_cost"),
        "mean_primitive_evals": _mean(picked, "primitive_evals"),
        "natural_opportunity_rate": sum(1.0 for r in picked if int(r.get("natural_opportunities") or 0) > 0) / len(picked),
    }


def _run_quad(config, task, seed, index, split, phase, table, selected, rows, allow_initial=False, track_nat=False):
    prefix = list(task["constructed_prefix"]) if task.get("constructed_prefix") else None
    prim = solve_equiv(
        config, task, seed, phase, index, table, mode="primitive",
        constructed_prefix=prefix, allow_initial_lookup=allow_initial, track_natural_opportunity=track_nat,
    )
    rows.append(_row(seed, task, split, "primitive", prim))
    agents = (
        ("exact", "exact"),
        ("supplied", "supplied"),
        ("learned", "learned"),
    )
    for label, mode in agents:
        out = solve_equiv(
            config, task, seed, phase, index, table, mode=mode, selected=selected,
            constructed_prefix=prefix, allow_initial_lookup=allow_initial,
        )
        rec = _row(seed, task, split, label, out, prim)
        rec["remaining_search_avoided"] = (prim.get("remaining_primitive_evals") or 0) - (
            out.get("remaining_primitive_evals") or 0
        )
        rows.append(rec)


def run_experiment(config: Config) -> dict:
    store_tasks, fresh_tasks = generate_splits(config)
    table = ContinuationTable()
    rows = []
    donors = []
    print(f"store {len(store_tasks)} boxes; fresh {len(fresh_tasks)}", flush=True)
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"store primitive seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt11-store", index)
            n_new = table.learn_from_success(prim["env"], prim["ledger"], config.q_min)
            rec = _row(seed, task, "store", "primitive", prim)
            rec["learning_cost"] = prim["ledger"].learning_cost
            rec["reuse_cost"] = prim["ledger"].learning_cost
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
    train_ids, test_ids = partition_families([d["task_id"] for d in donors], config.train_frac)
    equiv_tasks = build_equivalence_tasks(donors, table, train_ids, config)
    foils = build_foil_tasks(equiv_tasks, table)
    test_foils = [t for t in foils if t.get("partition") == "test"]
    train_foils = [t for t in foils if t.get("partition") == "train"]
    foils = (test_foils + train_foils)[: max(4, min(8, len(foils)))]
    print(
        f"families train={len(train_ids)} test={len(test_ids)}; equiv {len(equiv_tasks)}; foils {len(foils)}",
        flush=True,
    )
    if not equiv_tasks:
        raise RuntimeError("no constructed equivalence tasks")
    if not any(t.get("partition") == "test" for t in equiv_tasks) and test_ids:
        print("warning: no test-family equivalence tasks were constructed", flush=True)

    selector = TransformSelector()
    for task in equiv_tasks:
        if task.get("partition") == "train":
            observe_train_case(task, table, selector)
    selected = selector.freeze()
    print(f"learned transforms {list(selected)} from {selector.as_dict()}", flush=True)

    primitive_store = {(r["seed"], r["task_id"]): r for r in rows if r["split"] == "store"}
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"recurring exact seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            exact = solve_exact(config, task, seed, "expt11-recurring", index, table, learn=False, allow_initial_lookup=True)
            store_ref = primitive_store[(seed, task["task_id"])]
            rows.append(
                _row(
                    seed,
                    task,
                    "recurring",
                    "exact",
                    exact,
                    {
                        "A": store_ref["primitive_evals"],
                        "Q": store_ref["Q"],
                        "remaining_primitive_evals": store_ref["primitive_evals"],
                    },
                )
            )

        train_eq = [t for t in equiv_tasks if t.get("partition") == "train"]
        test_eq = [t for t in equiv_tasks if t.get("partition") == "test"]
        for index, task in enumerate(train_eq):
            print(f"equiv-train {task['transform']} seed={seed} {index + 1}/{len(train_eq)} {task['task_id']}", flush=True)
            _run_quad(config, task, seed, index, "equiv_train", "expt11-equiv-train", table, selected, rows)
        for index, task in enumerate(test_eq):
            print(f"equiv-test {task['transform']} seed={seed} {index + 1}/{len(test_eq)} {task['task_id']}", flush=True)
            _run_quad(config, task, seed, index, "equiv_test", "expt11-equiv-test", table, selected, rows)
        for index, task in enumerate(foils):
            print(f"foil {task['kind']} seed={seed} {index + 1}/{len(foils)} {task['task_id']}", flush=True)
            _run_quad(config, task, seed, index, "foil", "expt11-foil", table, selected, rows)
        for index, task in enumerate(fresh_tasks):
            print(f"fresh seed={seed} {index + 1}/{len(fresh_tasks)} {task['task_id']}", flush=True)
            _run_quad(
                config, task, seed, index, "fresh", "expt11-fresh", table, selected, rows,
                allow_initial=True, track_nat=True,
            )

    summaries = []
    for split in ("store", "recurring", "equiv_train", "equiv_test", "foil", "fresh"):
        for cond in ("primitive", "exact", "supplied", "learned"):
            summaries.append(_summarise(rows, split, cond))
    summaries = [s for s in summaries if s.get("n")]

    test_learned = next((s for s in summaries if s["split"] == "equiv_test" and s["condition"] == "learned"), {})
    test_supplied = next((s for s in summaries if s["split"] == "equiv_test" and s["condition"] == "supplied"), {})
    test_exact = next((s for s in summaries if s["split"] == "equiv_test" and s["condition"] == "exact"), {})
    fresh_prim = next((s for s in summaries if s["split"] == "fresh" and s["condition"] == "primitive"), {})
    foil_supplied = next((s for s in summaries if s["split"] == "foil" and s["condition"] == "supplied"), {})

    learned_useful = (
        (test_learned.get("mean_effort_saving") or 0) > 0
        and test_learned.get("quality_loss_rate") is not None
        and test_learned.get("quality_loss_rate") <= 0.2
        and (test_learned.get("n_equiv_hits") or 0) > 0
        and (test_learned.get("n_initial_state_hits") or 0) == 0
    )
    exact_evades = (test_exact.get("n_equiv_hits") or 0) == 0 and (test_exact.get("n_exact_hits") or 0) == 0
    return {
        "store_ids": [t["task_id"] for t in store_tasks],
        "fresh_ids": [t["task_id"] for t in fresh_tasks],
        "train_families": sorted(train_ids),
        "test_families": sorted(test_ids),
        "n_equiv_train": sum(1 for t in equiv_tasks if t.get("partition") == "train"),
        "n_equiv_test": sum(1 for t in equiv_tasks if t.get("partition") == "test"),
        "equiv_meta": [
            {
                "task_id": t["task_id"],
                "donor_task_id": t["donor_task_id"],
                "partition": t["partition"],
                "transform": t["transform"],
                "cut": t["cut"],
                "kind": t["kind"],
            }
            for t in equiv_tasks
        ],
        "foil_ids": [t["task_id"] for t in foils],
        "rows": rows,
        "summaries": summaries,
        "n_keys": len(table.entries),
        "n_initial_keys": table.n_initial_keys(),
        "n_overwrites": table.n_overwrites,
        "storage_bytes": table.bytes(),
        "table_frozen": True,
        "selector": selector.as_dict(),
        "exact_evades_transformed_test": exact_evades,
        "supplied_saves_on_test": (test_supplied.get("mean_effort_saving") or 0) > 0,
        "learned_useful_on_unseen_families": learned_useful,
        "foil_supplied_equiv_hits": foil_supplied.get("n_equiv_hits"),
        "natural_opportunity_rate_fresh": fresh_prim.get("natural_opportunity_rate"),
        "note": (
            "Engineered (supplied) and learned selection are reported separately. "
            "Learning chooses among declared D4 candidates; it does not invent transforms. "
            "Constructed equivalence is labeled. Natural opportunity on fresh traces is separate. "
            "Paired quality-loss versus the same-start primitive is reported, including first-write cases."
        ),
    }
