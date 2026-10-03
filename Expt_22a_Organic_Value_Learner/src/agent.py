"""Value-learning agent: afterstate value MLP, lambda-return targets, prioritised sleep, dreams, slow LTM, concept library."""

from __future__ import annotations

import numpy as np

import engine as E
import feat as F
from config import Cfg
from net import MLP

SC_MU, SC_SD = 70.0, 10.0  # value scaling: net output o -> S1 = 70 + 10 o


class Episode:
    __slots__ = ("X", "keys", "placed", "s1", "v", "w")

    def __init__(self, X, keys, placed, s1, v, w=None):
        self.X, self.keys, self.placed, self.s1, self.v = X, keys, placed, int(s1), v
        self.w = np.ones(len(keys), np.float32) if w is None else w


class Library:
    """Concept library: promoted local arrangements (oriented piece + ring occupancy) with a learned value residual."""

    def __init__(self) -> None:
        self.stats: dict[int, list] = {}
        self.keys = np.empty(0, np.int64)
        self.val = np.empty(0, np.float32)

    def lookup(self, keys: np.ndarray) -> np.ndarray:
        if self.keys.size == 0:
            return np.zeros(len(keys), np.float32)
        pos = np.minimum(np.searchsorted(self.keys, keys), self.keys.size - 1)
        hit = self.keys[pos] == keys
        return np.where(hit, self.val[pos], 0.0).astype(np.float32)

    def observe(self, keys: np.ndarray, resid: np.ndarray) -> None:
        uk, inv = np.unique(keys, return_inverse=True)
        n = np.bincount(inv)
        s = np.bincount(inv, weights=resid)
        q = np.bincount(inv, weights=resid * resid)
        st = self.stats
        for k, a, b, c in zip(uk.tolist(), n.tolist(), s.tolist(), q.tolist()):
            e = st.get(k)
            if e is None:
                st[k] = [a, b, c]
            else:
                e[0] += a; e[1] += b; e[2] += c

    def promote(self, cfg: Cfg) -> int:
        ks = np.fromiter(self.stats.keys(), np.int64, len(self.stats))
        arr = np.array(list(self.stats.values()), dtype=float)
        if arr.size == 0:
            return 0
        n, s, q = arr[:, 0], arr[:, 1], arr[:, 2]
        mean = s / np.maximum(n, 1)
        var = np.maximum(q / np.maximum(n, 1) - mean ** 2, 1e-6)
        z = np.abs(mean) / np.sqrt(var / np.maximum(n, 1))
        ok = (n >= cfg.con_min_n) & (z >= cfg.con_z) & (np.abs(mean) >= cfg.con_min_abs)
        idx = np.flatnonzero(ok)
        if idx.size > cfg.con_cap:
            idx = idx[np.argsort(-(np.abs(mean[idx]) * np.sqrt(n[idx])))[: cfg.con_cap]]
        order = idx[np.argsort(ks[idx])]
        self.keys = ks[order]
        self.val = np.clip(mean[order] / 3.0, -2, 2).astype(np.float32)
        return int(self.keys.size)


class Agent:
    def __init__(self, cfg: Cfg, flags: dict, seed: int, hidden: int | None = None) -> None:
        self.cfg, self.flags = cfg, flags
        self.h = dict(cfg.h0)
        self.h.update(flags.get("h", {}))
        if flags.get("lam_fixed") is not None:
            self.h["lam"] = flags["lam_fixed"]
        self.rng = np.random.default_rng(seed * 104729 + 7)
        self.hidden = hidden or cfg.hidden
        self.fast = MLP(F.D, self.hidden, self.rng)
        self.slow = self.fast.copy()
        self.lib = Library()
        self.stm: list[Episode] = []
        self.prio: list[float] = []
        self.new_since_sleep = 0
        self.sleeps = 0
        self.train_steps_done = 0
        self.last_stats: dict = {}

    # ---- acting ----------------------------------------------------------------------------------------------
    def value(self, net: MLP, X: np.ndarray) -> np.ndarray:
        return SC_MU + SC_SD * net.forward(X)

    def play(self, rng: np.random.Generator, tau: float, eps: float, budget: int, prefix=None, net: MLP | None = None,
             record: bool = True, ctx: Episode | None = None):
        """Play one box with softmax(value/tau) over natural placements (mixed with eps uniform)."""
        net = net or self.fast
        use_con = self.flags.get("concepts", True)
        box = E.Box(budget=budget)
        Xs, Ks, Vs = [], [], []
        if prefix is not None:
            for i in prefix:
                box.place(i)
            Xs = [x for x in ctx.X[: len(prefix)]]
            Ks = list(ctx.keys[: len(prefix)])
            Vs = list(ctx.v[: len(prefix)])
        while True:
            r = F.step_features(box, budget)
            if r is None:
                break
            cand, X, sig = r
            if use_con and self.lib.keys.size:
                X[:, F.C_CON] = self.lib.lookup(sig)
            v = self.value(net, X)
            n = v.size
            if n == 1:
                j = 0
            elif tau <= 0.05:
                j = int(np.argmax(v))
            else:
                z = (v - v.max()) / tau
                p = np.exp(z)
                p /= p.sum()
                if eps > 0:
                    p = (1 - eps) * p + eps / n
                j = int(np.searchsorted(np.cumsum(p), rng.random() * 0.999999999))
                j = min(j, n - 1)
            box.place(int(cand[j]))
            if record:
                Xs.append(X[j]); Ks.append(int(sig[j])); Vs.append(float(v[j]))
        if not record:
            return box, None
        if not Xs:
            return box, None
        ep = Episode(np.array(Xs, np.float32), np.array(Ks, np.int64), list(box.placed), box.s1, np.array(Vs, np.float32))
        return box, ep

    # ---- learning --------------------------------------------------------------------------------------------
    def _pack(self, eps: list[Episode]):
        N = len(eps)
        Tm = max(len(e.keys) for e in eps)
        X = np.zeros((N, Tm, F.D), np.float32)
        K = np.zeros((N, Tm), np.int64)
        M = np.zeros((N, Tm), bool)
        W = np.zeros((N, Tm), np.float32)
        L = np.zeros(N, np.int64)
        fin = np.zeros(N)
        for i, e in enumerate(eps):
            t = len(e.keys)
            X[i, :t], K[i, :t], M[i, :t], W[i, :t], L[i], fin[i] = e.X, e.keys, True, e.w, t, e.s1
        if self.flags.get("concepts", True) and self.lib.keys.size:
            X[..., F.C_CON] = self.lib.lookup(K.ravel()).reshape(K.shape) * M
        else:
            X[..., F.C_CON] = 0.0
        return X, K, M, W, L, fin

    def _targets(self, X, M, L, fin, lam):
        N, Tm, _ = X.shape
        V = ((self.slow.forward(X.reshape(-1, F.D)).reshape(N, Tm)) )
        fin_s = (fin - SC_MU) / SC_SD
        G = np.zeros((N, Tm))
        nxt = np.zeros(N)
        for t in range(Tm - 1, -1, -1):
            last = (L - 1 == t)
            g = np.where(last, fin_s, (1 - lam) * (V[:, t + 1] if t + 1 < Tm else 0.0) + lam * nxt)
            g = np.where(t < L, g, 0.0)
            G[:, t] = g
            nxt = np.where(t < L, g, nxt)
        return G, V

    def _train(self, X, M, W, G, steps: int, lr: float, batch: int, net: MLP | None = None, rng=None):
        net = net or self.fast
        rng = rng or self.rng
        idx = np.flatnonzero((M & (W > 0)).ravel())
        if idx.size == 0:
            return 0.0, 0.0
        Xf, Gf, Wf = X.reshape(-1, F.D)[idx], G.ravel()[idx], W.ravel()[idx]
        first = last = 0.0
        for s in range(steps):
            b = rng.integers(0, idx.size, min(batch, idx.size)) if idx.size > batch else np.arange(idx.size)
            l = net.step(Xf[b], Gf[b].astype(np.float32), Wf[b], lr)
            if s < 3:
                first += l / 3
            last = 0.8 * last + 0.2 * l if s else l
        return first, last

    def online_step(self, ep: Episode) -> None:
        X, K, M, W, L, fin = self._pack([ep])
        G, _ = self._targets(X, M, L, fin, self.h["lam"])
        self._train(X, M, W, G, 1, self.h["lr"] * self.cfg.online_lr_mult, 64)

    def remember(self, ep: Episode) -> None:
        self.stm.append(ep)
        self.prio.append(1.0)
        self.new_since_sleep += 1
        cap = int(self.h["stm"])
        if len(self.stm) > cap:
            d = len(self.stm) - cap
            del self.stm[:d]
            del self.prio[:d]

    def _sample_prio(self, pool: list[int], n: int) -> list[int]:
        if not pool or n <= 0:
            return []
        p = np.array([self.prio[i] for i in pool]) ** self.cfg.per_alpha + 1e-3
        p /= p.sum()
        return [pool[j] for j in self.rng.choice(len(pool), min(n, len(pool)), replace=False, p=p)]

    def sleep(self, dream_on: bool, budget: int) -> dict:
        cfg, h = self.cfg, self.h
        n_new = min(self.new_since_sleep, len(self.stm))
        self.new_since_sleep = 0
        ids_new = list(range(len(self.stm) - n_new, len(self.stm)))
        ids_old = self._sample_prio(list(range(0, len(self.stm) - n_new)), cfg.n_old)
        dreams: list[Episode] = []
        if dream_on and h["dream"] > 0:
            base = self._sample_prio(list(range(len(self.stm))), int(h["dream"] * n_new))
            for bi in base:
                src = self.stm[bi]
                T = len(src.keys)
                if T < 2:
                    continue
                cut = int(self.rng.integers(1, T))
                _, ep = self.play(self.rng, max(h["tau"], 0.3) * cfg.dream_tau_mult, cfg.dream_eps, budget,
                                  prefix=src.placed[:cut], ctx=src)
                if ep is not None:
                    ep.w[:cut] = 0.0
                    ep.w[cut:] = cfg.dream_w
                    dreams.append(ep)
        eps = [self.stm[i] for i in ids_new] + [self.stm[i] for i in ids_old] + dreams
        X, K, M, W, L, fin = self._pack(eps)
        G, _ = self._targets(X, M, L, fin, h["lam"])
        N, Tm = M.shape
        # diagnostics before training: replay loss on new vs old episodes (catastrophic-forgetting / staleness probe)
        Vf = self.fast.forward(X.reshape(-1, F.D)).reshape(N, Tm)
        err0 = (Vf - G) ** 2 * M
        nn, no = len(ids_new), len(ids_old)
        l_new = float(err0[:nn].sum() / max(M[:nn].sum(), 1))
        l_old = float(err0[nn:nn + no].sum() / max(M[nn:nn + no].sum(), 1)) if no else l_new
        # concept residuals of the real new episodes, measured against the concept-free prediction
        if self.flags.get("concepts", True) and nn:
            Xc = X[:nn].copy()
            Xc[..., F.C_CON] = 0.0
            V0 = self.fast.forward(Xc.reshape(-1, F.D)).reshape(nn, Tm)
            m = M[:nn]
            self.lib.observe(K[:nn][m], (SC_SD * (G[:nn] - V0))[m])
        first, last = self._train(X, M, W, G, int(h["steps"] * h["sleep_every"] / 200.0 if False else h["steps"]), h["lr"], int(h["batch"]))
        Vf2 = self.fast.forward(X.reshape(-1, F.D)).reshape(N, Tm)
        td = (np.abs(Vf2 - G) * M).sum(1) / np.maximum(L, 1)
        for j, i in enumerate(ids_new + ids_old):
            self.prio[i] = float(td[j]) + 1e-3
        b = cfg.slow_beta
        for k in self.slow.p:
            self.slow.p[k] = (1 - b) * self.slow.p[k] + b * self.fast.p[k]
        ncon = self.lib.promote(cfg) if (self.flags.get("concepts", True) and self.sleeps % 5 == 0) else len(self.lib.keys)
        self.sleeps += 1
        self.last_stats = {"loss_first": first, "loss_last": last, "l_new": l_new, "l_old": l_old, "n_dream": len(dreams),
                           "n_concepts": ncon}
        return self.last_stats

    # ---- capacity diagnostic ---------------------------------------------------------------------------------
    def capacity_test(self) -> dict:
        """Shadow test: is model capacity the bottleneck? Compare a same-width control and a function-preserving widened
        copy, trained identically for the same extra steps on the same replay data; validate on held-out episodes."""
        cfg, h = self.cfg, self.h
        if len(self.stm) < 400 or self.hidden >= cfg.hidden_steps[-1]:
            return {"tested": False}
        ids = self._sample_prio(list(range(len(self.stm))), 600)
        eps = [self.stm[i] for i in ids]
        X, K, M, W, L, fin = self._pack(eps)
        G, _ = self._targets(X, M, L, fin, h["lam"])
        ntr = int(0.8 * len(eps))
        new_h = cfg.hidden_steps[cfg.hidden_steps.index(self.hidden) + 1]
        rs = np.random.default_rng(int(self.rng.integers(1 << 30)))
        ctrl, wide = self.fast.copy(), self.fast.widen(new_h, rs)
        for net in (ctrl, wide):
            r2 = np.random.default_rng(123)
            self._train(X[:ntr], M[:ntr], W[:ntr], G[:ntr], cfg.grow_test_steps, h["lr"], int(h["batch"]), net=net, rng=r2)

        def val(net):
            V = net.forward(X[ntr:].reshape(-1, F.D)).reshape(M[ntr:].shape)
            return float((((V - G[ntr:]) ** 2) * M[ntr:]).sum() / M[ntr:].sum())

        vc, vw = val(ctrl), val(wide)
        grow = vw < cfg.grow_ratio * vc
        out = {"tested": True, "val_ctrl": vc, "val_wide": vw, "ratio": vw / vc, "from": self.hidden, "to": new_h, "grow": grow}
        if grow:
            self.fast = wide
            self.slow = self.slow.widen(new_h, rs)
            self.hidden = new_h
        return out