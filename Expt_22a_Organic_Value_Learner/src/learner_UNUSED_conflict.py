"""Organic afterstate-value learner: MLP V(s'), 1-step lookahead softmax, SARSA(lambda)/lambda-returns,
STM -> sleep (prioritised replay + dreams), meta-controller, shadow-widen growth.

Policy scores are learned values of afterstates — no hand-written packing heuristic in the policy.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field

import numpy as np

import engine as E
import feat
from config import Cfg
from net import MLP


@dataclass
class Transition:
    X: np.ndarray          # afterstate features (D,)
    r: float               # cells gained this step
    td_err: float = 0.0    # |delta| for prioritised replay


@dataclass
class Episode:
    transitions: list
    s1: int
    placed: list
    priority: float = 1.0


@dataclass
class MetaState:
    tau: float
    eps: float
    lr: float
    lam: float
    dream_ratio: float
    sleep_every: int
    stm_boxes: int
    residual_ema: float = 1.0
    probe_s1: float = 67.0
    train_s1_ema: float = 67.0


class Agent:
    """Learned afterstate value + organic parameter adaptation."""

    def __init__(self, cfg: Cfg, rng: np.random.Generator, use_meta: bool = True, growth: str = "shadow") -> None:
        self.cfg = cfg
        self.rng = rng
        self.use_meta = use_meta
        self.growth_mode = growth
        self.net = MLP(cfg.din, cfg.h0, rng, b_out=float(cfg.budget * 0.55))
        self.stage = 0
        self.sleeps = 0
        self.widens = 0
        self.meta = MetaState(
            tau=cfg.tau0, eps=cfg.eps0, lr=cfg.lr0, lam=cfg.lam0,
            dream_ratio=cfg.dream_ratio, sleep_every=cfg.sleep_every, stm_boxes=cfg.stm_boxes,
        )
        self._boxes_seen = 0
        if growth == "upfront":
            while self.net.h + cfg.h_grow <= cfg.max_h:
                self.net = self.net.widen(self.net.h + cfg.h_grow, rng)
                self.widens += 1
                self.stage += 1

    # ---- schedule / meta ---------------------------------------------------------------------------------------
    def anneal(self, i: int) -> None:
        """Base anneal of tau/eps/lr; meta may have already nudged the floors."""
        cfg = self.cfg
        f = min(1.0, i / max(cfg.anneal_boxes, 1))
        if not self.use_meta:
            self.meta.tau = cfg.tau0 + (cfg.tau_min - cfg.tau0) * f
            self.meta.eps = cfg.eps0 + (cfg.eps_min - cfg.eps0) * f
            self.meta.lr = cfg.lr0 + (cfg.lr_min - cfg.lr0) * f
        else:
            # approach floors but keep meta's relative offsets
            base_tau = cfg.tau0 + (cfg.tau_min - cfg.tau0) * f
            base_eps = cfg.eps0 + (cfg.eps_min - cfg.eps0) * f
            base_lr = cfg.lr0 + (cfg.lr_min - cfg.lr0) * f
            # blend gently toward annealed base
            self.meta.tau = 0.7 * self.meta.tau + 0.3 * base_tau
            self.meta.eps = 0.7 * self.meta.eps + 0.3 * base_eps
            self.meta.lr = 0.7 * self.meta.lr + 0.3 * base_lr

    def meta_update(self, train_s1_window: float, probe_s1: float, residual: float) -> dict:
        """Adapt tau/eps/lr/lam/dream/sleep/STM from prequential residual + probe."""
        m = self.meta
        m.residual_ema = 0.9 * m.residual_ema + 0.1 * residual
        m.probe_s1 = probe_s1
        m.train_s1_ema = 0.9 * m.train_s1_ema + 0.1 * train_s1_window
        gap = m.train_s1_ema - probe_s1  # positive => overfitting / high train noise
        changes = {}
        if not self.use_meta:
            return changes
        # high residual => learn faster / explore more / dream more
        if m.residual_ema > 2.5:
            m.lr = min(self.cfg.lr0 * 1.5, m.lr * 1.15)
            m.eps = min(0.25, m.eps * 1.1)
            m.dream_ratio = min(1.0, m.dream_ratio * 1.1)
            m.lam = min(0.95, m.lam + 0.02)
            changes["high_residual"] = True
        elif m.residual_ema < 0.8:
            m.lr = max(self.cfg.lr_min, m.lr * 0.92)
            m.eps = max(self.cfg.eps_min, m.eps * 0.95)
            m.lam = max(0.5, m.lam - 0.02)
            changes["low_residual"] = True
        # train >> probe => more sleep / more STM / cooler tau
        if gap > 3.0:
            m.sleep_every = max(100, int(m.sleep_every * 0.85))
            m.stm_boxes = min(2000, int(m.stm_boxes * 1.15))
            m.tau = max(self.cfg.tau_min, m.tau * 0.95)
            m.dream_ratio = min(1.0, m.dream_ratio * 1.1)
            changes["overfit_gap"] = gap
        elif gap < -1.0:
            # probe better than noisy train => more exploitation
            m.tau = max(self.cfg.tau_min, m.tau * 0.97)
            m.eps = max(self.cfg.eps_min, m.eps * 0.97)
            changes["probe_lead"] = gap
        # stall: probe flat-ish and residual not huge => nudge exploration
        return changes

    # ---- acting ------------------------------------------------------------------------------------------------
    def values(self, X: np.ndarray) -> np.ndarray:
        return self.net.forward(X)

    def choose(self, scores: np.ndarray, tau: float, eps: float) -> int:
        n = scores.size
        if n == 1:
            return 0
        if eps >= 1.0 - 1e-12:
            return int(self.rng.integers(n))
        z = scores / max(tau, 1e-6)
        z -= z.max()
        p = np.exp(z)
        p /= p.sum()
        if eps > 0:
            p = (1.0 - eps) * p + eps / n
        return int(np.searchsorted(np.cumsum(p), self.rng.random() * 0.999999999))

    def play_box(self, tau: float | None = None, eps: float | None = None, prefix: list | None = None,
                 learnable: bool = True) -> Episode:
        """Fill one box with 1-step lookahead over natural afterstates. Optionally record transitions."""
        cfg = self.cfg
        tau = self.meta.tau if tau is None else tau
        eps = self.meta.eps if eps is None else eps
        box = E.Box(budget=cfg.budget)
        for i in prefix or ():
            box.place(i)
        transitions: list[Transition] = []
        while True:
            out = feat.step_features(box, cfg.budget)
            if out is None:
                break
            cand, X, _sig = out
            if learnable and self._boxes_seen > 0:
                scores = self.values(X)
            else:
                # frozen / cold start: uniform among natural (zeros => choose falls to uniform via any())
                scores = np.zeros(cand.size, dtype=np.float32)
            j = self.choose(scores, tau, eps)
            i = int(cand[j])
            area = float(E.AREA[i])
            box.place(i)
            if learnable:
                transitions.append(Transition(X=X[j].copy(), r=area))
        ep = Episode(transitions=transitions, s1=box.s1, placed=list(box.placed))
        return ep

    # ---- learning ----------------------------------------------------------------------------------------------
    def _lambda_returns(self, transitions: list[Transition], lam: float, gamma: float) -> np.ndarray:
        """Backward view of lambda-returns with bootstrap at end = 0 (episode terminal).
        Reward = cells gained; return ≈ remaining cells-to-end ≈ related to final S1 contribution.
        """
        T = len(transitions)
        if T == 0:
            return np.zeros(0, dtype=np.float32)
        r = np.array([t.r for t in transitions], dtype=np.float64)
        # bootstrap values of afterstates (for SARSA-style: use V of next afterstate)
        X = np.stack([t.X for t in transitions], axis=0)
        V = self.net.forward(X).astype(np.float64)
        G = np.zeros(T, dtype=np.float64)
        g = 0.0
        for t in range(T - 1, -1, -1):
            if t == T - 1:
                # terminal afterstate: remaining return is 0 beyond final reward already in r? 
                # After last place, episode ends; target for last afterstate = 0 future cells, but we want
                # V(afterstate) ≈ expected *remaining* cells after this placement.
                # Remaining after placing step t = sum(r[t+1:]) 
                # So MC target for afterstate t is sum(r[t+1:]). Equivalently store reward as next-step.
                # Cleaner: redefine target as cells-from-now including current? Use:
                #   y_t = r_t + gamma * ((1-lam)*V_{t+1} + lam*y_{t+1}) with V_T=0, but then y includes r_t
                # We want V(s'_t) ≈ E[sum_{k>t} r_k]. So shift: target uses future only.
                g = 0.0
            else:
                # SARSA(lambda): g = r_{t+1} + gamma*((1-lam)*V(s'_{t+1}) + lam*g)  wait
                # Standard afterstate: G_t = sum_{k=0}^{T-t-1} gamma^k r_{t+1+k}
                boot = V[t + 1]
                g = r[t + 1] + gamma * ((1.0 - lam) * boot + lam * g)
            G[t] = g
        # Also add a direct MC signal blended: remaining cells after each step
        rem = np.cumsum(r[::-1])[::-1] - r  # sum of future r
        # blend lambda-bootstrap G with pure MC remaining (stabilises early)
        y = 0.5 * G + 0.5 * rem
        # TD errors for prioritisation
        for t in range(T):
            transitions[t].td_err = float(abs(y[t] - V[t]))
        return y.astype(np.float32)

    def learn_episode(self, ep: Episode, weight: float = 1.0) -> float:
        if not ep.transitions:
            return 0.0
        y = self._lambda_returns(ep.transitions, self.meta.lam, self.cfg.gamma)
        X = np.stack([t.X for t in ep.transitions], axis=0)
        w = np.full(len(y), weight, dtype=np.float32)
        # prioritise high |td| steps inside the episode
        pri = np.array([max(t.td_err, 0.05) for t in ep.transitions], dtype=np.float32)
        pri = pri ** self.cfg.prioritise_temp
        w = w * (pri / (pri.mean() + 1e-9))
        mse = 0.0
        for _ in range(self.cfg.train_epochs_online):
            mse = self.net.step(X, y, w, self.meta.lr)
        ep.priority = float(np.mean([t.td_err for t in ep.transitions]) + 0.1)
        return mse

    def sleep(self, stm: list[Episode], n_new: int, dream: bool) -> dict:
        cfg = self.cfg
        m = self.meta
        new = stm[-n_new:] if n_new else []
        old = stm[:-n_new] if len(stm) > n_new else list(stm)
        # prioritised rehearsal from old STM
        reh: list[Episode] = []
        if old:
            pr = np.array([ep.priority for ep in old], dtype=np.float64)
            pr = pr / (pr.sum() + 1e-12)
            k = min(cfg.rehearse, len(old))
            idx = self.rng.choice(len(old), size=k, replace=False, p=pr)
            reh = [old[j] for j in idx]
        mse_acc, n_steps = 0.0, 0
        for ep in new:
            mse_acc += self.learn_episode(ep, 1.0)
            n_steps += 1
        for ep in reh:
            mse_acc += self.learn_episode(ep, 0.5)
            n_steps += 1
        n_dream = 0
        if dream and stm:
            n_d = int(m.dream_ratio * max(n_new, 1))
            for _ in range(n_d):
                ep0 = stm[int(self.rng.integers(len(stm)))]
                if not ep0.placed:
                    continue
                cut = int(self.rng.integers(0, len(ep0.placed)))
                # dream from prefix with hotter exploration
                dep = self.play_box(tau=m.tau * cfg.dream_tau_mult, eps=cfg.dream_eps,
                                    prefix=ep0.placed[:cut], learnable=True)
                # only train on suffix transitions
                if cut < len(dep.transitions) or dep.transitions:
                    # play_box with prefix still records transitions only for new placements
                    mse_acc += self.learn_episode(dep, cfg.dream_w)
                    n_steps += 1
                    n_dream += 1
        # extra sleep epochs over new+reh
        for _ in range(max(0, cfg.sleep_epochs - 1)):
            for ep in new:
                self.learn_episode(ep, 0.7)
            for ep in reh[: max(1, len(reh) // 2)]:
                self.learn_episode(ep, 0.35)
        self.sleeps += 1
        return {"dreams": n_dream, "replayed": len(new) + len(reh), "mse": mse_acc / max(n_steps, 1)}

    # ---- growth ------------------------------------------------------------------------------------------------
    def shadow_should_grow(self, stm: list[Episode]) -> tuple[bool, float, float]:
        """Train a widened shadow copy briefly; grow if its residual is clearly better."""
        cfg = self.cfg
        if self.net.h + cfg.h_grow > cfg.max_h or len(stm) < 40:
            return False, 0.0, 0.0
        # build a small supervised batch from recent STM using current targets
        xs, ys = [], []
        for ep in stm[-min(200, len(stm)):]:
            if not ep.transitions:
                continue
            y = self._lambda_returns(ep.transitions, self.meta.lam, cfg.gamma)
            for t, yi in zip(ep.transitions, y):
                xs.append(t.X)
                ys.append(yi)
        if len(xs) < 80:
            return False, 0.0, 0.0
        X = np.stack(xs, axis=0)
        y = np.asarray(ys, dtype=np.float32)
        # hold out last 20%
        n = X.shape[0]
        n_tr = int(n * 0.8)
        idx = self.rng.permutation(n)
        tr, te = idx[:n_tr], idx[n_tr:]
        w = np.ones(n_tr, dtype=np.float32)

        def mse_of(net, Xe, ye):
            pred = net.forward(Xe)
            return float(np.mean((pred - ye) ** 2))

        base = self.net.copy()
        shadow = self.net.widen(self.net.h + cfg.h_grow, self.rng)
        for _ in range(cfg.shadow_epochs):
            base.step(X[tr], y[tr], w, self.meta.lr)
            shadow.step(X[tr], y[tr], w, self.meta.lr)
        m0 = mse_of(base, X[te], y[te])
        m1 = mse_of(shadow, X[te], y[te])
        rel = (m0 - m1) / max(m0, 1e-6)
        return rel >= cfg.shadow_improve, rel, m0

    def maybe_grow(self, stm: list[Episode]) -> dict | None:
        if self.growth_mode != "shadow":
            return None
        ok, rel, m0 = self.shadow_should_grow(stm)
        if not ok:
            return {"grew": False, "rel_improve": rel, "base_mse": m0}
        self.net = self.net.widen(self.net.h + self.cfg.h_grow, self.rng)
        self.widens += 1
        self.stage += 1
        # reconsolidate: a few passes over STM
        for ep in stm[-min(len(stm), self.meta.stm_boxes):]:
            self.learn_episode(ep, 0.8)
        return {"grew": True, "rel_improve": rel, "base_mse": m0, "h": self.net.h, "stage": self.stage}

    # ---- bookkeeping -------------------------------------------------------------------------------------------
    def stats(self) -> dict:
        return {"h": self.net.h, "stage": self.stage, "sleeps": self.sleeps, "widens": self.widens,
                "tau": self.meta.tau, "eps": self.meta.eps, "lr": self.meta.lr, "lam": self.meta.lam,
                "dream_ratio": self.meta.dream_ratio, "sleep_every": self.meta.sleep_every,
                "stm_boxes": self.meta.stm_boxes, "residual_ema": self.meta.residual_ema,
                "entries": self.net.h}  # stand-in for memory_entries in reports

    def summary(self) -> dict:
        return {"stats": self.stats(), "meta": self.meta.__dict__.copy()}

    def dump(self, path) -> None:
        with open(path, "wb") as fh:
            pickle.dump({"cfg": self.cfg.as_dict(), "h": self.net.h, "p": self.net.p,
                         "stage": self.stage, "meta": self.meta.__dict__}, fh)


def play_box(agent: Agent | None, rng: np.random.Generator, tau: float, eps: float,
             prefix: list | None = None, budget: int | None = None, cfg: Cfg | None = None) -> E.Box:
    """Convenience: return a Box (for eval / hand-ref). If agent is None, uniform natural."""
    cfg = cfg or Cfg()
    if agent is None:
        box = E.Box(budget=budget or cfg.budget)
        for i in prefix or ():
            box.place(i)
        while True:
            out = feat.step_features(box, cfg.budget)
            if out is None:
                return box
            cand, X, _ = out
            box.place(int(cand[int(rng.integers(cand.size))]))
        return box
    # use agent policy but return Box
    old_rng = agent.rng
    agent.rng = rng
    ep = agent.play_box(tau=tau, eps=eps, prefix=prefix, learnable=True)
    agent.rng = old_rng
    box = E.Box(budget=budget or cfg.budget)
    for i in ep.placed:
        box.place(i)
    return box


def hand_box(rng: np.random.Generator, budget: int, w_area: float = 2.0) -> E.Box:
    """Reference ONLY (never used by the learner): hand-written contact/hole/area heuristic."""
    box = E.Box(budget=budget)
    while True:
        cand, f = E.natural_candidates(box, 0)
        if cand.size == 0:
            return box
        sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + w_area * E.AREA[cand] + rng.random(cand.size) * 0.5
        box.place(int(cand[int(np.argmax(sc))]))
