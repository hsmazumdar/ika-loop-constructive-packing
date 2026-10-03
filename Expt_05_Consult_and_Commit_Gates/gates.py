"""Cheap linear gates. No hardcoded operation or occupancy rules."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from pieces import PIECE_TYPES


CONSULT_NAMES = (
    "occupancy",
    "remaining_piece_count",
    "n_types_remaining",
    "actions_used",
    "undos",
) + tuple(f"mix_{name}" for name in PIECE_TYPES)

COMMIT_NAMES = CONSULT_NAMES + ("op_size", "depth", "applicability_score", "composed")


def _mix(remaining: dict) -> dict[str, float]:
    total = sum(int(remaining.get(name, 0) or 0) for name in PIECE_TYPES) or 1.0
    return {name: int(remaining.get(name, 0) or 0) / total for name in PIECE_TYPES}


def consult_vector(occupied, remaining: dict, actions_used, undos) -> list[float]:
    mix = _mix(remaining)
    n_types = sum(1 for name in PIECE_TYPES if int(remaining.get(name, 0) or 0) > 0)
    n_pieces = sum(int(remaining.get(name, 0) or 0) for name in PIECE_TYPES)
    return [
        float(occupied) / 100.0,
        n_pieces / 30.0,
        n_types / 16.0,
        float(actions_used) / 80.0,
        float(undos) / 4.0,
        *[mix[name] for name in PIECE_TYPES],
    ]


def commit_vector(occupied, remaining: dict, actions_used, undos, op_size, depth, score, composed) -> list[float]:
    return consult_vector(occupied, remaining, actions_used, undos) + [
        float(op_size) / 5.0,
        float(depth) / 4.0,
        float(score),
        1.0 if composed else 0.0,
    ]


def _sigmoid(value: float) -> float:
    if value >= 30:
        return 1.0
    if value <= -30:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def sample_weight(remaining_saving: float, quality_ok: bool, scale: float, quality_fail_weight: float) -> float:
    """Severe losses outweigh a pile of modest gains."""
    extra = max(0.0, -float(remaining_saving)) / max(1.0, float(scale))
    fail = 0.0 if quality_ok else float(quality_fail_weight)
    return 1.0 + extra + fail


@dataclass
class LinearGate:
    """Weighted logistic classifier. Per-op bias is learned, not a handwritten reject list."""

    names: tuple[str, ...]
    weights: list[float]
    bias: float = 0.0
    op_bias: dict[str, float] = field(default_factory=dict)
    threshold: float = 0.5
    frozen: bool = False

    def score(self, vector: list[float], op_id: str | None = None) -> float:
        total = self.bias
        for weight, value in zip(self.weights, vector):
            total += weight * float(value)
        if op_id is not None:
            total += self.op_bias.get(op_id, 0.0)
        return total

    def probability(self, vector: list[float], op_id: str | None = None) -> float:
        return _sigmoid(self.score(vector, op_id))

    def admit(self, vector: list[float], op_id: str | None = None) -> bool:
        return self.probability(vector, op_id) >= self.threshold

    def to_dict(self) -> dict:
        return {
            "names": list(self.names),
            "weights": [float(w) for w in self.weights],
            "bias": float(self.bias),
            "op_bias": {key: float(value) for key, value in self.op_bias.items()},
            "threshold": float(self.threshold),
            "frozen": self.frozen,
        }


def fit_gate(
    names: tuple[str, ...],
    rows: list[dict],
    *,
    use_op_bias: bool,
    steps: int,
    scale: float,
    quality_fail_weight: float,
) -> LinearGate:
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
            y = 1.0 if row["y"] else 0.0
            w = sample_weight(row["remaining_saving"], row["quality_ok"], scale, quality_fail_weight)
            op_id = row.get("op_id") if use_op_bias else None
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
    return LinearGate(names=names, weights=weights, bias=bias, op_bias=op_bias, threshold=0.5, frozen=False)


def choose_threshold(gate: LinearGate, rows: list[dict], use_op_bias: bool) -> LinearGate:
    """Freeze threshold on held-out training replays. Prefer no severe admitted loss, then mean saving."""
    if not rows:
        gate.threshold = 1.0
        gate.frozen = True
        return gate
    scored = []
    for row in rows:
        p = gate.probability(row["vector"], row.get("op_id") if use_op_bias else None)
        scored.append((p, row))
    candidates = sorted({0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0} | {p for p, _ in scored})
    best = None
    for threshold in candidates:
        admitted = [row for p, row in scored if p >= threshold]
        if not admitted:
            quality_rate = 0.0
            mean_saving = 0.0
            severe = 0
        else:
            quality_rate = sum(1.0 for row in admitted if not row["quality_ok"]) / len(admitted)
            mean_saving = sum(row["remaining_saving"] for row in admitted) / len(admitted)
            severe = sum(1 for row in admitted if row["remaining_saving"] < -500)
        # Rank: no severe admitted losses, quality-loss rate <= 0.2, then higher mean saving.
        key = (0 if severe == 0 else 1, 0 if quality_rate <= 0.2 else 1, -mean_saving, threshold)
        if best is None or key < best[0]:
            best = (key, threshold)
    gate.threshold = float(best[1]) if best else 1.0
    gate.frozen = True
    return gate
