"""Expt-17: read-only census of small arrangements from successful packings.

Translation normalisation is an engineered representation choice. It is not an
autonomously discovered equivalence. No rotation or reflection is applied.
A pattern is not required to have a rectangular outline, and groups are not
ordered by piece size. Nothing in this experiment places a stored group.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class Config:
    # Primitive settings copied from the Expt-16 diagnostic so store and fresh
    # trajectories are the same solves. Phase strings are likewise unchanged.
    q_min: float = 75.0
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    store_seeds: tuple[int, ...] = (11, 22, 33)
    store_phase: str = "expt15-t2-store"
    applicability_seed: int = 11
    applicability_phase: str = "expt16-applicability"
    # Pattern size and extraction work, fixed before any count is seen.
    min_pieces: int = 2
    max_pieces: int = 3
    max_checks_per_box: int = 4000
    # A pattern recurs across problems only when at least this many distinct
    # training inventories support it. Repeats inside one trajectory count once.
    # Two seeds of the same inventory are one inventory.
    min_inventories: int = 2
    # Occupied-cell thirds of the 10x10 board. Census bins, not a learned stage.
    early_below: int = 34
    middle_below: int = 67
    # Matching cost below this fraction of the same box's primitive effort is
    # the predeclared bar for "cheap enough to justify a later commit test".
    cheap_fraction: float = 0.10
    min_fit_boxes: int = 3
    manifest_set: str = "diagnostic"
    store_limit: int | None = None
    fresh_limit: int | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["representation"] = "translation-normalised relative anchors and piece counts; engineered, not discovered"
        data["rotations_or_reflections"] = False
        data["rectangular_outline_required"] = False
        data["large_pieces_first"] = False
        data["commitment"] = False
        data["stage_bins"] = {
            "early": f"occupied cells < {self.early_below}",
            "middle": f"{self.early_below} <= occupied cells < {self.middle_below}",
            "late": f"occupied cells >= {self.middle_below}",
        }
        data["question"] = (
            "Do successful packing trajectories contain small arrangements that recur across "
            "different problems and can be recognized cheaply enough to justify testing their reuse?"
        )
        return data


def smoke_config() -> Config:
    return Config(store_seeds=(11,), manifest_set="smoke", store_limit=2, fresh_limit=2)


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["applicability_seed"] = int(args.seed)
    return replace(config, **updates) if updates else config
