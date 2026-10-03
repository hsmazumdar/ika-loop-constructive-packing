"""Expt-12: mixed streams at predeclared useful-recurrence rates. Expt-11 consult frozen."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "At what predeclared useful-recurrence frequency does frozen learned isometry selection "
    "produce a net evaluation-effort saving after unsuccessful consultations, while preserving "
    "quality? Task category is hidden. This does not expand the abstraction claim."
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
    generate_seed: int = 2026093014
    max_prefix_cells: int = 22
    min_prefix_cells: int = 8
    min_prefix_placements: int = 1
    max_transforms_per_donor: int = 7
    train_frac: float = 2.0 / 3.0
    rates: tuple[float, ...] = (0.0, 0.05, 0.10, 0.25, 0.50, 1.0)
    n_stream: int = 24

    def to_dict(self) -> dict:
        data = asdict(self)
        data["mechanism"] = "frozen Expt-11 exact lookup + declared D4 + Expt-11 selection rule"
        data["category_hidden"] = True
        data["A_identity"] = "primitive_evals + lookup + matching + transformation + validation + learning"
        data["does_not_invent_transforms"] = True
        data["does_not_expand_abstraction"] = True
        return data


def smoke_config() -> Config:
    return Config(
        seeds=(11,),
        n_store=2,
        n_fresh=2,
        n_boxes=4,
        generate_seed=2026093015,
        max_transforms_per_donor=3,
        min_prefix_cells=4,
        rates=(0.0, 1.0),
        n_stream=6,
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
