"""Expt-21 parameters. Every number that shapes the experiment lives here and is written into manifest.json."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

BUDGET = 14  # difficulty handicap: at most 14 pieces per box (calibrated so uniform natural placing scores S1 ~ 67)


@dataclass
class Cfg:
    budget: int = BUDGET
    # exploration (annealed by real boxes seen, then held at the floor)
    tau0: float = 2.0
    tau_min: float = 0.7
    eps0: float = 0.10
    eps_min: float = 0.02
    anneal_boxes: int = 15_000
    tau_eval: float = 0.3  # held-out evaluation: near-greedy softmax, no epsilon
    # memory
    sleep_every: int = 200
    stm_boxes: int = 1000
    decay: float = 0.98  # LTM counts forget by this factor at every sleep
    shrink_k: float = 2.0
    epochs: int = 2
    dream_ratio: float = 0.5  # dream rollouts per real box since the last sleep
    dream_tau_mult: float = 1.5
    dream_eps: float = 0.20
    prune_n: float = 0.3
    prune_w: float = 0.05
    prune_occupancy: float = 0.85
    dream_w: float = 0.5  # weight of a dreamed experience relative to a real one
    bl_rate: float = 0.01  # running per-step baseline
    # table capacities (log2 slots) at stage 0 and their growth
    bits: dict = field(default_factory=lambda: {"type": 8, "pair": 10, "trip": 12, "A": 13, "S1": 14, "S2": 15})
    # growth stages: (name, feature added, extra capacity bits for all tables, STM multiplier, dream multiplier)
    stages: tuple = (
        ("stage0 type+context(A)", ("type", "A"), 0, 1.0, 1.0),
        ("G1 pair combos", ("pair",), 0, 1.0, 1.0),
        ("G2 3x3 context", ("S1",), 1, 1.0, 1.0),
        ("G3 triple combos + 2x STM", ("trip",), 1, 2.0, 1.0),
        ("G4 5x5 context + 2x dreams", ("S2",), 1, 2.0, 2.0),
        ("G5 capacity + 4x STM", (), 1, 4.0, 2.0),
    )
    # saturation detector
    check_every: int = 2000
    sat_window: int = 6000
    sat_delta: float = 0.30  # saturated when the upper bound (z=sat_z) of the gain between two windows is below this
    max_stage_boxes: int = 40_000  # forced growth if a stage never saturates
    sat_z: float = 1.645
    rehearse: int = 200  # old STM episodes replayed per sleep (at half weight)
    stop_after_flat_stages: int = 2
    min_boxes: int = 60_000
    max_boxes: int = 150_000
    # held-out evaluation
    eval_boxes: int = 2000
    eval_seed: int = 7_700_000
    checkpoints: tuple = (0, 500, 1000, 2000, 5000, 10000, 20000, 30000, 40000, 50000, 60000, 80000, 100000, 125000, 150000)

    def as_dict(self) -> dict:
        return asdict(self)


VARIANTS = {
    # name: (learn, sleep, dream, growth)   growth in {"sat", "none", "upfront"}
    "full": (True, True, True, "sat"),
    "no_sleep": (True, False, False, "sat"),
    "sleep_no_dream": (True, True, False, "sat"),
    "no_growth": (True, True, True, "none"),
    "all_upfront": (True, True, True, "upfront"),
    "frozen": (False, False, False, "none"),
}