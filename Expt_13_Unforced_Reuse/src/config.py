"""Expt-13: unforced reuse during ordinary search. Frozen table and selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "Does frozen exact and learned-transform memory reduce total effort at preserved quality "
    "when the agent must reach reusable states through its own ordinary decisions, without "
    "constructed prefixes or scheduled matches? Absence of reuse means none was observed in these "
    "streams with this frozen table and exact state representation. It does not establish how rare "
    "recurrence is throughout the environment, and it does not mean demonstrated recall has disappeared."
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
    n_store_independent: int = 8
    n_families: int = 4
    n_store_per_family: int = 2
    n_eval_per_family: int = 3
    n_fresh_per_stream: int = 8
    n_streams: int = 3
    generate_seed: int = 2026093017
    max_prefix_cells: int = 22
    min_prefix_cells: int = 8
    min_prefix_placements: int = 1
    max_transforms_per_donor: int = 7
    train_frac: float = 2.0 / 3.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["mechanism"] = "frozen Expt-11/12 exact lookup + declared D4 + Expt-11 selection rule"
        data["constructed_prefix_on_eval"] = False
        data["scheduled_matches"] = False
        data["online_memory_growth"] = False
        data["category_hidden"] = True
        data["A_identity"] = "primitive_evals + lookup + matching + transformation + validation + learning"
        data["does_not_invent_transforms"] = True
        data["does_not_expand_abstraction"] = True
        data["seeds_are_paired_not_independent_memories"] = True
        return data


def smoke_config() -> Config:
    return Config(
        seeds=(11,),
        n_store_independent=2,
        n_families=1,
        n_store_per_family=1,
        n_eval_per_family=2,
        n_fresh_per_stream=2,
        n_streams=1,
        generate_seed=2026093016,
        max_transforms_per_donor=3,
        min_prefix_cells=4,
    )


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["seeds"] = (int(args.seed),)
    if getattr(args, "n_boxes", None) is not None:
        n = max(2, int(args.n_boxes))
        updates["n_store_independent"] = max(1, n // 2)
        updates["n_fresh_per_stream"] = n - updates["n_store_independent"]
    return replace(config, **updates) if updates else config
