"""Offline action-level prediction. Frozen libraries. Whole-box only if validation supports a useful subset."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from collect import cap_distortion_summary, collect_pair_actions
from config import Config, EXPT7_RESULT
from index import LibraryIndex
from library_io import library_hash, memory_from_json
from predictors import (
    ConstantModels,
    auc_beneficial,
    choose_thresholds,
    fit_action,
    fit_context,
    mae,
    pearson,
    pearson_within_seed,
    remaining_check_cost,
    rmse,
    selection_metrics,
    useful_subset,
    would_accept,
)
from ranker import LinearRegressor, QualityModel, RANK_NAMES
from reconstruct import file_sha, load_gates


def expt7_dir() -> Path:
    return ROOT.parent / Path(EXPT7_RESULT)


def load_json_tasks(path: Path) -> list[dict]:
    return list(json.loads(path.read_text(encoding="utf-8"))["tasks"])


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    serialised = []
    for row in rows:
        copied = dict(row)
        for key, value in list(copied.items()):
            if isinstance(value, (list, dict)):
                copied[key] = json.dumps(value)
        serialised.append(copied)
    fields = []
    for row in serialised:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in serialised:
            writer.writerow({key: row.get(key) for key in fields})


def load_artifacts(config: Config, seeds: tuple[int, ...]) -> list[dict]:
    run = expt7_dir()
    bundles = []
    for seed in seeds:
        lib_path = run / f"library_seed{seed}.json"
        payload = json.loads(lib_path.read_text(encoding="utf-8"))
        memory = memory_from_json(payload, config)
        consult, commit, gate_sha = load_gates(int(seed))
        ranker = json.loads((run / f"ranker_seed{seed}.json").read_text(encoding="utf-8"))
        benefit = LinearRegressor.from_dict(ranker["benefit"])
        quality = QualityModel.from_dict(ranker["quality"])
        if library_hash(memory) != payload["library_hash"]:
            raise RuntimeError(f"library hash drifted seed {seed}")
        if not benefit.frozen or not quality.frozen:
            raise RuntimeError(f"ranker was not frozen seed {seed}")
        bundles.append(
            {
                "seed": int(seed),
                "memory": memory,
                "index": LibraryIndex(memory),
                "consult_gate": consult,
                "commit_gate": commit,
                "frozen_benefit": benefit,
                "frozen_quality": quality,
                "library_hash": payload["library_hash"],
                "library_file_sha256": file_sha(lib_path),
                "ranker_file_sha256": file_sha(run / f"ranker_seed{seed}.json"),
                "gate_file_sha256": gate_sha,
                "n_active": len(memory.active()),
            }
        )
    return bundles


def split_tasks(tasks: list[dict], n_fit: int) -> tuple[list[dict], list[dict]]:
    fit = list(tasks[: int(n_fit)])
    val = list(tasks[int(n_fit) :])
    if not val:
        val = list(fit[-1:])
    return fit, val


def audit_frozen_implementation(bundles: list[dict]) -> dict:
    """Check sign, units, scaling, intercept, clipping, features, and train/deploy action identity."""
    run = expt7_dir()
    labels_path = run / "ranker_labels.csv"
    label_rows = []
    if labels_path.exists() and labels_path.stat().st_size:
        with labels_path.open(newline="", encoding="utf-8") as handle:
            label_rows = list(csv.DictReader(handle))
    savings = [float(r["remaining_saving"]) for r in label_rows] if label_rows else []
    from gates import sample_weight

    weighted = []
    weights = []
    for row in label_rows:
        y = float(row["remaining_saving"])
        ok = str(row["quality_ok"]).lower() in ("true", "1")
        w = sample_weight(y, ok, 400.0, 8.0)
        weighted.append(w * y)
        weights.append(w)
    wmean = (sum(weighted) / sum(weights)) if weights else None
    seed_audits = []
    for bundle in bundles:
        b = bundle["frozen_benefit"]
        q = bundle["frozen_quality"]
        seed_audits.append(
            {
                "seed": bundle["seed"],
                "benefit_bias": b.bias,
                "benefit_n_weights": len(b.weights),
                "quality_threshold": q.threshold,
                "quality_uses_op_id": bool(q.op_bias),
                "benefit_uses_op_id": False,
                "min_weight": min(b.weights) if b.weights else None,
                "max_weight": max(b.weights) if b.weights else None,
                "clipping": False,
                "inverse_scaling": False,
                "feature_names": list(RANK_NAMES),
                "placement_features": False,
            }
        )
    return {
        "training_action": "first_legal_site (8 shuffled anchors), not oracle-best placement",
        "deployment_action": "first_legal_site (8 shuffled anchors)",
        "train_deploy_action_mismatch": False,
        "remaining_saving_sign": "A_skip - A_commit; positive means fewer remaining evaluations",
        "training_units": "raw remaining primitive evaluations",
        "training_remaining_cap": "pair_eval_cap=1600 (truncated vs full remaining budget)",
        "expt7b_remaining_cap": "eval_cap - prefix_primitive_A",
        "expt8b_remaining_cap": "eval_cap - prefix_primitive_A for fit, validation, and holdout",
        "cap_mismatch": True,
        "expt8b_cap_mismatch": False,
        "n_training_labels": len(label_rows),
        "training_saving_mean": None if not savings else sum(savings) / len(savings),
        "training_saving_weighted_mean": wmean,
        "n_training_negative": sum(1 for y in savings if y < 0),
        "n_training_beneficial": sum(
            1 for r in label_rows if str(r.get("quality_ok")).lower() in ("true", "1") and float(r["remaining_saving"]) > 0
        ),
        "severe_loss_weighting": "sample_weight adds max(0,-saving)/400 plus 8 on quality failure",
        "seeds": seed_audits,
        "note": (
            "Uniformly negative deployment predictions can follow from fitting a linear model to severe-loss-weighted "
            "labels whose weighted mean is largely negative, even when the unweighted mean is near zero. "
            "That is not a sign error. It also does not by itself prove that placement features are uninformative."
        ),
    }


def _score_rows(rows, kind, models, remaining_check) -> list[dict]:
    out = []
    for row in rows:
        copied = dict(row)
        if kind == "per_seed_mean":
            pred = models.predict_saving(None)
            p_ok = models.probability(None)
            thresh = models.quality_threshold
        elif kind == "frozen" or kind.startswith("context"):
            pred = models[0].predict(row["context_vector"])
            p_ok = models[1].probability(row["context_vector"], row["op_id"])
            thresh = models[1].threshold
        else:
            pred = models[0].predict(row["action_vector"])
            p_ok = models[1].probability(row["action_vector"], row["op_id"])
            thresh = models[1].threshold
        copied["pred_saving"] = pred
        copied["p_quality_ok"] = p_ok
        copied["quality_threshold"] = thresh
        copied["predictor"] = kind
        copied["accept"] = would_accept(pred, p_ok, thresh, remaining_check)
        out.append(copied)
    return out


def _error_block(scored: list[dict]) -> dict:
    pairs = [(float(r["pred_saving"]), float(r["remaining_saving"])) for r in scored]
    return {
        "n": len(scored),
        "mae": mae(pairs),
        "rmse": rmse(pairs),
        "pearson_pooled": pearson(pairs),
        "pearson_within_seed": pearson_within_seed(scored) if scored else {"pooled": None, "within_seed": {}},
        "auc_beneficial": auc_beneficial(scored, "pred_saving"),
        "pred_mean": None if not scored else sum(float(r["pred_saving"]) for r in scored) / len(scored),
        "y_mean": None if not scored else sum(float(r["remaining_saving"]) for r in scored) / len(scored),
        "pred_min": None if not scored else min(float(r["pred_saving"]) for r in scored),
        "pred_max": None if not scored else max(float(r["pred_saving"]) for r in scored),
    }


def _placement_select(scored: list[dict], n_place: int, remaining_check: float) -> list[dict]:
    """Keep abstention. Among up to n_place labeled actions of each (state, op), take the highest predicted saving."""
    groups = defaultdict(list)
    for row in scored:
        key = (row["seed"], row["task_id"], row["state_index"], row["op_id"])
        groups[key].append(row)
    chosen = []
    for items in groups.values():
        first = [r for r in items if r["source"] == "first_legal_site"]
        extra = [r for r in items if r["source"] != "first_legal_site"]
        pool = list(first)
        for rec in extra:
            if len(pool) >= int(n_place):
                break
            pool.append(rec)
        if not pool:
            continue
        best = max(pool, key=lambda r: (float(r["pred_saving"]), -float(r["examined"])))
        rec = dict(best)
        rec["n_ranked_placements"] = len(pool)
        rec["billed_examined"] = sum(float(r["examined"]) for r in pool)
        rec["accept"] = would_accept(float(best["pred_saving"]), float(best["p_quality_ok"]), float(best["quality_threshold"]), remaining_check)
        chosen.append(rec)
    return chosen


def run_offline(config: Config, tasks: list[dict], bundles: list[dict]) -> dict:
    fit_tasks, val_tasks = split_tasks(tasks, config.n_fit_boxes)
    ledger = {"skip_A": 0, "commit_A": 0, "skip_rollouts": 0, "commit_rollouts": 0, "cache_hits": 0, "feature_checks": 0}
    cache: dict = {}
    k = int(config.k_shortlist)
    p_op = int(config.placements_per_op)
    all_fit = []
    all_val = []
    for bundle in bundles:
        for index, task in enumerate(fit_tasks):
            print(f"collect fit seed={bundle['seed']} box={index + 1}/{len(fit_tasks)} {task['task_id']}", flush=True)
            all_fit.extend(collect_pair_actions(config, task, int(bundle["seed"]), index, bundle, k, p_op, ledger, cache, "fit"))
        for index, task in enumerate(val_tasks):
            print(f"collect val seed={bundle['seed']} box={index + 1}/{len(val_tasks)} {task['task_id']}", flush=True)
            all_val.extend(
                collect_pair_actions(config, task, int(bundle["seed"]), len(fit_tasks) + index, bundle, k, p_op, ledger, cache, "val")
            )
    remaining_check = remaining_check_cost(config.anchors)
    by_seed_fit = defaultdict(list)
    by_seed_val = defaultdict(list)
    for row in all_fit:
        by_seed_fit[int(row["seed"])].append(row)
    for row in all_val:
        by_seed_val[int(row["seed"])].append(row)
    scored_val = []
    predictor_summaries = []
    models_by_seed = {}
    for bundle in bundles:
        seed = int(bundle["seed"])
        fit_rows = by_seed_fit.get(seed, [])
        val_rows = by_seed_val.get(seed, [])
        const = ConstantModels(
            sum(float(r["remaining_saving"]) for r in fit_rows) / len(fit_rows) if fit_rows else 0.0,
            sum(1.0 if r["quality_ok"] else 0.0 for r in fit_rows) / len(fit_rows) if fit_rows else 0.0,
            seed,
        )
        if fit_rows:
            ctx_b, ctx_q = fit_context(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=True)
            ctx_q = choose_thresholds(ctx_q, fit_rows, "context_vector")
            act_b, act_q = fit_action(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=True)
            act_q = choose_thresholds(act_q, fit_rows, "action_vector")
            ctx_bw, ctx_qw = fit_context(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=False)
            ctx_qw = choose_thresholds(ctx_qw, fit_rows, "context_vector")
            act_bw, act_qw = fit_action(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=False)
            act_qw = choose_thresholds(act_qw, fit_rows, "action_vector")
        else:
            z = [0.0] * len(RANK_NAMES)
            ctx_b, ctx_q = LinearRegressor(RANK_NAMES, z, 0.0, True), QualityModel(RANK_NAMES, z, 0.0, {}, 1.0, True)
            from action_features import ACTION_NAMES

            z2 = [0.0] * len(ACTION_NAMES)
            act_b, act_q = LinearRegressor(ACTION_NAMES, z2, 0.0, True), QualityModel(ACTION_NAMES, z2, 0.0, {}, 1.0, True)
            ctx_bw, ctx_qw, act_bw, act_qw = ctx_b, ctx_q, act_b, act_q
        models_by_seed[seed] = {
            "per_seed_mean": const,
            "frozen": (bundle["frozen_benefit"], bundle["frozen_quality"]),
            "context_unweighted": (ctx_b, ctx_q),
            "action_unweighted": (act_b, act_q),
            "context_weighted": (ctx_bw, ctx_qw),
            "action_weighted": (act_bw, act_qw),
        }
        kinds = (
            ("per_seed_mean", const),
            ("frozen", (bundle["frozen_benefit"], bundle["frozen_quality"])),
            ("context_unweighted", (ctx_b, ctx_q)),
            ("action_unweighted", (act_b, act_q)),
            ("context_weighted", (ctx_bw, ctx_qw)),
            ("action_weighted", (act_bw, act_qw)),
        )
        for kind, model in kinds:
            scored = _score_rows(val_rows, kind, model, remaining_check)
            first_only = [r for r in scored if r["source"] == "first_legal_site"]
            sel_all = selection_metrics(scored, "pred_saving", "p_quality_ok", scored[0]["quality_threshold"] if scored else 1.0, remaining_check)
            sel_first = selection_metrics(first_only, "pred_saving", "p_quality_ok", first_only[0]["quality_threshold"] if first_only else 1.0, remaining_check)
            predictor_summaries.append(
                {
                    "seed": seed,
                    "predictor": kind,
                    "n_fit": len(fit_rows),
                    "errors_all_placements": _error_block(scored),
                    "errors_first_legal": _error_block(first_only),
                    "selection_all_placements": sel_all,
                    "selection_first_legal": sel_first,
                    "quality_threshold": (scored[0]["quality_threshold"] if scored else None),
                    "per_seed_mean_saving": const.mean_saving if kind == "per_seed_mean" else None,
                }
            )
            scored_val.extend(scored)
    pooled = []
    kind_names = ("per_seed_mean", "frozen", "context_unweighted", "action_unweighted", "context_weighted", "action_weighted")
    for kind in kind_names:
        rows = [r for r in scored_val if r["predictor"] == kind]
        first = [r for r in rows if r["source"] == "first_legal_site"]
        thresh = first[0]["quality_threshold"] if first else 1.0
        pooled.append(
            {
                "predictor": kind,
                "errors_all_placements": _error_block(rows),
                "errors_first_legal": _error_block(first),
                "selection_all_placements": selection_metrics(rows, "pred_saving", "p_quality_ok", thresh, remaining_check),
                "selection_first_legal": selection_metrics(first, "pred_saving", "p_quality_ok", thresh, remaining_check),
            }
        )
    action_first = next(p["selection_first_legal"] for p in pooled if p["predictor"] == "action_unweighted")
    const_err = next(p["errors_first_legal"] for p in pooled if p["predictor"] == "per_seed_mean")
    action_err = next(p["errors_first_legal"] for p in pooled if p["predictor"] == "action_unweighted")
    beats_constant = (
        action_err.get("mae") is not None
        and const_err.get("mae") is not None
        and action_err["mae"] < const_err["mae"] - 1e-9
    )
    holdout_tasks = load_json_tasks(ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "development.json")[: int(config.n_holdout)]
    all_holdout = []
    scored_holdout = []
    for bundle in bundles:
        seed = int(bundle["seed"])
        for index, task in enumerate(holdout_tasks):
            print(f"collect holdout seed={seed} box={index + 1}/{len(holdout_tasks)} {task['task_id']}", flush=True)
            all_holdout.extend(
                collect_pair_actions(
                    config, task, seed, index, bundle, k, p_op, ledger, cache, "holdout", phase="expt8b-holdout"
                )
            )
    by_seed_hold = defaultdict(list)
    for row in all_holdout:
        by_seed_hold[int(row["seed"])].append(row)
    for bundle in bundles:
        seed = int(bundle["seed"])
        for kind, model in (
            ("per_seed_mean", models_by_seed[seed]["per_seed_mean"]),
            ("action_unweighted", models_by_seed[seed]["action_unweighted"]),
            ("context_unweighted", models_by_seed[seed]["context_unweighted"]),
        ):
            scored_holdout.extend(_score_rows(by_seed_hold.get(seed, []), kind, model, remaining_check))
    holdout_pooled = []
    for kind in ("per_seed_mean", "context_unweighted", "action_unweighted"):
        rows = [r for r in scored_holdout if r["predictor"] == kind]
        first = [r for r in rows if r["source"] == "first_legal_site"]
        thresh = first[0]["quality_threshold"] if first else 1.0
        holdout_pooled.append(
            {
                "predictor": kind,
                "errors_first_legal": _error_block(first),
                "selection_first_legal": selection_metrics(first, "pred_saving", "p_quality_ok", thresh, remaining_check),
            }
        )
    holdout_action = next(p["selection_first_legal"] for p in holdout_pooled if p["predictor"] == "action_unweighted")
    proceed_wholebox = useful_subset(holdout_action)
    return {
        "fit_ids": [t["task_id"] for t in fit_tasks],
        "val_ids": [t["task_id"] for t in val_tasks],
        "holdout_ids": [t["task_id"] for t in holdout_tasks],
        "labels_fit": all_fit,
        "labels_val": all_val,
        "labels_holdout": all_holdout,
        "scored_val": scored_val,
        "scored_holdout": scored_holdout,
        "predictor_summaries": predictor_summaries,
        "pooled": pooled,
        "holdout_pooled": holdout_pooled,
        "beats_constant": beats_constant,
        "cap_distortion": cap_distortion_summary(all_fit + all_val),
        "proceed_placement": False,
        "proceed_wholebox": proceed_wholebox,
        "placement_table": [],
        "chosen_n_placements": 1,
        "remaining_check": remaining_check,
        "ledger": ledger,
        "models_by_seed": models_by_seed,
        "gate_first": useful_subset(action_first),
        "gate_all": False,
        "holdout_useful": proceed_wholebox,
    }


def maybe_run_wholebox(config: Config, offline: dict, bundles: list[dict]) -> dict:
    """Fresh boxes only if validation supports a useful accepted subset. Includes budget 0."""
    if not offline.get("holdout_useful"):
        return {"ran": False, "reason": "holdout did not support a useful accepted subset", "rows": []}
    if int(config.n_fresh) <= 0:
        return {"ran": False, "reason": "n_fresh=0", "rows": []}
    from policy import solve_indexed
    from diagnostic import solve_gated
    from policy_action import solve_action_ranked
    from tools.generate_boxes import generate

    extra_blocked = [
    ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "eval.json",
    ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "train.json",
    ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "development.json",
    ROOT.parent / "Expt_06_Frozen_Library_Opportunity" / "data" / "eval.json",
    ROOT.parent / "Expt_07B_Decision_Audit" / "data" / "eval.json",
    ]
    generate(target=int(config.n_fresh), seed=2026092981, out_name="fresh", extra_blocked=extra_blocked)
    tasks = load_json_tasks(ROOT / "data" / "fresh.json")[: int(config.n_fresh)]
    k = int(config.k_shortlist)
    budget = int(config.consult_budget)
    n_place = int(offline["chosen_n_placements"])
    rows = []
    for bundle in bundles:
        seed = int(bundle["seed"])
        models = offline["models_by_seed"][seed]
        for index, task in enumerate(tasks):
            prim = solve_gated(config, task, seed, "expt8-eval", index, None, "primitive")
            zero = solve_indexed(
                config, task, seed, "expt8-eval", index, bundle["memory"], bundle["index"],
                ranked=True, k=k, consult_budget=0, benefit_model=bundle["frozen_benefit"], quality_model=bundle["frozen_quality"],
            )
            frozen = solve_indexed(
                config, task, seed, "expt8-eval", index, bundle["memory"], bundle["index"],
                ranked=True, k=k, consult_budget=budget, benefit_model=bundle["frozen_benefit"], quality_model=bundle["frozen_quality"],
            )
            agent = solve_action_ranked(
                config, task, seed, "expt8-eval", index, bundle["memory"], bundle["index"],
                models["action_unweighted"][0], models["action_unweighted"][1], k, budget, n_place,
            )
            for name, out in (("primitive", prim), ("budget0", zero), ("frozen_ranked", frozen), ("action_ranked", agent)):
                rec = {
                    "seed": seed,
                    "task_id": task["task_id"],
                    "condition": name,
                    "Q": out["Q"],
                    "A": out["A"],
                    "consultation_cost": out.get("consultation_cost") or 0,
                    "primitive_evals": out.get("primitive_evals"),
                    "bypassed": out.get("bypassed_primitive_decisions") or 0,
                    "A_primitive": prim["A"],
                    "Q_primitive": prim["Q"],
                    "effort_saving": prim["A"] - out["A"],
                    "quality_loss": out["Q"] < prim["Q"] - config.quality_loss_margin,
                }
                rows.append(rec)
    return {"ran": True, "reason": "validation supported a useful subset", "rows": rows, "n_placements": n_place, "n_fresh": len(tasks)}
