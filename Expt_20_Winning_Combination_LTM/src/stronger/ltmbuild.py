"""Build LTM-style weight tables from a uniform run (any ranking / top fraction) and placement-preference tables."""

from __future__ import annotations

from collections import Counter

from config import Config
from extract import frequency_table, multiset_keys, rank_order

LTM_KINDS = ("single_type", "pair_type", "triple_type")


def type_keysets(placements) -> dict:
    types = Counter(p[0] for p in placements)
    return {"single_type": set(types), "pair_type": multiset_keys(types, 2), "triple_type": multiset_keys(types, 3)}


def build_ltm(keysets: list[dict], meta: list[dict], ranking: str, fraction: float, label: str, config=None, keep: int = 500,
              extra_manifest: dict | None = None) -> dict:
    """LTM-compatible dict (only the kinds the guidance policy reads). meta rows need trial_id, S1, S2."""
    config = config or Config()
    n = len(meta)
    n_top = int(round(n * fraction))
    order = rank_order(meta, ranking)
    top = set(order[:n_top])
    is_top = [m["trial_id"] in top for m in meta]
    body = {}
    for kind in LTM_KINDS:
        rows = frequency_table(keysets, is_top, kind, config)
        body[kind] = {"entries": [{f: r[f] for f in ("key", "key_str", "freq_rank", "n_top", "n_bottom", "n_all", "frac_top",
                                                      "frac_bottom", "lift_vs_bottom", "lift_vs_all", "z", "winning")}
                                  for r in rows[:keep]]}
    by = {m["trial_id"]: m for m in meta}
    last = by[order[n_top - 1]]
    manifest = {"trials": n, "label": label, "ranking": ranking, "top_fraction": fraction, **(extra_manifest or {})}
    return {"schema": "expt20_stronger_ltm_v1", "default_ranking": ranking, "manifest": manifest,
            "cutoffs": {ranking: {"n_top": n_top, "cutoff_S1": last["S1"], "cutoff_S2": last["S2"]}}, "ltm": {ranking: body}}


def build_placement_table(trials: list[dict], ranking: str, fraction: float, smoothing: float = 2.0,
                          clip=(0.25, 4.0)) -> dict:
    """signature (type, rotation, x, y) -> smoothed lift of appearing in the top group vs the bottom group (once per trial)."""
    n = len(trials)
    n_top = int(round(n * fraction))
    order = rank_order(trials, ranking)
    top = set(order[:n_top])
    ct, cb = Counter(), Counter()
    for t in trials:
        sigs = {(p[0], int(p[1]), int(p[2]), int(p[3])) for p in t["placements"]}
        (ct if t["trial_id"] in top else cb).update(sigs)
    nb = n - n_top
    out = {}
    for sig in set(ct) | set(cb):
        ft = (ct[sig] + smoothing) / (n_top + 2 * smoothing)
        fb = (cb[sig] + smoothing) / (nb + 2 * smoothing)
        out[sig] = min(max(ft / fb, clip[0]), clip[1])
    return out