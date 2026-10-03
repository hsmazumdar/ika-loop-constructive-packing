"""Compatibility index over a frozen library. Not a packing strategy."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass

from enumerate_ops import leaf_demand
from library_io import definition_hash
from miner import rotate_steps
from pieces import PIECE_TYPES


def _bbox(steps: list[dict]) -> tuple[int, int]:
    cells = [tuple(c) for step in steps for c in step["cells"]]
    if not cells:
        return 0, 0
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def op_dimensions(op) -> tuple[int, int, int]:
    """Minimum bounding width/height over rotations, plus leaf area. Geometric necessity only."""
    area = sum(len(step["cells"]) for step in op.steps)
    best = None
    for k in range(4):
        w, h = _bbox(rotate_steps(op.steps, k))
        key = (min(w, h), max(w, h), w, h)
        if best is None or key < best[0]:
            best = (key, w, h)
    return int(best[1]), int(best[2]), int(area)


@dataclass(frozen=True)
class IndexEntry:
    op_id: str
    definition_hash: str
    demand: dict[str, int]
    required_types: tuple[str, ...]
    bbox_w: int
    bbox_h: int
    area: int
    n_steps: int
    depth: int


class LibraryIndex:
    """Inverted by required piece types. Lookup is billed; it is not free."""

    def __init__(self, memory):
        started = time.perf_counter()
        self.entries: list[IndexEntry] = []
        self.by_required_type: dict[str, list[int]] = {t: [] for t in PIECE_TYPES}
        for op in memory.active():
            demand = {k: int(v) for k, v in leaf_demand(op).items() if int(v) > 0}
            w, h, area = op_dimensions(op)
            entry = IndexEntry(
                op_id=op.op_id,
                definition_hash=definition_hash(op),
                demand=demand,
                required_types=tuple(sorted(demand)),
                bbox_w=w,
                bbox_h=h,
                area=area,
                n_steps=len(op.steps),
                depth=op.depth,
            )
            idx = len(self.entries)
            self.entries.append(entry)
            for t in entry.required_types:
                self.by_required_type[t].append(idx)
        self.build_s = time.perf_counter() - started
        self.n_bytes = sys.getsizeof(self.entries) + sum(sys.getsizeof(v) for v in self.by_required_type.values())

    def to_json(self) -> dict:
        return {
            "n_entries": len(self.entries),
            "build_s": self.build_s,
            "n_bytes": self.n_bytes,
            "entries": [
                {
                    "op_id": e.op_id,
                    "definition_hash": e.definition_hash,
                    "demand": e.demand,
                    "bbox_w": e.bbox_w,
                    "bbox_h": e.bbox_h,
                    "area": e.area,
                    "n_steps": e.n_steps,
                    "depth": e.depth,
                }
                for e in self.entries
            ],
        }

    def query(self, remaining: dict, occupied: int) -> tuple[list[IndexEntry], int, int]:
        """Return compatible entries. Charges: 1 probe + one check per posted candidate.

        Compatibility: remaining counts cover demand, leftover cells cover area,
        and the operation bounding box fits on a 10×10 board. No occupancy-band rule.
        """
        empty = 100 - int(occupied)
        missing = {t for t in PIECE_TYPES if int(remaining.get(t, 0) or 0) <= 0}
        posted: set[int] = set(range(len(self.entries)))
        probes = 1
        for t in missing:
            for idx in self.by_required_type[t]:
                posted.discard(idx)
        kept = []
        checks = 0
        for idx in sorted(posted):
            checks += 1
            entry = self.entries[idx]
            if entry.area > empty:
                continue
            if entry.bbox_w > 10 or entry.bbox_h > 10:
                continue
            ok = True
            for t, n in entry.demand.items():
                if int(remaining.get(t, 0) or 0) < n:
                    ok = False
                    break
            if ok:
                kept.append(entry)
        kept.sort(key=lambda e: (e.definition_hash, e.op_id))
        return kept, probes, checks
