"""Board isometries that preserve the packing problem when piece orientations allow them.

Declared candidates are the non-identity elements of D4. A transform is applicable
only if every placement in a continuation maps to a catalogue orientation of the
same piece type. Reflections of chiral pieces often do not. This module does not
invent transforms.
"""

from __future__ import annotations

from pieces import ALL_PLACEMENTS, BOARD_SIZE, PIECE_TYPES, bit_for, cell_coords, cells_mask, placed_cells

CANDIDATES: tuple[str, ...] = (
    "rot90",
    "rot180",
    "rot270",
    "refl_x",
    "refl_y",
    "refl_d",
    "refl_ad",
)

_INVERSE = {
    "rot90": "rot270",
    "rot180": "rot180",
    "rot270": "rot90",
    "refl_x": "refl_x",
    "refl_y": "refl_y",
    "refl_d": "refl_d",
    "refl_ad": "refl_ad",
}

_PLACEMENT_BY_TYPE_MASK: dict[tuple[str, int], tuple] = {}
for _p in ALL_PLACEMENTS:
    _PLACEMENT_BY_TYPE_MASK[(_p.piece_type, _p.mask)] = (_p.piece_type, _p.rotation, _p.x, _p.y)


def inverse(name: str) -> str:
    return _INVERSE[name]


def transform_cell(name: str, x: int, y: int) -> tuple[int, int]:
    n = BOARD_SIZE
    if name == "rot90":
        return n - 1 - y, x
    if name == "rot180":
        return n - 1 - x, n - 1 - y
    if name == "rot270":
        return y, n - 1 - x
    if name == "refl_x":
        return n - 1 - x, y
    if name == "refl_y":
        return x, n - 1 - y
    if name == "refl_d":
        return y, x
    if name == "refl_ad":
        return n - 1 - y, n - 1 - x
    raise KeyError(name)


def transform_mask(name: str, mask: int) -> int:
    out = 0
    remaining = int(mask)
    while remaining:
        bit = remaining & -remaining
        x, y = cell_coords(bit.bit_length() - 1)
        nx, ny = transform_cell(name, x, y)
        out |= bit_for(nx, ny)
        remaining ^= bit
    return out


def transform_placement(name: str, piece: str, rotation: int, x: int, y: int) -> tuple | None:
    cells = placed_cells(piece, rotation, x, y)
    mapped = tuple(transform_cell(name, cx, cy) for cx, cy in cells)
    found = _PLACEMENT_BY_TYPE_MASK.get((piece, cells_mask(mapped)))
    return found


def transform_suffix(name: str, suffix: list[tuple]) -> list[tuple] | None:
    out = []
    for piece, rotation, x, y in suffix:
        mapped = transform_placement(name, piece, rotation, x, y)
        if mapped is None:
            return None
        out.append(mapped)
    return out


def is_symmetric(name: str, mask: int) -> bool:
    return transform_mask(name, mask) == int(mask)


def counts_tuple(counts: dict[str, int]) -> tuple[int, ...]:
    return tuple(int(counts.get(t, 0)) for t in PIECE_TYPES)


class TransformSelector:
    """Select useful supplied transforms from experience. No usefulness labels in.

    Selection rule is frozen from Expt-11. Coverage stats are recorded separately:
    attempts, compatible keys, valid replays, successes. Zero successes with zero
    compatible keys is insufficient coverage, not evidence that T is useless.
    """

    def __init__(self) -> None:
        self.attempts: dict[str, int] = {name: 0 for name in CANDIDATES}
        self.compatible: dict[str, int] = {name: 0 for name in CANDIDATES}
        self.valid_replays: dict[str, int] = {name: 0 for name in CANDIDATES}
        self.success: dict[str, int] = {name: 0 for name in CANDIDATES}
        self.fail: dict[str, int] = {name: 0 for name in CANDIDATES}
        self.frozen = False
        self.chosen: tuple[str, ...] = ()

    def note_attempt(self, name: str) -> None:
        if not self.frozen and name in self.attempts:
            self.attempts[name] += 1

    def observe(self, name: str, *, transformed_ok: bool, validation_ok: bool, acceptable: bool) -> None:
        if self.frozen or name not in self.success:
            return
        if transformed_ok:
            self.compatible[name] += 1
        if transformed_ok and validation_ok:
            self.valid_replays[name] += 1
        if transformed_ok and validation_ok and acceptable:
            self.success[name] += 1
        elif transformed_ok:
            self.fail[name] += 1

    def freeze(self) -> tuple[str, ...]:
        chosen = []
        for name in CANDIDATES:
            ok = self.success[name]
            bad = self.fail[name]
            # Declared Expt-11 rule: keep T iff experience showed valid successful reuse and no failed reuse.
            if ok >= 1 and bad == 0:
                chosen.append(name)
        self.chosen = tuple(chosen)
        self.frozen = True
        return self.chosen

    def as_dict(self) -> dict:
        coverage = {}
        for name in CANDIDATES:
            coverage[name] = {
                "attempts": self.attempts[name],
                "compatible": self.compatible[name],
                "valid_replays": self.valid_replays[name],
                "successes": self.success[name],
                "fails": self.fail[name],
                "insufficient_coverage": self.compatible[name] == 0,
            }
        return {
            "candidates": list(CANDIDATES),
            "coverage": coverage,
            "success": dict(self.success),
            "fail": dict(self.fail),
            "selected": list(self.chosen),
            "rule": "select T if train successes >= 1 and train validation/transform failures == 0",
            "does_not_invent_transforms": True,
            "zero_success_without_compatible_is_not_useless": True,
        }


def remaining_table_match(mask: int, inv: tuple[int, ...], table) -> dict | None:
    """Identity or any permitted T with a transformable stored suffix. No billing."""
    if table.lookup_key(int(mask), tuple(inv)) is not None:
        return {"via": "identity", "transform": None}
    for name in CANDIDATES:
        stored = table.lookup_key(transform_mask(inverse(name), int(mask)), tuple(inv))
        if stored is None:
            continue
        if transform_suffix(name, stored) is not None:
            return {"via": "equivalence", "transform": name}
    return None
