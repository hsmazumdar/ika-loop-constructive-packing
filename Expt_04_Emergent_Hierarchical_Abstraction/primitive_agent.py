"""Primitive baseline.

The fallback score is the Expt-3 score: area + 0.2 * contact + 0.05 * boundary.
It is a documented human prior so the baseline stays comparable. It is not used
to invent, name, or filter learned operations.

The objective of this experiment is not to discover a better packing heuristic.
Packing is the observable environment. The experiment asks whether repeated
information can autonomously become compressed reusable knowledge, and whether
that knowledge allows future problems to be solved with less deliberation.
"""

from __future__ import annotations

from pieces import ALL_PLACEMENTS


class PrimitiveAgent:
    name = "primitive"

    def __init__(self, config, memory=None) -> None:
        self.config = config
        self.memory = memory

    def enabled(self) -> bool:
        return False


def primitive_choice(env, rng, scan: int, area_w: float, contact_w: float, boundary_w: float, tabu: set | None = None):
    """Examine at most `scan` inventory-legal rows. Returns (index or None, evaluated, failed)."""
    blocked = tabu or set()
    feasible = [
        index
        for index, placement in enumerate(ALL_PLACEMENTS)
        if env.inventory.can_take(placement.piece_type) and placement.signature not in blocked
    ]
    if not feasible:
        return None, 0, 0
    rng.shuffle(feasible)
    window = feasible[:scan]
    best = None
    failed = 0
    for index in window:
        placement = ALL_PLACEMENTS[index]
        if placement.mask & env.mask:
            failed += 1
            continue
        contact = (placement.neighbor_mask & env.mask).bit_count()
        score = area_w * float(placement.area) + contact_w * float(contact) + boundary_w * float(placement.boundary_contacts)
        tie = rng.random()
        if best is None or (score, tie) > best[0]:
            best = ((score, tie), index)
    if best is None:
        return None, len(window), failed
    return best[1], len(window), failed
