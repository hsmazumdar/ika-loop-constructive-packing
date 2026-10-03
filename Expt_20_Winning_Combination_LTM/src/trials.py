"""Random legal box filling. One trial = one fresh 10x10 box filled until no placement is legal."""

from __future__ import annotations

import random

from mga.environment import Action, PackingEnv
from mga.pieces import N_CELLS


def trial_seed(seed: int, trial_id: int) -> int:
    """Independent, replayable per-trial seed."""
    return int(seed) * 1_000_000 + int(trial_id)


def run_trial(seed: int, trial_id: int) -> dict:
    tseed = trial_seed(seed, trial_id)
    rng = random.Random(tseed)
    env = PackingEnv()
    while not env.terminal:
        legal = env.legal_placements()
        if not legal:
            break
        env.step(Action.place_from(rng.choice(legal)))
    empty = sum(1 for row in env.cells for cell in row if cell is None)
    s1 = N_CELLS - empty
    if s1 != env.occupied:
        raise AssertionError(f"trial {trial_id}: 100-empty={s1} but env.occupied={env.occupied}")
    attempts = env.placements_count
    s2 = s1 / attempts if attempts else 0.0
    placements = [(i.piece_type, int(i.rotation), int(i.x), int(i.y)) for i in env.stack]
    return {
        "trial_id": trial_id,
        "trial_seed": tseed,
        "S1": s1,
        "empty_cells": empty,
        "attempts": attempts,
        "S2": s2,
        "invalid_attempts": env.invalid_attempts,
        "actions_used": env.actions_used,
        "termination_reason": env.termination_reason or "no_legal_placement",
        "placements": placements,
    }


def run_trials(seed: int, n: int) -> list[dict]:
    return [run_trial(seed, i) for i in range(n)]