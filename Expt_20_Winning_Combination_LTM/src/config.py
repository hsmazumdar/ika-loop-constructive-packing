"""Expt-20 configuration. Fixed definitions, no tuning."""

from __future__ import annotations

from dataclasses import asdict, dataclass

DEFAULT_SEED = 20260930
DEFAULT_TRIALS = 10_000
TOP_FRACTION = 0.25
# A combination is flagged "winning" only if it is enriched in the top group and the
# difference is unlikely to be noise. Ranking tables are still ordered by top-group frequency.
WIN_MIN_TOP_COUNT = 25
WIN_MIN_LIFT = 1.0
WIN_MIN_Z = 1.96
DEFAULT_RANKING = "S2"   # primary/default ranking (user decision); S1 is kept as the secondary ranking
LTM_PATTERN_LIMIT = 500   # retained oriented connected patterns per size in the LTM


@dataclass(frozen=True)
class Config:
    seed: int = DEFAULT_SEED
    trials: int = DEFAULT_TRIALS
    top_fraction: float = TOP_FRACTION
    default_ranking: str = DEFAULT_RANKING
    win_min_top_count: int = WIN_MIN_TOP_COUNT
    win_min_lift: float = WIN_MIN_LIFT
    win_min_z: float = WIN_MIN_Z
    ltm_pattern_limit: int = LTM_PATTERN_LIMIT

    def as_dict(self) -> dict:
        return asdict(self)