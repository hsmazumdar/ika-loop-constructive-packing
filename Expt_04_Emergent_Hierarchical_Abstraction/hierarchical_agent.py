"""Hierarchical memory: a learned operation may contain earlier learned operations.

Depth is an outcome of promotion, not a target the controller chases.
"""

from __future__ import annotations

from flat_memory_agent import make_memory
from primitive_agent import PrimitiveAgent


class HierarchicalAgent(PrimitiveAgent):
    name = "hierarchical"

    def __init__(self, config, unlimited: bool = False) -> None:
        super().__init__(
            config,
            memory=make_memory(config, hierarchical=True, unlimited=unlimited, control=False),
        )
        self.unlimited = unlimited
        if unlimited:
            self.name = "hierarchical_unlimited"

    def enabled(self) -> bool:
        return True
