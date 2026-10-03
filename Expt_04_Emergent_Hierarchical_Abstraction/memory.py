"""Episodic memory and learned-operation memory.

Capacity is finite. Operations compete on utility and can be forgotten.
Neutral names are M0001, M0002, ... No shape names are assigned.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LearnedOperation:
    op_id: str
    depth: int
    children: list[str]
    steps: list[dict]
    nbytes: int
    canonical: str
    context: list[float]
    created_at: int
    last_used: int
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    attempts_saved: float = 0.0
    q_sum: float = 0.0
    age_penalty: float = 0.0
    utility: float = 0.0

    @property
    def average_q(self) -> float | None:
        if self.successes <= 0:
            return None
        return self.q_sum / self.successes

    def recompute(self, fail_penalty: float, storage_weight: float) -> None:
        self.utility = (
            self.successes * (1.0 + self.attempts_saved)
            - self.failures * fail_penalty
            - self.nbytes * storage_weight
            - self.age_penalty
        )


@dataclass
class Episode:
    episode_id: int
    task_id: str
    inventory: dict
    decisions: list[dict]
    q: float
    a: int
    acceptable: bool


@dataclass
class OperationMemory:
    """Learned operations plus a bounded buffer of successful episodes."""

    hierarchical: bool
    unlimited: bool
    control: bool
    episodic_capacity: int
    operation_capacity: int
    byte_cap: int
    decay: float
    fail_penalty: float
    storage_weight: float
    max_depth: int
    episodes: list[Episode] = field(default_factory=list)
    operations: list[LearnedOperation] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    _next_id: int = 1

    def next_name(self) -> str:
        name = f"M{self._next_id:04d}"
        self._next_id += 1
        return name

    def remember_episode(self, episode: Episode) -> None:
        self.episodes.append(episode)
        if len(self.episodes) > self.episodic_capacity:
            dropped = self.episodes.pop(0)
            self.events.append({"time": episode.episode_id, "kind": "forget_episode", "episode_id": dropped.episode_id})

    def contains_canonical(self, canonical: str) -> bool:
        return any(op.canonical == canonical for op in self.operations)

    def add_operation(self, op: LearnedOperation, time: int) -> bool:
        if op.depth > self.max_depth:
            return False
        if not self.hierarchical and op.depth > 1:
            return False
        if self.contains_canonical(op.canonical):
            return False
        self.operations.append(op)
        self.events.append({"time": time, "kind": "create", "op_id": op.op_id, "depth": op.depth, "nbytes": op.nbytes})
        self.enforce_pressure(time)
        return op.op_id in {item.op_id for item in self.operations}

    def note_use(self, op: LearnedOperation, success: bool, saved: float, q: float, time: int) -> None:
        op.attempts += 1
        op.last_used = time
        if success:
            op.successes += 1
            op.attempts_saved += saved
            op.q_sum += q
            blend = 0.2
            # Context is updated by the caller when a feature vector is available.
        else:
            op.failures += 1
        op.recompute(self.fail_penalty, self.storage_weight)
        if not success:
            op.utility -= self.fail_penalty

    def age(self, time: int) -> None:
        if self.unlimited or self.decay <= 0:
            return
        for op in self.operations:
            if op.last_used < time:
                op.age_penalty += self.decay
            if op.failures > op.successes and op.attempts >= 2:
                op.age_penalty += self.decay
            op.recompute(self.fail_penalty, self.storage_weight)

    def enforce_pressure(self, time: int) -> None:
        if self.unlimited:
            return
        while self.operations and (
            len(self.operations) > self.operation_capacity or sum(op.nbytes for op in self.operations) > self.byte_cap
        ):
            victim = min(self.operations, key=lambda op: (op.utility, op.op_id))
            self.operations.remove(victim)
            self.events.append({"time": time, "kind": "delete", "op_id": victim.op_id, "reason": "memory_pressure", "utility": victim.utility})

    def snapshot_operations(self) -> list[LearnedOperation]:
        return list(self.operations)

    def bytes_used(self) -> int:
        return sum(op.nbytes for op in self.operations)


def clone_operations(memory: OperationMemory) -> OperationMemory:
    """Transfer only learned operations. Episodes and events are not copied."""
    copied = OperationMemory(
        hierarchical=memory.hierarchical,
        unlimited=memory.unlimited,
        control=memory.control,
        episodic_capacity=memory.episodic_capacity,
        operation_capacity=memory.operation_capacity,
        byte_cap=memory.byte_cap,
        decay=memory.decay,
        fail_penalty=memory.fail_penalty,
        storage_weight=memory.storage_weight,
        max_depth=memory.max_depth,
    )
    copied._next_id = memory._next_id
    for op in memory.operations:
        copied.operations.append(
            LearnedOperation(
                op_id=op.op_id,
                depth=op.depth,
                children=list(op.children),
                steps=[dict(step) for step in op.steps],
                nbytes=op.nbytes,
                canonical=op.canonical,
                context=list(op.context),
                created_at=op.created_at,
                last_used=op.last_used,
                attempts=op.attempts,
                successes=op.successes,
                failures=op.failures,
                attempts_saved=op.attempts_saved,
                q_sum=op.q_sum,
                age_penalty=op.age_penalty,
                utility=op.utility,
            )
        )
    return copied
