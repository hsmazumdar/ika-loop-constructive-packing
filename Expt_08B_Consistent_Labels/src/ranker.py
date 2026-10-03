"""Predict remaining-solve benefit and quality-loss risk separately. Training only."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from gates import _sigmoid, sample_weight
from pieces import PIECE_TYPES


RANK_NAMES = (
    "occupancy",
    "remaining_piece_count",
    "n_types_remaining",
    "actions_used",
    "undos",
    "op_size",
    "depth",
    "applicability_score",
    "composed",
    "op_area",
) + tuple(f"mix_{name}" for name in PIECE_TYPES)


def rank_vector(occupied, remaining: dict, actions_used, undos, op_size, depth, score, composed, op_area) -> list[float]:
    total = sum(int(remaining.get(name, 0) or 0) for name in PIECE_TYPES) or 1.0
    n_types = sum(1 for name in PIECE_TYPES if int(remaining.get(name, 0) or 0) > 0)
    n_pieces = sum(int(remaining.get(name, 0) or 0) for name in PIECE_TYPES)
    mix = [int(remaining.get(name, 0) or 0) / total for name in PIECE_TYPES]
    return [
        float(occupied) / 100.0,
        n_pieces / 30.0,
        n_types / 16.0,
        float(actions_used) / 80.0,
        float(undos) / 4.0,
        float(op_size) / 5.0,
        float(depth) / 4.0,
        float(score),
        1.0 if composed else 0.0,
        float(op_area) / 20.0,
        *mix,
    ]


@dataclass
class LinearRegressor:
    names: tuple[str, ...]
    weights: list[float]
    bias: float = 0.0
    frozen: bool = False

    def predict(self, vector: list[float]) -> float:
        return self.bias + sum(w * float(v) for w, v in zip(self.weights, vector))

    def to_dict(self) -> dict:
        return {"names": list(self.names), "weights": [float(w) for w in self.weights], "bias": float(self.bias), "frozen": self.frozen}

    @staticmethod
    def from_dict(data: dict) -> "LinearRegressor":
        return LinearRegressor(
            names=tuple(data["names"]),
            weights=[float(w) for w in data["weights"]],
            bias=float(data["bias"]),
            frozen=bool(data.get("frozen", True)),
        )


@dataclass
class QualityModel:
    names: tuple[str, ...]
    weights: list[float]
    bias: float = 0.0
    op_bias: dict[str, float] = field(default_factory=dict)
    threshold: float = 0.5
    frozen: bool = False

    def probability(self, vector: list[float], op_id: str | None = None) -> float:
        total = self.bias + (self.op_bias.get(op_id, 0.0) if op_id else 0.0)
        total += sum(w * float(v) for w, v in zip(self.weights, vector))
        return _sigmoid(total)

    def admit(self, vector: list[float], op_id: str | None = None) -> bool:
        return self.probability(vector, op_id) >= self.threshold

    def to_dict(self) -> dict:
        return {
            "names": list(self.names),
            "weights": [float(w) for w in self.weights],
            "bias": float(self.bias),
            "op_bias": {k: float(v) for k, v in self.op_bias.items()},
            "threshold": float(self.threshold),
            "frozen": self.frozen,
        }

    @staticmethod
    def from_dict(data: dict) -> "QualityModel":
        return QualityModel(
            names=tuple(data["names"]),
            weights=[float(w) for w in data["weights"]],
            bias=float(data["bias"]),
            op_bias={str(k): float(v) for k, v in (data.get("op_bias") or {}).items()},
            threshold=float(data.get("threshold", 0.5)),
            frozen=bool(data.get("frozen", True)),
        )


def fit_regressor(names: tuple[str, ...], rows: list[dict], steps: int, scale: float, quality_fail_weight: float) -> LinearRegressor:
    dim = len(names)
    weights = [0.0] * dim
    bias = 0.0
    rate = 0.05
    for _ in range(max(1, steps)):
        g_w = [0.0] * dim
        g_b = 0.0
        total_w = 0.0
        for row in rows:
            vec = row["vector"]
            y = float(row["remaining_saving"])
            w = sample_weight(y, row["quality_ok"], scale, quality_fail_weight)
            pred = bias + sum(a * b for a, b in zip(weights, vec))
            err = w * (pred - y)
            total_w += w
            g_b += err
            for i, value in enumerate(vec):
                g_w[i] += err * value
        denom = max(1.0, total_w)
        bias -= rate * g_b / denom
        weights = [w - rate * g / denom for w, g in zip(weights, g_w)]
        rate *= 0.98
    return LinearRegressor(names=names, weights=weights, bias=bias, frozen=True)


def fit_quality(names: tuple[str, ...], rows: list[dict], steps: int, scale: float, quality_fail_weight: float) -> QualityModel:
    dim = len(names)
    weights = [0.0] * dim
    bias = 0.0
    op_bias: dict[str, float] = {}
    rate = 0.15
    for _ in range(max(1, steps)):
        g_w = [0.0] * dim
        g_b = 0.0
        g_op: dict[str, float] = {}
        total_w = 0.0
        for row in rows:
            vec = row["vector"]
            y = 1.0 if row["quality_ok"] else 0.0
            w = sample_weight(row["remaining_saving"], row["quality_ok"], scale, quality_fail_weight)
            op_id = row.get("op_id")
            extra = op_bias.get(op_id, 0.0) if op_id else 0.0
            s = bias + extra + sum(a * b for a, b in zip(weights, vec))
            p = _sigmoid(s)
            err = w * (p - y)
            total_w += w
            g_b += err
            for i, value in enumerate(vec):
                g_w[i] += err * value
            if op_id:
                g_op[op_id] = g_op.get(op_id, 0.0) + err
        denom = max(1.0, total_w)
        bias -= rate * g_b / denom
        weights = [w - rate * g / denom for w, g in zip(weights, g_w)]
        for op_id, g in g_op.items():
            op_bias[op_id] = op_bias.get(op_id, 0.0) - rate * g / denom
        rate *= 0.98
    return QualityModel(names=names, weights=weights, bias=bias, op_bias=op_bias, threshold=0.5, frozen=True)


def choose_quality_threshold(model: QualityModel, rows: list[dict]) -> QualityModel:
    if not rows:
        model.threshold = 1.0
        model.frozen = True
        return model
    scored = [(model.probability(row["vector"], row.get("op_id")), row) for row in rows]
    best = None
    for threshold in sorted({0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0} | {p for p, _ in scored}):
        admitted = [row for p, row in scored if p >= threshold]
        if not admitted:
            quality_rate = 0.0
            mean_saving = 0.0
            severe = 0
        else:
            quality_rate = sum(1.0 for row in admitted if not row["quality_ok"]) / len(admitted)
            mean_saving = sum(row["remaining_saving"] for row in admitted) / len(admitted)
            severe = sum(1 for row in admitted if row["remaining_saving"] < -500)
        key = (0 if severe == 0 else 1, 0 if quality_rate <= 0.2 else 1, -mean_saving, threshold)
        if best is None or key < best[0]:
            best = (key, threshold)
    model.threshold = float(best[1]) if best else 1.0
    model.frozen = True
    return model
