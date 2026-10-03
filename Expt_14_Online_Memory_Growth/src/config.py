"""Expt-14: online exact-memory growth with chronological evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "Does accumulating exact continuations online, box by box, create useful future matches that "
    "the frozen table lacked? Each box is solved with only the memory available before it; eligible "
    "continuations are stored afterwards and insertion is billed. Retrieval is exact state identity. "
    "Transformation matching is excluded from the primary comparison."
)


@dataclass(frozen=True)
class Config:
    q_min: float = 75.0
    quality_loss_margin: float = QUALITY_LOSS_MARGIN
    scan: int = 48
    physical: int = 80
    undo_budget: int = 4
    eval_cap: int = 8000
    store_seeds: tuple[int, ...] = (11, 22, 33)
    stream_seeds: tuple[int, ...] = (11, 22, 33, 44, 55, 66)
    score_area: float = 1.0
    score_contact: float = 0.2
    score_boundary: float = 0.05
    n_store_independent: int = 8
    n_families: int = 4
    n_store_per_family: int = 2
    n_per_stream: int = 30
    generate_seed: int = 2026093019
    growth_substantial_factor: float = 1.5

    @property
    def n_streams(self) -> int:
        return len(self.stream_seeds)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["n_streams"] = self.n_streams
        data["conditions"] = ["primitive", "frozen_exact", "growing_exact"]
        data["retrieval"] = "exact (mask, inventory) identity"
        data["transformation_matching_in_primary"] = False
        data["first_write_wins"] = True
        data["per_stream_memory_copy"] = True
        data["constructed_prefix_on_eval"] = False
        data["future_tasks_chosen_by_memory"] = False
        data["insertion_billing"] = "1 per stack state probed + 1 per key written, charged to the box that inserts"
        data["A_identity"] = "primitive_evals + lookup + validation + insertion"
        return data


def smoke_config() -> Config:
    return Config(
        store_seeds=(11,),
        stream_seeds=(11,),
        n_store_independent=2,
        n_families=1,
        n_store_per_family=1,
        n_per_stream=4,
        generate_seed=2026093018,
    )


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["stream_seeds"] = (int(args.seed),)
    if getattr(args, "n_boxes", None) is not None:
        updates["n_per_stream"] = max(2, int(args.n_boxes))
    return replace(config, **updates) if updates else config
