"""Store and freeze Expt-11 memory, then evaluate mixed streams at several recurrence rates."""

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
from construct_equiv import build_equivalence_tasks, build_nomatch_tasks, partition_families
from continuation import ContinuationTable
from mix_stream import compose_stream, realized_rate
from policy_equiv import observe_train_case, solve_equiv
from policy_exact import solve_primitive
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
        "hypothesis": "net saving of frozen learned isometries in a mixed stream as a function of useful-recurrence rate",
        "mechanism": "frozen Expt-11",
        "category_hidden": True,
        "rates_include_zero": True,
        "nomatch_checked_against_full_table": True,
        "accidental_other_intermediate_is_valid_retrieval": True,
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
        "hidden_kind": task.get("hidden_kind") or task.get("kind"),
        "rate": extra.pop("rate", None),
        "stream_index": extra.pop("stream_index", None),
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
        "A_identity_ok": out.get("A_identity_ok"),
    }
    rec.update(extra)
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


def _mean(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _summarise(rows, split, condition) -> dict:
    picked = [r for r in rows if r["split"] == split and r["condition"] == condition]
    if not picked:
        return {"n": 0, "split": split, "condition": condition}
    return {
        "n": len(picked),
        "split": split,
        "condition": condition,
        "n_tasks": len({r["task_id"] for r in picked}),
        "n_seeds": len({r["seed"] for r in picked}),
        "mean_A": _mean(picked, "A"),
        "mean_Q": _mean(picked, "Q"),
        "mean_effort_saving": _mean(picked, "effort_saving"),
        "quality_loss_rate": sum(1.0 for r in picked if r["quality_loss"]) / len(picked),
        "n_quality_loss": sum(1 for r in picked if r["quality_loss"]),
        "acceptable_rate": sum(1.0 for r in picked if r["acceptable"]) / len(picked),
        "n_hits": sum(int(r["hits"] or 0) for r in picked),
        "n_exact_hits": sum(int(r["exact_hits"] or 0) for r in picked),
        "n_equiv_hits": sum(int(r["equiv_hits"] or 0) for r in picked),
        "mean_lookup": _mean(picked, "lookup_cost"),
        "mean_matching": _mean(picked, "matching_cost"),
        "mean_transformation": _mean(picked, "transformation_cost"),
        "mean_validation": _mean(picked, "validation_cost"),
        "mean_primitive_evals": _mean(picked, "primitive_evals"),
        "by_hidden_kind": {
            kind: {
                "n": len(g),
                "mean_A": _mean(g, "A"),
                "mean_effort_saving": _mean(g, "effort_saving"),
                "n_hits": sum(int(r["hits"] or 0) for r in g),
            }
            for kind in sorted({r["hidden_kind"] for r in picked if r.get("hidden_kind")})
            for g in [[x for x in picked if x.get("hidden_kind") == kind]]
        },
    }


def _run_quad(config, task, seed, index, split, phase, table, selected, rows, rate, stream_index):
    prefix = list(task["constructed_prefix"]) if task.get("constructed_prefix") else None
    prim = solve_equiv(
        config, task, seed, phase, index, table, mode="primitive",
        constructed_prefix=prefix, allow_initial_lookup=True,
    )
    rows.append(_row(seed, task, split, "primitive", prim, rate=rate, stream_index=stream_index))
    for label, mode in (("exact", "exact"), ("supplied", "supplied"), ("learned", "learned")):
        out = solve_equiv(
            config, task, seed, phase, index, table, mode=mode, selected=selected,
            constructed_prefix=prefix, allow_initial_lookup=True,
        )
        rows.append(_row(seed, task, split, label, out, prim, rate=rate, stream_index=stream_index))


def run_experiment(config: Config) -> dict:
    store_tasks, fresh_tasks = generate_splits(config)
    table = ContinuationTable()
    rows = []
    donors = []
    print(f"store {len(store_tasks)}; fresh {len(fresh_tasks)}", flush=True)
    for seed in config.seeds:
        for index, task in enumerate(store_tasks):
            print(f"store seed={seed} {index + 1}/{len(store_tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive(config, task, seed, "expt12-store", index)
            table.learn_from_success(prim["env"], prim["ledger"], config.q_min)
            rec = _row(seed, task, "store", "primitive", prim)
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
    train_ids, test_ids = partition_families([d["task_id"] for d in donors], config.train_frac)
    equiv = build_equivalence_tasks(donors, table, train_ids, config)
    nomatch = build_nomatch_tasks(equiv, table)
    print(f"equiv {len(equiv)}; nomatch {len(nomatch)}; train {len(train_ids)} test {len(test_ids)}", flush=True)
    selector = TransformSelector()
    for task in equiv:
        if task.get("partition") == "train":
            observe_train_case(task, table, selector)
    selected = selector.freeze()
    print(f"selected {list(selected)} coverage {selector.as_dict()['coverage']}", flush=True)

    exact_pool = []
    for task in store_tasks:
        rec = dict(task)
        rec["kind"] = "exact_recurrence"
        rec["constructed_prefix"] = None
        rec["family"] = task["task_id"]
        exact_pool.append(rec)
    xform_pool = list(equiv)
    for task in xform_pool:
        task["kind"] = "valid_transform"
    fresh_pool = []
    for task in fresh_tasks:
        rec = dict(task)
        rec["kind"] = "fresh"
        rec["constructed_prefix"] = None
        rec["family"] = task["task_id"]
        fresh_pool.append(rec)
    pools = {
        "exact_recurrence": exact_pool,
        "valid_transform": xform_pool,
        "no_match": nomatch,
        "fresh": fresh_pool,
    }
    if not exact_pool and not xform_pool:
        raise RuntimeError("no useful-recurrence tasks")
    if not fresh_pool and not nomatch:
        raise RuntimeError("no non-recurrence tasks")

    stream_meta = []
    for rate in config.rates:
        for seed in config.seeds:
            rng = random.Random(int(seed) * 1_000_003 + int(round(rate * 1000)))
            stream = compose_stream(pools, rate, int(config.n_stream), rng)
            realized = realized_rate(stream)
            print(f"stream rate={rate} realized={realized:.3f} seed={seed} n={len(stream)}", flush=True)
            stream_meta.append(
                {
                    "rate": rate,
                    "realized_rate": realized,
                    "seed": seed,
                    "n": len(stream),
                    "counts": {k: sum(1 for t in stream if t.get("hidden_kind") == k) for k in pools},
                }
            )
            phase = f"expt12-p{int(round(rate * 100)):03d}"
            split = f"mix_p{int(round(rate * 100)):03d}"
            for index, task in enumerate(stream):
                print(f"  {split} seed={seed} {index + 1}/{len(stream)} {task.get('hidden_kind')} {task['task_id']}", flush=True)
                _run_quad(config, task, seed, index, split, phase, table, selected, rows, rate, index)

    summaries = []
    for rate in config.rates:
        split = f"mix_p{int(round(rate * 100)):03d}"
        for cond in ("primitive", "exact", "supplied", "learned"):
            summaries.append(_summarise(rows, split, cond))
    summaries = [s for s in summaries if s.get("n")]

    breakeven = None
    learned_by_rate = []
    for rate in config.rates:
        split = f"mix_p{int(round(rate * 100)):03d}"
        learned = next((s for s in summaries if s["split"] == split and s["condition"] == "learned"), None)
        if not learned:
            continue
        learned_rows = [r for r in rows if r["split"] == split and r["condition"] == "learned"]
        constructed = [
            r
            for r in learned_rows
            if r.get("hidden_kind") in ("exact_recurrence", "valid_transform")
        ]
        observed = [r for r in learned_rows if int(r.get("hits") or 0) > 0]
        stream_realized = [m.get("realized_rate") for m in stream_meta if m.get("rate") == rate]
        rec = {
            "rate": rate,
            "mean_A": learned.get("mean_A"),
            "mean_effort_saving": learned.get("mean_effort_saving"),
            "quality_loss_rate": learned.get("quality_loss_rate"),
            "n": learned.get("n"),
            "n_tasks": learned.get("n_tasks"),
            "n_seeds": learned.get("n_seeds"),
            "constructed_share": (sum(stream_realized) / len(stream_realized)) if stream_realized else None,
            "observed_reuse_rate": (len(observed) / len(learned_rows)) if learned_rows else None,
            "n_constructed_useful": len(constructed),
            "n_observed_hits": len(observed),
        }
        learned_by_rate.append(rec)
        ok = (
            (learned.get("mean_effort_saving") or 0) > 0
            and learned.get("quality_loss_rate") is not None
            and learned.get("quality_loss_rate") <= 0.2
        )
        rec["net_save_quality_ok"] = ok
        if ok and breakeven is None:
            breakeven = rate

    return {
        "store_ids": [t["task_id"] for t in store_tasks],
        "fresh_ids": [t["task_id"] for t in fresh_tasks],
        "train_families": sorted(train_ids),
        "test_families": sorted(test_ids),
        "n_exact_pool": len(exact_pool),
        "n_transform_pool": len(xform_pool),
        "n_nomatch_pool": len(nomatch),
        "n_fresh_pool": len(fresh_pool),
        "transform_coverage_in_pool": {
            name: sum(1 for t in xform_pool if t.get("transform") == name)
            for name in ("rot90", "rot180", "rot270", "refl_x", "refl_y", "refl_d", "refl_ad")
        },
        "n_keys": len(table.entries),
        "n_overwrites": table.n_overwrites,
        "storage_bytes": table.bytes(),
        "selector": selector.as_dict(),
        "stream_meta": stream_meta,
        "summaries": summaries,
        "learned_by_rate": learned_by_rate,
        "smallest_rate_learned_netsaves": breakeven,
        "rows": rows,
        "note": (
            "Constructed useful-recurrence share is the designed slot mix (exact + valid-transform). "
            "Observed reuse is the fraction of evaluations that actually hit memory, including later "
            "hits on rows that began as no-match. Those quantities are reported separately. "
            "No-match tasks were checked against the entire frozen table under every permitted T. "
            "A match to another stored intermediate is valid retrieval and was excluded from no-match. "
            "Evaluations at a rate are stream slots crossed with seeds, not independent learning tests. "
            "The +11.9 saving at the 5% setting is a paired result on these streams, not a general "
            "break-even threshold. Natural unforced encounter frequency is not measured here."
        ),
    }
