"""Expt-22a parameters. Hyperparameters in H0 are the *initial* values; the meta-controller may change them online."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

H0 = dict(tau=2.0, eps=0.10, lr=1e-3, lam=1.0, dream=0.5, sleep_every=200, stm=1000, steps=40, batch=256)


@dataclass
class Cfg:
    budget: int = 14
    hidden: int = 64
    tau0: float = 2.0
    tau_min: float = 0.35
    eps0: float = 0.10
    eps_min: float = 0.01
    anneal_boxes: int = 15_000  # only for the fixed (non-meta) schedule
    tau_eval: float = 0.25
    online_lr_mult: float = 0.5
    slow_beta: float = 0.3
    dream_tau_mult: float = 1.5
    dream_eps: float = 0.15
    dream_w: float = 0.5
    n_old: int = 150
    per_alpha: float = 0.6
    epoch: int = 1000
    probe_boxes: int = 80
    probe_tau: float = 0.25
    # concept library
    con_min_n: int = 25
    con_z: float = 3.0
    con_min_abs: float = 0.3
    con_cap: int = 6000
    # capacity growth test
    hidden_steps: tuple = (64, 128, 256)
    grow_every_epochs: int = 4
    grow_min_box: int = 8000
    grow_ratio: float = 0.93
    grow_test_steps: int = 150
    # held-out evaluation
    eval_boxes: int = 2000
    eval_seed: int = 7_700_000
    n_boxes: int = 40_000
    checkpoints: tuple = (0, 500, 1000, 2000, 3000, 5000, 7500, 10000, 15000, 20000, 24000, 28000, 32000, 36000, 40000, 44000, 48000, 52000, 56000, 60000)
    transfer_budgets: tuple = (12, 14, 16, 20, 40)
    transfer_boxes: int = 1000
    h0: dict = field(default_factory=lambda: dict(H0))

    def as_dict(self) -> dict:
        return asdict(self)


_ALL = dict(sched=False, learn=True, online=True, sleep=True, dream=True, meta=True, concepts=True, growth=True, lam_fixed=None, h={})

VARIANTS = {
    "full": dict(_ALL),
    "no_meta": dict(_ALL, meta=False, growth=False, sched=True),       # fixed hyperparameters + fixed V21-style anneal
    "no_sleep": dict(_ALL, sleep=False, dream=False),
    "no_dream": dict(_ALL, dream=False),
    "no_concepts": dict(_ALL, concepts=False),
    "no_growth": dict(_ALL, growth=False),
    # Expt-22d: fixed hyperparameters, but tau/eps annealed (linearly) to the floors the meta-controller itself reaches
    # at 32k boxes in Expt-22c (mean tau 0.2507, eps 0.0077) over 32k boxes -> tests whether the late surge is only the floors.
    "no_meta_matched_floor": dict(_ALL, meta=False, growth=False, sched=True, sched_tau_min=0.25, sched_eps_min=0.0077, sched_boxes=32000),
    "td095": dict(_ALL, lam_fixed=0.95, h=dict(lam=0.95)),  # bootstrapped lambda-return targets (V22a setting)
    "frozen": dict(_ALL, learn=False, meta=False, growth=False),
    # robustness: deliberately poor initial hyperparameters
    "badinit_meta": dict(_ALL, h=dict(lr=8e-3, tau=0.3, eps=0.0, lam=0.5, dream=0.0, sleep_every=800, stm=300)),
    "badinit_fixed": dict(_ALL, meta=False, growth=False, h=dict(lr=8e-3, tau=0.3, eps=0.0, lam=0.5, dream=0.0, sleep_every=800, stm=300)),
}
