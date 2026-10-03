"""Neutral observable features. No shape-class detector and no hard hole filter."""

from __future__ import annotations

from mga2.pieces import BOARD_SIZE, FULL_MASK, NEIGHBORS, N_CELLS, max_piece_area

FEATURE_NAMES: tuple[str, ...] = (
    "norm_area",
    "boundary_contacts",
    "occupied_contacts",
    "empty_cc_count",
    "empty_cc_mean_size",
    "inventory_fraction",
    "filled_fraction",
    "candidate_count",
    "remaining_physical",
    "remaining_compute",
    "rollout_outcome",
)


def empty_components(mask: int) -> tuple[int, float]:
    """Count and mean size of empty 4-connected components on the current board."""
    empty = FULL_MASK ^ (mask & FULL_MASK)
    seen = 0
    count = 0
    total = 0
    remaining = empty
    while remaining:
        bit = remaining & -remaining
        stack = bit
        comp = 0
        while stack:
            b = stack & -stack
            stack ^= b
            if b & comp:
                continue
            comp |= b
            idx = b.bit_length() - 1
            x = idx % BOARD_SIZE
            y = idx // BOARD_SIZE
            for dx, dy in NEIGHBORS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    nb = 1 << (ny * BOARD_SIZE + nx)
                    if (nb & empty) and not (nb & comp):
                        stack |= nb
        seen |= comp
        remaining &= ~comp
        count += 1
        total += comp.bit_count()
    mean = (total / count) if count else 0.0
    return count, mean


def board_features(env, budgets, candidate_count: int) -> dict[str, float]:
    cc, mean = empty_components(env.mask)
    phys_room = max(0, budgets.physical_cap - env.actions_used) / max(1, budgets.physical_cap)
    eval_room = max(0, budgets.eval_cap - budgets.candidate_evals) / max(1, budgets.eval_cap)
    return {
        "empty_cc_count": cc / N_CELLS,
        "empty_cc_mean_size": mean / N_CELLS,
        "filled_fraction": env.score / N_CELLS,
        "candidate_count": candidate_count / max(1, len_hint()),
        "remaining_physical": phys_room,
        "remaining_compute": eval_room,
    }


def len_hint() -> int:
    from mga2.pieces import ALL_PLACEMENTS

    return max(1, len(ALL_PLACEMENTS))


def candidate_features(
    env,
    index: int,
    board: dict[str, float],
    rollout_outcome: float = 0.0,
) -> dict[str, float]:
    from mga2.pieces import P_AREAS, P_BOUNDARY, P_NEIGH, P_TYPES

    occ = env.mask
    area = P_AREAS[index]
    contacts = (P_NEIGH[index] & occ).bit_count()
    inv_frac = 1.0
    if not env.inventory.unlimited:
        t = P_TYPES[index]
        initial = env.inventory.initial.get(t, 0)
        inv_frac = (env.inventory.counts.get(t, 0) / initial) if initial else 0.0
    feats = dict(board)
    feats.update(
        {
            "norm_area": area / max_piece_area(),
            "boundary_contacts": P_BOUNDARY[index] / 28.0,
            "occupied_contacts": contacts / 28.0,
            "inventory_fraction": inv_frac,
            "rollout_outcome": rollout_outcome,
        }
    )
    return feats


def dot(weights: dict[str, float], feats: dict[str, float]) -> float:
    score = 0.0
    for name in FEATURE_NAMES:
        score += float(weights.get(name, 0.0)) * float(feats.get(name, 0.0))
    return score


def zero_weights() -> dict[str, float]:
    return {name: 0.0 for name in FEATURE_NAMES}
