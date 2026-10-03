"""Problem-agnostic afterstate encoding (Expt 23, DESIGN.md 3.2). No hand-designed board counts.

Per candidate placement (the afterstate): a 9x9 window centred on the piece centroid with 3 binary channels
(earlier pieces, outside-board-or-obstacle, cells of the new piece) = 243 inputs; 6 piece-shape descriptors (area, bounding box,
second moments - no piece identity); 7 global raw context numbers. D = 256. The piece is NOT rotated to a canonical frame
(amendment A2): its orientation is visible in the piece channel.
"""
from __future__ import annotations

import numpy as np

from env import Env, State

D = 256
HALF = 4
_DY, _DX = np.meshgrid(np.arange(-HALF, HALF + 1), np.arange(-HALF, HALF + 1), indexing="ij")
_DY, _DX = _DY.ravel(), _DX.ravel()


class Encoder:
    def __init__(self, env: Env) -> None:
        self.env = env
        H, W, HW = env.prob.H, env.prob.W, env.HW
        self.H, self.W, self.HW = H, W, HW
        C = env.CELLS
        valid = C < HW
        y, x = C // W, C % W
        cnt = np.maximum(valid.sum(axis=1), 1)
        my = (y * valid).sum(axis=1) / cnt
        mx = (x * valid).sum(axis=1) / cnt
        self.cy = np.floor(my + 0.5).astype(np.int32)
        self.cx = np.floor(mx + 0.5).astype(np.int32)
        big = 10 ** 6
        h = np.where(valid, y, -big).max(axis=1) - np.where(valid, y, big).min(axis=1) + 1
        w = np.where(valid, x, -big).max(axis=1) - np.where(valid, x, big).min(axis=1) + 1
        vx = (((x - mx[:, None]) ** 2) * valid).sum(axis=1) / cnt
        vy = (((y - my[:, None]) ** 2) * valid).sum(axis=1) / cnt
        cxy = (((x - mx[:, None]) * (y - my[:, None])) * valid).sum(axis=1) / cnt
        self.desc = np.stack([env.AREA / 7.0, w / 7.0, h / 7.0, vx / 2.0, vy / 2.0, cxy / 2.0], axis=1).astype(np.float32)
        self.ob = np.zeros(HW + 2, bool)
        for b in env.prob.blocked:
            self.ob[b] = True
        k = len(env.prob.catalogue)
        self.glob_static = np.array([H / 12.0, W / 12.0, k / 16.0], np.float32)
        self.free = max(env.free_cells, 1)
        self.max_area = max(env.max_area, 1)

    def features(self, s: State, cand: np.ndarray) -> np.ndarray:
        env = self.env
        n = cand.size
        wy = self.cy[cand][:, None] + _DY[None, :]
        wx = self.cx[cand][:, None] + _DX[None, :]
        out = (wy < 0) | (wy >= self.H) | (wx < 0) | (wx >= self.W)
        idx = np.where(out, self.HW, wy * self.W + wx)
        obm = self.ob[idx]
        ch_pc = s.occ[idx] & ~obm & ~out
        ch_wall = out | obm
        idx2 = np.where(out, -1, idx)
        ch_new = (idx2[:, :, None] == env.CELLS[cand][:, None, :]).any(axis=2)
        X = np.empty((n, D), np.float32)
        X[:, :81], X[:, 81:162], X[:, 162:243] = ch_pc, ch_wall, ch_new
        X[:, 243:249] = self.desc[cand]
        budget = env.prob.budget
        rem = 14 if budget is None else max(budget - s.n, 1)
        left_frac = 1.0 if budget is None else max(budget - s.n - 1, 0) / 14.0
        g = np.array([s.filled / self.free, left_frac, min((self.free - s.filled) / (self.max_area * rem), 3.0) / 3.0], np.float32)
        X[:, 249:252] = g
        X[:, 252:255] = self.glob_static
        X[:, 255] = len(env.prob.blocked) / max(self.H * self.W, 1)
        return X