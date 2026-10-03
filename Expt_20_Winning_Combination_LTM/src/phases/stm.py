"""Short-term memory (STM): running once-per-trial frequencies, top-25% (by S2) versus the rest.

The STM is a *session* structure: it is built while trials run and is meant to be compared with the frozen LTM.
Kinds kept: single_type, pair_type, triple_type, pair_conn_type, triple_conn_type (oriented kinds are not kept: too large).
Each trial adds 1 to a key's `n_all` at most once. Top-25% membership depends on the final cutoff, so it is computed
from the trials seen so far at every snapshot (online estimate) and once more at the end (final STM).
"""

from __future__ import annotations

import hashlib
import json
import pickle
from collections import Counter
from pathlib import Path

from config import Config
from extract import frequency_table, rank_order, trial_keysets

STM_KINDS = ("single_type", "pair_type", "triple_type", "pair_conn_type", "triple_conn_type")
STM_SCHEMA = "expt20_stm_v1"
FOCUS = (("single_type", ("P",)), ("pair_type", ("N", "P")), ("pair_type", ("O", "P")), ("pair_type", ("E", "P")),
         ("triple_type", ("N", "O", "P")), ("triple_type", ("E", "N", "P")))


class STM:
    def __init__(self, ranking="S2", top_fraction=0.25, config=None):
        self.ranking = ranking
        self.top_fraction = top_fraction
        self.config = config or Config()
        self.trials: list[dict] = []
        self.keysets: list[dict] = []
        self.running_n_all = {k: Counter() for k in STM_KINDS}   # running frequency over all trials, once per trial
        self.snapshots: list[dict] = []

    # -- online update -------------------------------------------------
    def observe(self, trial: dict) -> None:
        ks = trial_keysets(trial["placements"])
        self.trials.append({k: trial[k] for k in ("trial_id", "S1", "S2")})
        self.keysets.append({k: ks[k] for k in STM_KINDS})
        for k in STM_KINDS:
            self.running_n_all[k].update(ks[k])

    @property
    def n(self) -> int:
        return len(self.trials)

    # -- top-25% estimate from trials seen so far ------------------------
    def top_split(self) -> tuple[list[bool], dict]:
        n = self.n
        n_top = int(round(n * self.top_fraction))
        order = rank_order(self.trials, self.ranking)
        top = set(order[:n_top])
        by_id = {t["trial_id"]: t for t in self.trials}
        last = by_id[order[n_top - 1]] if n_top else None
        cut = {"n_trials": n, "n_top": n_top,
               "cutoff_S1": last["S1"] if last else None, "cutoff_S2": last["S2"] if last else None}
        return [t["trial_id"] in top for t in self.trials], cut

    def tables(self, kinds=STM_KINDS) -> tuple[dict, dict]:
        is_top, cut = self.top_split()
        return {k: frequency_table(self.keysets, is_top, k, self.config) for k in kinds}, cut

    def snapshot(self, top_n=10) -> dict:
        tabs, cut = self.tables()
        focus = {}
        for kind, key in FOCUS:
            want = key[0] if kind == "single_type" else key   # single_type keys are plain strings
            row = next((r for r in tabs[kind] if r["key"] == want), None)
            focus[f"{kind}:{'+'.join(key)}"] = None if row is None else {
                "n_top": row["n_top"], "frac_top": row["frac_top"], "lift_vs_bottom": row["lift_vs_bottom"], "winning": row["winning"]}
        snap = {"n_trials": self.n, "cutoff": cut, "focus": focus,
                "top": {k: [{"key_str": r["key_str"], "n_top": r["n_top"], "frac_top": r["frac_top"],
                             "lift_vs_bottom": r["lift_vs_bottom"], "winning": r["winning"]} for r in tabs[k][:top_n]]
                        for k in STM_KINDS}}
        self.snapshots.append(snap)
        return snap

    def export(self, label: str, phase: str, meta: dict, keep=500) -> dict:
        tabs, cut = self.tables()
        body = {}
        for k in STM_KINDS:
            rows = tabs[k]
            body[k] = {"n_rows_total": len(rows), "n_rows_kept": min(keep, len(rows)),
                       "entries": [{f: r[f] for f in ("key", "key_str", "freq_rank", "n_top", "n_bottom", "n_all", "frac_top",
                                                      "frac_bottom", "frac_all", "lift_vs_bottom", "lift_vs_all", "z", "winning")}
                                   for r in rows[:keep]]}
        return {"schema": STM_SCHEMA, "label": label, "phase": phase, "ranking": self.ranking,
                "ranking_rule": "S2 desc, tie-break S1 desc, then trial_id asc", "top_fraction": self.top_fraction,
                "final_cutoff": cut, "n_trials": self.n, "meta": meta,
                "running_frequency_all_trials": {k: {"+".join(key) if isinstance(key, tuple) else str(key): c
                                                     for key, c in self.running_n_all[k].most_common(keep)} for k in STM_KINDS},
                "snapshots": self.snapshots, "stm": body}


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    return o


def save_stm(stm_dict: dict, folder: Path, stem: str) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    pkl, js = folder / f"{stem}.pkl", folder / f"{stem}.json"
    with pkl.open("wb") as fh:
        pickle.dump(stm_dict, fh, protocol=4)
    js.write_text(json.dumps(_jsonable(stm_dict), indent=1), encoding="utf-8")
    return {"pkl": str(pkl), "json": str(js), "pkl_sha256": hashlib.sha256(pkl.read_bytes()).hexdigest(),
            "json_sha256": hashlib.sha256(js.read_bytes()).hexdigest()}


def load_stm(path) -> dict:
    with Path(path).open("rb") as fh:
        return pickle.load(fh)