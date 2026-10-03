"""Curve statistics: rolling means, saturation test, paired/independent bootstrap."""

from __future__ import annotations

import numpy as np


def rolling_mean(x: np.ndarray, w: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.size < w:
        return np.array([])
    c = np.cumsum(np.insert(x, 0, 0.0))
    return (c[w:] - c[:-w]) / w


def saturation_test(prev: np.ndarray, last: np.ndarray, delta: float, z: float) -> tuple[bool, float, float]:
    """Saturated when the upper confidence bound of (mean(last) - mean(prev)) is below `delta` (cells of S1 per window)."""
    gain = float(np.mean(last) - np.mean(prev))
    se = float(np.sqrt(np.var(last, ddof=1) / len(last) + np.var(prev, ddof=1) / len(prev)))
    return gain + z * se < delta, gain, se


def boot_mean_ci(x: np.ndarray, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, x.size, (n_boot, x.size))
    m = x[idx].mean(axis=1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def boot_diff_ci(a: np.ndarray, b: np.ndarray, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """mean(a) - mean(b) with a 95% bootstrap interval (independent samples: the boxes are identical empty boxes,
    so there is no per-box pairing other than the seed stream)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    ma = a[rng.integers(0, a.size, (n_boot, a.size))].mean(axis=1)
    mb = b[rng.integers(0, b.size, (n_boot, b.size))].mean(axis=1)
    d = ma - mb
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))