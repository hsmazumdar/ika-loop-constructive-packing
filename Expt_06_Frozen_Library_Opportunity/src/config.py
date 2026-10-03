"""Expt-6 configuration. Library learner and gates are frozen."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

PHILOSOPHY = (
    "Does the existing learned library contain operations that could reduce future "
    "deliberation if they were selected well, or is there too little useful opportunity "
    "in the library itself? The oracle sees future outcomes and is not a deployable agent."
)

QUALITY_LOSS_MARGIN = 1.0
CHOOSER_COST = 1
OCCUPANCY_SCHEDULE = (0, 10, 20, 30, 40, 50, 60)
COST_CURVE = (0, 10, 25, 50, 100, 200, 400, 800)
EXPT5_LEARNING_A = 486500
EXPT5_RESULT = "Expt_05_Consult_and_Commit_Gates/results/20260929_212658_diagnostic"
CONDITIONS = ("primitive", "both_gates_frozen", "oracle_single_free", "oracle_single_scan_charged")


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
    checkpoints: tuple[int, ...] = (0, 80)
    seeds: tuple[int, ...] = (11, 22, 33)
    train_val_count: int = 4
    master_seed: int = 11
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    occupancy_schedule: tuple[int, ...] = OCCUPANCY_SCHEDULE
    max_states_per_box: int = 7
    max_candidates_per_state: int = 24
    n_boxes: int = 24
    chooser_cost: int = CHOOSER_COST
    change_at: int = 10**9

    def to_dict(self) -> dict:
        data = asdict(self)
        data["effort_saving_definition"] = "A_primitive - A_agent (positive = fewer evaluations)"
        data["a_identity"] = "A = primitive_evals + retrieval + applicability + learned_site_checks + gate_checks"
        data["remaining_budget"] = "eval_cap - prefix_primitive_A"
        data["chooser_cost"] = int(self.chooser_cost)
        data["quality_loss_margin"] = float(self.quality_loss_margin)
        data["oracle_sees_futures"] = True
        return data


def smoke_config() -> Config:
    return Config(seeds=(11,), n_boxes=4, max_states_per_box=4, max_candidates_per_state=8, occupancy_schedule=(0, 10, 20, 30))


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["seeds"] = (int(args.seed),)
        updates["master_seed"] = int(args.seed)
    if getattr(args, "n_boxes", None) is not None:
        updates["n_boxes"] = int(args.n_boxes)
    if getattr(args, "max_candidates", None) is not None:
        updates["max_candidates_per_state"] = int(args.max_candidates)
    return replace(config, **updates) if updates else config
