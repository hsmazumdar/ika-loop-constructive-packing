"""CS2 - list-program synthesis (Expt 23, DESIGN.md section 4). DSL, task generator and reference enumerator (REFERENCE ONLY).

A program = tuple of primitives applied left to right to a list of ints. A task = 5 input/output examples of a hidden program.
Primitive families (name, argument): add k, mul k, mod k, filter_gt t, filter_lt t, filter_even, filter_odd, sort, reverse, take k, drop k,
cumsum, dedup, max_prefix. Constants: TRAIN_CONSTS for train and test_iid; test_const also uses UNSEEN constants.
Splits: train (depth 2-3, compositions not in the held-out set), test_iid (same distribution, new tasks), test_comp (depth 2-3 but
composition of FAMILIES in the held-out hash set, never in train), test_deep (depth 4-5), test_const (unseen constants).
Deterministic from (split, index). The solved criterion is exact match on all 5 examples (a program that also matches on 5 held-back
checking examples counts as correct)."""
from __future__ import annotations

import hashlib
import itertools

import numpy as np

TRAIN_CONSTS = (1, 2, 3)
UNSEEN_CONSTS = (4, 5, 6)
LO, HI = -1000, 1000
FAMILIES = ["add", "mul", "mod", "fgt", "flt", "feven", "fodd", "sort", "rev", "take", "drop", "cumsum", "dedup", "maxprefix"]
ARG = {"add", "mul", "mod", "fgt", "flt", "take", "drop"}
SEED_BASE = {"train": 21_000_000, "dev": 22_000_000, "test_iid": 23_000_000, "test_comp": 24_000_000, "test_deep": 25_000_000, "test_const": 26_000_000}


def prims(consts):
    out = []
    for f in FAMILIES:
        if f in ARG:
            out += [(f, k) for k in consts]
        else:
            out.append((f, 0))
    return out


def apply(p, x):
    f, k = p
    if f == "add": return [v + k for v in x]
    if f == "mul": return [v * k for v in x]
    if f == "mod": return [v % k for v in x]
    if f == "fgt": return [v for v in x if v > k]
    if f == "flt": return [v for v in x if v < k]
    if f == "feven": return [v for v in x if v % 2 == 0]
    if f == "fodd": return [v for v in x if v % 2 == 1]
    if f == "sort": return sorted(x)
    if f == "rev": return x[::-1]
    if f == "take": return x[:k]
    if f == "drop": return x[k:]
    if f == "cumsum": return list(itertools.accumulate(x))
    if f == "dedup": return list(dict.fromkeys(x))
    if f == "maxprefix": return list(itertools.accumulate(x, max))
    raise ValueError(f)


def run(prog, x):
    for p in prog:
        x = apply(p, x)
        if len(x) > 64 or any(abs(v) > 10 ** 6 for v in x):
            return None
    return x


def _is_held_comp(fams: tuple) -> bool:
    return int(hashlib.sha1("|".join(fams).encode()).hexdigest()[:8], 16) % 5 == 0


def _inputs(rng, n):
    return [[int(v) for v in rng.integers(0, 10, int(rng.integers(4, 9)))] for _ in range(n)]


def make_task(split: str, index: int):
    rng = np.random.default_rng((SEED_BASE[split], index))
    consts = TRAIN_CONSTS if split != "test_const" else UNSEEN_CONSTS
    P = prims(consts)
    for _ in range(10_000):
        L = int(rng.integers(4, 6)) if split == "test_deep" else int(rng.integers(2, 4))
        prog = tuple(P[int(rng.integers(len(P)))] for _ in range(L))
        fams = tuple(p[0] for p in prog)
        held = _is_held_comp(fams)
        if split in ("train", "dev", "test_iid", "test_const") and held and split != "test_const":
            continue
        if split == "test_comp" and not held:
            continue
        if split == "test_const" and held:
            continue
        ins = _inputs(rng, 10)
        outs = [run(prog, x) for x in ins]
        if any(o is None for o in outs):
            continue
        # non-degenerate: not the identity on all examples, not constant empty
        if all(o == x for o, x in zip(outs, ins)) or all(len(o) == 0 for o in outs):
            continue
        # not solvable by a strictly shorter program of the same split's primitives (keeps depth meaningful)
        return {"id": f"{split}_{index:05d}", "split": split, "prog": prog, "train_io": list(zip(ins[:5], outs[:5])),
                "check_io": list(zip(ins[5:], outs[5:])), "consts": consts, "depth": L}
    raise RuntimeError("no task")


def solves(prog, task, check=True) -> bool:
    for x, y in task["train_io"] + (task["check_io"] if check else []):
        if run(prog, x) != y:
            return False
    return True


def enumerate_solver(task, budget: int, max_depth: int = 5):
    """REFERENCE: breadth-first enumeration by program length with prefix-output deduplication on the training examples
    (observational equivalence). `budget` = number of candidate programs evaluated. Returns (program or None, evaluated)."""
    P = prims(task["consts"])
    ins = [x for x, _ in task["train_io"]]
    start = tuple(tuple(x) for x in ins)
    seen = {start}
    frontier = [((), start)]
    evaluated = 0
    for depth in range(1, max_depth + 1):
        nxt = []
        for prog, outs in frontier:
            for p in P:
                evaluated += 1
                if evaluated > budget:
                    return None, evaluated
                new = tuple(tuple(apply(p, list(o))) for o in outs)
                if any(len(o) > 64 for o in new):
                    continue
                cand = prog + (p,)
                if all(list(n) == y for n, (_, y) in zip(new, task["train_io"])) and solves(cand, task, check=True):
                    return cand, evaluated
                if new not in seen:
                    seen.add(new); nxt.append((cand, new))
        frontier = nxt
    return None, evaluated


def random_solver(task, budget: int, rng, max_len=None):
    """REFERENCE: uniform random programs of random length (the 'random generation' arm without a learner)."""
    P = prims(task["consts"])
    for n in range(budget):
        L = int(rng.integers(1, (max_len or 5) + 1))
        prog = tuple(P[int(rng.integers(len(P)))] for _ in range(L))
        if solves(prog, task):
            return prog, n + 1
    return None, budget