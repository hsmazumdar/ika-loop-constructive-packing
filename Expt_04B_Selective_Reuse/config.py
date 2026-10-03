"""Expt-4B configuration.

The objective is not a better packing heuristic. Packing is the observable
world. Expt-4B asks whether the agent can distinguish a recurring pattern
from a useful piece of knowledge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

PHILOSOPHY = (
    "The objective of this experiment is not to discover a better packing heuristic. "
    "Packing is the observable environment. Expt-4 has implemented remembering and "
    "composition. Expt-4B tests whether the system can learn selective, beneficial reuse."
)

PRIMITIVE_SCORE_AREA = 1.0
PRIMITIVE_SCORE_CONTACT = 0.2
PRIMITIVE_SCORE_BOUNDARY = 0.05

CONDITION_NAMES = (
    "primitive",
    "current_hierarchy",
    "utility_promotion",
    "contextual_abstention",
    "both",
)


@dataclass(frozen=True)
class Config:
    q_min: float = 75.0
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
    train_boxes: int = 60
    change_at: int = 30
    checkpoints: tuple[int, ...] = (0, 15, 30, 60)
    seeds: tuple[int, ...] = (11, 22)
    heldout_limit: int | None = None
    train_val_count: int = 4
    probe_count: int = 3
    master_seed: int = 11
    score_area: float = PRIMITIVE_SCORE_AREA
    score_contact: float = PRIMITIVE_SCORE_CONTACT
    score_boundary: float = PRIMITIVE_SCORE_BOUNDARY

    def to_dict(self) -> dict:
        return asdict(self)


def smoke_config() -> Config:
    return Config(
        train_boxes=10,
        change_at=5,
        checkpoints=(0, 5, 10),
        seeds=(11,),
        heldout_limit=3,
        train_val_count=2,
        probe_count=2,
        episodic_capacity=8,
        operation_capacity=6,
        provisional_capacity=6,
        pair_eval_cap=600,
        anchors=6,
        retrieval_pool=8,
        top_k=3,
        eval_cap=2500,
    )


def diagnostic_config() -> Config:
    """Compact five-condition comparison. Not a 10,000-box lifetime."""
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["master_seed"] = int(args.seed)
        updates["seeds"] = (int(args.seed),)
    if getattr(args, "train_boxes", None) is not None:
        updates["train_boxes"] = int(args.train_boxes)
    if getattr(args, "memory_capacity", None) is not None:
        updates["operation_capacity"] = int(args.memory_capacity)
        updates["episodic_capacity"] = int(args.memory_capacity)
    if getattr(args, "top_k", None) is not None:
        updates["top_k"] = int(args.top_k)
    if getattr(args, "max_depth", None) is not None:
        updates["max_depth"] = int(args.max_depth)
    return replace(config, **updates) if updates else config
