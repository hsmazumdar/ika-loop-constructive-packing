"""Generic neural baselines for Expt 23 (REFERENCE LEARNERS, torch, CPU): DQN and PPO on the same 256-d afterstate encoding as the
afterstate-MC learner. No hand rule, no sleep/dream/concepts. See DESIGN.md amendment A2."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from encode import D

torch.set_num_threads(1)
SD = 0.15


def mlp(din, h=128, out=1):
    return nn.Sequential(nn.Linear(din, 256), nn.ReLU(), nn.Linear(256, h), nn.ReLU(), nn.Linear(h, h), nn.ReLU(), nn.Linear(h, out))


def rollout(env, enc, score, select, rng, natural):
    """Plays one episode. score(X)->np value/logit vector; select(v, rng)->index. Returns (state, steps) with steps = list of (X, j, v)."""
    s = env.new_state()
    steps = []
    while True:
        cand, _ = env.candidates(s, natural)
        if cand.size == 0:
            break
        X = enc.features(s, cand)
        v = score(X)
        j = 0 if v.size == 1 else select(v, rng)
        env.place(s, int(cand[j]))
        steps.append((X, j, v))
    return s, steps


def softmax_select(tau, eps):
    def sel(v, rng):
        n = v.size
        if tau <= 0.02:
            return int(np.argmax(v))
        z = (v - v.max()) * (SD * 100.0 / max(tau, 1e-3))
        p = np.exp(z); p /= p.sum()
        if eps > 0:
            p = (1 - eps) * p + eps / n
        return min(int(np.searchsorted(np.cumsum(p), rng.random() * 0.999999999)), n - 1)
    return sel


def sample_select(v, rng):  # PPO: sample from softmax(logits)
    p = np.exp(v - v.max()); p /= p.sum()
    return min(int(np.searchsorted(np.cumsum(p), rng.random() * 0.999999999)), v.size - 1)


def greedy_select(v, rng):
    return int(np.argmax(v))


class DQN:
    K = 32

    def __init__(self, seed, cap=6000, lr=5e-4, updates=4, batch=64, sync=500, warm=500):
        torch.manual_seed(seed)
        self.q, self.tq = mlp(D), mlp(D)
        self.tq.load_state_dict(self.q.state_dict())
        self.opt = torch.optim.Adam(self.q.parameters(), lr=lr)
        self.cap, self.updates, self.batch, self.sync, self.warm = cap, updates, batch, sync, warm
        self.x = np.zeros((cap, D), np.float32)
        self.nx = np.zeros((cap, self.K, D), np.float16)
        self.nm = np.zeros((cap, self.K), bool)
        self.term = np.zeros(cap, bool)
        self.y = np.zeros(cap, np.float32)
        self.n = 0; self.ptr = 0; self.eps_done = 0
        self.rng = np.random.default_rng(seed * 104729 + 7)

    def score(self, X):
        with torch.no_grad():
            return self.q(torch.from_numpy(X))[:, 0].numpy()

    def _store(self, x, nx, nm, term, y):
        i = self.ptr
        self.x[i] = x; self.nx[i] = nx; self.nm[i] = nm; self.term[i] = term; self.y[i] = y
        self.ptr = (i + 1) % self.cap; self.n = min(self.n + 1, self.cap)

    def observe(self, steps, ynorm):
        T = len(steps)
        for t in range(T):
            X, j, v = steps[t]
            if t == T - 1:
                self._store(X[j], np.zeros((self.K, D)), np.zeros(self.K, bool), True, ynorm)
            else:
                Xn, _, vn = steps[t + 1]
                m = Xn.shape[0]
                if m > self.K:
                    top = np.argsort(-vn)[:24]
                    rest = np.setdiff1d(np.arange(m), top)
                    pick = np.concatenate([top, self.rng.choice(rest, self.K - 24, replace=False)])
                else:
                    pick = np.arange(m)
                nx = np.zeros((self.K, D), np.float32); nm = np.zeros(self.K, bool)
                nx[:len(pick)] = Xn[pick]; nm[:len(pick)] = True
                self._store(X[j], nx, nm, False, 0.0)
        self.eps_done += 1
        if self.n >= self.warm:
            for _ in range(self.updates):
                self._update()
        if self.eps_done % self.sync == 0:
            self.tq.load_state_dict(self.q.state_dict())

    def _update(self):
        b = self.rng.integers(0, self.n, self.batch)
        x = torch.from_numpy(self.x[b])
        nx = torch.from_numpy(self.nx[b].astype(np.float32)); nm = torch.from_numpy(self.nm[b])
        with torch.no_grad():
            qn = self.tq(nx.reshape(-1, D)).reshape(self.batch, self.K)
            qn = qn.masked_fill(~nm, -1e9).max(dim=1).values
            tgt = torch.where(torch.from_numpy(self.term[b]), torch.from_numpy(self.y[b]), qn)
        loss = nn.functional.smooth_l1_loss(self.q(x)[:, 0], tgt)
        self.opt.zero_grad(); loss.backward()
        nn.utils.clip_grad_norm_(self.q.parameters(), 5.0)
        self.opt.step()


class PPO:
    """PPO with a candidate-scoring policy (segment softmax over each step's candidate set, no padding). Terminal-only reward."""
    def __init__(self, seed, lr=3e-4, per_update=16, epochs=2, clip=0.2, ent=0.01, mb=64):
        torch.manual_seed(seed)
        self.pi, self.vf = mlp(D), mlp(D)
        self.opt = torch.optim.Adam(list(self.pi.parameters()) + list(self.vf.parameters()), lr=lr)
        self.per_update, self.epochs, self.clip, self.ent, self.mb = per_update, epochs, clip, ent, mb
        self.buf = []
        self.n_ep = 0
        self.rng = np.random.default_rng(seed * 104729 + 7)

    def score(self, X):
        with torch.no_grad():
            return self.pi(torch.from_numpy(X))[:, 0].numpy()

    def observe(self, steps, ynorm):
        for X, j, v in steps:
            lp = v - v.max(); lp = lp - np.log(np.exp(lp).sum())
            self.buf.append((X, j, float(lp[j]), ynorm))
        self.n_ep += 1
        if self.n_ep % self.per_update == 0:
            self._update(); self.buf = []

    def _update(self):
        N = len(self.buf)
        Y = torch.tensor([b[3] for b in self.buf], dtype=torch.float32)
        LP = torch.tensor([b[2] for b in self.buf], dtype=torch.float32)
        J = np.array([b[1] for b in self.buf])
        mean_x = torch.from_numpy(np.stack([b[0].mean(axis=0) for b in self.buf]))
        with torch.no_grad():
            adv = Y - self.vf(mean_x)[:, 0]
            adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        for _ in range(self.epochs):
            perm = self.rng.permutation(N)
            for s in range(0, N, self.mb):
                ids = perm[s:s + self.mb]
                B = len(ids)
                sizes = np.array([self.buf[i][0].shape[0] for i in ids])
                Xc = torch.from_numpy(np.concatenate([self.buf[i][0] for i in ids]))
                seg = torch.from_numpy(np.repeat(np.arange(B), sizes))
                off = np.concatenate([[0], np.cumsum(sizes)[:-1]])
                logit = self.pi(Xc)[:, 0]
                mx = torch.full((B,), -1e30).scatter_reduce(0, seg, logit, "amax", include_self=True)
                e = torch.exp(logit - mx[seg])
                z = torch.zeros(B).index_add(0, seg, e)
                logz = torch.log(z) + mx
                chosen = torch.from_numpy(off + J[ids])
                lp_new = logit[chosen] - logz
                p = e / z[seg]
                ent = -torch.zeros(B).index_add(0, seg, p * (logit - logz[seg])).mean()
                it = torch.from_numpy(ids)
                ratio = torch.exp(lp_new - LP[it])
                a = adv[it]
                l_pi = -torch.min(ratio * a, torch.clamp(ratio, 1 - self.clip, 1 + self.clip) * a).mean()
                l_v = ((self.vf(mean_x[it])[:, 0] - Y[it]) ** 2).mean()
                loss = l_pi + 0.5 * l_v - self.ent * ent
                self.opt.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(list(self.pi.parameters()) + list(self.vf.parameters()), 5.0)
                self.opt.step()
