"""Expt-10: exact subproblem reuse inside otherwise new problems. Memorization, not abstraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "Can an exact remaining-state continuation replace the rest of search after a genuine "
    "non-empty primitive prefix inside an otherwise new problem? This is memorization, not "
    "abstraction. Whole-solution recall from the empty board is retained only as a positive control."
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
    generate_seed: int = 2026093010
    max_prefix_cells: int = 22
    min_prefix_cells: int = 4
    min_prefix_placements: int = 1

    def to_dict(self) -> dict:
        data = asdict(self)
        data["no_library_retrain"] = True
        data["no_operation_predictor"] = True
        data["memory"] = "exact continuation keyed by (mask, inventory)"
        data["exact_reuse_is"] = "memorization, not abstraction"
        data["memory_sharing"] = "one shared table across seeds; frozen before eval; first write wins"
        data["A_identity"] = "primitive_evals + lookup + validation + learning"
        data["constructed_recurrence"] = "labeled; alternative covering of a stored prefix region"
        data["natural_recurrence_separate"] = True
        data["remaining_saving_not_used"] = True
        return data


def smoke_config() -> Config:
    return Config(seeds=(11,), n_store=2, n_fresh=2, n_boxes=4, generate_seed=2026093011)


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
