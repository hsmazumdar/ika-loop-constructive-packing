"""Control library, distribution shift, transfer, and knockout.

The control agent promotes on the same support rule, then stores a different
random sequence of matched length. It does not keep the mined target sequence.
"""

from __future__ import annotations

import random

from flat_memory_agent import make_memory
from pieces import piece_area
from primitive_agent import PrimitiveAgent


class ControlAgent(PrimitiveAgent):
    name = "control"

    def __init__(self, config) -> None:
        super().__init__(config, memory=make_memory(config, hierarchical=True, unlimited=False, control=True))

    def enabled(self) -> bool:
        return True


def shift_inventory(inventory: dict[str, int], rng: random.Random) -> dict[str, int]:
    """Change piece-size counts without naming a packing strategy.

    Half of the copies of each piece larger than 4 cells are replaced by
    M, N, or O. The board and the catalogue stay the same.
    """
    updated = {name: int(count) for name, count in inventory.items() if int(count) > 0}
    donated = 0
    for name in list(updated):
        if piece_area(name) < 5:
            continue
        move = updated[name] // 2
        if move <= 0:
            continue
        updated[name] -= move
        donated += move
        if updated[name] <= 0:
            del updated[name]
    small = ["M", "N", "O"]
    rng.shuffle(small)
    for index in range(donated):
        name = small[index % 3]
        updated[name] = updated.get(name, 0) + 1
    return updated


def knockout(memory, mode: str, rng: random.Random):
    """Return a transferred copy with some operations removed. Episodes stay empty."""
    from memory import clone_operations

    copied = clone_operations(memory)
    ops = list(copied.operations)
    if mode == "all":
        remove = ops
    elif mode == "highest":
        if not ops:
            remove = []
        else:
            top = max(op.depth for op in ops)
            remove = [op for op in ops if op.depth == top and top > 0]
    elif mode == "frequent":
        ranked = sorted(ops, key=lambda op: (-op.successes, op.op_id))
        remove = ranked[: max(1, len(ranked) // 2)] if ranked else []
    elif mode == "random":
        pool = list(ops)
        rng.shuffle(pool)
        width = max(1, len(pool) // 2) if pool else 0
        remove = pool[:width]
    else:
        raise KeyError(mode)
    removed_ids = {op.op_id for op in remove}
    copied.operations = [op for op in copied.operations if op.op_id not in removed_ids]
    copied.events.append({"time": -1, "kind": "knockout", "mode": mode, "removed": sorted(removed_ids)})
    return copied
