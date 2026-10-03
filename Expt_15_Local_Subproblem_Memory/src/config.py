"""Expt-15: local subproblem memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

QUALITY_LOSS_MARGIN = 1.0
PHILOSOPHY = (
    "Can experience preserve a useful solution fragment while discarding details of the surrounding "
    "problem that are irrelevant to its reuse? A local entry records how to fill a bounded free region "
    "with a specified piece multiset; it matches when the region geometry is identical and the pieces "
    "are available, while the rest of the board and the unused inventory may differ. Test 1 supplies "
    "independent regions and budgets as an experimental aid. Test 2 uses ordinary packing with an "
    "engineered, billed region detector; it is not learned decomposition."
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
    region_node_cap: int = 20000
    # Test 1
    t1_seeds: tuple[int, ...] = (11, 22, 33)
    t1_n_library: int = 12
    t1_k_min: int = 2
    t1_k_max: int = 4
    t1_n_embed_per_region: int = 2
    t1_n_control: int = 12
    # Test 2
    store_seeds: tuple[int, ...] = (11, 22, 33)
    stream_seeds: tuple[int, ...] = (11, 22, 33, 44)
    n_store_independent: int = 8
    n_families: int = 4
    n_store_per_family: int = 2
    n_per_stream: int = 15
    generate_seed: int = 2026093021

    @property
    def n_streams(self) -> int:
        return len(self.stream_seeds)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["n_streams"] = self.n_streams
        data["t1_conditions"] = ["primitive_whole", "exact_whole", "primitive_decomposed", "local_decomposed"]
        data["t2_conditions"] = ["primitive", "exact_whole", "local"]
        data["region_supplied_in_test1"] = "experimental aid, not learned decomposition"
        data["region_detector_in_test2"] = "engineered flood fill next to the last placement; billed per free cell visited"
        data["local_match_rule"] = "identical translation-normalised geometry and multiset available; first stored available entry"
        data["transformations"] = False
        data["hierarchy"] = False
        data["learned_gate"] = False
        data["local_memory_frozen_during_eval"] = True
        data["A_identity"] = "primitive_evals (incl. region search) + detection + lookup + availability + validation + insertion"
        return data


def smoke_config() -> Config:
    return Config(
        t1_seeds=(11,),
        t1_n_library=2,
        t1_n_embed_per_region=1,
        t1_n_control=1,
        store_seeds=(11,),
        stream_seeds=(11,),
        n_store_independent=2,
        n_families=1,
        n_store_per_family=1,
        n_per_stream=3,
        generate_seed=2026093020,
    )


def diagnostic_config() -> Config:
    return Config()


def apply_overrides(config: Config, args) -> Config:
    updates = {}
    if getattr(args, "seed", None) is not None:
        updates["stream_seeds"] = (int(args.seed),)
        updates["t1_seeds"] = (int(args.seed),)
    if getattr(args, "n_boxes", None) is not None:
        updates["n_per_stream"] = max(2, int(args.n_boxes))
    return replace(config, **updates) if updates else config
