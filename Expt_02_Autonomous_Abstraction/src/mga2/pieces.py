"""Canonical 16-piece catalogue, rotations, and placement enumeration."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

BOARD_SIZE = 10
N_CELLS = BOARD_SIZE * BOARD_SIZE
FULL_MASK = (1 << N_CELLS) - 1

# Exact catalogue from Cursor_Instructions_MGA_Expt01.md. Labels are identifiers.
PIECES: dict[str, tuple[tuple[int, int], ...]] = {
    "A": ((1, 0), (2, 0), (0, 1), (1, 1), (1, 2)),
    "B": ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
    "C": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
    "D": ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3)),
    "E": ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2)),
    "F": ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2)),
    "G": ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1)),
    "H": ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
    "I": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    "J": ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
    "K": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    "L": ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    "M": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "N": ((0, 0), (0, 1), (0, 2), (1, 2)),
    "O": ((0, 0), (1, 0), (2, 0), (1, 1)),
    "P": ((0, 0), (1, 0), (0, 1), (0, 2), (1, 2), (0, 3), (1, 3)),
}

PIECE_TYPES: tuple[str, ...] = tuple(PIECES.keys())
ROTATIONS: tuple[int, ...] = (0, 1, 2, 3)

# Colours matched to MGA_Expt01_Populated_Canvas.png
PIECE_COLORS: dict[str, str] = {
    "A": "#2BBBAD",
    "B": "#F5A623",
    "C": "#5B8DEF",
    "D": "#9B7EDE",
    "E": "#E57BA4",
    "F": "#7ED957",
    "G": "#4ECDC4",
    "H": "#E8913A",
    "I": "#6B7FD7",
    "J": "#D4537E",
    "K": "#88B04B",
    "L": "#F4D03F",
    "M": "#48C9B0",
    "N": "#A1887F",
    "O": "#7F8CFF",
    "P": "#E67E50",
}

NEIGHBORS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def cell_index(x: int, y: int) -> int:
    return y * BOARD_SIZE + x


def cell_coords(index: int) -> tuple[int, int]:
    return index % BOARD_SIZE, index // BOARD_SIZE


def bit_for(x: int, y: int) -> int:
    return 1 << cell_index(x, y)


def normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_x = min(x for x, _ in cells)
    min_y = min(y for _, y in cells)
    return tuple(sorted((x - min_x, y - min_y) for x, y in cells))


def rotate90_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """90° clockwise in screen coordinates (y downward): (x, y) -> (-y, x)."""
    return tuple((-y, x) for x, y in cells)


def reflect_x(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Left-right reflection, used only to prove we do not apply it."""
    return normalize(((-x, y) for x, y in cells))


def orientation(cells: Iterable[tuple[int, int]], k: int) -> tuple[tuple[int, int], ...]:
    coords = tuple(cells)
    for _ in range(k % 4):
        coords = rotate90_cw(coords)
    return normalize(coords)


def unique_orientations(piece_type: str) -> dict[tuple[tuple[int, int], ...], int]:
    """Map distinct normalised cell sets to the first user rotation (0-3) that yields them."""
    seen: dict[tuple[tuple[int, int], ...], int] = {}
    for k in ROTATIONS:
        cells = orientation(PIECES[piece_type], k)
        if cells not in seen:
            seen[cells] = k
    return seen


def placed_cells(piece_type: str, rotation: int, x: int, y: int) -> tuple[tuple[int, int], ...]:
    return tuple((x + dx, y + dy) for dx, dy in orientation(PIECES[piece_type], rotation))


def in_bounds(cells: Iterable[tuple[int, int]]) -> bool:
    for x, y in cells:
        if x < 0 or y < 0 or x >= BOARD_SIZE or y >= BOARD_SIZE:
            return False
    return True


def cells_mask(cells: Iterable[tuple[int, int]]) -> int:
    mask = 0
    for x, y in cells:
        mask |= bit_for(x, y)
    return mask


def is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    cell_set = set(cells)
    if not cell_set:
        return False
    start = next(iter(cell_set))
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for dx, dy in NEIGHBORS:
            nb = (x + dx, y + dy)
            if nb in cell_set and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return seen == cell_set


def bounding_box(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return min(xs), min(ys), max(xs), max(ys)


def piece_area(piece_type: str) -> int:
    return len(PIECES[piece_type])


def min_piece_area() -> int:
    return min(len(c) for c in PIECES.values())


def max_piece_area() -> int:
    return max(len(c) for c in PIECES.values())


def catalogue_payload() -> dict:
    return {
        name: [list(cell) for cell in cells] for name, cells in PIECES.items()
    }


def catalogue_hash() -> str:
    payload = json.dumps(catalogue_payload(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def neighbor_mask_and_boundary(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    own = set(cells)
    nmask = 0
    boundary = 0
    for x, y in cells:
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
                boundary += 1
            elif (nx, ny) not in own:
                nmask |= bit_for(nx, ny)
    return nmask, boundary


@dataclass(frozen=True, slots=True)
class Placement:
    piece_type: str
    rotation: int
    x: int
    y: int
    cells: tuple[tuple[int, int], ...]
    mask: int
    area: int
    signature: tuple
    neighbor_mask: int
    boundary_contacts: int

    @property
    def canon_rotation(self) -> int:
        return self.rotation


def _build_all_placements() -> tuple[Placement, ...]:
    out: list[Placement] = []
    for piece_type in PIECE_TYPES:
        for cells, rot in unique_orientations(piece_type).items():
            w = max(x for x, _ in cells) + 1
            h = max(y for _, y in cells) + 1
            for y in range(BOARD_SIZE - h + 1):
                for x in range(BOARD_SIZE - w + 1):
                    placed = tuple((x + dx, y + dy) for dx, dy in cells)
                    mask = cells_mask(placed)
                    nmask, boundary = neighbor_mask_and_boundary(placed)
                    out.append(
                        Placement(
                            piece_type=piece_type,
                            rotation=rot,
                            x=x,
                            y=y,
                            cells=placed,
                            mask=mask,
                            area=len(placed),
                            signature=(piece_type, rot, x, y),
                            neighbor_mask=nmask,
                            boundary_contacts=boundary,
                        )
                    )
    out.sort(key=lambda p: (p.piece_type, p.rotation, p.y, p.x))
    return tuple(out)


ALL_PLACEMENTS: tuple[Placement, ...] = _build_all_placements()

_PLACEMENT_BY_SIG = {p.signature: p for p in ALL_PLACEMENTS}


def lookup_placement(piece_type: str, rotation: int, x: int, y: int) -> Placement | None:
    """Map a user rotation onto the canonical unique placement, if in-bounds."""
    cells = placed_cells(piece_type, rotation, x, y)
    if not in_bounds(cells):
        return None
    canon = unique_orientations(piece_type)[orientation(PIECES[piece_type], rotation)]
    return _PLACEMENT_BY_SIG.get((piece_type, canon, x, y))


def placements_covering(index: int) -> tuple[Placement, ...]:
    bit = 1 << index
    return tuple(p for p in ALL_PLACEMENTS if p.mask & bit)


P_MASKS: tuple[int, ...] = tuple(p.mask for p in ALL_PLACEMENTS)
P_TYPES: tuple[str, ...] = tuple(p.piece_type for p in ALL_PLACEMENTS)
P_ROTS: tuple[int, ...] = tuple(p.rotation for p in ALL_PLACEMENTS)
P_XS: tuple[int, ...] = tuple(p.x for p in ALL_PLACEMENTS)
P_YS: tuple[int, ...] = tuple(p.y for p in ALL_PLACEMENTS)
P_AREAS: tuple[int, ...] = tuple(p.area for p in ALL_PLACEMENTS)
P_NEIGH: tuple[int, ...] = tuple(p.neighbor_mask for p in ALL_PLACEMENTS)
P_BOUNDARY: tuple[int, ...] = tuple(p.boundary_contacts for p in ALL_PLACEMENTS)


def save_catalogue_json(path) -> None:
    payload = {
        "pieces": catalogue_payload(),
        "catalogue_hash": catalogue_hash(),
        "areas": {k: len(v) for k, v in PIECES.items()},
        "n_unique_placements": len(ALL_PLACEMENTS),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
