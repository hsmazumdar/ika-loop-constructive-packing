"""Expt-16: search-acquired local memory (bounded acquisition diagnosis)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "Were the bounded regions observed during ordinary packing fillable with the pieces available at "
    "that moment, but left unfinished by the primitive policy? Acquisition searches each recorded "
    "region offline, under a predeclared budget, without changing the store trajectory. Successful "
    "exact fillings are frozen as local entries and first tested read-only on fresh ordinary "
    "trajectories. Downstream consequences at compatible matches are measured by paired counterfactuals "
    "from the same saved state; these are diagnostic work, not information available to an agent. "
    "Partial fillings are not considered."
)


@dataclass(frozen=True)
class Config:
    q_min: float = 75.0
    quality_loss_margin: float = QUALITY_LOSS_MARGIN
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    region_min_cells: int = 8
    region_max_cells: int = 20
    # Acquisition: offline exact-cover search per recorded region, budget in candidate placements examined.
    search_budget: int = 20000
    store_seeds: tuple[int, ...] = (11, 22, 33)
    store_phase: str = "expt15-t2-store"
    store_acceptable_only: bool = True
    # Applicability (read-only) on fresh ordinary trajectories from frozen manifests.
    applicability_seed: int = 11
    applicability_phase: str = "expt16-applicability"
    # Counterfactuals: at most this many compatible entries diagnosed per matched region.
    max_entries_per_match: int = 4
    # Predeclared decision thresholds.
    few_fill_rate: float = 0.10
    min_recur_boxes: int = 3
    harm_quality_loss_rate: float = 0.10
    harm_mean_quality_delta: float = -0.25
    manifest_set: str = "diagnostic"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["search_outcomes"] = ["found", "impossible (exhaustive search, no filling)", "budget_exhausted (feasibility unknown)"]
        data["search_pruning"] = "first uncovered cell; area feasibility of remaining region against remaining piece sizes (sound)"
        data["detector"] = "Expt-15 flood fill next to each new placement, billed per free cell visited; unchanged"
        data["entry_key"] = "(translation-normalised geometry, consumed multiset); alternative placements for the same key recorded, not merged away"
        data["match_rule"] = "identical geometry and multiset available in the remaining inventory; read-only"
        data["counterfactual"] = "same saved state (board, inventory, RNG state, tabu); commit filling then primitive vs primitive only; remaining cap = eval_cap - prefix A"
        data["decision_rows"] = {
            "few_fillings": "exact fill rate < few_fill_rate, or no entries",
            "no_recurrence": "entries exist but compatible matches in fewer than min_recur_boxes fresh boxes (stop before counterfactuals if 0)",
            "commitment_harms": "quality-loss rate > harm_quality_loss_rate, or mean quality delta < harm_mean_quality_delta, or mean or median remaining-effort saving <= 0",
            "saves_and_preserves": "otherwise; next test a deployable commitment rule and acquisition payback on the validation manifests",
        }
        data["transformations"] = False
        data["hierarchy"] = False
        data["learned_gate"] = False
        data["partial_fillings"] = False
        return data


def smoke_config() -> Config:
    return Config(store_seeds=(11,), search_budget=5000, manifest_set="smoke")


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["applicability_seed"] = int(args.seed)
    return replace(config, **updates) if updates else config
