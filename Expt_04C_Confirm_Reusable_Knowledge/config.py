"""Expt-4C configuration.

Quality-loss margin is declared here BEFORE any confirmation run.
A per-box effort win requires Q_agent >= Q_primitive - QUALITY_LOSS_MARGIN
and strictly lower A. This margin is not tuned after seeing results.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

PHILOSOPHY = (
    "The objective of this experiment is not to discover a better packing heuristic. "
    "Expt-4C keeps the Expt-4B selective mechanism unchanged and asks whether learned "
    "knowledge genuinely reduces future deliberation under transfer and lesion."
)

# Occupied-cell allowance when counting an effort win against primitive.
# Chosen before the confirmation run. Not a significance test.
QUALITY_LOSS_MARGIN = 1.0

PRIMITIVE_SCORE_AREA = 1.0
PRIMITIVE_SCORE_CONTACT = 0.2
PRIMITIVE_SCORE_BOUNDARY = 0.05

TRAIN_CONDITIONS = ("primitive", "selective_flat", "selective_hierarchical")
FINAL_CONDITIONS = (
    "primitive",
    "selective_flat",
    "selective_hierarchical",
    "transfer",
    "lesion",
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
    train_boxes: int = 200
    change_at: int = 10**9
    checkpoints: tuple[int, ...] = (0, 30, 60, 100, 200)
    seeds: tuple[int, ...] = (11, 22, 33, 44, 55, 66, 77, 88, 99, 111)
    train_val_count: int = 4
    master_seed: int = 11
    score_area: float = PRIMITIVE_SCORE_AREA
    score_contact: float = PRIMITIVE_SCORE_CONTACT
    score_boundary: float = PRIMITIVE_SCORE_BOUNDARY

    def to_dict(self) -> dict:
        data = asdict(self)
        data["quality_loss_margin"] = float(self.quality_loss_margin)
        data["quality_loss_margin_declared_before_run"] = True
        return data


def smoke_config() -> Config:
    return Config(
        train_boxes=8,
        checkpoints=(0, 8),
        seeds=(11,),
        train_val_count=2,
        pair_eval_cap=500,
        eval_cap=2500,
        retrieval_pool=8,
        top_k=3,
        anchors=6,
        episodic_capacity=8,
        operation_capacity=6,
        provisional_capacity=6,
    )


def confirm_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["master_seed"] = int(args.seed)
        updates["seeds"] = (int(args.seed),)
    if getattr(args, "train_boxes", None) is not None:
        updates["train_boxes"] = int(args.train_boxes)
    return replace(config, **updates) if updates else config
