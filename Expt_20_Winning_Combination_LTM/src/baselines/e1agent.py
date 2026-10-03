"""The Expt-1 'none' agent (engineered heuristic, eps 0.15, UNDO allowed, 100-action budget) on the Expt-20 task.

Runs the unmodified mga.agent.PackingAgent with configs/default.json, mode 'none' (no STM, no LTM). Same environment class
as Expt-20. The box is the same empty 10x10 box with unlimited pieces. Final score = occupied cells when the episode ends
(action limit or full board), as in Expt-1's terminal_score.
Effort: candidate_evaluations (placements the agent scored with its hole/contact heuristic; each needs flood fills) and
3636 placement-visits per select call for its scan over the catalogue."""

from __future__ import annotations

import json
import random
from pathlib import Path

from mga.environment import PackingEnv
from mga.pieces import N_CELLS
from stronger.engine import N_ALL
from trials import trial_seed

CONFIG_PATH = Path(__file__).resolve().parents[3] / "Expt_01_10x10_Packing" / "configs" / "default.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def run_e1_trial(seed: int, trial_id: int, cfg: dict | None = None, mode: str = "none") -> dict:
    from mga.agent import PackingAgent
    cfg = cfg or load_config()
    rng = random.Random(trial_seed(seed, trial_id))
    env = PackingEnv(budget=int(cfg.get("action_budget", 100)))
    agent = PackingAgent(mode, cfg)
    agent.begin_box()
    calls = 0
    while not env.terminal:
        occ_before, mask_before = env.occupied, env.mask
        action = agent.select(env, rng)
        calls += 1
        result = env.step(action)
        if result.accepted and action.kind.value == "PLACE":
            agent.after_step(env, action, occ_before, mask_before)
    agent.end_box(env)
    empty = sum(1 for row in env.cells for cell in row if cell is None)
    s1 = N_CELLS - empty
    assert s1 == env.occupied
    att = env.placements_count
    n_p = sum(1 for i in env.stack if i.piece_type == "P")
    return {"trial_id": trial_id, "S1": s1, "attempts": att, "S2": s1 / att if att else 0.0, "n_P": n_p,
            "pieces": len(env.stack), "undos": env.undos, "actions": env.actions_used,
            "enum_ops": N_ALL * calls, "mask_ops": 0, "cand_evals": agent.candidate_evaluations,
            "n_explore_steps": 0, "n_boost_steps": 0}