"""Expt-9: exact continuation reuse. Memorization, not abstraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "Can remembering a successful continuation replace primitive search on an exact remaining "
    "board-and-inventory match? This is memorization, not abstraction, and not a rescue of Expt-8C."
)


@dataclass(frozen=True)
class Config:
    q_min: float = 75.0
    quality_loss_margin: float = QUALITY_LOSS_MARGIN
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    seeds: tuple[int, ...] = (11, 22, 33)
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    n_store: int = 12
    n_fresh: int = 12
    n_boxes: int = 24
    generate_seed: int = 2026092992
    n_fresh_wholebox: int = 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["no_library_retrain"] = True
        data["no_operation_predictor"] = True
        data["memory"] = "exact continuation keyed by (mask, inventory)"
        data["exact_reuse_is"] = "memorization, not abstraction"
        data["A_identity"] = "primitive_evals + lookup + validation + learning"
        data["remaining_saving_not_used"] = True
        return data


def smoke_config() -> Config:
    return Config(seeds=(11,), n_store=2, n_fresh=2, n_boxes=4, generate_seed=2026092993)


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["seeds"] = (int(args.seed),)
    if getattr(args, "n_boxes", None) is not None:
        updates["n_store"] = max(1, int(args.n_boxes) // 2)
        updates["n_fresh"] = int(args.n_boxes) - updates["n_store"]
        updates["n_boxes"] = int(args.n_boxes)
    return replace(config, **updates) if updates else config
