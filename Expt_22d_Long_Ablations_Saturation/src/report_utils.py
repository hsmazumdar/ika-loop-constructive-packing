import numpy as np


def boot(v, n=4000, seed=0):
    v = np.asarray([x for x in v if not np.isnan(x)], float)
    if v.size == 0:
        return np.nan, np.nan, np.nan
    if v.size < 3:
        return float(v.mean()), np.nan, np.nan
    rng = np.random.default_rng(seed)
    m = v[rng.integers(0, v.size, (n, v.size))].mean(1)
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def boot_diff(a, b, n=5000, seed=1):
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(seed)
    d = a[rng.integers(0, a.size, (n, a.size))].mean(1) - b[rng.integers(0, b.size, (n, b.size))].mean(1)
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def welch_p(a, b):
    from math import erfc, sqrt
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.size < 2 or b.size < 2:
        return np.nan
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
    if se == 0:
        return 0.0 if a.mean() != b.mean() else 1.0
    return float(erfc(abs((a.mean() - b.mean()) / se) / sqrt(2)))


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=150)
    fig.savefig(out / f"{name}.pdf")


def rolling(x, w):
    c = np.cumsum(np.insert(np.asarray(x, float), 0, 0.0))
    return (c[w:] - c[:-w]) / w
