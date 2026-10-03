"""Expt-4 configuration.

The objective of this experiment is not to discover a better packing heuristic.
Packing is the observable environment. The experiment asks whether repeated
information can autonomously become compressed reusable knowledge, and whether
that knowledge allows future problems to be solved with less deliberation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace


PHILOSOPHY = (
    "The objective of this experiment is not to discover a better packing heuristic. "
    "Packing is the observable environment. The experiment asks whether repeated "
    "information can autonomously become compressed reusable knowledge, and whether "
    "that knowledge allows future problems to be solved with less deliberation."
)

# Inherited so the primitive baseline uses the same placement score as Expt-3.
# These weights are a documented human prior of the fallback search. The miner
# does not use them, and it does not name or prefer any packing shape.
PRIMITIVE_SCORE_AREA = 1.0
PRIMITIVE_SCORE_CONTACT = 0.2
PRIMITIVE_SCORE_BOUNDARY = 0.05

FULL_SEEDS = (11, 22, 33, 44, 55, 66, 77, 88, 99, 111)


@dataclass(frozen=True)
class Config:
    q_min: float = 75.0
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    top_k: int = 5
    retrieval_pool: int = 16
    anchors: int = 8
    max_depth: int = 4
    min_len: int = 2
    max_len: int = 5
    min_support: int = 2
    episodic_capacity: int = 48
    operation_capacity: int = 24
    byte_cap: int = 65536
    decay: float = 0.05
    fail_penalty: float = 1.0
    storage_weight: float = 0.001
    applicability_min: float = 0.05
    max_promotions_per_episode: int = 2
    train_boxes: int = 10000
    change_at: int = 5000
    checkpoints: tuple[int, ...] = (0, 10, 30, 100, 300, 1000, 3000, 10000)
    seeds: tuple[int, ...] = FULL_SEEDS
    heldout_limit: int | None = None
    probe_count: int = 4
    master_seed: int = 11
    score_area: float = PRIMITIVE_SCORE_AREA
    score_contact: float = PRIMITIVE_SCORE_CONTACT
    score_boundary: float = PRIMITIVE_SCORE_BOUNDARY

    def to_dict(self) -> dict:
        return asdict(self)


def smoke_config() -> Config:
    return Config(
        train_boxes=12,
        change_at=6,
        checkpoints=(0, 6, 12),
        seeds=(11,),
        heldout_limit=3,
        probe_count=2,
        episodic_capacity=8,
        operation_capacity=6,
        anchors=8,
        retrieval_pool=8,
        top_k=3,
    )


def pilot_config() -> Config:
    return Config(
        train_boxes=100,
        change_at=50,
        checkpoints=(0, 10, 30, 100),
        seeds=(11, 22, 33),
        heldout_limit=6,
        probe_count=3,
        episodic_capacity=24,
        operation_capacity=16,
    )


def full_config() -> Config:
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
