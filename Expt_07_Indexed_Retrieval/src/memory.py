"""Operations with explicit status: provisional, active, or inactive.

Neutral names only (M0001, ...). No shape labels.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


def _zeros(n: int) -> list[float]:
    return [0.0] * n


@dataclass
class ApplicabilityRule:
    """Learned from success and failure contexts. Checking it is charged."""

    dim: int
    success_sum: list[float] = field(default_factory=list)
    fail_sum: list[float] = field(default_factory=list)
    success_n: int = 0
    fail_n: int = 0
    threshold: float = 0.05

    def __post_init__(self) -> None:
        if not self.success_sum:
            self.success_sum = _zeros(self.dim)
        if not self.fail_sum:
            self.fail_sum = _zeros(self.dim)

    def observe(self, features: list[float] | tuple[float, ...], useful: bool) -> None:
        vec = list(features)
        if len(vec) != self.dim:
            return
        if useful:
            self.success_n += 1
            self.success_sum = [a + b for a, b in zip(self.success_sum, vec)]
        else:
            self.fail_n += 1
            self.fail_sum = [a + b for a, b in zip(self.fail_sum, vec)]
        self._refresh_threshold()

    def _mean(self, total: list[float], n: int) -> list[float] | None:
        if n <= 0:
            return None
        return [v / n for v in total]

    def _refresh_threshold(self) -> None:
        if self.success_n >= 2 and self.fail_n >= 2:
            self.threshold = 0.0
        elif self.success_n >= 1:
            self.threshold = max(self.threshold, 0.05)

    def score(self, features: list[float] | tuple[float, ...]) -> float:
        from retrieval import cosine

        vec = list(features)
        success = self._mean(self.success_sum, self.success_n)
        fail = self._mean(self.fail_sum, self.fail_n)
        if success is None and fail is None:
            return 0.0
        if success is None:
            return -cosine(vec, fail)
        if fail is None:
            return cosine(vec, success)
        return cosine(vec, success) - cosine(vec, fail)

    def useful_here(self, features: list[float] | tuple[float, ...]) -> tuple[bool, float]:
        if self.success_n == 0 and self.fail_n == 0:
            return True, 0.0
        value = self.score(features)
        return value > self.threshold, value


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
    status: str = "provisional"
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    attempts_saved: float = 0.0
    q_sum: float = 0.0
    age_penalty: float = 0.0
    utility: float = 0.0
    retrievals: int = 0
    applicability_failures: int = 0
    commitments: int = 0
    paired_savings: float = 0.0
    applicability: ApplicabilityRule | None = None

    def ensure_rule(self, dim: int, threshold: float) -> ApplicabilityRule:
        if self.applicability is None:
            self.applicability = ApplicabilityRule(dim=dim, threshold=threshold)
        return self.applicability

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
            - 0.01 * self.applicability_failures
            + self.paired_savings
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
    hierarchical: bool
    episodic_capacity: int
    operation_capacity: int
    provisional_capacity: int
    byte_cap: int
    decay: float
    fail_penalty: float
    storage_weight: float
    max_depth: int
    retire_utility: float
    env_discount: float
    selective_retire: bool = True
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

    def all_by_status(self, status: str) -> list[LearnedOperation]:
        return [op for op in self.operations if op.status == status]

    def active(self) -> list[LearnedOperation]:
        return self.all_by_status("active")

    def contains_canonical(self, canonical: str) -> bool:
        return any(op.canonical == canonical for op in self.operations)

    def add_operation(self, op: LearnedOperation, time: int) -> bool:
        if op.depth > self.max_depth:
            return False
        if self.contains_canonical(op.canonical):
            return False
        self.operations.append(op)
        self.events.append(
            {"time": time, "kind": "create", "op_id" : op.op_id, "depth": op.depth, "status": op.status, "nbytes": op.nbytes}
        )
        self.enforce_pressure(time)
        return any(item.op_id == op.op_id for item in self.operations)

    def promote(self, op: LearnedOperation, time: int, reason: str) -> None:
        op.status = "active"
        self.events.append({"time": time, "kind": "promote", "op_id": op.op_id, "reason": reason})
        self.enforce_pressure(time)

    def deactivate(self, op: LearnedOperation, time: int, reason: str) -> None:
        op.status = "inactive"
        self.events.append({"time": time, "kind": "deactivate", "op_id": op.op_id, "reason": reason, "utility": op.utility})

    def note_retrieval(self, op: LearnedOperation) -> None:
        op.retrievals += 1

    def note_applicability_failure(self, op: LearnedOperation) -> None:
        op.applicability_failures += 1
        op.recompute(self.fail_penalty, self.storage_weight)

    def note_use(self, op: LearnedOperation, success: bool, saved: float, q: float, time: int, features=None) -> None:
        op.attempts += 1
        op.last_used = time
        if success:
            op.successes += 1
            op.commitments += 1
            op.attempts_saved += saved
            op.q_sum += q
        else:
            op.failures += 1
        if features is not None:
            rule = op.ensure_rule(len(features), 0.05)
            rule.observe(features, success)
        op.recompute(self.fail_penalty, self.storage_weight)

    def discount_after_change(self, time: int) -> None:
        factor = self.env_discount
        for op in self.operations:
            op.successes = int(op.successes * factor)
            op.failures = int(op.failures * factor)
            op.attempts_saved *= factor
            op.paired_savings *= factor
            op.q_sum *= factor
            if op.applicability is not None:
                op.applicability.success_n = int(op.applicability.success_n * factor)
                op.applicability.fail_n = int(op.applicability.fail_n * factor)
                op.applicability.success_sum = [v * factor for v in op.applicability.success_sum]
                op.applicability.fail_sum = [v * factor for v in op.applicability.fail_sum]
            op.recompute(self.fail_penalty, self.storage_weight)
            if self.selective_retire and op.status == "active" and op.utility < self.retire_utility:
                self.deactivate(op, time, "lost_usefulness_after_change")
        self.events.append({"time": time, "kind": "environment_discount", "factor": factor})

    def age(self, time: int) -> None:
        if self.decay <= 0:
            return
        for op in self.operations:
            if op.status != "active":
                continue
            if op.last_used < time:
                op.age_penalty += self.decay
            if op.failures > op.successes and op.attempts >= 2:
                op.age_penalty += self.decay
            op.recompute(self.fail_penalty, self.storage_weight)
            if self.selective_retire and op.utility < self.retire_utility and op.attempts >= 3:
                self.deactivate(op, time, "lost_usefulness")

    def enforce_pressure(self, time: int) -> None:
        provisional = self.all_by_status("provisional")
        while len(provisional) > self.provisional_capacity:
            victim = min(provisional, key=lambda op: (op.utility, op.op_id))
            self.operations.remove(victim)
            self.events.append({"time": time, "kind": "drop_provisional", "op_id": victim.op_id})
            provisional = self.all_by_status("provisional")
        active = self.active()
        while active and (
            len(active) > self.operation_capacity or sum(op.nbytes for op in active) > self.byte_cap
        ):
            victim = min(active, key=lambda op: (op.utility, op.op_id))
            self.deactivate(victim, time, "memory_pressure")
            active = self.active()

    def bytes_used(self) -> int:
        return sum(op.nbytes for op in self.active())

    def snapshot_active(self) -> list[LearnedOperation]:
        return list(self.active())


def clone_active(memory: OperationMemory) -> OperationMemory:
    copied = OperationMemory(
        hierarchical=memory.hierarchical,
        episodic_capacity=memory.episodic_capacity,
        operation_capacity=memory.operation_capacity,
        provisional_capacity=memory.provisional_capacity,
        byte_cap=memory.byte_cap,
        decay=memory.decay,
        fail_penalty=memory.fail_penalty,
        storage_weight=memory.storage_weight,
        max_depth=memory.max_depth,
        retire_utility=memory.retire_utility,
        env_discount=memory.env_discount,
        selective_retire=memory.selective_retire,
    )
    copied._next_id = memory._next_id
    for op in memory.operations:
        copied.operations.append(replace(op, applicability=None if op.applicability is None else replace(op.applicability)))
    return copied


def clone_library_only(memory: OperationMemory) -> OperationMemory:
    """Transfer active operations and applicability rules. Episodes are dropped."""
    copied = OperationMemory(
        hierarchical=memory.hierarchical,
        episodic_capacity=memory.episodic_capacity,
        operation_capacity=memory.operation_capacity,
        provisional_capacity=memory.provisional_capacity,
        byte_cap=memory.byte_cap,
        decay=memory.decay,
        fail_penalty=memory.fail_penalty,
        storage_weight=memory.storage_weight,
        max_depth=memory.max_depth,
        retire_utility=memory.retire_utility,
        env_discount=memory.env_discount,
        selective_retire=False,
    )
    copied._next_id = memory._next_id
    for op in memory.active():
        rule = None
        if op.applicability is not None:
            rule = replace(
                op.applicability,
                success_sum=list(op.applicability.success_sum),
                fail_sum=list(op.applicability.fail_sum),
            )
        copied.operations.append(
            replace(
                op,
                status="active",
                applicability=rule,
                context=list(op.context),
                children=list(op.children),
                steps=[dict(step) for step in op.steps],
            )
        )
    return copied


def make_memory(config, hierarchical: bool = True, selective_retire: bool = True) -> OperationMemory:
    return OperationMemory(
        hierarchical=hierarchical,
        episodic_capacity=int(config.episodic_capacity),
        operation_capacity=int(config.operation_capacity),
        provisional_capacity=int(config.provisional_capacity),
        byte_cap=int(config.byte_cap),
        decay=float(config.decay),
        fail_penalty=float(config.fail_penalty),
        storage_weight=float(config.storage_weight),
        max_depth=1 if not hierarchical else int(config.max_depth),
        retire_utility=float(config.retire_utility),
        env_discount=float(config.env_discount),
        selective_retire=selective_retire,
    )
