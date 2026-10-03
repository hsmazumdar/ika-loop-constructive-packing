"""Full organic learner for variable packing problems (Expt 23, E1-E4): afterstate-value MLP with Monte Carlo returns, fast net,
STM, sleep (prioritised replay + EMA slow net), dreams, concept library, meta-controller (reused unchanged from Expt 22d). No hand rule.
Flags: sleep / dream / concepts / meta; `random=True` generates experience (incl. dream continuations) uniformly from the action set
instead of from the value net (the E1 contrast); learning machinery identical in both modes. D = 257 (256 encoding + concept column)."""
from __future__ import annotations

import numpy as np

import polyomino as PM
from env import Env
from encode import Encoder, D as D0
from net import MLP
from meta import Meta

D = D0 + 1
C_CON = D0
MU, SD = 0.7, 0.15
CELLS_UNIT = SD * 100.0
H0 = dict(tau=2.0, eps=0.10, lr=1e-3, lam=1.0, dream=0.5, sleep_every=200, stm=1000, steps=40, batch=256)


class MetaCfg:
    grow_min_box = 10 ** 9
    grow_every_epochs = 10 ** 9


class Library:
    def __init__(self, cap=6000, min_n=25, z=3.0, min_abs=0.3):
        self.stats, self.keys, self.val = {}, np.empty(0, np.int64), np.empty(0, np.float32)
        self.cap, self.min_n, self.z, self.min_abs = cap, min_n, z, min_abs

    def lookup(self, keys):
        if self.keys.size == 0:
            return np.zeros(len(keys), np.float32)
        pos = np.minimum(np.searchsorted(self.keys, keys), self.keys.size - 1)
        return np.where(self.keys[pos] == keys, self.val[pos], 0.0).astype(np.float32)

    def observe(self, keys, resid):
        uk, inv = np.unique(keys, return_inverse=True)
        n, s, q = np.bincount(inv), np.bincount(inv, weights=resid), np.bincount(inv, weights=resid * resid)
        for k, a, b, c in zip(uk.tolist(), n.tolist(), s.tolist(), q.tolist()):
            e = self.stats.get(k)
            if e is None:
                self.stats[k] = [a, b, c]
            else:
                e[0] += a; e[1] += b; e[2] += c

    def promote(self):
        if not self.stats:
            return 0
        ks = np.fromiter(self.stats.keys(), np.int64, len(self.stats)); arr = np.array(list(self.stats.values()), float)
        n, s, q = arr[:, 0], arr[:, 1], arr[:, 2]
        mean = s / np.maximum(n, 1); var = np.maximum(q / np.maximum(n, 1) - mean ** 2, 1e-6)
        z = np.abs(mean) / np.sqrt(var / np.maximum(n, 1))
        idx = np.flatnonzero((n >= self.min_n) & (z >= self.z) & (np.abs(mean) >= self.min_abs))
        if idx.size > self.cap:
            idx = idx[np.argsort(-(np.abs(mean[idx]) * np.sqrt(n[idx])))[: self.cap]]
        order = idx[np.argsort(ks[idx])]
        self.keys, self.val = ks[order], np.clip(mean[order] / 3.0, -2, 2).astype(np.float32)
        return int(self.keys.size)


class FEncoder(Encoder):
    """Encoder + catalogue-independent concept keys (pool piece id, orientation rank, ring occupancy bits)."""
    def __init__(self, env: Env):
        super().__init__(env)
        base = []
        for pidx in env.prob.catalogue:
            for r in range(len(PM.orientations(PM.POOL[pidx]))):
                base.append(pidx * 4 + r)
        self.kbase = np.array(base, np.int64)
        R = env.RING.shape[1]
        self.bitw = (1 << np.arange(R, dtype=np.int64))

    def keys(self, s, cand):
        occr = s.occ[self.env.RING[cand]] & self.env.RING_OK[cand]
        return (self.kbase[self.env.ORIENT[cand]] << 24) + (occr * self.bitw).sum(axis=1)

    def features(self, s, cand):
        X = super().features(s, cand)
        return np.concatenate([X, np.zeros((len(cand), 1), np.float32)], axis=1)


class Episode:
    __slots__ = ("X", "keys", "prob", "placed", "y", "w")

    def __init__(self, X, keys, prob, placed, y, w=None):
        self.X, self.keys, self.prob, self.placed, self.y = X, keys, prob, placed, y
        self.w = np.ones(len(X), np.float32) if w is None else w


class FullAgent:
    def __init__(self, seed: int, hidden=128, sleep=True, dream=True, concepts=True, meta=True, random=False):
        self.rng = np.random.default_rng(seed * 104729 + 7)
        self.fast = MLP(D, hidden, self.rng)
        self.slow = self.fast.copy()
        self.h = dict(H0)
        self.flags = dict(sleep=sleep, dream=dream, concepts=concepts, meta=meta, growth=False)
        self.random = random
        self.lib = Library()
        self.meta = Meta(MetaCfg, meta)
        self.buf, self.prio, self.new, self.sleeps = [], [], 0, 0
        self.sleep_stats = []
        self._envs: dict = {}

    def memory_net(self):
        return self.slow if self.flags["sleep"] else self.fast

    def get_env(self, prob):
        k = prob.spec_hash() + str(prob.budget)
        if k not in self._envs:
            if len(self._envs) > 48:
                self._envs.pop(next(iter(self._envs)))
            e = Env(prob); self._envs[k] = (e, FEncoder(e))
        return self._envs[k]

    def _fill(self, X, keys):
        if self.flags["concepts"] and self.lib.keys.size:
            X[:, C_CON] = self.lib.lookup(keys)
        return X

    def play(self, env, enc, rng, tau, eps, natural, net=None, record=True, prefix=None, random=None):
        net = net or self.fast
        random = self.random if random is None else random
        s = env.new_state()
        if prefix is not None:
            for i in prefix:
                env.place(s, int(i))
        Xs, Ks, pl = [], [], []
        while True:
            cand, _ = env.candidates(s, natural)
            if cand.size == 0:
                break
            X = enc.features(s, cand); keys = enc.keys(s, cand)
            n = cand.size
            if random:
                j = int(rng.integers(n)); need_v = False
            else:
                self._fill(X, keys)
                v = net.forward(X)
                if n == 1:
                    j = 0
                elif tau <= 0.02:
                    j = int(np.argmax(v))
                else:
                    z = (v - v.max()) * (CELLS_UNIT / max(tau, 1e-3)); p = np.exp(z); p /= p.sum()
                    if eps > 0:
                        p = (1 - eps) * p + eps / n
                    j = min(int(np.searchsorted(np.cumsum(p), rng.random() * 0.999999999)), n - 1)
            if random and record:
                pass
            env.place(s, int(cand[j]))
            if record:
                Xs.append(X[j]); Ks.append(int(keys[j])); pl.append(int(cand[j]))
        if not record or not Xs:
            return s, None
        y = (s.filled / max(env.free_cells, 1) - MU) / SD
        return s, Episode(np.array(Xs, np.float32), np.array(Ks, np.int64), env.prob, (list(prefix) if prefix is not None else []) + pl, y)

    # ---- learning ----
    def online_step(self, ep):
        X = ep.X.copy(); self._fill(X, ep.keys)
        self.fast.step(X, np.full(len(X), ep.y, np.float32), ep.w, self.h["lr"] * 0.5)

    def remember(self, ep):
        self.buf.append(ep); self.prio.append(1.0); self.new += 1
        cap = int(self.h["stm"])
        if len(self.buf) > cap:
            d = len(self.buf) - cap; del self.buf[:d]; del self.prio[:d]

    def due(self):
        return self.flags["sleep"] and self.new >= self.h["sleep_every"]

    def _prio_sample(self, pool, n):
        if not pool or n <= 0:
            return []
        p = np.array([self.prio[i] for i in pool]) ** 0.6 + 1e-3; p /= p.sum()
        return [pool[j] for j in self.rng.choice(len(pool), min(n, len(pool)), replace=False, p=p)]

    def sleep(self):
        h = self.h
        n_new = min(self.new, len(self.buf)); self.new = 0
        ids_new = list(range(len(self.buf) - n_new, len(self.buf)))
        ids_old = self._prio_sample(list(range(0, len(self.buf) - n_new)), 150)
        dreams = []
        if self.flags["dream"] and h["dream"] > 0 and self.buf:
            for bi in self._prio_sample(list(range(len(self.buf))), int(h["dream"] * n_new)):
                src = self.buf[bi]; T = len(src.placed)
                if T < 2:
                    continue
                cut = int(self.rng.integers(1, T))
                env, enc = self.get_env(src.prob)
                _, ep = self.play(env, enc, self.rng, max(h["tau"], 0.3) * 1.5, 0.15, True, prefix=src.placed[:cut], random=self.random)
                if ep is not None:
                    ep.w[:] = 0.5; dreams.append(ep)
        eps = [self.buf[i] for i in ids_new + ids_old] + dreams
        X = np.concatenate([e.X for e in eps]); K = np.concatenate([e.keys for e in eps])
        Y = np.concatenate([np.full(len(e.X), e.y, np.float32) for e in eps]); W = np.concatenate([e.w for e in eps])
        self._fill(X, K)
        n_real_new = sum(len(self.buf[i].X) for i in ids_new); n_real_old = sum(len(self.buf[i].X) for i in ids_old)
        err0 = (self.fast.forward(X) - Y) ** 2
        l_new = float(err0[:n_real_new].mean()) if n_real_new else 0.0
        l_old = float(err0[n_real_new:n_real_new + n_real_old].mean()) if n_real_old else l_new
        if self.flags["concepts"] and n_real_new:
            Xc = X[:n_real_new].copy(); Xc[:, C_CON] = 0.0
            self.lib.observe(K[:n_real_new], CELLS_UNIT * (Y[:n_real_new] - self.fast.forward(Xc)))
        first = last = 0.0
        for st in range(int(h["steps"])):
            b = self.rng.integers(0, len(Y), min(int(h["batch"]), len(Y)))
            l = self.fast.step(X[b], Y[b], W[b], h["lr"])
            if st < 3: first += l / 3
            last = 0.8 * last + 0.2 * l if st else l
        err1 = np.abs(self.fast.forward(X) - Y)
        off = 0
        for i in ids_new + ids_old:
            n = len(self.buf[i].X); self.prio[i] = float(err1[off:off + n].mean()) + 1e-3; off += n
        for k in self.slow.p:
            self.slow.p[k] = 0.7 * self.slow.p[k] + 0.3 * self.fast.p[k]
        ncon = self.lib.promote() if (self.flags["concepts"] and self.sleeps % 5 == 0) else int(self.lib.keys.size)
        self.sleeps += 1
        st = {"loss_first": first, "loss_last": last, "l_new": l_new, "l_old": l_old, "n_dream": len(dreams), "n_concepts": ncon}
        self.sleep_stats.append(st)
        return st