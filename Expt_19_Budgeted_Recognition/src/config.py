"""Expt-19: budgeted recognition. Commitment is disabled.

The access rule is an engineered mechanism, frozen before fresh evaluation.
Anchor count and the empty-board origin are not chosen to recover any
Expt-18 pattern or box. The absolute budget is 0.10 of mean primitive effort
on the development manifests. The agent does not see the eval box's primitive cost.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Config:
    q_min: float = 75.0
    quality_loss_margin: float = 1.0
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    seed: int = 11
    early_below: int = 34
    middle_below: int = 67
    min_saving: int = 48
    frozen_sha256: str = "b02cd72c92b7a9f00b8660b7a54633a1cb93844c62d20ff98ae0812ea62c904c"
    # Reference sample for diagnostic counterfactuals. Same rule as Expt-18.
    # Not a list of patterns that won there.
    high_support: int = 3
    support_two_sample: int = 8
    sample_seed: int = 18
    pattern_limit: int | None = None
    # Access rule. Small, deterministic, and not fit to held-out outcomes.
    max_anchors: int = 4
    empty_anchor: tuple[int, int] = (0, 0)
    cheap_fraction: float = 0.10
    min_state_recall: float = 0.50
    min_retention: float = 0.50
    min_boxes_with_reference: int = 3
    development_limit: int | None = None
    eval_limit: int | None = None
    manifest_set: str = "diagnostic"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["empty_anchor"] = list(self.empty_anchor)
        data["question"] = (
            "Can a frozen budgeted matcher expose quality-preserving placement actions "
            "from the 58 arrangements, within an absolute recognition budget, without "
            "using future outcomes to choose where to look?"
        )
        data["commitment"] = "disabled"
        data["budget_rule"] = (
            "absolute per-box limit = floor(cheap_fraction * mean primitive effort on the "
            "development manifests). Eval boxes do not enter that mean."
        )
        data["evaluation_gate"] = "mean recognition cost / mean primitive effort on validation fresh < 0.10"
        data["anchors"] = (
            f"If the board is empty, the only anchor is {list(self.empty_anchor)}. "
            f"Otherwise the first {self.max_anchors} free cells in row-major order that touch "
            "an occupied cell. The scan stops when that many anchors are found."
        )
        data["recall"] = (
            "A hit is the same pattern and the same origin as a sampled reference action "
            "that preserves quality and saves at least min_saving. Another placement of the "
            "same pattern is not a hit. The reference is not an exhaustive list of useful actions."
        )
        data["decision_rows"] = {
            "retains_opportunities": "cheap on validation fresh, and the sampled reference opportunities are recalled and retained",
            "misses_opportunities": "cheap, but recall or retention is below the floor; diagnose anchor coverage before changing the library",
            "recognition_expensive": "validation-fresh recognition cost is not under 0.10 of primitive effort; stop this access design",
        }
        data["not_this_experiment"] = (
            "No commitment policy. No learned embedding. No claim of cheaper autonomous solving. "
            "Rejected consultations are not yet repaid because nothing is committed."
        )
        return data


def smoke_config() -> Config:
    return Config(
        manifest_set="smoke",
        development_limit=2,
        eval_limit=1,
        pattern_limit=4,
    )


def diagnostic_config() -> Config:
    return Config()
