"""Expt-4D configuration.

The learner is frozen after training. Diagnostics run on a development set
that is disjoint from the Expt-4C final test boxes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

PHILOSOPHY = (
    "The broader idea remains unproven, rather than disproved. Expt-4D locates "
    "whether reuse loses its advantage in retrieval cost, harmful execution, or "
    "wrong-context selection. Effort saving = A_primitive - A_agent; positive means "
    "the agent used fewer candidate evaluations."
)

QUALITY_LOSS_MARGIN = 1.0

PRIMITIVE_SCORE_AREA = 1.0
PRIMITIVE_SCORE_CONTACT = 0.2
PRIMITIVE_SCORE_BOUNDARY = 0.05

DIAGNOSTIC_MODES = (
    "primitive",
    "retrieve_check_then_primitive",
    "normal_reuse",
)


@dataclass(frozen=True)
class Config:
    q_min: float = 75.0
    quality_loss_margin: float = QUALITY_LOSS_MARGIN
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    pair_eval_cap: int = 1600
    top_k: int = 5
    retrieval_pool: int = 16
    anchors: int = 8
    max_depth: int = 4
    min_len: int = 2
    max_len: int = 5
    min_support: int = 2
    episodic_capacity: int = 48
    operation_capacity: int = 24
    provisional_capacity: int = 16
    byte_cap: int = 65536
    decay: float = 0.05
    fail_penalty: float = 1.0
    storage_weight: float = 0.001
    applicability_min: float = 0.05
    abstention_margin: float = 0.0
    env_discount: float = 0.3
    retire_utility: float = 0.0
    max_promotions_per_episode: int = 2
    train_boxes: int = 80
    change_at: int = 10**9
    checkpoints: tuple[int, ...] = (0, 80)
    seeds: tuple[int, ...] = (11, 22, 33)
    train_val_count: int = 4
    max_replays_per_box: int = 8
    master_seed: int = 11
    score_area: float = PRIMITIVE_SCORE_AREA
    score_contact: float = PRIMITIVE_SCORE_CONTACT
    score_boundary: float = PRIMITIVE_SCORE_BOUNDARY

    def to_dict(self) -> dict:
        data = asdict(self)
        data["effort_saving_definition"] = "A_primitive - A_agent (positive = fewer evaluations than primitive)"
        data["quality_loss_margin"] = float(self.quality_loss_margin)
        return data


def smoke_config() -> Config:
    return Config(
        train_boxes=8,
        checkpoints=(0, 8),
        seeds=(11,),
        eval_cap=2500,
        pair_eval_cap=500,
        max_replays_per_box=3,
        retrieval_pool=8,
        top_k=3,
        anchors=6,
        episodic_capacity=8,
        operation_capacity=6,
        provisional_capacity=6,
    )


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["master_seed"] = int(args.seed)
        updates["seeds"] = (int(args.seed),)
    if getattr(args, "train_boxes", None) is not None:
        updates["train_boxes"] = int(args.train_boxes)
    return replace(config, **updates) if updates else config
