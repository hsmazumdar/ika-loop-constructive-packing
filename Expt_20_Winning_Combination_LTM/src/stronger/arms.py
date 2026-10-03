"""Process-pool execution of arms. Trials are independent and seeded per trial id, so results do not depend on the worker count,
except the online variants, which are sequential by construction and run as one task each."""

from __future__ import annotations

import sys
import time
from pathlib import Path

_CTX = None
_PATHS: list[str] = []


def init_worker(paths: list[str], ltms: dict, tables: dict, n_all_guard: int) -> None:
    for p in paths:
        if p not in sys.path:
            sys.path.insert(0, p)
    from stronger.policies import Context
    global _CTX
    _CTX = Context(ltms, tables)


def _wrap_plain(t: dict, n_all: int) -> dict:
    n_p = sum(1 for p in t["placements"] if p[0] == "P")
    return {"trial_id": t["trial_id"], "S1": t["S1"], "S2": t["S2"], "attempts": t["attempts"], "n_P": n_p,
            "enum_ops": n_all * (t["attempts"] + 1), "mask_ops": 0, "cand_evals": 0, "n_explore_steps": 0, "n_boost_steps": 0}


def run_chunk(job: tuple) -> tuple:
    """job = (kind, seed, ids, payload). Returns (kind_key, results, seconds)."""
    kind, seed, ids, payload = job
    from stronger.engine import N_ALL
    from stronger.policies import Spec, run_online_arm, run_trial
    t0 = time.perf_counter()
    if kind == "control":
        from trials import run_trial as plain
        out = [_wrap_plain(plain(seed, i), N_ALL) for i in ids]
    elif kind == "control_full":
        from trials import run_trial as plain
        out = [plain(seed, i) for i in ids]
    elif kind == "ref":
        from phases.policy import Policy, run_guided_trial
        pol = Policy.from_ltm(_CTX.ltms["S2_frozen"], epsilon=0.1)
        out = [_wrap_plain(run_guided_trial(seed, i, pol), N_ALL) for i in ids]
    elif kind == "spec":
        spec = Spec(**payload)
        out = run_online_arm(seed, ids, spec, _CTX) if spec.type_mode == "online" else [run_trial(seed, i, spec, _CTX) for i in ids]
    else:
        raise ValueError(kind)
    return kind, out, time.perf_counter() - t0


def jobs_for(kind: str, seed: int, n: int, payload=None, chunk: int = 250, online: bool = False) -> list[tuple]:
    if online:
        return [(kind, seed, list(range(n)), payload)]
    return [(kind, seed, list(range(s, min(s + chunk, n))), payload) for s in range(0, n, chunk)]