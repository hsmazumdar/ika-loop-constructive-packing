"""Budgeted recogniser. It proposes placements and does not commit them.

Checks are inventory, anchor selection, geometry, cache creation, cache
invalidation, and lookup. When the absolute budget is spent, consulting stops.
"""

from __future__ import annotations

from pieces import BOARD_SIZE

_NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Budget:
    def __init__(self, limit: int) -> None:
        self.limit = int(limit)
        self.spent = 0
        self.inventory = 0
        self.anchor = 0
        self.geometry = 0
        self.cache_create = 0
        self.cache_invalidate = 0
        self.lookup = 0

    @property
    def left(self) -> int:
        return self.limit - self.spent

    @property
    def exhausted(self) -> bool:
        return self.spent >= self.limit

    def take(self, bucket: str, n: int = 1) -> bool:
        """Spend n if the whole charge fits. Otherwise spend nothing and report exhaustion."""
        n = int(n)
        if n <= 0:
            return True
        if self.spent + n > self.limit:
            return False
        self.spent += n
        setattr(self, bucket, getattr(self, bucket) + n)
        return True

    def as_dict(self) -> dict:
        return {
            "limit": self.limit,
            "spent": self.spent,
            "inventory": self.inventory,
            "anchor": self.anchor,
            "geometry": self.geometry,
            "cache_create": self.cache_create,
            "cache_invalidate": self.cache_invalidate,
            "lookup": self.lookup,
            "exhausted": self.exhausted,
        }


def select_anchors(occupied: set[tuple[int, int]], config) -> tuple[list[tuple[int, int]], int, bool]:
    """Return (anchors, checks, complete).

    Empty board: one declared origin, no frontier scan.
    Otherwise: the first max_anchors free cells in row-major order that touch
    an occupied cell. The scan stops once that many exist.
    """
    if not occupied:
        return [tuple(config.empty_anchor)], 1, True
    chosen: list[tuple[int, int]] = []
    checks = 1
    limit = int(config.max_anchors)
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            checks += 1
            if (x, y) in occupied:
                continue
            touches = False
            for dx, dy in _NEIGHBORS:
                checks += 1
                if (x + dx, y + dy) in occupied:
                    touches = True
                    break
            if touches:
                chosen.append((x, y))
                if len(chosen) >= limit:
                    return chosen, checks, True
    return chosen, checks, True


def _fits_at(pattern: dict, origin: tuple[int, int], occupied: set[tuple[int, int]]) -> tuple[int, bool]:
    ox, oy = origin
    checks = 1
    for dx, dy in pattern["cells"]:
        x, y = ox + int(dx), oy + int(dy)
        checks += 1
        if x < 0 or y < 0 or x >= BOARD_SIZE or y >= BOARD_SIZE or (x, y) in occupied:
            return checks, False
    return checks, True


def _available(pattern: dict, remaining: dict) -> bool:
    return all(int(remaining.get(piece, 0)) >= int(need) for piece, need in pattern["counts"].items())


def _placement_cells(pattern: dict, origin: tuple[int, int]) -> set[tuple[int, int]]:
    ox, oy = origin
    return {(ox + int(dx), oy + int(dy)) for dx, dy in pattern["cells"]}


class Recogniser:
    """One box. Cache entries are (pattern index, origin) -> fits."""

    def __init__(self, patterns: list[dict], budget: Budget) -> None:
        self.patterns = patterns
        self.budget = budget
        self.available: dict[int, bool] = {}
        self.cache: dict[tuple[int, tuple[int, int]], bool] = {}
        self.cache_cells: dict[tuple[int, tuple[int, int]], set[tuple[int, int]]] = {}
        self.consults: list[dict] = []
        self.stopped = False

    def _stop(self) -> None:
        self.stopped = True

    def filter_inventory(self, remaining: dict, piece_types: set[str] | None) -> None:
        """Bill one check per pattern whose availability is (re)computed."""
        for pattern in self.patterns:
            if self.budget.exhausted or self.stopped:
                self._stop()
                return
            index = int(pattern["pattern_index"])
            if piece_types is not None and not (piece_types & set(pattern["counts"])):
                continue
            if not self.budget.take("inventory", 1):
                self._stop()
                return
            was = self.available.get(index)
            now = _available(pattern, remaining)
            self.available[index] = now
            if was and not now:
                self._drop_pattern(index)

    def _drop_pattern(self, index: int) -> None:
        keys = [key for key in self.cache if key[0] == index]
        for key in keys:
            if not self.budget.take("cache_invalidate", 1):
                self._stop()
                return
            self.cache.pop(key, None)
            self.cache_cells.pop(key, None)

    def invalidate(self, changed: set[tuple[int, int]]) -> None:
        """Bill one invalidation check per cached entry. Drop entries that meet a changed cell."""
        if not changed:
            return
        for key in list(self.cache):
            if self.budget.exhausted or self.stopped:
                self._stop()
                return
            if not self.budget.take("cache_invalidate", 1):
                self._stop()
                return
            if self.cache_cells.get(key, set()) & changed:
                self.cache.pop(key, None)
                self.cache_cells.pop(key, None)

    def consult(self, prefix: int, occupied: set[tuple[int, int]], config) -> dict:
        """Expose cached or newly tested fits at the current anchors. Does not place."""
        record = {
            "prefix": prefix,
            "anchors": [],
            "anchor_complete": False,
            "inventory_rejected": [],
            "unchecked": [],
            "tested": [],
            "exposed": [],
            "completed": False,
        }
        if self.stopped or self.budget.exhausted:
            self._stop()
            self.consults.append(record)
            return record
        anchors, checks, complete = select_anchors(occupied, config)
        if not self.budget.take("anchor", checks):
            self._stop()
            self.consults.append(record)
            return record
        record["anchors"] = anchors
        record["anchor_complete"] = complete
        for pattern in self.patterns:
            if self.stopped or self.budget.exhausted:
                self._stop()
                break
            index = int(pattern["pattern_index"])
            if index not in self.available:
                record["unchecked"].append(index)
                continue
            if not self.available[index]:
                record["inventory_rejected"].append(index)
                continue
            for origin in anchors:
                if self.stopped or self.budget.exhausted:
                    self._stop()
                    break
                key = (index, origin)
                if key in self.cache:
                    if not self.budget.take("lookup", 1):
                        self._stop()
                        break
                    if self.cache[key]:
                        record["exposed"].append({"pattern_index": index, "origin": origin})
                    continue
                geom_checks, fits = _fits_at(pattern, origin, occupied)
                if not self.budget.take("geometry", geom_checks):
                    self._stop()
                    break
                if not self.budget.take("cache_create", 1):
                    self._stop()
                    break
                self.cache[key] = fits
                self.cache_cells[key] = _placement_cells(pattern, origin)
                record["tested"].append({"pattern_index": index, "origin": origin, "fits": fits})
                if fits:
                    record["exposed"].append({"pattern_index": index, "origin": origin})
        else:
            if not self.stopped:
                record["completed"] = True
        self.consults.append(record)
        return record


def changed_piece_types(before: dict, after: dict) -> set[str]:
    keys = set(before) | set(after)
    return {key for key in keys if int(before.get(key, 0)) != int(after.get(key, 0))}


def absolute_budget(primitive_efforts: list[int], fraction: float) -> int:
    if not primitive_efforts:
        raise RuntimeError("development primitive effort is empty")
    mean = sum(primitive_efforts) / len(primitive_efforts)
    return max(1, int(float(fraction) * mean))
