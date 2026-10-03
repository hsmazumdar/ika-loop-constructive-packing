"""Afterstate features for the learned value function (all read from the board; no decision rule lives here)."""

from __future__ import annotations

import numpy as np

import engine as E

D = 29  # 28 board features + 1 concept-library column (0 until concepts are promoted)
C_CON = 28
# columns 0-15 one-hot piece type; then:
C_AREA, C_OCC, C_WALL, C_P1, C_N3, C_C2, C_FR, C_R2, C_REM, C_S1, C_GH, C_GN = range(16, 28)


def step_features(box: E.Box, budget: int):
    """Natural candidates (legal, touching wall/piece) with their afterstate feature matrix.

    Returns (cand, X[N, D] float32, sig1[N] int64) or None if no legal placement is left.
    Features of the afterstate (board after placing the candidate):
      type one-hot, area, contact with placed pieces, contact with wall, new 1-cell holes (empty cell with 4 blocked
      sides), new dead-end notches (3 blocked sides), cells with 2 blocked sides, free frontier cells around the piece,
      occupied count in the 2nd ring, pieces still allowed, cells filled so far, and two global counts of existing
      holes / notches on the board.
    """
    legal = box.legal()
    if legal.size == 0:
        return None
    ring = E.RINGF[legal]
    occr = box.occ_arr[ring]
    inb = E.IN_BOARD[legal]
    occ_c = (occr & inb).sum(axis=1)
    wall = E.BOUND[legal]
    nat = (occ_c + wall) > 0
    if not nat.all():
        legal, ring, occr, inb, occ_c, wall = legal[nat], ring[nat], occr[nat], inb[nat], occ_c[nat], wall[nat]
        if legal.size == 0:
            return None
    bn = box.blocked_neighbours()
    bl = bn[ring] + E.CPN[legal]
    er = (~occr) & inb
    n = legal.size
    X = np.zeros((n, D), dtype=np.float32)
    X[np.arange(n), E.PTYPE[legal]] = 1.0
    X[:, C_AREA] = E.AREA[legal] / 7.0
    X[:, C_OCC] = occ_c / 12.0
    X[:, C_WALL] = wall / 6.0
    X[:, C_P1] = (er & (bl >= 4)).sum(axis=1) / 2.0
    X[:, C_N3] = (er & (bl == 3)).sum(axis=1) / 3.0
    X[:, C_C2] = (er & (bl == 2)).sum(axis=1) / 4.0
    X[:, C_FR] = er.sum(axis=1) / 8.0
    X[:, C_R2] = box.occ_arr[E.RING2[legal]].sum(axis=1) / 10.0
    X[:, C_REM] = min(max(budget - box.n - 1, 0), 20) / 14.0
    X[:, C_S1] = box.s1 / 100.0
    emp = ~box.occ_arr[:100]
    X[:, C_GH] = (emp & (bn[:100] >= 4)).sum() / 3.0
    X[:, C_GN] = (emp & (bn[:100] == 3)).sum() / 6.0
    sig1 = E.ORIENT[legal] * 4096 + (occr * E.BITW).sum(axis=1)
    return legal, X, sig1