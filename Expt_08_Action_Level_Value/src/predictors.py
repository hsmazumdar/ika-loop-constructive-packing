"""Fit constant, context, and action-level predictors. No library updates."""

from __future__ import annotations

import math

from ranker import LinearRegressor, QualityModel, RANK_NAMES, choose_quality_threshold, fit_quality, fit_regressor
from action_features import ACTION_NAMES


def _mean(values) -> float:
    return 0.0 if not values else sum(values) / len(values)


def mae(pairs) -> float | None:
    if not pairs:
        return None
    return sum(abs(p - y) for p, y in pairs) / len(pairs)


def rmse(pairs) -> float | None:
    if not pairs:
        return None
    return math.sqrt(sum((p - y) ** 2 for p, y in pairs) / len(pairs))


def pearson(pairs) -> float | None:
    if len(pairs) < 3:
        return None
    xs = [p for p, _ in pairs]
    ys = [y for _, y in pairs]
    mx = _mean(xs)
    my = _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx <= 1e-12 or dy <= 1e-12:
        return None
    return num / (dx * dy)


def auc_beneficial(rows: list[dict], pred_key: str) -> float | None:
    pos = [float(r[pred_key]) for r in rows if r.get("beneficial_free")]
    neg = [float(r[pred_key]) for r in rows if not r.get("beneficial_free")]
    if not pos or not neg:
        return None
    wins = 0.0
    n = 0
    for a in pos:
        for b in neg:
            n += 1
            if a > b:
                wins += 1.0
            elif a == b:
                wins += 0.5
    return wins / n if n else None


def fit_constant(rows: list[dict]) -> tuple[LinearRegressor, QualityModel]:
    y = [float(r["remaining_saving"]) for r in rows]
    q = [1.0 if r["quality_ok"] else 0.0 for r in rows]
    benefit = LinearRegressor(RANK_NAMES, [0.0] * len(RANK_NAMES), _mean(y), True)
    quality = QualityModel(RANK_NAMES, [0.0] * len(RANK_NAMES), 0.0, {}, 1.0 if _mean(q) < 0.5 else 0.0, True)
    # constant probability via bias: sigmoid(bias) ~ mean quality. Store mean in threshold logic instead.
    quality.bias = 0.0
    quality.threshold = 1.0 if _mean(q) < 0.8 else 0.5
    quality._constant_p = _mean(q)  # type: ignore[attr-defined]
    return benefit, quality


class ConstantModels:
    def __init__(self, mean_saving: float, mean_quality: float):
        self.mean_saving = mean_saving
        self.mean_quality = mean_quality
        self.quality_threshold = 1.0 if mean_quality < 0.8 else 0.5

    def predict_saving(self, _vec) -> float:
        return self.mean_saving

    def probability(self, _vec, _op_id=None) -> float:
        return self.mean_quality


def fit_context(rows: list[dict], steps: int, scale: float, qfail: float) -> tuple[LinearRegressor, QualityModel]:
    train = [{"vector": r["context_vector"], "remaining_saving": r["remaining_saving"], "quality_ok": r["quality_ok"], "op_id": r["op_id"]} for r in rows]
    benefit = fit_regressor(RANK_NAMES, train, steps, scale, qfail)
    quality = fit_quality(RANK_NAMES, train, steps, scale, qfail)
    return benefit, quality


def fit_action(rows: list[dict], steps: int, scale: float, qfail: float) -> tuple[LinearRegressor, QualityModel]:
    train = [{"vector": r["action_vector"], "remaining_saving": r["remaining_saving"], "quality_ok": r["quality_ok"], "op_id": r["op_id"]} for r in rows]
    benefit = fit_regressor(ACTION_NAMES, train, steps, scale, qfail)
    quality = fit_quality(ACTION_NAMES, train, steps, scale, qfail)
    return benefit, quality


def choose_thresholds(quality: QualityModel, rows: list[dict], vec_key: str) -> QualityModel:
    packed = [{"vector": r[vec_key], "remaining_saving": r["remaining_saving"], "quality_ok": r["quality_ok"], "op_id": r.get("op_id")} for r in rows]
    return choose_quality_threshold(quality, packed)


def remaining_check_cost(anchors: int) -> int:
    return max(1, int(anchors))


def would_accept(pred_saving: float, p_ok: float, quality_threshold: float, remaining_check: float) -> bool:
    return (p_ok >= quality_threshold) and (pred_saving > remaining_check)


def selection_metrics(rows: list[dict], pred_key: str, p_key: str, threshold: float, remaining_check: float, examined_key: str = "examined") -> dict:
    accepted = []
    for r in rows:
        if "accept" in r:
            if r["accept"]:
                accepted.append(r)
        elif would_accept(float(r[pred_key]), float(r[p_key]), float(r.get("quality_threshold") or threshold), remaining_check):
            accepted.append(r)
    n = len(rows)
    n_acc = len(accepted)
    boxes = {(r["seed"], r["task_id"]) for r in rows}
    acc_boxes = {(r["seed"], r["task_id"]) for r in accepted}
    seeds = {r["seed"] for r in rows}
    acc_seeds = {r["seed"] for r in accepted}
    if not accepted:
        return {
            "n_actions": n,
            "n_accepted": 0,
            "coverage_actions": 0.0,
            "n_boxes": len(boxes),
            "n_boxes_covered": 0,
            "n_seeds_covered": 0,
            "mean_remaining_saving": None,
            "mean_net_after_check": None,
            "quality_loss_rate": None,
            "severe_loss_n": 0,
            "severe_loss_rate": None,
            "mean_pred": None,
            "mean_observed": None,
            "zero_coverage": True,
        }
    sav = [float(r["remaining_saving"]) for r in accepted]
    net = [float(r["remaining_saving"]) - float(r.get(examined_key) or 0) for r in accepted]
    ql = sum(1.0 for r in accepted if not r["quality_ok"]) / n_acc
    severe = [s for s in sav if s < -200]
    return {
        "n_actions": n,
        "n_accepted": n_acc,
        "coverage_actions": n_acc / n,
        "n_boxes": len(boxes),
        "n_boxes_covered": len(acc_boxes),
        "n_seeds_covered": len(acc_seeds),
        "mean_remaining_saving": _mean(sav),
        "mean_net_after_check": _mean(net),
        "quality_loss_rate": ql,
        "severe_loss_n": len(severe),
        "severe_loss_rate": len(severe) / n_acc,
        "mean_pred": _mean([float(r[pred_key]) for r in accepted]),
        "mean_observed": _mean(sav),
        "zero_coverage": False,
        "n_seeds": len(seeds),
    }


def useful_subset(metrics: dict) -> bool:
    if metrics.get("zero_coverage"):
        return False
    if int(metrics.get("n_accepted") or 0) <= 0:
        return False
    if int(metrics.get("n_boxes_covered") or 0) < 2:
        return False
    if int(metrics.get("n_seeds_covered") or 0) < 1:
        return False
    ql = metrics.get("quality_loss_rate")
    if ql is None or ql > 0.2:
        return False
    net = metrics.get("mean_net_after_check")
    return net is not None and net > 0
