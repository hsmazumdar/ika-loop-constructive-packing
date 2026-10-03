"""Polyomino pool (rotation classes only, no reflections, matching the Expt-01 catalogue convention)."""
from __future__ import annotations
import hashlib

def normalize(cells):
    mx = min(x for x, _ in cells); my = min(y for _, y in cells)
    return tuple(sorted((x - mx, y - my) for x, y in cells))

def rot90(cells):
    return tuple((-y, x) for x, y in cells)

def orientations(cells):
    """Distinct rotations (0/90/180/270) as normalised cell tuples, sorted."""
    out, c = set(), tuple(cells)
    for _ in range(4):
        c = rot90(c)
        out.add(normalize(c))
    return sorted(out)

def rot_class(cells):
    return orientations(cells)[0]

def fixed_polyominoes(n):
    cur = {((0, 0),)}
    for _ in range(n - 1):
        nxt = set()
        for p in cur:
            s = set(p)
            for x, y in p:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in s:
                        nxt.add(normalize(s | {q}))
        cur = nxt
    return cur

def build_pool(sizes=(3, 4, 5, 6, 7)):
    pool = []
    for n in sizes:
        reps = sorted({rot_class(p) for p in fixed_polyominoes(n)})
        pool.extend(reps)
    return pool

POOL = build_pool()
POOL_INDEX = {p: i for i, p in enumerate(POOL)}

def is_test_piece(idx, mod=5):
    """Deterministic hold-out of ~20% of the pieces: these never appear in TRAIN catalogues."""
    h = hashlib.sha1(repr(POOL[idx]).encode()).hexdigest()
    return int(h[:8], 16) % mod == 0

TEST_PIECES = [i for i in range(len(POOL)) if is_test_piece(i)]
TRAIN_PIECES = [i for i in range(len(POOL)) if not is_test_piece(i)]

# the 16-piece catalogue of Expt 01 .. 22 (identifiers A-P), used as the 'legacy' anchor problem
LEGACY = {
    "A": ((1, 0), (2, 0), (0, 1), (1, 1), (1, 2)), "B": ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
    "C": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)), "D": ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3)),
    "E": ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2)), "F": ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2)),
    "G": ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1)), "H": ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
    "I": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)), "J": ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
    "K": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)), "L": ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    "M": ((0, 0), (0, 1), (0, 2), (0, 3)), "N": ((0, 0), (0, 1), (0, 2), (1, 2)),
    "O": ((0, 0), (1, 0), (2, 0), (1, 1)), "P": ((0, 0), (1, 0), (0, 1), (0, 2), (1, 2), (0, 3), (1, 3)),
}
LEGACY_POOL_IDX = tuple(POOL_INDEX[rot_class(c)] for c in LEGACY.values())