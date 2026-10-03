"""10x10 sequential packing environment.

Simulation logic is independent of GUI imports so tests can run headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mga.pieces import (
    ALL_PLACEMENTS,
    BOARD_SIZE,
    FULL_MASK,
    N_CELLS,
    PIECE_TYPES,
    Placement,
    in_bounds,
    lookup_placement,
    placed_cells,
)


class ActionKind(str, Enum):
    PLACE = "PLACE"
    UNDO = "UNDO"
    SUBMIT = "SUBMIT"


@dataclass(frozen=True, slots=True)
class Action:
    kind: ActionKind
    piece_type: str | None = None
    rotation: int | None = None
    x: int | None = None
    y: int | None = None

    @staticmethod
    def place(piece_type: str, rotation: int, x: int, y: int) -> "Action":
        return Action(ActionKind.PLACE, piece_type, rotation, x, y)

    @staticmethod
    def place_from(p: Placement) -> "Action":
        return Action(ActionKind.PLACE, p.piece_type, p.rotation, p.x, p.y)

    @staticmethod
    def undo() -> "Action":
        return Action(ActionKind.UNDO)

    @staticmethod
    def submit() -> "Action":
        return Action(ActionKind.SUBMIT)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "piece_type": self.piece_type,
            "rotation": self.rotation,
            "x": self.x,
            "y": self.y,
        }


@dataclass(slots=True)
class PlacedInstance:
    instance_id: int
    piece_type: str
    rotation: int
    x: int
    y: int
    cells: tuple[tuple[int, int], ...]
    mask: int


@dataclass(slots=True)
class StepResult:
    accepted: bool
    consumed_action: bool
    terminal: bool
    invalid: bool
    score: int
    blanks: int
    occupied: int
    actions_used: int
    reason: str
    last_action: dict[str, Any]
    instance_id: int | None = None


@dataclass
class PackingEnv:
    budget: int = 100
    size: int = BOARD_SIZE

    def __post_init__(self) -> None:
        self.reset_box()

    def reset_box(self) -> None:
        """Clear the board, placement stack and action counters. Does not touch LTM."""
        self.cells: list[list[tuple[str, int] | None]] = [
            [None] * self.size for _ in range(self.size)
        ]
        self.mask: int = 0
        self.stack: list[PlacedInstance] = []
        self.actions_used: int = 0
        self.invalid_attempts: int = 0
        self.undos: int = 0
        self.placements_count: int = 0
        self.next_instance_id: int = 1
        self.terminal: bool = False
        self.termination_reason: str | None = None
        self.last_action: dict[str, Any] | None = None
        self.trace: list[dict[str, Any]] = []

    @property
    def occupied(self) -> int:
        return self.mask.bit_count()

    @property
    def blanks(self) -> int:
        return N_CELLS - self.occupied

    @property
    def score(self) -> int:
        return self.occupied

    @property
    def can_undo(self) -> bool:
        return bool(self.stack)

    def occupancy_grid(self) -> list[list[str]]:
        grid = [[""] * self.size for _ in range(self.size)]
        for y in range(self.size):
            for x in range(self.size):
                cell = self.cells[y][x]
                if cell is not None:
                    grid[y][x] = cell[0]
        return grid

    def instance_grid(self) -> list[list[int]]:
        grid = [[0] * self.size for _ in range(self.size)]
        for y in range(self.size):
            for x in range(self.size):
                cell = self.cells[y][x]
                if cell is not None:
                    grid[y][x] = cell[1]
        return grid

    def legal_placements(self) -> list[Placement]:
        occ = self.mask
        return [p for p in ALL_PLACEMENTS if not (p.mask & occ)]

    def _can_place_cells(self, cells: tuple[tuple[int, int], ...]) -> bool:
        if not in_bounds(cells):
            return False
        for x, y in cells:
            if self.cells[y][x] is not None:
                return False
        return True

    def _place(self, piece_type: str, rotation: int, x: int, y: int, cells, mask: int) -> int:
        iid = self.next_instance_id
        self.next_instance_id += 1
        for cx, cy in cells:
            self.cells[cy][cx] = (piece_type, iid)
        self.mask |= mask
        self.stack.append(
            PlacedInstance(
                instance_id=iid,
                piece_type=piece_type,
                rotation=rotation,
                x=x,
                y=y,
                cells=cells,
                mask=mask,
            )
        )
        self.placements_count += 1
        return iid

    def _undo(self) -> PlacedInstance:
        inst = self.stack.pop()
        for cx, cy in inst.cells:
            self.cells[cy][cx] = None
        self.mask &= ~inst.mask
        self.undos += 1
        return inst

    def peek_top(self) -> PlacedInstance | None:
        return self.stack[-1] if self.stack else None

    def mask_without_top(self) -> int:
        if not self.stack:
            return self.mask
        return self.mask & ~self.stack[-1].mask

    def step(self, action: Action) -> StepResult:
        if self.terminal:
            return StepResult(
                accepted=False,
                consumed_action=False,
                terminal=True,
                invalid=True,
                score=self.score,
                blanks=self.blanks,
                occupied=self.occupied,
                actions_used=self.actions_used,
                reason="already_terminal",
                last_action=action.as_dict(),
            )

        self.actions_used += 1
        accepted = False
        invalid = False
        reason = "ok"
        instance_id = None

        if action.kind is ActionKind.PLACE:
            if (
                action.piece_type not in PIECE_TYPES
                or action.rotation is None
                or action.x is None
                or action.y is None
            ):
                invalid = True
                reason = "invalid_place_args"
            else:
                cells = placed_cells(action.piece_type, action.rotation, action.x, action.y)
                if not self._can_place_cells(cells):
                    invalid = True
                    reason = "invalid_place"
                else:
                    mask = 0
                    for cx, cy in cells:
                        mask |= 1 << (cy * BOARD_SIZE + cx)
                    instance_id = self._place(
                        action.piece_type, action.rotation, action.x, action.y, cells, mask
                    )
                    accepted = True
                    reason = "placed"
        elif action.kind is ActionKind.UNDO:
            if not self.stack:
                invalid = True
                reason = "invalid_undo_empty"
            else:
                self._undo()
                accepted = True
                reason = "undone"
        elif action.kind is ActionKind.SUBMIT:
            accepted = True
            self.terminal = True
            self.termination_reason = "submit"
            reason = "submit"
        else:
            invalid = True
            reason = "unknown_action"

        if invalid:
            self.invalid_attempts += 1

        if not self.terminal:
            if self.occupied == N_CELLS:
                self.terminal = True
                self.termination_reason = "board_full"
                reason = "board_full"
            elif self.actions_used >= self.budget:
                self.terminal = True
                self.termination_reason = "action_limit"
                reason = "action_limit"

        self.last_action = action.as_dict()
        record = {
            "action": action.as_dict(),
            "accepted": accepted,
            "invalid": invalid,
            "reason": reason,
            "score": self.score,
            "actions_used": self.actions_used,
            "instance_id": instance_id,
            "mask": self.mask,
        }
        self.trace.append(record)

        return StepResult(
            accepted=accepted,
            consumed_action=True,
            terminal=self.terminal,
            invalid=invalid,
            score=self.score,
            blanks=self.blanks,
            occupied=self.occupied,
            actions_used=self.actions_used,
            reason=reason,
            last_action=self.last_action,
            instance_id=instance_id,
        )

    def replay_placements(self, placements: list[dict]) -> StepResult:
        """Replay PLACE records through the public API. Used for witness validation."""
        self.reset_box()
        result = None
        for rec in placements:
            result = self.step(
                Action.place(rec["type"], rec["rotation"], rec["x"], rec["y"])
            )
            if result.invalid:
                return result
        return result

    def snapshot(self) -> dict[str, Any]:
        return {
            "mask": self.mask,
            "score": self.score,
            "blanks": self.blanks,
            "actions_used": self.actions_used,
            "terminal": self.terminal,
            "termination_reason": self.termination_reason,
            "invalid_attempts": self.invalid_attempts,
            "undos": self.undos,
            "placements": [
                {
                    "instance_id": inst.instance_id,
                    "type": inst.piece_type,
                    "rotation": inst.rotation,
                    "x": inst.x,
                    "y": inst.y,
                    "cells": [list(c) for c in inst.cells],
                }
                for inst in self.stack
            ],
            "occupancy": self.occupancy_grid(),
            "instances": self.instance_grid(),
        }

    def invariants(self) -> None:
        occupied_cells = 0
        seen_ids: dict[int, str] = {}
        mask = 0
        for y in range(self.size):
            for x in range(self.size):
                cell = self.cells[y][x]
                if cell is None:
                    continue
                occupied_cells += 1
                ptype, iid = cell
                seen_ids.setdefault(iid, ptype)
                if seen_ids[iid] != ptype:
                    raise AssertionError("instance id mapped to two types")
                mask |= 1 << (y * BOARD_SIZE + x)
        if occupied_cells != self.occupied:
            raise AssertionError("occupancy count mismatch")
        if mask != self.mask:
            raise AssertionError("bitmask mismatch")
        if not (0 <= self.score <= N_CELLS):
            raise AssertionError("score out of range")
        if self.score != N_CELLS - self.blanks:
            raise AssertionError("score/blank inconsistency")
        stacked = 0
        for inst in self.stack:
            stacked += len(inst.cells)
            for x, y in inst.cells:
                if not (0 <= x < self.size and 0 <= y < self.size):
                    raise AssertionError("placed cell out of bounds")
                cell = self.cells[y][x]
                if cell != (inst.piece_type, inst.instance_id):
                    raise AssertionError("stack does not match board")
        if stacked != occupied_cells:
            raise AssertionError("stack cells != occupied")
        if self.actions_used > self.budget:
            raise AssertionError("action budget exceeded")


def replay_trace(trace: list[dict], budget: int = 100) -> PackingEnv:
    env = PackingEnv(budget=budget)
    for rec in trace:
        action = rec["action"]
        kind = ActionKind(action["kind"])
        if kind is ActionKind.PLACE:
            step = Action.place(action["piece_type"], action["rotation"], action["x"], action["y"])
        elif kind is ActionKind.UNDO:
            step = Action.undo()
        else:
            step = Action.submit()
        env.step(step)
    return env
