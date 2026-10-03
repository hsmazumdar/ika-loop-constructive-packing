"""Expt-11: remaining-state equivalence. Engineered rules vs experience-selected transforms."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "Can a remaining-state isometry, either supplied as a rule or selected from experience, "
    "transform a stored continuation and replace remaining search? Exact matching is the miss "
    "control. This tests which declared transforms are useful, not inventing transforms, and "
    "not a general claim of abstraction."
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
    generate_seed: int = 2026093012
    max_prefix_cells: int = 22
    min_prefix_cells: int = 8
    min_prefix_placements: int = 1
    max_transforms_per_donor: int = 4
    train_frac: float = 2.0 / 3.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["no_library_retrain"] = True
        data["memory"] = "exact continuation plus declared D4 isometries"
        data["exact_reuse_is"] = "memorization"
        data["equivalence_is"] = "declared isometries; learned selects among them"
        data["does_not_invent_transforms"] = True
        data["memory_sharing"] = "one shared table across seeds; frozen before eval; first write wins"
        data["A_identity"] = "primitive_evals + lookup + matching + transformation + validation + learning"
        return data


def smoke_config() -> Config:
    return Config(
        seeds=(11,),
        n_store=2,
        n_fresh=2,
        n_boxes=4,
        generate_seed=2026093013,
        max_transforms_per_donor=2,
        min_prefix_cells=4,
    )


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
