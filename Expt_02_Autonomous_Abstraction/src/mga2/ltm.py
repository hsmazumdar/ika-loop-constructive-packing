"""Long-term library of immutable operation versions and durable statistics.

Frozen evaluation rejects new entries, updates, promotions and evictions.
"""

from __future__ import annotations

from mga2.ops import Operation, call_ids, canonical_bytes, mean_utility


class LongTermMemory:
    def __init__(self, byte_cap: int, confirm_uses: int = 3, confirm_tasks: int = 2, expiry_boxes: int = 20) -> None:
        self.byte_cap = int(byte_cap)
        self.confirm_uses = int(confirm_uses)
        self.confirm_tasks = int(confirm_tasks)
        self.expiry_boxes = int(expiry_boxes)
        self.ops: dict[str, Operation] = {}
        self.selector: dict[str, dict] = {}
        self.events: list[dict] = []
        self.frozen = False
        self._protected: set[str] = set()
        self.evictions = 0
        self.rejected_positive = 0

    def logical_bytes(self) -> int:
        payload = {
            "ops": {k: op.storage_dict() for k, op in sorted(self.ops.items())},
            "selector": self.selector,
        }
        return canonical_bytes(payload)

    def to_dict(self) -> dict:
        return {
            "byte_cap": self.byte_cap,
            "confirm_uses": self.confirm_uses,
            "confirm_tasks": self.confirm_tasks,
            "expiry_boxes": self.expiry_boxes,
            "frozen": self.frozen,
            "evictions": self.evictions,
            "rejected_positive": self.rejected_positive,
            "selector": self.selector,
            "ops": {k: op.storage_dict() for k, op in self.ops.items()},
        }

    @staticmethod
    def from_dict(data: dict) -> "LongTermMemory":
        mem = LongTermMemory(
            byte_cap=int(data.get("byte_cap", 0)),
            confirm_uses=int(data.get("confirm_uses", 3)),
            confirm_tasks=int(data.get("confirm_tasks", 2)),
            expiry_boxes=int(data.get("expiry_boxes", 20)),
        )
        mem.frozen = bool(data.get("frozen", False))
        mem.evictions = int(data.get("evictions", 0))
        mem.rejected_positive = int(data.get("rejected_positive", 0))
        mem.selector = dict(data.get("selector", {}))
        for key, raw in data.get("ops", {}).items():
            mem.ops[key] = Operation.from_dict(raw)
        return mem

    def copy(self) -> "LongTermMemory":
        return LongTermMemory.from_dict(self.to_dict())

    def ids(self) -> set[str]:
        return set(self.ops)

    def add_provisional(self, op: Operation, episode: int) -> bool:
        if self.frozen:
            return False
        if op.op_id in self.ops:
            return True
        op.status = "provisional"
        op.created_episode = episode
        self.ops[op.op_id] = op
        if not self._evict_until_fit():
            self.ops.pop(op.op_id, None)
            self.rejected_positive += 1
            self.events.append({"type": "rejected_capacity", "op_id": op.op_id})
            return False
        self.events.append({"type": "promotion", "op_id": op.op_id, "status": "provisional", "episode": episode})
        return op.op_id in self.ops

    def note_real_use(self, op_id: str, utility: float, success: bool, task_id: str, origin: tuple) -> None:
        if self.frozen:
            return
        op = self.ops.get(op_id)
        if op is None:
            return
        op.record_utility(utility, real=True, task_id=task_id, origin=origin, success=success)
        self.events.append(
            {
                "type": "reuse",
                "op_id": op_id,
                "utility": utility,
                "success": success,
                "task_id": task_id,
                "origin": list(origin),
            }
        )
        self._maybe_confirm(op)

    def note_paired(self, op_id: str, utility: float) -> None:
        if self.frozen:
            return
        op = self.ops.get(op_id)
        if op is None:
            return
        op.record_utility(utility, real=False, task_id=None, origin=None, success=utility > 0)

    def bump_selector(self, arm: str, reward: float) -> None:
        if self.frozen:
            return
        row = self.selector.setdefault(arm, {"n": 0, "sum": 0.0})
        row["n"] += 1
        row["sum"] += float(reward)

    def end_box(self, used_beneficial: set[str]) -> None:
        if self.frozen:
            return
        for op in list(self.ops.values()):
            if op.status != "provisional":
                continue
            if op.op_id in used_beneficial:
                op.stats["boxes_since_benefit"] = 0
            else:
                op.stats["boxes_since_benefit"] = int(op.stats.get("boxes_since_benefit", 0)) + 1
                if op.stats["boxes_since_benefit"] >= self.expiry_boxes:
                    self._evict(op.op_id, "expiry")
        self._evict_until_fit()

    def _maybe_confirm(self, op: Operation) -> None:
        if op.status == "confirmed":
            return
        tasks = list(op.stats.get("real_task_ids", []))
        uses = int(op.stats.get("real_uses", 0))
        agg = float(op.stats.get("utility_sum", 0.0))
        if uses >= self.confirm_uses and agg > 0 and len(tasks) >= self.confirm_tasks:
            op.status = "confirmed"
            op.confirmation_scope = "cross_task"
            self.events.append({"type": "confirmation", "op_id": op.op_id, "scope": "cross_task"})
        elif uses >= self.confirm_uses and agg > 0 and len(tasks) == 1:
            op.confirmation_scope = "same_task"
            if op.status == "provisional":
                op.status = "same_task_reuse"
            self.events.append({"type": "confirmation", "op_id": op.op_id, "scope": "same_task"})

    def _dependents(self, op_id: str) -> set[str]:
        deps: set[str] = set()
        for other_id, other in self.ops.items():
            if op_id in other.parents or op_id in call_ids(other.ast):
                deps.add(other_id)
        return deps

    def _closure(self, op_id: str) -> set[str]:
        """Op plus parents that would dangle, transitively."""
        closure = {op_id}
        changed = True
        while changed:
            changed = False
            for oid in list(closure):
                for dep in self._dependents(oid):
                    if dep not in closure:
                        closure.add(dep)
                        changed = True
        return closure

    def _evict(self, op_id: str, reason: str) -> None:
        if self.frozen or op_id not in self.ops:
            return
        closure = self._closure(op_id)
        if closure & self._protected:
            return
        for cid in sorted(closure):
            op = self.ops.get(cid)
            if op is None:
                continue
            op.status = "evicted"
            op.stats["eviction_reason"] = reason
            self.events.append({"type": "eviction", "op_id": cid, "reason": reason})
            self.ops.pop(cid, None)
            self.evictions += 1

    def _pick_victim(self) -> str | None:
        provisional = [op for op in self.ops.values() if op.status == "provisional" and op.op_id not in self._protected]
        pool = provisional or [op for op in self.ops.values() if op.op_id not in self._protected]
        if not pool:
            return None
        def key(op: Operation):
            utility = mean_utility(op.stats)
            size = max(1, op.logical_bytes())
            per_byte = utility / size
            # Provisional records leave first; then low value per byte. Tie-break by id.
            return (0 if op.status == "provisional" else 1, per_byte, utility, op.op_id)
        pool.sort(key=key)
        return pool[0].op_id

    def _evict_until_fit(self) -> bool:
        if self.byte_cap <= 0:
            for oid in list(self.ops):
                self._evict(oid, "zero_capacity")
            return False
        guard = 0
        while self.logical_bytes() > self.byte_cap and self.ops and guard < 10000:
            guard += 1
            victim = self._pick_victim()
            if victim is None:
                return False
            before = set(self.ops)
            self._evict(victim, "capacity")
            if set(self.ops) == before:
                return False
        return self.logical_bytes() <= self.byte_cap

    def confirmed_ops(self) -> list[Operation]:
        return [op for op in self.ops.values() if op.status == "confirmed"]

    def useful_count(self) -> int:
        return sum(
            1
            for op in self.ops.values()
            if op.status in {"confirmed", "same_task_reuse"} or (
                op.status == "provisional" and int(op.stats.get("real_uses", 0)) > 0 and float(op.stats.get("utility_sum", 0.0)) > 0
            )
        )
