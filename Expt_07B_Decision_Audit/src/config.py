"""Expt-7B: inspect the frozen ranker. No learning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
EXPT7_RESULT = "Expt_07_Indexed_Retrieval/results/20260929_220030_diagnostic"
EXPT6_SNAPSHOTS = "Expt_06_Frozen_Library_Opportunity/snapshots"
PHILOSOPHY = (
    "Does the frozen indexed ranker ever commit, or does it only pay consultation and then copy primitive search? "
    "Counterfactual remaining-solves are diagnosis only."
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
    checkpoints: tuple[int, ...] = (0, 80)
    seeds: tuple[int, ...] = (11, 22, 33)
    train_val_count: int = 4
    master_seed: int = 11
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    occupancy_schedule: tuple[int, ...] = (0, 10, 20, 30, 40, 50, 60)
    max_states_per_box: int = 7
    max_candidates_per_state: int = 24
    n_boxes: int = 16
    k_shortlist: int = 2
    consult_budget: int = 25
    quality_admit: float = 0.5
    chooser_cost: int = 1
    change_at: int = 10**9
    collect_counterfactuals: bool = True

    def to_dict(self) -> dict:
        data = asdict(self)
        data["consultation_identity"] = (
            "consultation_cost = retrieval + applicability + learned_site_checks + index_probes + ranking"
        )
        data["no_retrain"] = True
        return data


def smoke_config() -> Config:
    return Config(
        seeds=(11,),
        n_boxes=4,
        occupancy_schedule=(0, 10, 20, 30),
        max_states_per_box=4,
        max_candidates_per_state=8,
        collect_counterfactuals=False,
    )


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["seeds"] = (int(args.seed),)
    if getattr(args, "n_boxes", None) is not None:
        updates["n_boxes"] = int(args.n_boxes)
    return replace(config, **updates) if updates else config
