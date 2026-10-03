"""Independent exact-cover / backtracking validator.

Solver results are feasibility witnesses, not learning results. The agent never
imports this module. Timeout reports UNKNOWN, not UNSOLVABLE.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any

from mga.environment import PackingEnv
from mga.pieces import (
    ALL_PLACEMENTS,
    BOARD_SIZE,
    FULL_MASK,
    N_CELLS,
    Placement,
    catalogue_hash,
    placements_covering,
)


def _rot90_grid(grid: list[list[str]]) -> list[list[str]]:
    n = len(grid)
    new = [[""] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            nx, ny = n - 1 - y, x
            new[ny][nx] = grid[y][x]
    return new


def _reflect_grid(grid: list[list[str]]) -> list[list[str]]:
    n = len(grid)
    return [[grid[y][n - 1 - x] for x in range(n)] for y in range(n)]


def canonical_label_grid(grid: list[list[str]]) -> str:
    """Canonicalize a completed tiling under board rotations and reflections.

    Instance IDs are ignored; type labels are kept. Two witnesses with the same
    labels after a dihedral transform are equivalent.
    """
    variants = []
    g = [row[:] for row in grid]
    for _ in range(4):
        variants.append(tuple(tuple(row) for row in g))
        variants.append(tuple(tuple(row) for row in _reflect_grid(g)))
        g = _rot90_grid(g)
    return repr(min(variants))


def _records_to_grid(records: list[dict]) -> list[list[str]]:
    grid = [[""] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    env = PackingEnv()
    for rec in records:
        env.step_silent = None
        from mga.environment import Action

        result = env.step(Action.place(rec["type"], rec["rotation"], rec["x"], rec["y"]))
        if result.invalid:
            raise ValueError(f"witness placement invalid: {rec}")
    if env.occupied != N_CELLS:
        raise ValueError("witness does not fill the board")
    return env.occupancy_grid()


def replay_witness(records: list[dict]) -> PackingEnv:
    from mga.environment import Action

    env = PackingEnv()
    for rec in records:
        result = env.step(Action.place(rec["type"], rec["rotation"], rec["x"], rec["y"]))
        if result.invalid:
            raise AssertionError(f"witness failed replay: {rec} reason={result.reason}")
    if env.occupied != N_CELLS:
        raise AssertionError("replay did not fill the board")
    return env


def _placement_record(p: Placement) -> dict[str, Any]:
    return {"type": p.piece_type, "rotation": p.rotation, "x": p.x, "y": p.y}


def constructive_witnesses() -> list[list[dict[str, Any]]]:
    """Two hand-checkable perfect tilings, still validated by environment replay."""
    by_sig = {(p.piece_type, p.rotation, p.x, p.y): p for p in ALL_PLACEMENTS}

    def must(ptype: str, rot: int, x: int, y: int) -> Placement:
        # Map user rotation onto the unique canonical placement.
        for p in ALL_PLACEMENTS:
            if p.piece_type != ptype or p.x != x or p.y != y:
                continue
            from mga.pieces import PIECES, orientation, unique_orientations

            canon = unique_orientations(ptype)[orientation(PIECES[ptype], rot)]
            if p.rotation == canon:
                return p
        raise KeyError((ptype, rot, x, y))

    # Witness 1: 20 vertical I-pentominoes (type B) covering the 10x10.
    w1 = []
    b_vert = None
    for p in ALL_PLACEMENTS:
        if p.piece_type == "B" and p.cells == ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)):
            b_vert = p.rotation
            break
    if b_vert is None:
        # Find the canonical rotation whose cells are a vertical bar at origin.
        from mga.pieces import PIECES, orientation, unique_orientations

        for cells, rot in unique_orientations("B").items():
            if cells == ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)):
                b_vert = rot
                break
    for x in range(10):
        for y in (0, 5):
            w1.append({"type": "B", "rotation": b_vert, "x": x, "y": y})

    # Witness 2: vertical B on columns 0-7, E-strip on columns 8-9.
    from mga.pieces import PIECES, orientation, unique_orientations

    e_map = unique_orientations("E")
    e0 = e_map[orientation(PIECES["E"], 0)]
    e2 = e_map[orientation(PIECES["E"], 2)]
    w2 = []
    for x in range(8):
        for y in (0, 5):
            w2.append({"type": "B", "rotation": b_vert, "x": x, "y": y})
    w2.append({"type": "E", "rotation": e0, "x": 8, "y": 0})
    w2.append({"type": "E", "rotation": e2, "x": 8, "y": 2})
    w2.append({"type": "E", "rotation": e0, "x": 8, "y": 5})
    w2.append({"type": "E", "rotation": e2, "x": 8, "y": 7})
    return [w1, w2]


class ExactCoverSolver:
    """Algorithm X over occupancy bits. Piece types are unlimited."""

    def __init__(self, placements: tuple[Placement, ...] | None = None) -> None:
        self.placements = placements or ALL_PLACEMENTS
        self.by_cell: list[list[int]] = [[] for _ in range(N_CELLS)]
        for i, p in enumerate(self.placements):
            mask = p.mask
            while mask:
                bit = mask & -mask
                mask ^= bit
                self.by_cell[bit.bit_length() - 1].append(i)

    def solve(
        self,
        n_solutions: int = 2,
        timeout: float = 60.0,
        forbid_canonical: set[str] | None = None,
        prefix: list[int] | None = None,
        type_ban: set[str] | None = None,
    ) -> tuple[str, list[list[dict[str, Any]]]]:
        t0 = time.perf_counter()
        forbid_canonical = forbid_canonical or set()
        type_ban = type_ban or set()
        found: list[list[dict[str, Any]]] = []
        found_canon: set[str] = set(forbid_canonical)
        timed_out = False

        def choose_cell(occ: int) -> int | None:
            empty = FULL_MASK ^ occ
            if not empty:
                return None
            best_i = None
            best_n = 10**9
            remain = empty
            while remain:
                bit = remain & -remain
                remain ^= bit
                i = bit.bit_length() - 1
                n = 0
                for pi in self.by_cell[i]:
                    p = self.placements[pi]
                    if p.piece_type in type_ban:
                        continue
                    if not (p.mask & occ):
                        n += 1
                if n < best_n:
                    best_n = n
                    best_i = i
                    if n == 0:
                        return i
            return best_i

        def search(occ: int, stack: list[int]) -> None:
            nonlocal timed_out
            if timed_out or len(found) >= n_solutions:
                return
            if time.perf_counter() - t0 > timeout:
                timed_out = True
                return
            if occ == FULL_MASK:
                recs = [_placement_record(self.placements[i]) for i in stack]
                grid = _records_to_grid(recs)
                canon = canonical_label_grid(grid)
                if canon not in found_canon:
                    found_canon.add(canon)
                    found.append(recs)
                return
            cell = choose_cell(occ)
            if cell is None:
                return
            cands = []
            for pi in self.by_cell[cell]:
                p = self.placements[pi]
                if p.piece_type in type_ban:
                    continue
                if p.mask & occ:
                    continue
                cands.append(pi)
            # Larger pieces first, then type, to find diverse covers quickly.
            cands.sort(key=lambda i: (-self.placements[i].area, self.placements[i].piece_type, i))
            for pi in cands:
                stack.append(pi)
                search(occ | self.placements[pi].mask, stack)
                stack.pop()
                if timed_out or len(found) >= n_solutions:
                    return

        start_occ = 0
        start_stack: list[int] = []
        if prefix:
            for pi in prefix:
                start_occ |= self.placements[pi].mask
                start_stack.append(pi)
        search(start_occ, start_stack)
        if len(found) >= n_solutions:
            status = "SOLVED"
        elif timed_out:
            status = "UNKNOWN"
        else:
            status = "UNKNOWN" if len(found) < n_solutions else "SOLVED"
        return status, found


def find_perfect_tilings(n: int = 2, timeout: float = 60.0) -> dict[str, Any]:
    """Find at least n canonically distinct perfect tilings."""
    t0 = time.perf_counter()
    witnesses: list[list[dict[str, Any]]] = []
    canons: set[str] = set()
    methods: list[str] = []

    constructed = constructive_witnesses()
    for recs in constructed:
        env = replay_witness(recs)
        canon = canonical_label_grid(env.occupancy_grid())
        if canon not in canons:
            canons.add(canon)
            witnesses.append(recs)
            methods.append("constructive_replay_validated")

    remaining_timeout = max(1.0, timeout - (time.perf_counter() - t0))
    solver = ExactCoverSolver()
    status, found = solver.solve(
        n_solutions=n,
        timeout=remaining_timeout,
        forbid_canonical=set(canons),
    )
    for recs in found:
        env = replay_witness(recs)
        canon = canonical_label_grid(env.occupancy_grid())
        if canon not in canons:
            canons.add(canon)
            witnesses.append(recs)
            methods.append("exact_cover")

    if len(witnesses) < n and "B" not in (p.piece_type for recs in witnesses for p in []):
        pass

    if len(witnesses) < n:
        remaining_timeout = max(1.0, timeout - (time.perf_counter() - t0))
        no_b = tuple(p for p in ALL_PLACEMENTS if p.piece_type != "B")
        status2, found2 = ExactCoverSolver(no_b).solve(
            n_solutions=1, timeout=remaining_timeout
        )
        for recs in found2:
            env = replay_witness(recs)
            canon = canonical_label_grid(env.occupancy_grid())
            if canon not in canons:
                canons.add(canon)
                witnesses.append(recs)
                methods.append("exact_cover_no_B")

    n_found = len(witnesses)
    final_status = "SOLVED" if n_found >= n else "UNKNOWN"
    elapsed = time.perf_counter() - t0
    payload = {
        "status": final_status,
        "n_requested": n,
        "n_found": n_found,
        "timeout_seconds": timeout,
        "elapsed_seconds": round(elapsed, 4),
        "catalogue_hash": catalogue_hash(),
        "search_status": status,
        "methods": methods,
        "witnesses": [
            {
                "index": i,
                "n_placements": len(recs),
                "types_used": sorted({r["type"] for r in recs}),
                "canonical": canonical_label_grid(replay_witness(recs).occupancy_grid()),
                "placements": recs,
            }
            for i, recs in enumerate(witnesses[:n])
        ],
        "note": (
            "Witnesses are feasibility proofs for the catalogue. They are not "
            "shown to the packing agent and are not a learning result."
        ),
    }
    return payload


def save_validation(path, n: int = 2, timeout: float = 60.0) -> dict[str, Any]:
    payload = find_perfect_tilings(n=n, timeout=timeout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
