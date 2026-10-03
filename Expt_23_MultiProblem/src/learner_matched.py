"""Compute-matched plain learner (DESIGN.md amendment A5). Same as the plain afterstate-MC learner N (guided acting, online update only,
no replay / slow net / dreams / concepts / meta) but with EXTRA online Adam steps on the SAME episode's rows, so that the number of
gradient rows (mode 'rows', arm NM) or Adam steps (mode 'steps', arm NMs) per 200 episodes equals that of the full learner F:
F per 200 episodes = 200 online steps (the episode's rows) + one sleep of 40 steps x 256 rows (batch 256, lr 1e-3).
Extra credit per episode: rows mode 40*256/200 = 51.2 rows; steps mode 40/200 = 0.2 steps. Extra steps use the online learning rate (lr*0.5)."""
from __future__ import annotations

import numpy as np

import learner as Lr

SLEEP_STEPS, SLEEP_BATCH, SLEEP_EVERY = 40, 256, 200


class MatchedAgent(Lr.Agent):
    def __init__(self, seed: int, mode: str = "rows", **kw) -> None:
        assert mode in ("rows", "steps")
        super().__init__(seed, sleep=False, dream=False, **kw)
        self.mode = mode
        self.credit = 0.0
        self.total_steps = 0
        self.total_rows = 0
        self.total_eps = 0

    def online_step(self, ep: Lr.Episode) -> None:
        y = np.full(len(ep.X), ep.y, np.float32)
        n = len(ep.X)
        self.fast.step(ep.X, y, ep.w, self.lr * 0.5)
        self.total_steps += 1; self.total_rows += n; self.total_eps += 1
        if self.mode == "rows":
            self.credit += SLEEP_STEPS * SLEEP_BATCH / SLEEP_EVERY
            while self.credit >= n:
                self.fast.step(ep.X, y, ep.w, self.lr * 0.5)
                self.credit -= n; self.total_steps += 1; self.total_rows += n
        else:
            self.credit += SLEEP_STEPS / SLEEP_EVERY
            while self.credit >= 1.0:
                self.fast.step(ep.X, y, ep.w, self.lr * 0.5)
                self.credit -= 1.0; self.total_steps += 1; self.total_rows += n