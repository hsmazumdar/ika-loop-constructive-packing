"""Worker entry for baseline arms (falls back to stronger.arms for control / guided / spec arms)."""

from __future__ import annotations

import time


def run_chunk_b(job: tuple) -> tuple:
    kind, seed, ids, payload = job
    if kind == "rule":
        from baselines.rules import Rule, run_rule_trial
        t0 = time.perf_counter()
        rule = Rule(**payload)
        out = [run_rule_trial(seed, i, rule) for i in ids]
        return kind, out, time.perf_counter() - t0
    if kind == "e1":
        from baselines.e1agent import load_config, run_e1_trial
        t0 = time.perf_counter()
        cfg = load_config()
        out = [run_e1_trial(seed, i, cfg) for i in ids]
        return kind, out, time.perf_counter() - t0
    from stronger import arms as A
    return A.run_chunk(job)