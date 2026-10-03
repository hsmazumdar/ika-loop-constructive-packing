"""Short-term memory: recent trace, candidates, and selector statistics.

Statistics are sampled before ``clear`` so box-end logs are not forced to zero.
"""

from __future__ import annotations

from mga2.ops import Operation, canonical_bytes


class ShortTermMemory:
    def __init__(self, byte_cap: int) -> None:
        self.byte_cap = int(byte_cap)
        self.trace: list[dict] = []
        self.sim_traces: list[list[dict]] = []
        self.candidates: dict[str, Operation] = {}
        self.failures: list[dict] = []
        self.selector: dict[str, dict] = {}
        self.samples: list[int] = []
        self.peak_bytes = 0
        self.events: list[dict] = []

    def __len__(self) -> int:
        return len(self.candidates) + len(self.trace)

    def sample(self) -> int:
        size = self.logical_bytes()
        self.samples.append(size)
        if size > self.peak_bytes:
            self.peak_bytes = size
        return size

    def logical_bytes(self) -> int:
        payload = {
            "trace": self.trace,
            "sim_traces": self.sim_traces,
            "candidates": {k: op.storage_dict() for k, op in sorted(self.candidates.items())},
            "failures": self.failures[-32:],
            "selector": self.selector,
        }
        return canonical_bytes(payload)

    def snapshot_stats(self) -> dict:
        self.sample()
        avg = (sum(self.samples) / len(self.samples)) if self.samples else 0.0
        return {
            "entries": len(self.candidates),
            "trace_len": len(self.trace),
            "peak_bytes": self.peak_bytes,
            "avg_bytes": avg,
            "bytes": self.logical_bytes(),
        }

    def clear(self) -> None:
        self.trace.clear()
        self.sim_traces.clear()
        self.candidates.clear()
        self.failures.clear()
        self.selector.clear()
        self.samples.clear()
        self.peak_bytes = 0
        self.events.clear()

    def add_trace(self, placement: dict) -> None:
        self.trace.append(placement)
        self._fit()
        self.sample()

    def add_sim_trace(self, placements: list[dict]) -> None:
        if placements:
            self.sim_traces.append(list(placements))
            self.sim_traces = self.sim_traces[-4:]
            self._fit()

    def add_candidate(self, op: Operation) -> bool:
        if self.byte_cap <= 0:
            return False
        self.candidates[op.op_id] = op
        self._fit()
        self.sample()
        return op.op_id in self.candidates

    def note_failure(self, record: dict) -> None:
        self.failures.append(record)
        self.failures = self.failures[-64:]
        self._fit()

    def bump_selector(self, arm: str, reward: float) -> None:
        row = self.selector.setdefault(arm, {"n": 0, "sum": 0.0})
        row["n"] += 1
        row["sum"] += float(reward)
        self._fit()

    def _fit(self) -> None:
        if self.byte_cap <= 0:
            self.trace.clear()
            self.sim_traces.clear()
            self.candidates.clear()
            self.failures.clear()
            return
        guard = 0
        while self.logical_bytes() > self.byte_cap and guard < 10000:
            guard += 1
            if self.trace:
                self.trace.pop(0)
                continue
            if self.sim_traces:
                self.sim_traces.pop(0)
                continue
            if self.failures:
                self.failures.pop(0)
                continue
            if self.candidates:
                worst = min(self.candidates, key=lambda i: (self.candidates[i].stats.get("utility_sum", 0.0), i))
                self.candidates.pop(worst, None)
                continue
            break
