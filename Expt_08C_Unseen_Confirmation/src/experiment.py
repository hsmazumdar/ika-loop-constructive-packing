"""Freeze 8B models. Score them once on unseen boxes. No threshold retune. No new mechanism."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from collect import collect_pair_actions
from config import Config, EXPT7_RESULT
from index import LibraryIndex
from library_io import library_hash, memory_from_json
from predictors import (
    auc_beneficial,
    mae,
    pearson,
    pearson_within_seed,
    remaining_check_cost,
    rmse,
    selection_metrics,
    useful_subset,
    would_accept,
)
from provenance import build_audit
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
        from ranker import LinearRegressor, QualityModel

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


def audit_frozen_implementation(bundles: list[dict]) -> dict:
    audit = build_audit()
    audit["n_libraries"] = len(bundles)
    audit["train_deploy_action_mismatch"] = False
    audit["expt8b_cap_mismatch"] = False
    audit["cap_mismatch"] = True
    audit["training_action"] = "first_legal_site (8 shuffled anchors), not oracle-best placement"
    return audit


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
        copied["historical_comparator"] = kind in ("frozen", "context_weighted", "action_weighted")
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


def _state_overhead(rows: list[dict]) -> float:
    seen = set()
    total = 0.0
    for row in rows:
        key = (int(row["seed"]), str(row["task_id"]), int(row["state_index"]))
        if key in seen:
            continue
        seen.add(key)
        total += float(row.get("state_decision_cost") or 0)
    return total


def _decision_block(first: list[dict], accepted: list[dict]) -> dict:
    site_net = [float(r["remaining_saving"]) - float(r.get("examined") or 0) for r in accepted] if accepted else []
    action_cost = [float(r.get("examined") or 0) + float(r.get("feature_checks") or 0) for r in accepted] if accepted else []
    consult_all = _state_overhead(first)
    consult_accepted_states = _state_overhead(accepted) if accepted else 0.0
    sum_saving = sum(float(r["remaining_saving"]) for r in accepted) if accepted else 0.0
    sum_action_cost = sum(action_cost)
    net_all_consult = sum_saving - sum_action_cost - consult_all
    by_box = defaultdict(lambda: {"n": 0, "remaining_saving": 0.0, "examined": 0.0, "feature_checks": 0.0, "seeds": set()})
    by_seed = defaultdict(lambda: {"n": 0, "remaining_saving": 0.0, "boxes": set()})
    for row in accepted:
        bid = str(row["task_id"])
        seed = int(row["seed"])
        by_box[bid]["n"] += 1
        by_box[bid]["remaining_saving"] += float(row["remaining_saving"])
        by_box[bid]["examined"] += float(row.get("examined") or 0)
        by_box[bid]["feature_checks"] += float(row.get("feature_checks") or 0)
        by_box[bid]["seeds"].add(seed)
        by_seed[seed]["n"] += 1
        by_seed[seed]["remaining_saving"] += float(row["remaining_saving"])
        by_seed[seed]["boxes"].add(bid)
    box_rows = []
    for bid, rec in sorted(by_box.items(), key=lambda kv: kv[1]["remaining_saving"], reverse=True):
        box_rows.append(
            {
                "task_id": bid,
                "n_accepted": rec["n"],
                "seeds": sorted(rec["seeds"]),
                "remaining_saving": rec["remaining_saving"],
                "share_of_accepted_saving": None if not accepted else rec["remaining_saving"] / sum_saving if sum_saving else None,
                "examined": rec["examined"],
                "feature_checks": rec["feature_checks"],
            }
        )
    largest = box_rows[0] if box_rows else None
    leave_one = None
    if largest and accepted:
        rest = [r for r in accepted if str(r["task_id"]) != largest["task_id"]]
        leave_one = sum(float(r["remaining_saving"]) for r in rest) if rest else 0.0
    return {
        "n_accepted": len(accepted),
        "n_accepted_seeds": len(by_seed),
        "sum_remaining_saving": sum_saving if accepted else None,
        "mean_net_after_site_checks": None if not site_net else sum(site_net) / len(site_net),
        "sum_action_decision_cost": sum_action_cost if accepted else None,
        "consult_cost_all_states": consult_all,
        "consult_cost_accepted_states": consult_accepted_states,
        "net_after_decision_costs": net_all_consult if accepted else None,
        "largest_box": largest,
        "saving_without_largest_box": leave_one,
        "by_box": box_rows,
        "by_seed": {str(s): {"n_accepted": v["n"], "n_boxes": len(v["boxes"]), "remaining_saving": v["remaining_saving"]} for s, v in by_seed.items()},
        "note": "net_after_decision_costs subtracts accepted site checks and feature checks plus index/ranking on every consulted state, including rejected consultations. It is still not whole-box policy savings.",
    }


def _convincing(decision: dict, sel: dict) -> bool:
    if not useful_subset(sel):
        return False
    if int(decision.get("n_accepted_seeds") or 0) < 2:
        return False
    net = decision.get("net_after_decision_costs")
    if net is None or net <= 0:
        return False
    rest = decision.get("saving_without_largest_box")
    if rest is None or rest <= 0:
        return False
    return True


def generate_unseen(config: Config) -> list[dict]:
    from tools.generate_boxes import generate, all_prior_task_files

    extra = all_prior_task_files()
    generate(
        target=int(config.n_boxes),
        timeout=900.0,
        seed=int(config.generate_seed),
        out_name="unseen",
        extra_blocked=extra,
    )
    tasks = load_json_tasks(ROOT / "data" / "unseen.json")
    if len(tasks) < int(config.n_boxes):
        raise RuntimeError(f"generated {len(tasks)} unseen boxes, need {config.n_boxes}")
    return tasks[: int(config.n_boxes)]


def run_unseen(config: Config, tasks: list[dict], bundles: list[dict], frozen: dict) -> dict:
    ledger = {"skip_A": 0, "commit_A": 0, "skip_rollouts": 0, "commit_rollouts": 0, "cache_hits": 0, "feature_checks": 0}
    cache: dict = {}
    k = int(config.k_shortlist)
    p_op = int(config.placements_per_op)
    remaining_check = remaining_check_cost(config.anchors)
    all_rows = []
    for bundle in bundles:
        seed = int(bundle["seed"])
        for index, task in enumerate(tasks):
            print(f"collect unseen seed={seed} box={index + 1}/{len(tasks)} {task['task_id']}", flush=True)
            all_rows.extend(
                collect_pair_actions(
                    config, task, seed, index, bundle, k, p_op, ledger, cache, "unseen", phase="expt8c-unseen"
                )
            )
    models_by_seed = frozen["models_by_seed"]
    scored = []
    kinds_order = (
        "per_seed_mean",
        "frozen",
        "context_unweighted",
        "action_unweighted",
        "context_weighted",
        "action_weighted",
    )
    historical = {"frozen", "context_weighted", "action_weighted"}
    for bundle in bundles:
        seed = int(bundle["seed"])
        seed_rows = [r for r in all_rows if int(r["seed"]) == seed]
        packed = models_by_seed[seed]
        kinds = (
            ("per_seed_mean", packed["per_seed_mean"]),
            ("frozen", packed["frozen"]),
            ("context_unweighted", packed["context_unweighted"]),
            ("action_unweighted", packed["action_unweighted"]),
            ("context_weighted", packed["context_weighted"]),
            ("action_weighted", packed["action_weighted"]),
        )
        for kind, model in kinds:
            scored.extend(_score_rows(seed_rows, kind, model, remaining_check))
    pooled = []
    for kind in kinds_order:
        rows = [r for r in scored if r["predictor"] == kind]
        first = [r for r in rows if r["source"] == "first_legal_site"]
        thresh = first[0]["quality_threshold"] if first else 1.0
        sel = selection_metrics(first, "pred_saving", "p_quality_ok", thresh, remaining_check)
        accepted = [r for r in first if r.get("accept")]
        decision = _decision_block(first, accepted)
        pooled.append(
            {
                "predictor": kind,
                "historical_comparator": kind in historical,
                "errors_first_legal": _error_block(first),
                "selection_first_legal": sel,
                "decision_costs": decision,
            }
        )
    action = next(p for p in pooled if p["predictor"] == "action_unweighted")
    baseline = next(p for p in pooled if p["predictor"] == "per_seed_mean")
    beats_mae = (
        action["errors_first_legal"].get("mae") is not None
        and baseline["errors_first_legal"].get("mae") is not None
        and action["errors_first_legal"]["mae"] < baseline["errors_first_legal"]["mae"] - 1e-9
    )
    convincing = _convincing(action["decision_costs"], action["selection_first_legal"])
    return {
        "unseen_ids": [t["task_id"] for t in tasks],
        "labels_unseen": all_rows,
        "scored_unseen": scored,
        "pooled": pooled,
        "beats_constant": beats_mae,
        "remaining_check": remaining_check,
        "ledger": ledger,
        "proceed_wholebox": False,
        "convincing_offline": convincing,
        "holdout_status": "Expt-8B eight-box set is development/reused evaluation, not this confirmation set",
        "frozen_identity": {
            "labels_fit_sha256": frozen.get("labels_fit_sha256"),
            "model_payload_sha256": frozen.get("model_payload_sha256"),
            "frozen_file_sha256": frozen.get("frozen_file_sha256"),
            "label_remaining_budget": frozen.get("label_remaining_budget"),
            "cache_key": frozen.get("cache_key"),
        },
    }


def maybe_run_wholebox(config: Config, offline: dict, bundles: list[dict]) -> dict:
    if not offline.get("convincing_offline"):
        return {"ran": False, "reason": "unseen offline evidence was not convincing across seeds and boxes", "rows": []}
    if int(config.n_fresh) <= 0:
        return {"ran": False, "reason": "n_fresh=0; whole-box stays conditional", "rows": []}
    return {"ran": False, "reason": "n_fresh=0", "rows": []}
