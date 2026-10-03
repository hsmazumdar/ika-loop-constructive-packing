"""Arm comparison: distribution summaries, paired differences, STM-vs-LTM table."""

from __future__ import annotations

import numpy as np

from mga.pieces import PIECES


def arm_arrays(trials: list[dict]) -> dict:
    return {k: np.array([t[k] for t in trials], float) for k in ("S1", "S2", "attempts")}


def top_cutoff(trials: list[dict], ranking: str, fraction=0.25) -> dict:
    from extract import rank_order
    n_top = int(round(len(trials) * fraction))
    order = rank_order(trials, ranking)
    by = {t["trial_id"]: t for t in trials}
    last = by[order[n_top - 1]]
    return {"n_top": n_top, "cutoff_S1": last["S1"], "cutoff_S2": last["S2"]}


def summarize_arm(name: str, trials: list[dict], runtime_s: float | None = None) -> dict:
    a = arm_arrays(trials)
    n = len(trials)
    has_p = np.array([any(p[0] == "P" for p in t["placements"]) for t in trials])
    n_p = np.array([sum(1 for p in t["placements"] if p[0] == "P") for t in trials], float)
    out = {"arm": name, "n_trials": n, "runtime_s": runtime_s,
           "frac_trials_using_P": float(has_p.mean()), "mean_P_pieces_per_trial": float(n_p.mean()),
           "mean_attempts": float(a["attempts"].mean()), "mean_empty_cells": float(100 - a["S1"].mean())}
    for k in ("S1", "S2"):
        x = a[k]
        out[k] = {"mean": float(x.mean()), "median": float(np.median(x)), "max": float(x.max()), "min": float(x.min()),
                  "std": float(x.std()), "p75": float(np.percentile(x, 75)), "p90": float(np.percentile(x, 90))}
        out[f"top25_cutoff_by_{k}"] = top_cutoff(trials, k)
    out["frac_S1_ge_85"] = float((a["S1"] >= 85).mean())
    out["frac_S1_ge_90"] = float((a["S1"] >= 90).mean())
    out["S1_mean_when_P"] = float(a["S1"][has_p].mean()) if has_p.any() else None
    out["S1_mean_when_no_P"] = float(a["S1"][~has_p].mean()) if (~has_p).any() else None
    out["S2_mean_when_P"] = float(a["S2"][has_p].mean()) if has_p.any() else None
    out["S2_mean_when_no_P"] = float(a["S2"][~has_p].mean()) if (~has_p).any() else None
    return out


def paired_diff(base: list[dict], other: list[dict], key: str, n_boot=2000, seed=0) -> dict:
    """other - base on the same trial ids (same per-trial seeds). Bootstrap over trial pairs."""
    b = {t["trial_id"]: t[key] for t in base}
    o = {t["trial_id"]: t[key] for t in other}
    ids = sorted(set(b) & set(o))
    d = np.array([o[i] - b[i] for i in ids], float)
    n = len(d)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = d[idx].mean(axis=1)
    se = float(d.std(ddof=1) / np.sqrt(n))
    return {"key": key, "n_pairs": n, "mean_diff": float(d.mean()), "se": se,
            "ci95_boot_low": float(np.percentile(boots, 2.5)), "ci95_boot_high": float(np.percentile(boots, 97.5)),
            "frac_other_better": float((d > 0).mean()), "frac_equal": float((d == 0).mean()), "frac_other_worse": float((d < 0).mean()),
            "sd_diff": float(d.std(ddof=1)), "t_like": float(d.mean() / se) if se > 0 else None}


def boot_diff_unpaired(a: list[dict], b: list[dict], key: str, n_boot=2000, seed=1) -> dict:
    x = np.array([t[key] for t in a], float)
    y = np.array([t[key] for t in b], float)
    rng = np.random.default_rng(seed)
    bx = x[rng.integers(0, len(x), size=(n_boot, len(x)))].mean(axis=1)
    by = y[rng.integers(0, len(y), size=(n_boot, len(y)))].mean(axis=1)
    d = by - bx
    return {"key": key, "mean_diff": float(y.mean() - x.mean()), "ci95_boot_low": float(np.percentile(d, 2.5)),
            "ci95_boot_high": float(np.percentile(d, 97.5))}


def stm_vs_ltm_rows(stm: dict, ltm: dict, kinds=("single_type", "pair_type", "triple_type", "pair_conn_type", "triple_conn_type"), top=25) -> list[dict]:
    """Top-`top` STM keys by top-group frequency, with the LTM lift for the same key (if kept in the LTM)."""
    ranking = ltm["default_ranking"]
    rows = []
    for k in kinds:
        lt = {tuple(e["key"]): e for e in ltm["ltm"][ranking][k]["entries"]}
        for e in stm["stm"][k]["entries"][:top]:
            le = lt.get(tuple(e["key"]))
            rows.append({"kind": k, "key_str": e["key_str"], "stm_rank": e["freq_rank"], "stm_n_top": e["n_top"],
                         "stm_frac_top": e["frac_top"], "stm_lift_vs_bottom": e["lift_vs_bottom"], "stm_winning": e["winning"],
                         "ltm_frac_top": le["frac_top"] if le else None, "ltm_lift_vs_bottom": le["lift_vs_bottom"] if le else None,
                         "ltm_winning": le["winning"] if le else None, "in_ltm": le is not None})
    return rows