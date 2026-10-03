"""Problem distribution for Expt 23 case study 1. Deterministic given (split, index); disjoint TRAIN / TEST problems.

Splits
  dev          pilot / hyper-parameter selection ONLY (same distribution as train; never used for reporting)
  train        board sizes in TRAIN_SIZES, catalogues from TRAIN pieces only
  test_iid     new problems from the train distribution (seen sizes, seen pieces, new combinations/obstacles)
  test_size    unseen board sizes (never in train), train pieces
  test_piece   seen sizes, catalogue contains >= 2 held-out pieces (never in any train catalogue)
  test_both    unseen sizes AND >= 2 held-out pieces
  legacy       the 10x10, 16-piece (A-P) problem of Expt 01-22, no obstacles
Every catalogue contains exactly one 'large' piece (6 or 7 cells) and k-1 pieces of 3-5 cells, k in 6..16.
Per-problem handicap = random obstacle cells (0 .. 6% of the board) plus the catalogue subset itself.
"""
from __future__ import annotations

import numpy as np

import polyomino as PM
from env import Problem

TRAIN_SIZES = [(8, 8), (9, 9), (10, 10), (11, 11), (8, 10), (10, 8), (9, 11), (11, 9)]
TEST_SIZES = [(7, 7), (12, 12), (7, 10), (10, 7), (12, 9), (9, 12), (7, 12)]
assert not set(TRAIN_SIZES) & set(TEST_SIZES)

SEED_BASE = {"dev": 6_000_000, "train": 1_000_000, "test_iid": 2_000_000, "test_size": 3_000_000, "test_piece": 4_000_000,
             "test_both": 5_000_000}

_BY_SIZE = {n: [i for i, p in enumerate(PM.POOL) if len(p) == n] for n in (3, 4, 5, 6, 7)}


def _pick(rng, sizes_w, allowed: set, k):
    out = []
    ns = list(sizes_w)
    pw = np.array([sizes_w[n] for n in ns], float)
    pw /= pw.sum()
    tries = 0
    while len(out) < k and tries < 1000:
        tries += 1
        n = ns[rng.choice(len(ns), p=pw)]
        cand = [i for i in _BY_SIZE[n] if i in allowed and i not in out]
        if cand:
            out.append(int(cand[rng.integers(len(cand))]))
    return out


def make_problem(split: str, index: int, budget: int | None = 14, obst_frac: float = 0.06, k_range=(6, 16)) -> Problem:
    """obst_frac / k_range give the optional HARD variant (more obstacles, smaller catalogues); defaults = standard."""
    if split == "legacy":
        return Problem("legacy_10x10_A-P", "legacy", 10, 10, (), tuple(sorted(PM.LEGACY_POOL_IDX)), budget)
    rng = np.random.default_rng((SEED_BASE[split], index))
    sizes = TEST_SIZES if split in ("test_size", "test_both") else TRAIN_SIZES
    H, W = sizes[rng.integers(len(sizes))]
    train_set, test_set = set(PM.TRAIN_PIECES), set(PM.TEST_PIECES)
    k = int(rng.integers(k_range[0], k_range[1] + 1))
    large_pool = {i for i in _BY_SIZE[6] + _BY_SIZE[7]}
    if split in ("test_piece", "test_both"):
        n_test = int(rng.integers(2, min(4, k) + 1))
        ts = _pick(rng, {3: .1, 4: .25, 5: .65, 6: .5, 7: .5}, test_set, n_test)
        large_ok = any(len(PM.POOL[i]) >= 6 for i in ts)
        need_large = 0 if large_ok else 1
        rest = _pick(rng, {3: .1, 4: .25, 5: .65}, train_set, k - len(ts) - need_large)
        if need_large:
            rest += _pick(rng, {6: .5, 7: .5}, train_set & large_pool, 1)
        cat = ts + rest
    else:
        cat = _pick(rng, {3: .1, 4: .25, 5: .65}, train_set, k - 1) + _pick(rng, {6: .5, 7: .5}, train_set & large_pool, 1)
    cat = tuple(sorted(set(cat)))
    nb = int(rng.integers(0, int(obst_frac * H * W) + 1))
    blocked = tuple(sorted(int(c) for c in rng.choice(H * W, nb, replace=False))) if nb else ()
    return Problem(f"{split}_{index:05d}", split, H, W, blocked, cat, budget)


def problems(split: str, n: int, budget: int | None = 14, start: int = 0, **kw):
    return [make_problem(split, start + j, budget, **kw) for j in range(n)]


def check_disjoint(n_train=500, n_test=100) -> dict:
    """Spec-hash disjointness between train and every test split, and the piece / size hold-outs."""
    tr = problems("train", n_train)
    tr_h = {p.spec_hash() for p in tr}
    tr_pieces = {i for p in tr for i in p.catalogue}
    out = {"train_unique": len(tr_h), "train_used_test_piece": len(tr_pieces & set(PM.TEST_PIECES))}
    for sp in ("test_iid", "test_size", "test_piece", "test_both"):
        ps = problems(sp, n_test)
        h = {p.spec_hash() for p in ps}
        out[sp] = {"n_unique": len(h), "overlap_with_train": len(h & tr_h),
                   "mean_test_pieces": float(np.mean([sum(i in set(PM.TEST_PIECES) for i in p.catalogue) for p in ps])),
                   "sizes": sorted({(p.H, p.W) for p in ps})}
    return out