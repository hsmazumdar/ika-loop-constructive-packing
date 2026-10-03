"""Bounded STM exclusions and LTM local-context statistics.

STM and LTM are the agent's internal memory. The visible board and the
environment placement stack are external state, not agent memory.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from mga.pieces import BOARD_SIZE, Placement, catalogue_hash


NEIGHBORHOOD = 7
NEIGHBORHOOD_RADIUS = NEIGHBORHOOD // 2
EMPTY, OCCUPIED, OUTSIDE = 0, 1, 2


def occupancy_neighborhood(mask: int, anchor_x: int, anchor_y: int, size: int = BOARD_SIZE) -> str:
    """7x7 neighbourhood centred on the placement anchor.

    Cells are encoded as 0=empty, 1=occupied, 2=outside. This is a partial
    context; identical keys need not imply identical full boards.
    """
    chars: list[str] = []
    for dy in range(-NEIGHBORHOOD_RADIUS, NEIGHBORHOOD_RADIUS + 1):
        for dx in range(-NEIGHBORHOOD_RADIUS, NEIGHBORHOOD_RADIUS + 1):
            x = anchor_x + dx
            y = anchor_y + dy
            if x < 0 or y < 0 or x >= size or y >= size:
                chars.append("2")
            elif mask & (1 << (y * size + x)):
                chars.append("1")
            else:
                chars.append("0")
    return "".join(chars)


def ltm_key(mask: int, placement: Placement) -> str:
    nb = occupancy_neighborhood(mask, placement.x, placement.y)
    return f"{nb}|{placement.piece_type}|{placement.rotation}"


class ShortTermMemory:
    """Bounded queue of (occupancy_bitmask, action_signature) exclusions.

    Entries are specific to one board occupancy. An action that failed on one
    board is never blacklisted globally. Cleared on every box reset.
    """

    def __init__(self, capacity: int = 64) -> None:
        self.capacity = capacity
        self._items: OrderedDict[tuple[int, tuple], None] = OrderedDict()

    def __len__(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def exclude(self, occupancy_mask: int, signature: tuple) -> None:
        key = (occupancy_mask, signature)
        if key in self._items:
            return
        self._items[key] = None
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)

    def is_excluded(self, occupancy_mask: int, signature: tuple) -> bool:
        return (occupancy_mask, signature) in self._items

    def excluded_signatures(self, occupancy_mask: int) -> set[tuple]:
        return {sig for (mask, sig) in self._items if mask == occupancy_mask}


@dataclass(slots=True)
class LTMEntry:
    n: int
    mean: float
    updated: int

    def bonus(self, coefficient: float, k: int) -> float:
        if self.n <= 0:
            return 0.0
        shrink = self.n / (self.n + k)
        return coefficient * shrink * self.mean


class LongTermMemory:
    """Bounded statistics for a local context/action key.

    Update arithmetic: incremental mean. Eviction is deterministic
    least-recently-updated (tie-break: lexicographic key). Evaluation freezes
    values and eviction order. Empty / missing keys contribute zero.
    """

    def __init__(
        self,
        capacity: int = 4096,
        coefficient: float = 0.40,
        shrinkage_k: int = 5,
    ) -> None:
        self.capacity = capacity
        self.coefficient = coefficient
        self.shrinkage_k = shrinkage_k
        self.entries: dict[str, LTMEntry] = {}
        self.clock = 0
        self.evictions = 0
        self.frozen = False
        self.lookups = 0
        self.hits = 0
        self.catalogue_hash = catalogue_hash()
        self.config_hash = ""
        self._bytes_cache: bytes | None = None

    def reset_episode_counters(self) -> None:
        self.lookups = 0
        self.hits = 0

    def _invalidate(self) -> None:
        self._bytes_cache = None

    def bonus(self, key: str) -> float:
        self.lookups += 1
        entry = self.entries.get(key)
        if entry is None or entry.n <= 0:
            return 0.0
        self.hits += 1
        return entry.bonus(self.coefficient, self.shrinkage_k)

    def update(self, key: str, value: float) -> None:
        if self.frozen:
            return
        self._invalidate()
        self.clock += 1
        entry = self.entries.get(key)
        if entry is None:
            if len(self.entries) >= self.capacity:
                self._evict()
            self.entries[key] = LTMEntry(n=1, mean=float(value), updated=self.clock)
            return
        entry.n += 1
        entry.mean += (float(value) - entry.mean) / entry.n
        entry.updated = self.clock

    def _evict(self) -> None:
        victim_key = min(self.entries.items(), key=lambda kv: (kv[1].updated, kv[0]))[0]
        del self.entries[victim_key]
        self.evictions += 1

    def freeze(self) -> None:
        self.frozen = True
        self._invalidate()

    def unfreeze(self) -> None:
        self.frozen = False
        self._invalidate()

    def clear(self) -> None:
        if self.frozen:
            return
        self.entries.clear()
        self.clock = 0
        self.evictions = 0
        self.lookups = 0
        self.hits = 0
        self._invalidate()

    def to_payload(self) -> dict[str, Any]:
        entries = [
            {"key": key, "n": e.n, "mean": e.mean, "updated": e.updated}
            for key, e in sorted(self.entries.items())
        ]
        return {
            "version": 1,
            "catalogue_hash": self.catalogue_hash,
            "config_hash": self.config_hash,
            "capacity": self.capacity,
            "coefficient": self.coefficient,
            "shrinkage_k": self.shrinkage_k,
            "clock": self.clock,
            "evictions": self.evictions,
            "frozen": self.frozen,
            "n_entries": len(self.entries),
            "entries": entries,
        }

    def dump_bytes(self) -> bytes:
        if self._bytes_cache is None:
            self._bytes_cache = json.dumps(
                self.to_payload(), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        return self._bytes_cache

    def serialized_bytes(self) -> int:
        return len(self.dump_bytes())

    def save(self, path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.dump_bytes())

    @classmethod
    def load(
        cls,
        path,
        expected_catalogue_hash: str | None = None,
        expected_config_hash: str | None = None,
    ) -> "LongTermMemory":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_payload(
            payload,
            expected_catalogue_hash=expected_catalogue_hash,
            expected_config_hash=expected_config_hash,
        )

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        expected_catalogue_hash: str | None = None,
        expected_config_hash: str | None = None,
    ) -> "LongTermMemory":
        if payload.get("version") != 1:
            raise ValueError("unsupported LTM checkpoint version")
        if expected_catalogue_hash and payload.get("catalogue_hash") != expected_catalogue_hash:
            raise ValueError("LTM catalogue hash mismatch")
        if expected_config_hash and payload.get("config_hash") != expected_config_hash:
            raise ValueError("LTM configuration hash mismatch")
        mem = cls(
            capacity=payload["capacity"],
            coefficient=payload["coefficient"],
            shrinkage_k=payload["shrinkage_k"],
        )
        mem.catalogue_hash = payload["catalogue_hash"]
        mem.config_hash = payload.get("config_hash", "")
        mem.clock = payload["clock"]
        mem.evictions = payload["evictions"]
        mem.frozen = payload.get("frozen", False)
        for rec in payload["entries"]:
            mem.entries[rec["key"]] = LTMEntry(n=rec["n"], mean=rec["mean"], updated=rec["updated"])
        return mem


def config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EpisodeUpdateBuffer:
    """Training bookkeeping only. Not readable during decision making."""

    def __init__(self, max_actions: int = 100) -> None:
        self.max_actions = max_actions
        self.records: list[dict[str, Any]] = []

    def add(self, key: str, occupied_before: int, action_index: int) -> None:
        if len(self.records) >= self.max_actions:
            raise RuntimeError("episode update buffer exceeded action budget")
        self.records.append(
            {
                "key": key,
                "occupied_before": occupied_before,
                "action_index": action_index,
            }
        )

    def apply(self, ltm: LongTermMemory, terminal_occupied: int, terminal_actions: int) -> None:
        for rec in self.records:
            remaining = terminal_actions - rec["action_index"]
            value = (terminal_occupied - rec["occupied_before"]) / 100.0 - 0.001 * remaining
            ltm.update(rec["key"], value)
        self.clear()

    def clear(self) -> None:
        self.records.clear()
