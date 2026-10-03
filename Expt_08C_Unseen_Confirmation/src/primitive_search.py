"""Primitive fallback search. Documented Expt-3 score; not used to mine operations."""

from __future__ import annotations

from pieces import ALL_PLACEMENTS


def primitive_choice(env, rng, scan: int, area_w: float, contact_w: float, boundary_w: float, tabu: set | None = None):
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
