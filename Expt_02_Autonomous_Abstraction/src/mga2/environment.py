"""10x10 sequential packing environment with optional inventories.

No ``__slots__``: runtime bookkeeping must be attachable. The agent-facing
module does not import the offline witness validator.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from mga2.inventory import Inventory
from mga2.pieces import (
    BOARD_SIZE,
    N_CELLS,
    PIECE_TYPES,
    P_MASKS,
    P_TYPES,
    Placement,
    in_bounds,
    placed_cells,
)


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
    blanks: int
    occupied: int
    actions_used: int
    reason: str
    last_action: dict[str, Any]
    instance_id: int | None = None


class PackingEnv:
    """One real board. Clones used for internal simulation are separate objects."""

    def __init__(
        self,
        budget: int = 100,
        size: int = BOARD_SIZE,
        inventory: Inventory | None = None,
    ) -> None:
        if int(size) != BOARD_SIZE:
            raise ValueError(
                f"catalogue placements are defined for board_size {BOARD_SIZE}, got {size}"
            )
        self.budget = int(budget)
        self.size = int(size)
        self.inventory = inventory if inventory is not None else Inventory(None)
        self.best_score = 0
        self.reset_box()

    def reset_box(self) -> None:
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
        self.best_score = 0
        self.inventory.restore_initial()

    @property
    def occupied(self) -> int:
        return self.mask.bit_count()

    @property
    def blanks(self) -> int:
        return self.size * self.size - self.occupied

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

    def _note_best(self) -> None:
        if self.score > self.best_score:
            self.best_score = self.score

    def scan_placements(self, charge) -> list[int]:
        """Examine catalogue placements. ``charge(1)`` returns how many evals were allowed.

        Failed checks are included. The scan stops when a charge is refused.
        """
        legal: list[int] = []
        occ = self.mask
        inv = self.inventory
        for i, pmask in enumerate(P_MASKS):
            if charge(1) <= 0:
                break
            if pmask & occ:
                continue
            if not inv.can_take(P_TYPES[i]):
                continue
            legal.append(i)
        return legal

    def _can_place_cells(self, cells: tuple[tuple[int, int], ...]) -> bool:
        if not in_bounds(cells):
            return False
        for x, y in cells:
            if self.cells[y][x] is not None:
                return False
        return True

    def _place(self, piece_type: str, rotation: int, x: int, y: int, cells, mask: int) -> int:
        self.inventory.take(piece_type)
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
        self.inventory.restore(inst.piece_type)
        self.undos += 1
        return inst

    def peek_top(self) -> PlacedInstance | None:
        return self.stack[-1] if self.stack else None

    def force_terminal(self, reason: str) -> StepResult:
        self.terminal = True
        self.termination_reason = reason
        action = {"kind": "SUBMIT", "piece_type": None, "rotation": None, "x": None, "y": None}
        self.last_action = action
        record = {
            "action": action,
            "accepted": True,
            "invalid": False,
            "reason": reason,
            "score": self.score,
            "best_score": self.best_score,
            "actions_used": self.actions_used,
            "instance_id": None,
            "mask": self.mask,
            "inventory": self.inventory.as_dict(),
        }
        self.trace.append(record)
        return StepResult(
            accepted=True,
            consumed_action=False,
            terminal=True,
            invalid=False,
            score=self.score,
            blanks=self.blanks,
            occupied=self.occupied,
            actions_used=self.actions_used,
            reason=reason,
            last_action=action,
        )

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

        self.last_action = action.as_dict()
        record = {
            "action": action.as_dict(),
            "accepted": accepted,
            "invalid": invalid,
            "reason": reason,
            "score": self.score,
            "best_score": self.best_score,
            "actions_used": self.actions_used,
            "instance_id": instance_id,
            "mask": self.mask,
            "inventory": self.inventory.as_dict(),
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

    def clone(self) -> "PackingEnv":
        """Deep copy of the physical state. The clone does not share lists or RNG."""
        other = PackingEnv(budget=self.budget, size=self.size, inventory=self.inventory.copy())
        other.cells = [row[:] for row in self.cells]
        other.mask = self.mask
        other.stack = [
            PlacedInstance(
                instance_id=inst.instance_id,
                piece_type=inst.piece_type,
                rotation=inst.rotation,
                x=inst.x,
                y=inst.y,
                cells=inst.cells,
                mask=inst.mask,
            )
            for inst in self.stack
        ]
        other.actions_used = self.actions_used
        other.invalid_attempts = self.invalid_attempts
        other.undos = self.undos
        other.placements_count = self.placements_count
        other.next_instance_id = self.next_instance_id
        other.terminal = self.terminal
        other.termination_reason = self.termination_reason
        other.best_score = self.best_score
        other.trace = []
        other.last_action = None
        return other

    def snapshot(self) -> dict[str, Any]:
        return {
            "mask": self.mask,
            "score": self.score,
            "best_score": self.best_score,
            "blanks": self.blanks,
            "actions_used": self.actions_used,
            "terminal": self.terminal,
            "termination_reason": self.termination_reason,
            "invalid_attempts": self.invalid_attempts,
            "undos": self.undos,
            "inventory": self.inventory.as_dict(),
            "unlimited": self.inventory.unlimited,
            "placements": [
                {
                    "instance_id": inst.instance_id,
                    "type": inst.piece_type,
                    "rotation": inst.rotation,
                    "x": inst.x,
                    "y": inst.y,
                }
                for inst in self.stack
            ],
            "occupancy": self.occupancy_grid(),
        }

    def placed_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for inst in self.stack:
            counts[inst.piece_type] = counts.get(inst.piece_type, 0) + 1
        return counts

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
        if self.score != self.size * self.size - self.blanks:
            raise AssertionError("score/blank inconsistency")
        if self.best_score < self.score:
            raise AssertionError("best score below current score")
        stacked = 0
        for inst in self.stack:
            stacked += len(inst.cells)
            for x, y in inst.cells:
                if not (0 <= x < self.size and 0 <= y < self.size):
                    raise AssertionError("placed cell out of bounds")
                if self.cells[y][x] != (inst.piece_type, inst.instance_id):
                    raise AssertionError("stack does not match board")
        if stacked != occupied_cells:
            raise AssertionError("stack cells != occupied")
        if self.actions_used > self.budget:
            raise AssertionError("action budget exceeded")
        if not self.inventory.on_board_consistent(self.placed_type_counts()):
            raise AssertionError("inventory does not match stack")


def replay_trace(trace: list[dict], budget: int = 100, inventory: Inventory | None = None) -> PackingEnv:
    env = PackingEnv(budget=budget, inventory=inventory.copy() if inventory is not None else Inventory(None))
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
