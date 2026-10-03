"""Small numpy MLP (2 hidden ReLU layers) with Adam, function-preserving widening."""

from __future__ import annotations

import numpy as np


class MLP:
    def __init__(self, din: int, h: int, rng: np.random.Generator, b_out: float = 0.0) -> None:
        self.din, self.h = din, h
        s1, s2 = np.sqrt(2.0 / din), np.sqrt(2.0 / h)
        self.p = {"W1": (rng.standard_normal((din, h)) * s1).astype(np.float32), "b1": np.zeros(h, np.float32),
                  "W2": (rng.standard_normal((h, h)) * s2).astype(np.float32), "b2": np.zeros(h, np.float32),
                  "W3": (rng.standard_normal((h, 1)) * 0.01).astype(np.float32), "b3": np.full(1, b_out, np.float32)}
        self._adam_reset()

    def _adam_reset(self) -> None:
        self.m = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.p.items()}
        self.t = 0

    def forward(self, X: np.ndarray, cache: bool = False):
        p = self.p
        z1 = X @ p["W1"] + p["b1"]
        a1 = np.maximum(z1, 0)
        z2 = a1 @ p["W2"] + p["b2"]
        a2 = np.maximum(z2, 0)
        out = (a2 @ p["W3"])[:, 0] + p["b3"][0]
        return (out, (X, z1, a1, z2, a2)) if cache else out

    def step(self, X, y, w, lr: float, clip: float = 5.0) -> float:
        """One Adam step on 0.5 * sum(w*(out-y)^2)/sum(w). Returns the weighted MSE before the step."""
        out, (X, z1, a1, z2, a2) = self.forward(X, True)
        sw = float(w.sum()) + 1e-9
        err = out - y
        d = (w * err / sw).astype(np.float32)[:, None]
        g = {"W3": a2.T @ d, "b3": d.sum(axis=0)}
        da2 = (d @ self.p["W3"].T) * (z2 > 0)
        g["W2"], g["b2"] = a1.T @ da2, da2.sum(axis=0)
        da1 = (da2 @ self.p["W2"].T) * (z1 > 0)
        g["W1"], g["b1"] = X.T @ da1, da1.sum(axis=0)
        nrm = np.sqrt(sum(float((v ** 2).sum()) for v in g.values()))
        sc = min(1.0, clip / (nrm + 1e-9))
        self.t += 1
        b1, b2 = 0.9, 0.999
        for k, gk in g.items():
            gk = gk * sc
            self.m[k] = b1 * self.m[k] + (1 - b1) * gk
            self.v[k] = b2 * self.v[k] + (1 - b2) * gk * gk
            mh = self.m[k] / (1 - b1 ** self.t)
            vh = self.v[k] / (1 - b2 ** self.t)
            self.p[k] -= (lr * mh / (np.sqrt(vh) + 1e-8)).astype(np.float32)
        return float((w * err * err).sum() / sw)

    def copy(self) -> "MLP":
        n = MLP.__new__(MLP)
        n.din, n.h = self.din, self.h
        n.p = {k: v.copy() for k, v in self.p.items()}
        n.m = {k: v.copy() for k, v in self.m.items()}
        n.v = {k: v.copy() for k, v in self.v.items()}
        n.t = self.t
        return n

    def widen(self, new_h: int, rng: np.random.Generator) -> "MLP":
        """Function-preserving growth: new units get random inputs and zero outputs."""
        assert new_h > self.h
        n = MLP(self.din, new_h, rng)
        h = self.h
        for k in ("b1", "b2", "W3"):
            n.p[k][...] = 0
        n.p["W1"][:, :h] = self.p["W1"]
        n.p["b1"][:h] = self.p["b1"]
        n.p["W2"][:h, :h] = self.p["W2"]
        n.p["W2"][h:, :] *= 0.0  # new layer-1 units do not feed old layer-2 units
        n.p["W2"][:h, h:] = (rng.standard_normal((h, new_h - h)) * np.sqrt(2.0 / new_h) * 0.5).astype(np.float32)
        n.p["b2"][:h] = self.p["b2"]
        n.p["W3"][:h] = self.p["W3"]
        n.p["W3"][h:] = 0.0
        n.p["b3"] = self.p["b3"].copy()
        n._adam_reset()
        return n