"""Standalone script: the Expt-16 (and Expt-17..19) primitive policy run on the Expt-20 task.

Runs in its own process because Expt-16's modules share names (config, pieces, environment) with Expt-20's.
Unmodified Expt-16 code: environment.PackingEnv, primitive_choice scan window 48, area 1.0 / contact 0.2 / boundary 0.05,
undo_budget 4, physical budget 80, eval_cap 8000. Two changes, both needed to put it on the Expt-20 task:
  * inventory unlimited (Inventory(None)) instead of a per-box inventory;
  * q_min raised to 101 so it does not stop at Q >= 75 (its recorded stopping rule).
Effort A = candidates examined (Ledger primitive_evals); enum_ops = 3636 per primitive_choice call (it lists all placements).
Output: npz with one row per trial id."""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve()
E16_SRC = str(HERE.parents[3] / "Expt_16_Search_Acquired_Local_Memory" / "src")
if E16_SRC not in sys.path:
    sys.path.insert(0, E16_SRC)

import numpy as np  # noqa: E402


def trial_seed(seed: int, trial_id: int) -> int:
    return int(seed) * 1_000_000 + int(trial_id)


def run_chunk(args) -> tuple:
    seed, ids, q_min = args
    import random
    import diagnostic
    from config import Config
    from environment import PackingEnv
    from inventory import Inventory
    from pieces import ALL_PLACEMENTS
    calls = {"n": 0}
    orig = diagnostic.primitive_choice

    def counted(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)

    diagnostic.primitive_choice = counted
    config = replace(Config(), q_min=float(q_min))
    t0 = time.perf_counter()
    rows = []
    for tid in ids:
        rng = random.Random(trial_seed(seed, tid))
        env = PackingEnv(budget=config.physical, inventory=Inventory(None))
        calls["n"] = 0
        res = diagnostic.primitive_remaining(config, env, rng, set(), int(config.eval_cap))
        n_p = sum(1 for i in env.stack if i.piece_type == "P")
        att = len(env.stack) + env.undos
        rows.append((tid, env.occupied, att, len(env.stack), n_p, env.undos, env.actions_used, calls["n"] * len(ALL_PLACEMENTS), 0,
                     res["A"], {"quality": 0, "eval_cap": 1, "no_progress": 2}.get(res["termination"], 3)))
    return rows, time.perf_counter() - t0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--trials", type=int, default=10_000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--q-min", type=float, default=101.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    chunk = 200
    jobs = [(args.seed, list(range(s, min(s + chunk, args.trials))), args.q_min) for s in range(0, args.trials, chunk)]
    t0 = time.perf_counter()
    rows, cpu = [], 0.0
    if args.workers <= 1:
        for j in jobs:
            r, c = run_chunk(j); rows += r; cpu += c
    else:
        with ProcessPoolExecutor(args.workers) as ex:
            for r, c in ex.map(run_chunk, jobs):
                rows += r; cpu += c
    rows.sort()
    arr = np.array([[r[i] for i in range(11)] for r in rows], float)
    np.savez_compressed(args.out, data=arr, cpu_seconds=cpu, wall_seconds=time.perf_counter() - t0,
                        columns=np.array(["trial_id", "S1", "attempts", "pieces", "n_P", "undos", "actions", "enum_ops", "mask_ops", "A", "termination"]))
    print(f"e16 primitive: {len(rows)} trials, cpu {cpu:.1f}s wall {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()