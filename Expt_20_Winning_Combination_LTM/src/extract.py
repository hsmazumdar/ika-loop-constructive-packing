"""Winning-combination extraction. Read only: nothing here places a piece.

Definitions (also written to README.md and to the LTM):

piece          piece type id (A..P). Orientation is a separate, finer variant: (type, rotation).
combination    unordered multiset of piece types that all appear among the placements of ONE trial.
               {A,A,B} needs at least two A and one B in that trial.
connected      the same, but the pieces must form an edge-connected group (4-neighbour contact
               between placed pieces), like the Expt-17 connected groups. The oriented variant also
               keeps each piece's rotation and relative offset (translation-normalised by the minimum
               cell of the group, exactly as Expt-17). No rotation or reflection of the whole group.
counting       each key is counted at most once per trial.
"""

from __future__ import annotations

import math
from collections import Counter
from itertools import combinations_with_replacement

from mga.pieces import PIECE_TYPES, placed_cells

KINDS = (
    "single_type",
    "single_oriented",
    "pair_type",
    "triple_type",
    "pair_conn_type",
    "triple_conn_type",
    "pair_conn_oriented",
    "triple_conn_oriented",
)
KIND_SIZE = {k: (1 if k.startswith("single") else 2 if k.startswith("pair") else 3) for k in KINDS}
RANKINGS = ("S2", "S1")   # default (primary) first


def rank_order(trials: list[dict], ranking: str) -> list[int]:
    """Trial ids best first. S1: S1 desc, S2 desc, trial_id asc. S2: S2 desc, S1 desc, trial_id asc."""
    if ranking == "S1":
        key = lambda t: (-t["S1"], -t["S2"], t["trial_id"])  # noqa: E731
    elif ranking == "S2":
        key = lambda t: (-t["S2"], -t["S1"], t["trial_id"])  # noqa: E731
    else:
        raise ValueError(ranking)
    return [t["trial_id"] for t in sorted(trials, key=key)]


def top_ids(trials: list[dict], ranking: str, fraction: float) -> list[int]:
    n_top = int(round(len(trials) * fraction))
    return rank_order(trials, ranking)[:n_top]


def multiset_keys(types: Counter, size: int) -> set[tuple]:
    """All distinct unordered type multisets of `size` contained in the trial's type multiset."""
    out = set()
    present = sorted(types)
    for combo in combinations_with_replacement(present, size):
        need = Counter(combo)
        if all(types[t] >= n for t, n in need.items()):
            out.add(combo)
    return out


def _cells(p):
    return placed_cells(p[0], int(p[1]), int(p[2]), int(p[3]))


def adjacency(placements: list[tuple]) -> list[set[int]]:
    """Placements are adjacent when a cell of one is 4-neighbour to a cell of the other."""
    owner = {}
    for i, p in enumerate(placements):
        for c in _cells(p):
            owner[c] = i
    adj = [set() for _ in placements]
    for (x, y), i in owner.items():
        for dx, dy in ((1, 0), (0, 1)):
            j = owner.get((x + dx, y + dy))
            if j is not None and j != i:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def connected_groups(placements: list[tuple], size: int) -> set[tuple[int, ...]]:
    adj = adjacency(placements)
    if size == 2:
        return {(i, j) for i in range(len(adj)) for j in adj[i] if i < j}
    if size == 3:
        out = set()
        for v, nb in enumerate(adj):
            ns = sorted(nb)
            for a in range(len(ns)):
                for b in range(a + 1, len(ns)):
                    out.add(tuple(sorted((v, ns[a], ns[b]))))
        return out
    raise ValueError(size)


def oriented_pattern(group: list[tuple]) -> tuple:
    """Translation-normalised ((type, rotation, dx, dy), ...) sorted, as in Expt-17."""
    cells = [c for p in group for c in _cells(p)]
    min_x = min(x for x, _ in cells)
    min_y = min(y for _, y in cells)
    return tuple(sorted((p[0], int(p[1]), int(p[2]) - min_x, int(p[3]) - min_y) for p in group))


def trial_keysets(placements: list[tuple]) -> dict[str, set]:
    types = Counter(p[0] for p in placements)
    ks: dict[str, set] = {
        "single_type": set(types),
        "single_oriented": {(p[0], int(p[1])) for p in placements},
        "pair_type": multiset_keys(types, 2),
        "triple_type": multiset_keys(types, 3),
    }
    for size, name in ((2, "pair"), (3, "triple")):
        groups = connected_groups(placements, size)
        ks[f"{name}_conn_type"] = {tuple(sorted(placements[i][0] for i in g)) for g in groups}
        ks[f"{name}_conn_oriented"] = {oriented_pattern([placements[i] for i in g]) for g in groups}
    return ks


def key_to_str(kind: str, key) -> str:
    if kind == "single_oriented":
        return f"{key[0]}@r{key[1]}"
    if kind.endswith("_oriented"):
        return "+".join(f"{t}@r{r}({dx},{dy})" for t, r, dx, dy in key)
    if kind == "single_type":
        return str(key)
    return "+".join(key)


def two_prop_z(n_top: int, n_top_total: int, n_bot: int, n_bot_total: int) -> float:
    n_all, total = n_top + n_bot, n_top_total + n_bot_total
    if total == 0 or n_top_total == 0 or n_bot_total == 0:
        return 0.0
    pp = n_all / total
    se = math.sqrt(pp * (1 - pp) * (1 / n_top_total + 1 / n_bot_total))
    if se == 0:
        return 0.0
    return (n_top / n_top_total - n_bot / n_bot_total) / se


def frequency_table(keysets: list[dict[str, set]], is_top: list[bool], kind: str, config) -> list[dict]:
    """One row per key seen anywhere. Each trial counts a key at most once."""
    n_all_c: Counter = Counter()
    n_top_c: Counter = Counter()
    n_top_total = sum(is_top)
    n_total = len(keysets)
    n_bot_total = n_total - n_top_total
    for ks, top in zip(keysets, is_top):
        for k in ks[kind]:
            n_all_c[k] += 1
            if top:
                n_top_c[k] += 1
    rows = []
    for k, n_all in n_all_c.items():
        n_top = n_top_c.get(k, 0)
        n_bot = n_all - n_top
        f_top = n_top / n_top_total if n_top_total else 0.0
        f_bot = n_bot / n_bot_total if n_bot_total else 0.0
        f_all = n_all / n_total
        lift_bot = f_top / f_bot if f_bot > 0 else None
        lift_all = f_top / f_all if f_all > 0 else None
        z = two_prop_z(n_top, n_top_total, n_bot, n_bot_total)
        winning = (
            n_top >= config.win_min_top_count
            and lift_bot is not None and lift_bot > config.win_min_lift
            and z >= config.win_min_z
        ) or (n_top >= config.win_min_top_count and f_bot == 0 and f_top > 0)
        rows.append({
            "kind": kind, "key": k, "key_str": key_to_str(kind, k),
            "n_top": n_top, "n_bottom": n_bot, "n_all": n_all,
            "frac_top": f_top, "frac_bottom": f_bot, "frac_all": f_all,
            "lift_vs_bottom": lift_bot, "lift_vs_all": lift_all, "z": z, "winning": bool(winning),
        })
    rows.sort(key=lambda r: (-r["n_top"], -(r["lift_vs_bottom"] if r["lift_vs_bottom"] is not None else 1e9), r["key_str"]))
    for i, r in enumerate(rows, 1):
        r["freq_rank"] = i
    return rows


def mean_copies(trials: list[dict], is_top: list[bool]) -> dict[str, dict[str, float]]:
    """Extra single-piece view: mean copies of each type per trial in top vs bottom group."""
    top_sum, bot_sum = Counter(), Counter()
    nt = sum(is_top)
    nb = len(trials) - nt
    for t, top in zip(trials, is_top):
        c = Counter(p[0] for p in t["placements"])
        (top_sum if top else bot_sum).update(c)
    return {
        p: {"mean_copies_top": top_sum[p] / nt if nt else 0.0, "mean_copies_bottom": bot_sum[p] / nb if nb else 0.0}
        for p in PIECE_TYPES
    }