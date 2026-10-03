"""Paired statistics. Bootstrap is chunked so 10,000-pair resamples stay small in memory."""

from __future__ import annotations

import numpy as np


def paired_boot(d, n_boot: int = 2000, seed: int = 0, chunk: int = 250) -> dict:
    d = np.asarray(d, float)
    n = len(d)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for s in range(0, n_boot, chunk):
        k = min(chunk, n_boot - s)
        means[s:s + k] = d[rng.integers(0, n, size=(k, n))].mean(axis=1)
    return {"n": n, "mean": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0,
            "lo": float(np.percentile(means, 2.5)), "hi": float(np.percentile(means, 97.5)),
            "frac_better": float((d > 0).mean()), "frac_worse": float((d < 0).mean())}


def arm_arrays(results: list[dict]) -> dict:
    keys = ("S1", "S2", "attempts", "n_P", "enum_ops", "mask_ops", "cand_evals")
    ordered = sorted(results, key=lambda r: r["trial_id"])
    return {k: np.array([r[k] for r in ordered], float) for k in keys}


def arm_row(name: str, family: str, a: dict, ctrl: dict, cpu_s: float | None, n_boot: int = 2000, seed: int = 0) -> dict:
    n = len(a["S1"])
    n_top = int(round(n * 0.25))
    s1, s2 = a["S1"], a["S2"]
    d1 = paired_boot(s1 - ctrl["S1"], n_boot, seed)
    d2 = paired_boot(s2 - ctrl["S2"], n_boot, seed + 1)
    extra = float((a["mask_ops"] + a["cand_evals"]).mean())
    return {
        "variant": name, "family": family, "n": n,
        "S1_mean": float(s1.mean()), "S1_median": float(np.median(s1)), "S1_max": float(s1.max()),
        "S1_top25_cutoff": float(np.sort(s1)[::-1][n_top - 1]),
        "S1_gain": d1["mean"], "S1_gain_lo": d1["lo"], "S1_gain_hi": d1["hi"], "S1_gain_se": d1["se"],
        "S1_frac_better": d1["frac_better"], "S1_frac_worse": d1["frac_worse"],
        "S2_mean": float(s2.mean()), "S2_median": float(np.median(s2)), "S2_max": float(s2.max()),
        "S2_top25_cutoff": float(np.sort(s2)[::-1][n_top - 1]),
        "S2_gain": d2["mean"], "S2_gain_lo": d2["lo"], "S2_gain_hi": d2["hi"],
        "attempts_mean": float(a["attempts"].mean()), "frac_P": float((a["n_P"] > 0).mean()), "mean_P_pieces": float(a["n_P"].mean()),
        "frac_S1_ge_85": float((s1 >= 85).mean()), "frac_S1_ge_90": float((s1 >= 90).mean()),
        "extra_cost_units_per_box": extra, "enum_ops_per_box": float(a["enum_ops"].mean()),
        "S1_gain_per_1k_extra_units": (d1["mean"] / (extra / 1000.0)) if extra > 0 else None,
        "cpu_s": cpu_s, "S1_gain_ci_excludes_0": bool(d1["lo"] > 0 or d1["hi"] < 0),
    }