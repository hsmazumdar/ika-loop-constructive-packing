"""Expt-8C: freeze 8B models and evaluate once on unseen boxes. No new mechanism."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
EXPT7_RESULT = "Expt_07_Indexed_Retrieval/results/20260929_220030_diagnostic"
EXPT6_SNAPSHOTS = "Expt_06_Frozen_Library_Opportunity/snapshots"
EXPT8_RESULT = "Expt_08_Action_Level_Value/results/20260929_230403_diagnostic"
EXPT8B_RESULT = "Expt_08B_Consistent_Labels/results/20260929_231956_diagnostic"
PHILOSOPHY = (
    "Expt-8B holdout was reused development, not unseen confirmation. Freeze those models "
    "and decision rules, then evaluate once on genuinely new boxes. Do not retune thresholds."
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
    n_boxes: int = 50
    n_fit_boxes: int = 0
    k_shortlist: int = 2
    consult_budget: int = 25
    quality_admit: float = 0.5
    chooser_cost: int = 1
    change_at: int = 10**9
    placements_per_op: int = 1
    ranker_steps: int = 80
    severe_loss_scale: float = 400.0
    quality_fail_weight: float = 8.0
    fit_fraction: float = 0.75
    placement_candidates: tuple[int, ...] = (1,)
    n_fresh: int = 0
    collect_counterfactuals: bool = True
    replay_pair_cap: bool = False
    n_holdout: int = 0
    generate_seed: int = 2026092990

    def to_dict(self) -> dict:
        data = asdict(self)
        data["no_library_retrain"] = True
        data["no_threshold_retune"] = True
        data["consultation_identity"] = (
            "consultation_cost = retrieval + applicability + learned_site_checks + index_probes + ranking"
        )
        data["remaining_saving_sign"] = "A_skip - A_commit (positive = fewer remaining primitive evaluations)"
        data["label_remaining_budget"] = "eval_cap - prefix_primitive_A"
        data["label_excludes_site_checks"] = True
        data["admission_bound"] = "pred_saving > anchors (8); this is not subtracted from the label"
        data["net_after_check"] = "remaining_saving - examined (site checks only; not total deployment savings)"
        data["net_after_decision_costs"] = (
            "accepted remaining_saving minus examined, feature_checks, and all consulted-state "
            "index_probes + compat_checks + ranking, including rejected consultations"
        )
        data["primary_saving_fit"] = "unweighted (frozen from Expt-8B development fit)"
        data["cache_key"] = "(state_fingerprint, action_key, remaining_cap)"
        return data


def smoke_config() -> Config:
    return Config(
        seeds=(11,),
        n_boxes=4,
        occupancy_schedule=(0, 10, 20, 30),
        max_states_per_box=4,
        placements_per_op=1,
        n_fresh=0,
        ranker_steps=20,
        generate_seed=2026092991,
    )


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["seeds"] = (int(args.seed),)
    if getattr(args, "n-boxes", None) is not None or getattr(args, "n_boxes", None) is not None:
        n = getattr(args, "n_boxes", None)
        if n is not None:
            updates["n_boxes"] = int(n)
    return replace(config, **updates) if updates else config
