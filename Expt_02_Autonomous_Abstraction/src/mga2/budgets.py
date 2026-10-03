"""Physical and mental resource counters. Logging is not policy compute."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class BudgetLedger:
    physical_cap: int = 100
    model_cap: int = 10_000
    eval_cap: int = 50_000
    planning_cap: int = 128 * 1024
    physical: int = 0
    model_transitions: int = 0
    candidate_evals: int = 0
    planning_peak: int = 0
    macro_invocations: int = 0
    primitive_decisions: int = 0
    think_batches: int = 0
    logging_events: int = 0
    eval_ceiling: int | None = None
    model_ceiling: int | None = None
    # When positive, deliberation stops this many evaluations before the cap
    # so one cheap eligibility scan can still run.
    cheap_reserve: int = 0
    protect_reserve: bool = True
    cheap_actions: int = 0
    tally_stack: list = field(default_factory=list)
    part_think: int = 0
    part_paired: int = 0
    part_guard: int = 0
    part_selection: int = 0
    part_other: int = 0
    span_think: int = 0
    span_paired: int = 0
    # Partition of candidate evaluations for a decision trace.
    # Paired tests include the guard scans inside them. Library scans are
    # origin checks for a stored operation on the real board.
    buckets: dict = field(default_factory=dict)

    def eval_limit(self) -> int:
        if self.eval_ceiling is None:
            return self.eval_cap
        return min(self.eval_cap, self.eval_ceiling)

    def model_limit(self) -> int:
        if self.model_ceiling is None:
            return self.model_cap
        return min(self.model_cap, self.model_ceiling)

    def eval_spend_limit(self) -> int:
        hard = self.eval_limit()
        if self.protect_reserve and self.cheap_reserve > 0:
            protected = max(0, self.eval_cap - self.cheap_reserve)
            hard = min(hard, protected)
        return hard

    def can_eval(self) -> bool:
        return self.candidate_evals < self.eval_spend_limit()

    def reserve_remaining(self) -> bool:
        """True when the true cap still allows an eligibility scan."""
        return self.candidate_evals < self.eval_limit()

    def can_simulate(self) -> bool:
        return self.model_transitions < self.model_limit()

    def charge_eval(self, n: int = 1) -> int:
        room = self.eval_spend_limit() - self.candidate_evals
        take = max(0, min(int(n), room))
        self.candidate_evals += take
        if take:
            top = self.tally_stack[-1] if self.tally_stack else "other"
            if top == "think":
                self.part_think += take
            elif top == "paired":
                self.part_paired += take
            elif top == "guard":
                self.part_guard += take
            elif top == "selection":
                self.part_selection += take
            else:
                self.part_other += take
            if "think" in self.tally_stack:
                self.span_think += take
            if "paired" in self.tally_stack:
                self.span_paired += take
            bucket = self.decision_bucket()
            self.buckets[bucket] = self.buckets.get(bucket, 0) + take
        return take

    def decision_bucket(self) -> str:
        stack = self.tally_stack
        if "paired" in stack:
            return "paired"
        if "lookahead" in stack:
            return "lookahead"
        if "candidate" in stack:
            return "candidate"
        if "library" in stack:
            return "library_scan"
        if "placement" in stack:
            return "placement"
        if "think" in stack:
            return "think"
        return "other"

    @contextmanager
    def tally(self, name: str):
        self.tally_stack.append(name)
        try:
            yield
        finally:
            self.tally_stack.pop()

    def charge_model(self, n: int = 1) -> int:
        room = self.model_limit() - self.model_transitions
        take = max(0, min(int(n), room))
        self.model_transitions += take
        return take

    def note_planning(self, nbytes: int) -> bool:
        if nbytes > self.planning_peak:
            self.planning_peak = nbytes
        return nbytes <= self.planning_cap

    def note_log(self, n: int = 1) -> None:
        """Experiment logging. Not charged to policy computation."""
        self.logging_events += n

    def push_ceilings(self, eval_share: int, model_share: int) -> tuple[int | None, int | None]:
        prev = (self.eval_ceiling, self.model_ceiling)
        self.eval_ceiling = self.candidate_evals + max(0, eval_share)
        self.model_ceiling = self.model_transitions + max(0, model_share)
        return prev

    def pop_ceilings(self, prev: tuple[int | None, int | None]) -> None:
        self.eval_ceiling, self.model_ceiling = prev

    def as_dict(self) -> dict:
        return {
            "physical": self.physical,
            "physical_cap": self.physical_cap,
            "model_transitions": self.model_transitions,
            "model_cap": self.model_cap,
            "candidate_evals": self.candidate_evals,
            "eval_cap": self.eval_cap,
            "planning_peak": self.planning_peak,
            "planning_cap": self.planning_cap,
            "macro_invocations": self.macro_invocations,
            "primitive_decisions": self.primitive_decisions,
            "think_batches": self.think_batches,
            "logging_events": self.logging_events,
            "cheap_actions": self.cheap_actions,
            "cheap_reserve": self.cheap_reserve,
            "part_think": self.part_think,
            "part_paired": self.part_paired,
            "part_guard": self.part_guard,
            "part_selection": self.part_selection,
            "part_other": self.part_other,
            "span_think": self.span_think,
            "span_paired": self.span_paired,
            "buckets": dict(self.buckets),
        }


def ledger_from_config(cfg: dict) -> BudgetLedger:
    b = cfg.get("budgets", {})
    return BudgetLedger(
        physical_cap=int(b.get("physical_actions", 100)),
        model_cap=int(b.get("model_transitions", 10_000)),
        eval_cap=int(b.get("candidate_evals", 50_000)),
        planning_cap=int(b.get("planning_bytes", 128 * 1024)),
    )


@dataclass
class UtilityWeights:
    fill_scale: float = 100.0
    physical_weight: float = 0.002
    transition_weight: float = 0.0001
    horizon: int = 8

    @staticmethod
    def from_config(cfg: dict) -> "UtilityWeights":
        u = cfg.get("utility", {})
        return UtilityWeights(
            fill_scale=float(u.get("fill_scale", 100.0)),
            physical_weight=float(u.get("physical_weight", 0.002)),
            transition_weight=float(u.get("transition_weight", 0.0001)),
            horizon=int(u.get("horizon", 8)),
        )


def utility(delta_filled: float, physical_actions: float, model_transitions: float, w: UtilityWeights) -> float:
    """Published engineering utility. Footprint shape class is not a term."""
    return (
        float(delta_filled) / w.fill_scale
        - w.physical_weight * float(physical_actions)
        - w.transition_weight * float(model_transitions)
    )
