import numpy as np
import engine as E
from agent import Agent  # noqa: F401


def uniform_ref(cfg, budget: int, n: int) -> dict:
    """Uniform natural placing (the untrained baseline) on the same fresh boxes."""
    s1 = np.zeros(n, np.int16)
    att = np.zeros(n, np.int16)
    for j in range(n):
        rng = np.random.default_rng(cfg.eval_seed + j)
        b = E.Box(budget=budget)
        while True:
            c, _ = E.natural_candidates(b, 0)
            if c.size == 0:
                break
            b.place(int(c[rng.integers(c.size)]))
        s1[j], att[j] = b.s1, b.n
    return {"S1": s1, "attempts": att}


def hand_ref(cfg, budget: int, n: int) -> np.ndarray:
    """Hand contact/hole/area rule (REFERENCE ONLY, never used by a learner)."""
    out = np.zeros(n, np.int16)
    for j in range(n):
        rng = np.random.default_rng(cfg.eval_seed + j)
        b = E.Box(budget=budget)
        while True:
            c, f = E.natural_candidates(b, 0)
            if c.size == 0:
                break
            sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * E.AREA[c] + rng.random(c.size) * 0.5
            b.place(int(c[int(np.argmax(sc))]))
        out[j] = b.s1
    return out