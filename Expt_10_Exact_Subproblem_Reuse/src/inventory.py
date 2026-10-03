"""Per-box piece inventories.

Copied from Expt-3 mga3.inventory, which copied Expt-2. Expt-4 does not import mga3.
"""

from __future__ import annotations

from pieces import PIECE_TYPES, piece_area


class Inventory:
    def __init__(self, counts: dict[str, int] | None) -> None:
        self.unlimited = counts is None
        if counts is None:
            self.initial = {}
            self.counts = {}
        else:
            self.initial = {t: int(counts.get(t, 0)) for t in PIECE_TYPES}
            self.counts = dict(self.initial)

    def copy(self) -> "Inventory":
        other = Inventory(None if self.unlimited else self.initial)
        if not self.unlimited:
            other.counts = dict(self.counts)
        return other

    def can_take(self, piece_type: str, n: int = 1) -> bool:
        if piece_type not in PIECE_TYPES:
            return False
        if self.unlimited:
            return True
        return self.counts.get(piece_type, 0) >= n

    def fits_multiset(self, demand: dict[str, int]) -> bool:
        return all(self.can_take(t, int(n)) for t, n in demand.items() if int(n) > 0)

    def take(self, piece_type: str) -> None:
        if self.unlimited:
            return
        if self.counts.get(piece_type, 0) <= 0:
            raise RuntimeError(f"inventory underflow for {piece_type}")
        self.counts[piece_type] -= 1

    def restore(self, piece_type: str) -> None:
        if self.unlimited:
            return
        self.counts[piece_type] += 1
        if self.counts[piece_type] > self.initial[piece_type]:
            raise RuntimeError(f"inventory overflow for {piece_type}")

    def restore_initial(self) -> None:
        self.counts = {} if self.unlimited else dict(self.initial)

    def as_dict(self) -> dict[str, int]:
        if self.unlimited:
            return {}
        return {t: int(self.counts[t]) for t in PIECE_TYPES if self.initial.get(t, 0) or self.counts.get(t, 0)}

    def total_area(self) -> int | None:
        if self.unlimited:
            return None
        return sum(self.initial[t] * piece_area(t) for t in PIECE_TYPES)

    def on_board_consistent(self, placed_counts: dict[str, int]) -> bool:
        if self.unlimited:
            return True
        for t in PIECE_TYPES:
            if self.initial.get(t, 0) - placed_counts.get(t, 0) != self.counts.get(t, 0):
                return False
        return True
