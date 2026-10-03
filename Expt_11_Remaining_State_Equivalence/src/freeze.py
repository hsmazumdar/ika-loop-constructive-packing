"""Refit Expt-8B development models from hashed labels and freeze them with budget identity."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from config import Config, EXPT7_RESULT, EXPT8B_RESULT
from provenance import CACHE_KEY, LABEL_BUDGET, file_sha
from predictors import ConstantModels, choose_thresholds, fit_action, fit_context
from ranker import LinearRegressor, QualityModel

ROOT = Path(__file__).resolve().parents[1]


def _parse_vec(raw):
    if isinstance(raw, list):
        return [float(x) for x in raw]
    return [float(x) for x in json.loads(raw)]


def load_fit_rows(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row["context_vector"] = _parse_vec(row["context_vector"])
            row["action_vector"] = _parse_vec(row["action_vector"])
            row["remaining_saving"] = float(row["remaining_saving"])
            row["quality_ok"] = str(row["quality_ok"]).lower() in ("true", "1")
            row["seed"] = int(row["seed"])
            rows.append(row)
    return rows


def payload_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def freeze_from_expt8b(config: Config | None = None) -> dict:
    config = config or Config()
    labels_path = ROOT.parent / EXPT8B_RESULT / "labels_fit.csv"
    rows = load_fit_rows(labels_path)
    labels_sha = file_sha(labels_path)
    by_seed: dict[int, list] = defaultdict(list)
    for row in rows:
        by_seed[int(row["seed"])].append(row)
    expt7 = ROOT.parent / EXPT7_RESULT
    seeds = {}
    for seed, fit_rows in sorted(by_seed.items()):
        const = ConstantModels(
            sum(float(r["remaining_saving"]) for r in fit_rows) / len(fit_rows),
            sum(1.0 if r["quality_ok"] else 0.0 for r in fit_rows) / len(fit_rows),
            seed,
        )
        ctx_b, ctx_q = fit_context(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=True)
        ctx_q = choose_thresholds(ctx_q, fit_rows, "context_vector")
        act_b, act_q = fit_action(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=True)
        act_q = choose_thresholds(act_q, fit_rows, "action_vector")
        ctx_bw, ctx_qw = fit_context(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=False)
        ctx_qw = choose_thresholds(ctx_qw, fit_rows, "context_vector")
        act_bw, act_qw = fit_action(fit_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight, unweighted=False)
        act_qw = choose_thresholds(act_qw, fit_rows, "action_vector")
        ranker = json.loads((expt7 / f"ranker_seed{seed}.json").read_text(encoding="utf-8"))
        seeds[str(seed)] = {
            "per_seed_mean": {
                "mean_saving": const.mean_saving,
                "mean_quality": const.mean_quality,
                "quality_threshold": const.quality_threshold,
                "historical_comparator": False,
            },
            "action_unweighted": {
                "benefit": act_b.to_dict(),
                "quality": act_q.to_dict(),
                "historical_comparator": False,
            },
            "context_unweighted": {
                "benefit": ctx_b.to_dict(),
                "quality": ctx_q.to_dict(),
                "historical_comparator": False,
            },
            "action_weighted": {
                "benefit": act_bw.to_dict(),
                "quality": act_qw.to_dict(),
                "historical_comparator": True,
                "note": "Severe-loss-weighted fit. Not ordinary expected savings.",
            },
            "context_weighted": {
                "benefit": ctx_bw.to_dict(),
                "quality": ctx_qw.to_dict(),
                "historical_comparator": True,
                "note": "Severe-loss-weighted fit. Not ordinary expected savings.",
            },
            "frozen_expt7": {
                "benefit": ranker["benefit"],
                "quality": ranker["quality"],
                "historical_comparator": True,
                "training_remaining_cap": "pair_eval_cap=1600",
                "ranker_file_sha256": file_sha(expt7 / f"ranker_seed{seed}.json"),
            },
        }
    payload = {
        "label_remaining_budget": LABEL_BUDGET,
        "cache_key": CACHE_KEY,
        "primary_saving_fit": "unweighted",
        "labels_source": str(labels_path),
        "labels_fit_sha256": labels_sha,
        "n_fit_labels": len(rows),
        "ranker_steps": int(config.ranker_steps),
        "admission_bound": int(config.anchors),
        "no_threshold_retune": True,
        "seeds": seeds,
    }
    payload["model_payload_sha256"] = payload_hash({k: v for k, v in payload.items() if k != "model_payload_sha256"})
    out = ROOT / "frozen" / "expt8b_models.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_frozen(path: Path | None = None) -> dict:
    path = path or (ROOT / "frozen" / "expt8b_models.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = {}
    for seed_s, blob in payload["seeds"].items():
        seed = int(seed_s)
        pm = blob["per_seed_mean"]
        models[seed] = {
            "per_seed_mean": ConstantModels(pm["mean_saving"], pm["mean_quality"], seed),
            "action_unweighted": (LinearRegressor.from_dict(blob["action_unweighted"]["benefit"]), QualityModel.from_dict(blob["action_unweighted"]["quality"])),
            "context_unweighted": (LinearRegressor.from_dict(blob["context_unweighted"]["benefit"]), QualityModel.from_dict(blob["context_unweighted"]["quality"])),
            "action_weighted": (LinearRegressor.from_dict(blob["action_weighted"]["benefit"]), QualityModel.from_dict(blob["action_weighted"]["quality"])),
            "context_weighted": (LinearRegressor.from_dict(blob["context_weighted"]["benefit"]), QualityModel.from_dict(blob["context_weighted"]["quality"])),
            "frozen": (LinearRegressor.from_dict(blob["frozen_expt7"]["benefit"]), QualityModel.from_dict(blob["frozen_expt7"]["quality"])),
            "meta": blob,
        }
        models[seed]["per_seed_mean"].quality_threshold = float(pm["quality_threshold"])
    payload["models_by_seed"] = models
    payload["frozen_file"] = str(path)
    payload["frozen_file_sha256"] = file_sha(path)
    return payload
