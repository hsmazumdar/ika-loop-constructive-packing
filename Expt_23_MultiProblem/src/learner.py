"""Afterstate-value learner (numpy MLP, Monte Carlo returns) for variable problems. Plain version = online-only ('N');
flags enable sleep (replay + EMA slow net) and dreams for the later full-learner experiments (not run on the baseline day).
Target: y = (S1/free_cells - 0.7)/0.15, so returns are comparable across problems.  Memory for evaluation: slow net if sleep else fast net."""
from __future__ import annotations

import numpy as np

from env import Env, Problem, State
from encode import Encoder, D
from net import MLP

MU, SD = 0.7, 0.15


class Episode:
    __slots__ = ("X", "prob", "placed", "y", "w")

    def __init__(self, X, prob, placed, y, w=None):
        self.X, self.prob, self.placed, self.y = X, prob, placed, y
        self.w = np.ones(len(X), np.float32) if w is None else w


class Agent:
    def __init__(self, seed: int, hidden: int = 128, sleep: bool = False, dream: bool = False, lr: float = 1e-3,
                 sleep_every: int = 200, stm: int = 1000, n_old: int = 150, steps: int = 40, batch: int = 256,
                 dream_ratio: float = 0.5, beta: float = 0.3) -> None:
        self.rng = np.random.default_rng(seed * 104729 + 7)
        self.fast = MLP(D, hidden, self.rng)
        self.slow = self.fast.copy()
        self.sleep_on, self.dream_on = sleep, dream
        self.lr, self.sleep_every, self.stm, self.n_old, self.steps, self.batch = lr, sleep_every, stm, n_old, steps, batch
        self.dream_ratio, self.beta = dream_ratio, beta
        self.buf: list[Episode] = []
        self.prio: list[float] = []
        self.new = 0

    def memory_net(self) -> MLP:
        return self.slow if self.sleep_on else self.fast

    def play(self, env: Env, enc: Encoder, rng, tau: float, eps: float, natural: bool, net: MLP | None = None, record=True,
             prefix=None):
        net = net or self.fast
        s = env.new_state()
        Xs, pl = [], []
        if prefix is not None:
            for i in prefix:
                env.place(s, i)
        while True:
            cand, _ = env.candidates(s, natural)
            if cand.size == 0:
                break
            X = enc.features(s, cand)
            v = net.forward(X)
            n = v.size
            if n == 1:
                j = 0
            elif tau <= 0.02:
                j = int(np.argmax(v))
            else:
                z = (v - v.max()) * (SD * 100.0 / max(tau, 1e-3))   # tau in S1-cells-per-100-cell-board units (as in Expt 22)
                p = np.exp(z)
                p /= p.sum()
                if eps > 0:
                    p = (1 - eps) * p + eps / n
                j = min(int(np.searchsorted(np.cumsum(p), rng.random() * 0.999999999)), n - 1)
            env.place(s, int(cand[j]))
            if record:
                Xs.append(X[j]); pl.append(int(cand[j]))
        if not record or not Xs:
            return s, None
        y = (s.filled / max(env.free_cells, 1) - MU) / SD
        return s, Episode(np.array(Xs, np.float32), env.prob, pl, y)

    def online_step(self, ep: Episode) -> None:
        y = np.full(len(ep.X), ep.y, np.float32)
        self.fast.step(ep.X, y, ep.w, self.lr * 0.5)

    def remember(self, ep: Episode) -> None:
        self.buf.append(ep); self.prio.append(1.0); self.new += 1
        if len(self.buf) > self.stm:
            d = len(self.buf) - self.stm
            del self.buf[:d]; del self.prio[:d]

    def due(self) -> bool:
        return self.sleep_on and self.new >= self.sleep_every

    def sleep(self) -> None:
        n_new = min(self.new, len(self.buf)); self.new = 0
        ids = list(range(len(self.buf) - n_new, len(self.buf)))
        old = list(range(0, len(self.buf) - n_new))
        if old:
            p = np.array([self.prio[i] for i in old]) ** 0.6 + 1e-3; p /= p.sum()
            ids += [old[j] for j in self.rng.choice(len(old), min(self.n_old, len(old)), replace=False, p=p)]
        X = np.concatenate([self.buf[i].X for i in ids]); y = np.concatenate([np.full(len(self.buf[i].X), self.buf[i].y, np.float32) for i in ids])
        w = np.ones(len(y), np.float32)
        for _ in range(self.steps):
            b = self.rng.integers(0, len(y), min(self.batch, len(y)))
            self.fast.step(X[b], y[b], w[b], self.lr)
        b_ = self.beta
        for k in self.slow.p:
            self.slow.p[k] = (1 - b_) * self.slow.p[k] + b_ * self.fast.p[k]