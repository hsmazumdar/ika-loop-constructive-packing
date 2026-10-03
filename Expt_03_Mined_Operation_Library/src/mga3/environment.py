"""10x10 packing environment. Transition rules match Expt-2.

PLACE, UNDO, and SUBMIT each consume one physical action, including invalid
PLACE attempts. A macro is expanded into one PLACE per piece. There is no
free rollback.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from mga3.inventory import Inventory
from mga3.pieces import BOARD_SIZE, N_CELLS, PIECE_TYPES, in_bounds, placed_cells


class ActionKind(str, Enum):
    PLACE = "PLACE"
    UNDO = "UNDO"
    SUBMIT = "SUBMIT"


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    piece_type: str | None = None
    rotation: int | None = None
    x: int | None = None
    y: int | None = None

    @staticmethod
    def place(piece_type: str, rotation: int, x: int, y: int) -> "Action":
        return Action(ActionKind.PLACE, piece_type, int(rotation) % 4, int(x), int(y))

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


@dataclass
class PlacedInstance:
    instance_id: int
    piece_type: str
    rotation: int
    x: int
    y: int
    cells: tuple[tuple[int, int], ...]
    mask: int


@dataclass
class StepResult:
    accepted: bool
    consumed_action: bool
    terminal: bool
    invalid: bool
    score: int
    occupied: int
    actions_used: int
    reason: str


class PackingEnv:
    def __init__(self, budget: int = 100, inventory: Inventory | None = None) -> None:
        self.budget = int(budget)
        self.size = BOARD_SIZE
        self.inventory = inventory if inventory is not None else Inventory(None)
        self.reset_box()

    def reset_box(self) -> None:
        self.cells: list[list[tuple[str, int] | None]] = [
            [None] * self.size for _ in range(self.size)
        ]
        self.mask = 0
        self.stack: list[PlacedInstance] = []
        self.actions_used = 0
        self.invalid_attempts = 0
        self.invalid_places = 0
        self.undos = 0
        self.place_attempts = 0
        self.submits = 0
        self.next_instance_id = 1
        self.terminal = False
        self.termination_reason: str | None = None
        self.best_score = 0
        self.trace: list[dict[str, Any]] = []
        self.inventory.restore_initial()

    @property
    def occupied(self) -> int:
        return self.mask.bit_count()

    @property
    def score(self) -> int:
        return self.occupied

    def _note_best(self) -> None:
        if self.score > self.best_score:
            self.best_score = self.score

    def _can_place_cells(self, cells: tuple[tuple[int, int], ...]) -> bool:
        if not in_bounds(cells):
            return False
        for x, y in cells:
            if self.cells[y][x] is not None:
                return False
        return True

    def force_terminal(self, reason: str) -> StepResult:
        self.terminal = True
        self.termination_reason = reason
        self.submits += 1
        if self.actions_used < self.budget:
            self.actions_used += 1
        action = Action.submit().as_dict()
        self.trace.append(
            {
                "action": action,
                "accepted": True,
                "invalid": False,
                "reason": reason,
                "score": self.score,
                "best_score": self.best_score,
                "actions_used": self.actions_used,
            }
        )
        if self.actions_used > self.budget:
            self.actions_used = self.budget
        return StepResult(True, True, True, False, self.score, self.occupied, self.actions_used, reason)

    def step(self, action: Action) -> StepResult:
        if self.terminal:
            return StepResult(False, False, True, True, self.score, self.occupied, self.actions_used, "already_terminal")
        self.actions_used += 1
        accepted = False
        invalid = False
        reason = "ok"
        if action.kind is ActionKind.PLACE:
            self.place_attempts += 1
            if (
                action.piece_type not in PIECE_TYPES
                or action.rotation is None
                or action.x is None
                or action.y is None
            ):
                invalid = True
                reason = "invalid_place_args"
            elif not self.inventory.can_take(action.piece_type):
                invalid = True
                reason = "invalid_inventory"
            else:
                cells = placed_cells(action.piece_type, action.rotation, action.x, action.y)
                if not self._can_place_cells(cells):
                    invalid = True
                    reason = "invalid_place"
                else:
                    mask = 0
                    for cx, cy in cells:
                        mask |= 1 << (cy * BOARD_SIZE + cx)
                    self.inventory.take(action.piece_type)
                    iid = self.next_instance_id
                    self.next_instance_id += 1
                    for cx, cy in cells:
                        self.cells[cy][cx] = (action.piece_type, iid)
                    self.mask |= mask
                    self.stack.append(
                        PlacedInstance(iid, action.piece_type, action.rotation, action.x, action.y, cells, mask)
                    )
                    accepted = True
                    reason = "placed"
        elif action.kind is ActionKind.UNDO:
            if not self.stack:
                invalid = True
                reason = "invalid_undo_empty"
            else:
                inst = self.stack.pop()
                for cx, cy in inst.cells:
                    self.cells[cy][cx] = None
                self.mask &= ~inst.mask
                self.inventory.restore(inst.piece_type)
                self.undos += 1
                accepted = True
                reason = "undone"
        elif action.kind is ActionKind.SUBMIT:
            self.submits += 1
            accepted = True
            self.terminal = True
            self.termination_reason = "submit"
            reason = "submit"
        else:
            invalid = True
            reason = "unknown_action"
        if invalid:
            self.invalid_attempts += 1
            if action.kind is ActionKind.PLACE:
                self.invalid_places += 1
        self._note_best()
        if not self.terminal:
            if self.occupied == N_CELLS:
                self.terminal = True
                self.termination_reason = "board_full"
                reason = "board_full"
            elif self.actions_used >= self.budget:
                self.terminal = True
                self.termination_reason = "action_limit"
                reason = "action_limit"
        self.trace.append(
            {
                "action": action.as_dict(),
                "accepted": accepted,
                "invalid": invalid,
                "reason": reason,
                "score": self.score,
                "best_score": self.best_score,
                "actions_used": self.actions_used,
            }
        )
        return StepResult(accepted, True, self.terminal, invalid, self.score, self.occupied, self.actions_used, reason)

    def clone(self) -> "PackingEnv":
        other = PackingEnv(budget=self.budget, inventory=self.inventory.copy())
        other.cells = [row[:] for row in self.cells]
        other.mask = self.mask
        other.stack = [
            PlacedInstance(i.instance_id, i.piece_type, i.rotation, i.x, i.y, i.cells, i.mask) for i in self.stack
        ]
        other.actions_used = self.actions_used
        other.invalid_attempts = self.invalid_attempts
        other.invalid_places = self.invalid_places
        other.undos = self.undos
        other.place_attempts = self.place_attempts
        other.submits = self.submits
        other.next_instance_id = self.next_instance_id
        other.terminal = self.terminal
        other.termination_reason = self.termination_reason
        other.best_score = self.best_score
        return other

    def placed_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for inst in self.stack:
            counts[inst.piece_type] = counts.get(inst.piece_type, 0) + 1
        return counts

    def snapshot_placements(self) -> list[dict[str, Any]]:
        return [
            {
                "type": inst.piece_type,
                "rotation": inst.rotation,
                "x": inst.x,
                "y": inst.y,
                "cells": [list(c) for c in inst.cells],
            }
            for inst in self.stack
        ]
