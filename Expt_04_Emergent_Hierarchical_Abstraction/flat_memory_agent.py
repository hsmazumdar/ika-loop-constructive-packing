"""Flat memory: learned operations may contain only primitive actions."""

from __future__ import annotations

from memory import OperationMemory
from primitive_agent import PrimitiveAgent


class FlatMemoryAgent(PrimitiveAgent):
    name = "flat"

    def __init__(self, config) -> None:
        super().__init__(config, memory=make_memory(config, hierarchical=False, unlimited=False, control=False))

    def enabled(self) -> bool:
        return True


def make_memory(config, hierarchical: bool, unlimited: bool, control: bool) -> OperationMemory:
    capacity = 10**9 if unlimited else int(config.operation_capacity)
    byte_cap = 10**12 if unlimited else int(config.byte_cap)
    decay = 0.0 if unlimited else float(config.decay)
    return OperationMemory(
        hierarchical=hierarchical,
        unlimited=unlimited,
        control=control,
        episodic_capacity=10**9 if unlimited else int(config.episodic_capacity),
        operation_capacity=capacity,
        byte_cap=byte_cap,
        decay=decay,
        fail_penalty=float(config.fail_penalty),
        storage_weight=float(config.storage_weight),
        max_depth=int(config.max_depth),
    )
