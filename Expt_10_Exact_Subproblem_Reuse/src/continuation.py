"""Exact continuation table. Keyed by remaining mask and inventory. Memorization, not abstraction."""

from __future__ import annotations

import hashlib
import json

from environment import Action, PackingEnv
from inventory import Inventory
from pieces import PIECE_TYPES, placed_cells


def state_key(env: PackingEnv) -> tuple:
    inv = tuple(int(env.inventory.counts.get(t, 0)) for t in PIECE_TYPES)
    return (int(env.mask), inv)


def key_digest(key: tuple) -> str:
    return hashlib.sha256(json.dumps(key, separators=(",", ":")).encode()).hexdigest()[:16]


def _legal(env: PackingEnv, piece: str, rotation: int, x: int, y: int) -> bool:
    if not env.inventory.can_take(piece):
        return False
    cells = placed_cells(piece, rotation, x, y)
    return bool(env._can_place_cells(cells))


class ContinuationTable:
    def __init__(self) -> None:
        self.entries: dict[tuple, list[tuple]] = {}
        self.frozen = False
        self.n_writes = 0
        self.n_overwrites = 0

    def lookup(self, env: PackingEnv) -> list[tuple] | None:
        return self.entries.get(state_key(env))

    def learn_from_success(self, env: PackingEnv, ledger, q_min: float = 75.0) -> int:
        """Store remaining suffixes from a successful committed stack. Not billed if frozen."""
        if self.frozen:
            return 0
        if env.occupied < q_min:
            return 0
        start = PackingEnv(budget=env.budget, inventory=Inventory(dict(env.inventory.initial)))
        suffix = [(p.piece_type, int(p.rotation), int(p.x), int(p.y)) for p in env.stack]
        added = 0
        for i, rec in enumerate(env.stack):
            key = state_key(start)
            rest = suffix[i:]
            if not rest:
                break
            if key not in self.entries:
                self.entries[key] = rest
                self.n_writes += 1
                added += 1
                ledger.charge("learning", 1)
            elif self.entries[key] != rest:
                # First write wins. Colliding later continuations are not stored and are
                # not compared for quality. This is not a best-of rule.
                self.n_overwrites += 1
            start.step(Action.place(rec.piece_type, rec.rotation, rec.x, rec.y))
        return added

    def bytes(self) -> int:
        return len(json.dumps({"n": len(self.entries), "k": list(self.entries)[:1]}, default=str).encode()) + sum(
            8 + 16 * len(v) for v in self.entries.values()
        )

    def n_initial_keys(self) -> int:
        return sum(1 for mask, _inv in self.entries if mask == 0)

    def freeze(self) -> None:
        self.frozen = True


def replay_suffix(env: PackingEnv, suffix: list[tuple], ledger) -> dict:
    """Validate then execute. Stops and reports failure without executing an illegal PLACE."""
    n_ok = 0
    for piece, rotation, x, y in suffix:
        ledger.charge("validation", 1)
        if env.terminal or env.occupied >= 75:
            break
        if not _legal(env, piece, rotation, x, y):
            return {"ok": False, "n_validated": n_ok + 1, "n_executed": n_ok, "failed_at": n_ok}
        env.step(Action.place(piece, rotation, x, y))
        n_ok += 1
    return {"ok": True, "n_validated": n_ok, "n_executed": n_ok, "failed_at": None}
