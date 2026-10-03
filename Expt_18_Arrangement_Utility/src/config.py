"""Expt-18: bounded utility of the Expt-17 arrangements.

Expt-17 showed that a few small arrangements recur and often fit in free space,
and that scanning every translation at every prefix is far above the 0.10 cost
bar. This run does not relax that bar and does not build a matcher. It asks
whether a predeclared sample of those legal placements has enough
quality-preserving whole-box benefit, under ideal selection inside the sample,
to justify a later retrieval experiment.

All counterfactual solves are diagnostic cost.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class Config:
    # Primitive settings and phase strings match Expt-16 and Expt-17, so a
    # prefix is the same state those trajectories reached.
    q_min: float = 75.0
    quality_loss_margin: float = 1.0
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    applicability_seed: int = 11
    applicability_phase: str = "expt16-applicability"
    early_below: int = 34
    middle_below: int = 67
    # Frozen dictionary from the Expt-17 diagnostic. Not re-extracted.
    frozen_sha256: str = "b02cd72c92b7a9f00b8660b7a54633a1cb93844c62d20ff98ae0812ea62c904c"
    # Sample rule, fixed before any commit is scored.
    # Boxes: a stride through the manifest, not the boxes with the most fits.
    fresh_stride: int = 5
    fresh_sample_boxes: int = 12
    family_stride: int = 10
    family_sample_boxes: int = 6
    # Patterns: every frozen pattern supported by at least this many inventories,
    # plus this many patterns supported by exactly two. The two-inventory draw
    # uses sample_seed and does not look at fit counts.
    high_support: int = 3
    support_two_sample: int = 8
    sample_seed: int = 18
    stages: tuple[str, ...] = ("early", "middle")
    # A quality-preserving saving smaller than one primitive scan does not
    # count as enough benefit to justify building a matcher.
    min_saving: int = 48
    # "A few" versus "across independent boxes", same count the line already
    # used for recurrence.
    min_benefit_boxes: int = 3
    min_patterns_broad: int = 3
    # If more than this fraction of sampled placements fail to reproduce the
    # primitive trajectory, the comparison is not evidence.
    max_replay_failure_fraction: float = 0.5
    manifest_set: str = "diagnostic"
    pattern_limit: int | None = None
    fresh_sample_boxes_override: int | None = None
    family_sample_boxes_override: int | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["question"] = (
            "Do the recurring arrangements from Expt-17 have enough quality-preserving "
            "whole-box benefit, on a predeclared sample of legal placements, to justify "
            "building a cheaper matcher?"
        )
        data["not_this_experiment"] = (
            "Does not relax the Expt-17 cost gate, does not deploy a matcher, and does not "
            "treat a legal fit as admission."
        )
        data["sample"] = (
            "At most one legal placement per sampled box, pattern, and stage: the earliest "
            "prefix in that occupied-cell bin, and the first fitting translation in row-major "
            "order. Late prefixes are not sampled. Savings on one trajectory are not added."
        )
        data["counterfactual"] = (
            "Same saved state (board, inventory, RNG, tabu). Commit the pattern, charging one "
            "check per piece and per cell examined, then primitive. The other branch is primitive "
            "only. Both keep search room eval_cap - prefix A. Commitment checks are added to the "
            "commit branch's effort and do not shrink that search room."
        )
        data["ideal_selection"] = (
            "Inside one box, the opportunity is the largest remaining-effort saving among "
            "candidates that stay within the quality margin and do not lose acceptability. "
            "Harmful candidates are not selected. Candidate-level averages are not the decision."
        )
        data["decision_rows"] = {
            "stop_pattern_reuse": "no sampled box, fresh or family, reaches min_saving with quality preserved",
            "narrow_retrieval": "quality-preserving benefit exists but is confined to fewer than min_benefit_boxes independent fresh boxes, or to fewer than min_patterns_broad patterns, or to one stage, or only to the family workload",
            "build_budgeted_matcher": "at least min_benefit_boxes independent fresh boxes, at least min_patterns_broad patterns, and both early and middle",
            "inconclusive_replay": "primitive replay failed on more than max_replay_failure_fraction of sampled placements",
        }
        data["diagnostic_cost"] = "Discovery checks and both counterfactual branches are diagnostic. They are not a deployable recognition cost."
        return data


def smoke_config() -> Config:
    return Config(
        manifest_set="smoke",
        fresh_sample_boxes_override=1,
        family_sample_boxes_override=1,
        pattern_limit=5,
        stages=("early",),
    )


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    return replace(config)
