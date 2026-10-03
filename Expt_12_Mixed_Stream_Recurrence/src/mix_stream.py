"""Compose mixed streams at a predeclared useful-recurrence rate. Category is hidden from the agent."""

from __future__ import annotations

import random


def compose_stream(pools: dict[str, list], rate: float, n: int, rng: random.Random) -> list[dict]:
    """rate = share of useful recurrence (exact + valid transform). Remainder is no-match + fresh."""
    if n <= 0:
        return []
    useful_kinds = ["exact_recurrence", "valid_transform"]
    other_kinds = ["no_match", "fresh"]
    n_useful = int(round(float(rate) * n))
    n_useful = max(0, min(n, n_useful))
    n_other = n - n_useful

    def take(kinds: list[str], count: int) -> list[dict]:
        available = [(k, t) for k in kinds for t in pools.get(k) or []]
        if count <= 0:
            return []
        if not available:
            fallback = [(k, t) for k in (useful_kinds + other_kinds) for t in pools.get(k) or []]
            if not fallback:
                raise RuntimeError("empty task pools")
            picks = [rng.choice(fallback) for _ in range(count)]
        else:
            picks = [rng.choice(available) for _ in range(count)]
        out = []
        for kind, task in picks:
            rec = dict(task)
            rec["hidden_kind"] = kind
            rec["constructed_prefix"] = list(task["constructed_prefix"]) if task.get("constructed_prefix") else None
            out.append(rec)
        return out

    n_exact = n_useful // 2
    n_xform = n_useful - n_exact
    if not pools.get("valid_transform"):
        n_exact, n_xform = n_useful, 0
    if not pools.get("exact_recurrence"):
        n_exact, n_xform = 0, n_useful
    n_nomatch = n_other // 2
    n_fresh = n_other - n_nomatch
    if not pools.get("no_match"):
        n_nomatch, n_fresh = 0, n_other
    if not pools.get("fresh"):
        n_nomatch, n_fresh = n_other, 0

    stream = []
    stream += take(["exact_recurrence"], n_exact)
    stream += take(["valid_transform"], n_xform)
    stream += take(["no_match"], n_nomatch)
    stream += take(["fresh"], n_fresh)
    rng.shuffle(stream)
    if len(stream) != n:
        raise RuntimeError(f"stream length {len(stream)} != {n}")
    return stream


def realized_rate(stream: list[dict]) -> float:
    if not stream:
        return 0.0
    useful = sum(1 for t in stream if t.get("hidden_kind") in ("exact_recurrence", "valid_transform"))
    return useful / len(stream)
