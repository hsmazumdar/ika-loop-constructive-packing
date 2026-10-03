"""Fit constant, context, and action-level predictors. No library updates."""

from __future__ import annotations

import math

from ranker import LinearRegressor, QualityModel, RANK_NAMES, choose_quality_threshold, fit_quality, fit_regressor
from action_features import ACTION_NAMES
from gates import _sigmoid


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


def pearson_within_seed(rows: list[dict], pred_key: str = "pred_saving") -> dict:
    """A per-seed constant has undefined within-seed correlation. Pooled correlation can still be nonzero."""
    by_seed = {}
    for row in rows:
        by_seed.setdefault(int(row["seed"]), []).append(row)
    within = {}
    for seed, items in by_seed.items():
        pairs = [(float(r[pred_key]), float(r["remaining_saving"])) for r in items]
        preds = [p for p, _ in pairs]
        within[seed] = None if (max(preds) - min(preds) < 1e-9) else pearson(pairs)
    pooled = pearson([(float(r[pred_key]), float(r["remaining_saving"])) for r in rows])
    return {"pooled": pooled, "within_seed": within}


def fit_linear_unweighted(names: tuple[str, ...], rows: list[dict], vec_key: str, steps: int) -> LinearRegressor:
    dim = len(names)
    weights = [0.0] * dim
    bias = 0.0
    rate = 0.05
    packed = [(r[vec_key], float(r["remaining_saving"])) for r in rows]
    for _ in range(max(1, steps)):
        g_w = [0.0] * dim
        g_b = 0.0
        n = 0.0
        for vec, y in packed:
            pred = bias + sum(a * b for a, b in zip(weights, vec))
            err = pred - y
            n += 1.0
            g_b += err
            for i, value in enumerate(vec):
                g_w[i] += err * value
        denom = max(1.0, n)
        bias -= rate * g_b / denom
        weights = [w - rate * g / denom for w, g in zip(weights, g_w)]
        rate *= 0.98
    return LinearRegressor(names=names, weights=weights, bias=bias, frozen=True)


def fit_logistic_unweighted(names: tuple[str, ...], rows: list[dict], vec_key: str, y_fn, steps: int) -> QualityModel:
    dim = len(names)
    weights = [0.0] * dim
    bias = 0.0
    op_bias: dict[str, float] = {}
    rate = 0.15
    for _ in range(max(1, steps)):
        g_w = [0.0] * dim
        g_b = 0.0
        g_op: dict[str, float] = {}
        n = 0.0
        for row in rows:
            vec = row[vec_key]
            y = 1.0 if y_fn(row) else 0.0
            op_id = row.get("op_id")
            extra = op_bias.get(op_id, 0.0) if op_id else 0.0
            s = bias + extra + sum(a * b for a, b in zip(weights, vec))
            p = _sigmoid(s)
            err = p - y
            n += 1.0
            g_b += err
            for i, value in enumerate(vec):
                g_w[i] += err * value
            if op_id:
                g_op[op_id] = g_op.get(op_id, 0.0) + err
        denom = max(1.0, n)
        bias -= rate * g_b / denom
        weights = [w - rate * g / denom for w, g in zip(weights, g_w)]
        for op_id, g in g_op.items():
            op_bias[op_id] = op_bias.get(op_id, 0.0) - rate * g / denom
        rate *= 0.98
    return QualityModel(names=names, weights=weights, bias=bias, op_bias=op_bias, threshold=0.5, frozen=True)


class ConstantModels:
    """Per-seed mean baseline. Not a single global constant."""

    def __init__(self, mean_saving: float, mean_quality: float, seed: int):
        self.mean_saving = mean_saving
        self.mean_quality = mean_quality
        self.seed = seed
        self.quality_threshold = 1.0 if mean_quality < 0.8 else 0.5
        self.name = "per_seed_mean"

    def predict_saving(self, _vec) -> float:
        return self.mean_saving

    def probability(self, _vec, _op_id=None) -> float:
        return self.mean_quality


def fit_context(rows: list[dict], steps: int, scale: float, qfail: float, *, unweighted: bool) -> tuple[LinearRegressor, QualityModel]:
    if unweighted:
        benefit = fit_linear_unweighted(RANK_NAMES, rows, "context_vector", steps)
        quality = fit_logistic_unweighted(RANK_NAMES, rows, "context_vector", lambda r: r["quality_ok"], steps)
        return benefit, quality
    train = [{"vector": r["context_vector"], "remaining_saving": r["remaining_saving"], "quality_ok": r["quality_ok"], "op_id": r["op_id"]} for r in rows]
    benefit = fit_regressor(RANK_NAMES, train, steps, scale, qfail)
    quality = fit_quality(RANK_NAMES, train, steps, scale, qfail)
    return benefit, quality


def fit_action(rows: list[dict], steps: int, scale: float, qfail: float, *, unweighted: bool) -> tuple[LinearRegressor, QualityModel]:
    if unweighted:
        benefit = fit_linear_unweighted(ACTION_NAMES, rows, "action_vector", steps)
        quality = fit_logistic_unweighted(ACTION_NAMES, rows, "action_vector", lambda r: r["quality_ok"], steps)
        return benefit, quality
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


def coverage_counts(rows: list[dict]) -> dict:
    unique_boxes = {str(r["task_id"]) for r in rows}
    pairs = {(int(r["seed"]), str(r["task_id"])) for r in rows}
    states = {(int(r["seed"]), str(r["task_id"]), int(r["state_index"])) for r in rows}
    return {
        "n_unique_boxes": len(unique_boxes),
        "n_seed_box_pairs": len(pairs),
        "n_states": len(states),
        "n_actions": len(rows),
    }


def selection_metrics(rows: list[dict], pred_key: str, p_key: str, threshold: float, remaining_check: float, examined_key: str = "examined") -> dict:
    accepted = []
    for r in rows:
        if "accept" in r:
            if r["accept"]:
                accepted.append(r)
        elif would_accept(float(r[pred_key]), float(r[p_key]), float(r.get("quality_threshold") or threshold), remaining_check):
            accepted.append(r)
    cov = coverage_counts(rows)
    acc_cov = coverage_counts(accepted) if accepted else {"n_unique_boxes": 0, "n_seed_box_pairs": 0, "n_states": 0, "n_actions": 0}
    exam = [float(r.get(examined_key) or 0) for r in accepted] if accepted else []
    if not accepted:
        return {
            **cov,
            "n_accepted": 0,
            "n_accepted_unique_boxes": 0,
            "n_accepted_seed_box_pairs": 0,
            "n_accepted_states": 0,
            "coverage_actions": 0.0,
            "mean_remaining_saving": None,
            "mean_net_after_check": None,
            "mean_examined_billed": None,
            "admission_bound": remaining_check,
            "quality_loss_rate": None,
            "severe_loss_n": 0,
            "severe_loss_rate": None,
            "mean_pred": None,
            "mean_observed": None,
            "zero_coverage": True,
        }
    sav = [float(r["remaining_saving"]) for r in accepted]
    net = [float(r["remaining_saving"]) - float(r.get(examined_key) or 0) for r in accepted]
    ql = sum(1.0 for r in accepted if not r["quality_ok"]) / len(accepted)
    severe = [s for s in sav if s < -200]
    return {
        **cov,
        "n_accepted": len(accepted),
        "n_accepted_unique_boxes": acc_cov["n_unique_boxes"],
        "n_accepted_seed_box_pairs": acc_cov["n_seed_box_pairs"],
        "n_accepted_states": acc_cov["n_states"],
        "coverage_actions": len(accepted) / len(rows) if rows else 0.0,
        "mean_remaining_saving": _mean(sav),
        "mean_net_after_check": _mean(net),
        "mean_examined_billed": _mean(exam),
        "admission_bound": remaining_check,
        "quality_loss_rate": ql,
        "severe_loss_n": len(severe),
        "severe_loss_rate": len(severe) / len(accepted),
        "mean_pred": _mean([float(r[pred_key]) for r in accepted]),
        "mean_observed": _mean(sav),
        "zero_coverage": False,
    }


def useful_subset(metrics: dict) -> bool:
    if metrics.get("zero_coverage"):
        return False
    if int(metrics.get("n_accepted") or 0) <= 0:
        return False
    if int(metrics.get("n_accepted_unique_boxes") or 0) < 2:
        return False
    ql = metrics.get("quality_loss_rate")
    if ql is None or ql > 0.2:
        return False
    net = metrics.get("mean_net_after_check")
    return net is not None and net > 0
