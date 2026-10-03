"""Fixed-size hashed memory tables. Capacity is the memory size: a full table evicts weak entries, growth doubles it."""

from __future__ import annotations

import numpy as np

_C = np.uint64(0x9E3779B97F4A7C15)


class HashTable:
    """Direct-mapped table key -> (w, n). w = shrunk mean residual advantage, n = (decayed) evidence count."""

    def __init__(self, bits: int, k: float = 2.0) -> None:
        self.bits = int(bits)
        self.size = 1 << self.bits
        self.k = float(k)
        self.keys = np.full(self.size, -1, dtype=np.int64)
        self.w = np.zeros(self.size)
        self.n = np.zeros(self.size)
        self.evictions = 0

    def slot(self, keys: np.ndarray) -> np.ndarray:
        k = (np.asarray(keys, dtype=np.int64) + 1).astype(np.uint64)
        return ((k * _C) >> np.uint64(64 - self.bits)).astype(np.int64)

    def get(self, keys: np.ndarray) -> np.ndarray:
        keys = np.asarray(keys, dtype=np.int64)
        s = self.slot(keys)
        return np.where((self.keys[s] == keys) & (keys >= 0), self.w[s], 0.0)

    def update(self, keys: np.ndarray, f: np.ndarray, e: np.ndarray, cnt: np.ndarray) -> None:
        """w += sum(f*e) / (n + k + sum(f)) per key; n += sum(cnt). Unseen keys take a slot if free or if weaker."""
        if keys.size == 0:
            return
        uk, inv = np.unique(keys, return_inverse=True)
        m = np.bincount(inv, weights=f)
        se = np.bincount(inv, weights=f * e)
        mc = np.bincount(inv, weights=cnt)
        s = self.slot(uk)
        cur = self.keys[s]
        hit = cur == uk
        empty = cur == -1
        repl = (~hit) & (~empty) & (self.n[s] < mc)
        ok = np.flatnonzero(hit | empty | repl)
        if ok.size == 0:
            return
        _, first = np.unique(s[ok], return_index=True)
        ok = ok[first]
        so = s[ok]
        new = self.keys[so] != uk[ok]
        if new.any():
            self.evictions += int(((self.keys[so] >= 0) & new).sum())
            sn = so[new]
            self.keys[sn] = uk[ok][new]
            self.w[sn] = 0.0
            self.n[sn] = 0.0
        self.w[so] += se[ok] / (self.n[so] + self.k + m[ok])
        self.n[so] += mc[ok]

    def decay(self, g: float) -> None:
        self.n *= g

    def prune(self, n_min: float, w_min: float, occupancy: float) -> int:
        used = self.keys >= 0
        drop = used & (self.n < n_min) & (np.abs(self.w) < w_min)
        occ = used.mean()
        if occ > occupancy:  # still crowded: drop the least valuable entries (|w| * bounded evidence)
            val = np.where(used & ~drop, np.abs(self.w) * np.minimum(self.n, 10.0), np.inf)
            k = int((occ - occupancy * 0.9) * self.size)
            if k > 0:
                drop[np.argpartition(val, k)[:k]] |= used[np.argpartition(val, k)[:k]]
        nd = int(drop.sum())
        self.keys[drop] = -1
        self.w[drop] = 0.0
        self.n[drop] = 0.0
        return nd

    def grow(self, bits: int) -> None:
        if bits <= self.bits:
            return
        old = (self.keys.copy(), self.w.copy(), self.n.copy())
        self.__init__(bits, self.k)
        used = old[0] >= 0
        order = np.argsort(old[2][used])  # weakest first, so stronger entries win a shared slot
        k, w, n = old[0][used][order], old[1][used][order], old[2][used][order]
        s = self.slot(k)
        self.keys[s], self.w[s], self.n[s] = k, w, n

    def stats(self) -> dict:
        used = self.keys >= 0
        return {"size": self.size, "entries": int(used.sum()), "occupancy": float(used.mean()),
                "evictions": self.evictions}