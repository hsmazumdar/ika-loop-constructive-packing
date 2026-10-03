"""Common primitive controller and cost-aware macro retrieval.

Every comparison arm uses this controller. Retrieval is the only switch.
The shared score (area, contact, boundary) is designer-supplied. It is not
Expt-1's heuristic and it is not a learned rectangle preference.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mga3.environment import Action, PackingEnv
from mga3.hardware import PlacementWorkspace
from mga3.inventory import Inventory
from mga3.ops import placement_params, rotate_steps, translate_steps
from mga3.pieces import ALL_PLACEMENTS, FULL_MASK, piece_area
from mga3.rngutil import make_rng

_SHAPE_INDEX: dict[tuple, list] = {}
for _placement in ALL_PLACEMENTS:
    _norm = tuple(sorted((x - _placement.x, y - _placement.y) for x, y in _placement.cells))
    _SHAPE_INDEX.setdefault((_placement.piece_type, _norm), []).append(_placement)


@dataclass
class Ledger:
    eval_cap: int
    cheap_reserve: int
    candidate_evals: int = 0
    guard_evals: int = 0
    library_lookups: int = 0
    feature_evals: int = 0
    model_transitions: int = 0
    sim_expansions: int = 0
    cheap_actions: int = 0
    macros_invoked: int = 0
    macros_completed: int = 0
    macros_interrupted: int = 0
    buckets: dict = field(default_factory=lambda: {
        "selection": 0,
        "guard": 0,
        "library": 0,
        "simulation": 0,
        "feature": 0,
        "cheap": 0,
        "think": 0,
    })

    def spend_limit(self) -> int:
        return max(0, self.eval_cap - max(0, self.cheap_reserve))

    def can_eval(self) -> bool:
        return self.candidate_evals < self.spend_limit()

    def charge(self, bucket: str, n: int = 1, reserve: bool = False) -> int:
        limit = self.eval_cap if reserve else self.spend_limit()
        room = limit - self.candidate_evals
        take = max(0, min(int(n), room))
        if take:
            self.candidate_evals += take
            self.buckets[bucket] = self.buckets.get(bucket, 0) + take
            if bucket == "guard":
                self.guard_evals += take
            elif bucket == "library":
                self.library_lookups += take
            elif bucket == "feature":
                self.feature_evals += take
            elif bucket == "simulation":
                self.model_transitions += take
                self.sim_expansions += 1
        return take


def efficiency(q: int, p: int) -> float | None:
    if p <= 0:
        return None
    return float(q) / float(p)


def conditional_efficiency(q: int, p: int, target: int = 80) -> float | None:
    """Efficiency is undefined at P=0 and is not claimed below the quality target."""
    if p <= 0 or q < target:
        return None
    return float(q) / float(p)


def empty_component_sizes(mask: int) -> list[int]:
    """Sizes of 4-connected empty regions. A region smaller than every remaining piece cannot be filled."""
    remaining = FULL_MASK ^ (mask & FULL_MASK)
    sizes = []
    while remaining:
        start = (remaining & -remaining).bit_length() - 1
        stack = [start]
        remaining &= ~(1 << start)
        size = 0
        while stack:
            idx = stack.pop()
            size += 1
            x, y = idx % 10, idx // 10
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= 10 or ny >= 10:
                    continue
                bit = 1 << (ny * 10 + nx)
                if remaining & bit:
                    remaining &= ~bit
                    stack.append(ny * 10 + nx)
        sizes.append(size)
    return sizes


def leaves_unfillable(mask: int, inventory: Inventory) -> bool:
    if inventory.unlimited:
        return False
    areas = [piece_area(name) for name, count in inventory.counts.items() if count > 0]
    if not areas:
        return False
    smallest = min(areas)
    return any(0 < size < smallest for size in empty_component_sizes(mask))


def macro_fits(env: PackingEnv, steps: list[dict]) -> bool:
    mask = env.mask
    counts = None if env.inventory.unlimited else dict(env.inventory.counts)
    for step in steps:
        params = placement_params(step["type"], step["cells"])
        if params is None:
            return False
        bit = 0
        for x, y in step["cells"]:
            if x < 0 or y < 0 or x >= 10 or y >= 10:
                return False
            b = 1 << (y * 10 + x)
            if bit & b or mask & b:
                return False
            bit |= b
        if counts is not None:
            if counts.get(step["type"], 0) <= 0:
                return False
            counts[step["type"]] -= 1
        mask |= bit
    return True


class Controller:
    def __init__(self, config: dict, workspace: PlacementWorkspace, library: list[dict] | None, retrieve: bool) -> None:
        budgets = config["budgets"]
        self.physical = int(budgets["physical"])
        self.scan = int(budgets["scan_per_decision"])
        self.macros_considered = int(budgets["macros_considered"])
        self.anchors = int(budgets["anchors_per_macro"])
        self.max_consecutive = int(budgets["max_consecutive_retrieval"])
        self.think = int(budgets.get("think_allowance", 0))
        self.undo_budget = int(budgets.get("undo_budget", 8))
        self.continuation_steps = int(budgets.get("continuation_steps", 2))
        self.continuation_scan = int(budgets.get("continuation_scan", 8))
        self.target = int(config["quality_target"])
        self.workspace = workspace
        self.tabu: tuple | None = None
        self.library = list(library or [])
        self.retrieve = bool(retrieve and self.library)
        self.ledger = Ledger(int(budgets["eval_cap"]), int(budgets["cheap_reserve"]))

    def run(self, task: dict, seed: int, phase: str) -> dict:
        gpu_before = self.workspace.gpu_ops
        env = PackingEnv(budget=self.physical, inventory=Inventory(dict(task["inventory"])))
        select_rng = make_rng(seed, task["task_id"], phase, 0, "select")
        retrieve_rng = make_rng(seed, task["task_id"], phase, 0, "retrieve")
        simulate_rng = make_rng(seed, task["task_id"], phase, 0, "simulate")
        events = []
        first_hit = None
        consecutive = 0
        decisions = 0
        misses = 0
        while not env.terminal:
            if not self.ledger.can_eval():
                self._cheap(env, events, allow_undo=False)
                if not env.terminal:
                    env.force_terminal("compute_budget")
                break
            decisions += 1
            primitive = self._primitive(env, select_rng)
            chosen = None
            if primitive is not None and self.retrieve and consecutive < self.max_consecutive and self.ledger.can_eval():
                chosen = self._retrieve(env, retrieve_rng, simulate_rng, primitive)
            if chosen is not None:
                self._execute_macro(env, chosen, events)
                consecutive += 1
                misses = 0
            elif primitive is not None:
                self._place_index(env, primitive["index"])
                self.tabu = None
                consecutive = 0
                misses = 0
                events.append(self._event(env, "primitive", primitive["index"], None))
            else:
                misses += 1
                if misses < 3 and self.ledger.can_eval():
                    continue
                self._cheap(env, events)
                misses = 0
                if env.terminal:
                    break
            if first_hit is None and env.occupied >= self.target:
                first_hit = env.place_attempts
            if decisions > self.physical + self.undo_budget + 5:
                env.force_terminal("decision_guard")
                break
        if not env.terminal:
            env.force_terminal("submit")
        q = int(env.score)
        p = int(env.place_attempts)
        return {
            "task_id": task["task_id"],
            "Q": q,
            "best_Q": int(env.best_score),
            "P": p,
            "E": efficiency(q, p),
            "target_met": q >= self.target,
            "attempts_to_target": int(first_hit) if first_hit is not None else p,
            "censored": first_hit is None,
            "undos": int(env.undos),
            "physical": int(env.actions_used),
            "invalid_places": int(env.invalid_places),
            "submits": int(env.submits),
            "termination": env.termination_reason,
            "placements": env.snapshot_placements(),
            "events": events,
            "ledger": {
                "candidate_evals": self.ledger.candidate_evals,
                "guard_evals": self.ledger.guard_evals,
                "library_lookups": self.ledger.library_lookups,
                "feature_evals": self.ledger.feature_evals,
                "model_transitions": self.ledger.model_transitions,
                "sim_expansions": self.ledger.sim_expansions,
                "gpu_ops": int(self.workspace.gpu_ops - gpu_before),
                "cheap_actions": self.ledger.cheap_actions,
                "macros_invoked": self.ledger.macros_invoked,
                "macros_completed": self.ledger.macros_completed,
                "macros_interrupted": self.ledger.macros_interrupted,
                "buckets": dict(self.ledger.buckets),
            },
        }

    def _event(self, env: PackingEnv, kind: str, index: int | None, op_id: str | None) -> dict:
        return {
            "kind": kind,
            "placement_index": index,
            "op_id": op_id,
            "Q": env.score,
            "P": env.place_attempts,
            "occupied": env.occupied,
            "candidate_evals": self.ledger.candidate_evals,
            "mask": env.mask,
        }

    def _primitive(self, env: PackingEnv, rng, scan: int | None = None, charge: bool = True) -> dict | None:
        feasible = []
        for index, placement in enumerate(ALL_PLACEMENTS):
            if not env.inventory.can_take(placement.piece_type):
                continue
            signature = (placement.piece_type, placement.rotation, placement.x, placement.y)
            if signature == self.tabu:
                continue
            feasible.append(index)
        if not feasible:
            return None
        rng.shuffle(feasible)
        want = (self.scan if scan is None else scan) + (max(0, self.think) if scan is None else 0)
        window = feasible[:want]
        if charge and scan is None and self.think:
            extra = min(self.think, len(window))
            self.ledger.charge("think", extra)
        if charge:
            bucket = "selection" if scan is None else "simulation"
            take = self.ledger.charge(bucket, len(window))
            window = window[:take]
        else:
            window = window[:want]
        if not window:
            return None
        overlap, contact = self.workspace.score_indices(env.mask, window)
        best = None
        for local, index in enumerate(window):
            self.ledger.feature_evals += 1
            if overlap[local]:
                continue
            placement = ALL_PLACEMENTS[index]
            score = float(placement.area) + 0.2 * float(contact[local]) + 0.05 * float(placement.boundary_contacts)
            tie = rng.random()
            if best is None or (score, tie) > best[0]:
                best = ((score, tie), index, score)
        if best is None:
            return None
        return {"index": best[1], "score": best[2], "utility": best[2] - 0.002}

    def _retrieve(self, env: PackingEnv, rng, simulate_rng, primitive: dict | None) -> dict | None:
        ranked = sorted(
            self.library,
            key=lambda op: (-float(op.get("train_success", 0.0)), -len(op.get("support_tasks", [])), op["op_id"]),
        )
        considered = 0
        best = None
        prim_gain, prim_blocked = self._simulated_gain(
            env, simulate_rng, first_index=None if primitive is None else primitive["index"]
        )
        if prim_gain is None:
            return None
        if prim_blocked:
            prim_gain = -1.0
        for op in ranked:
            if considered >= self.macros_considered or not self.ledger.can_eval():
                break
            if not self.ledger.charge("library", 1):
                break
            considered += 1
            if not env.inventory.fits_multiset(op["demand"]):
                continue
            steps = self._first_site(env, op, rng)
            if steps is None:
                continue
            gain, blocked = self._simulated_gain(env, simulate_rng, macro_steps=steps)
            if blocked or gain is None:
                continue
            utility = gain + 0.05 * float(op.get("train_success", 0.0))
            if utility > prim_gain and (best is None or utility > best["utility"]):
                best = {"steps": steps, "op_id": op["op_id"], "utility": utility}
                prim_gain = utility
        return best

    def _simulated_gain(self, env: PackingEnv, rng, macro_steps: list[dict] | None = None, first_index: int | None = None):
        """Occupied-cell gain after the action plus a short continuation.

        Returns ``(None, True)`` when the simulation cannot be paid for.
        A continuation that leaves a hole smaller than every remaining piece is rejected.
        """
        clone = env.clone()
        if macro_steps is not None:
            if self.ledger.charge("simulation", len(macro_steps)) < len(macro_steps):
                return None, True
            for step in macro_steps:
                if clone.terminal:
                    return None, True
                params = placement_params(step["type"], step["cells"])
                if params is None:
                    return None, True
                rotation, x, y = params
                result = clone.step(Action.place(step["type"], rotation, x, y))
                if not result.accepted:
                    return None, True
        elif first_index is not None:
            if not self.ledger.charge("simulation", 1):
                return None, True
            self._place_index(clone, first_index)
        for _ in range(self.continuation_steps):
            if clone.terminal:
                break
            if not self.ledger.can_eval():
                return None, True
            nxt = self._primitive(clone, rng, scan=self.continuation_scan, charge=True)
            if nxt is None:
                if not self.ledger.can_eval():
                    return None, True
                break
            self._place_index(clone, nxt["index"])
        if leaves_unfillable(clone.mask, clone.inventory):
            return clone.occupied - env.occupied, True
        return clone.occupied - env.occupied, False

    def _first_site(self, env: PackingEnv, op: dict, rng) -> list[dict] | None:
        candidates = []
        for k in range(4):
            turned = rotate_steps(op["steps"], k)
            first = turned[0]
            cells = [tuple(c) for c in first["cells"]]
            min_x = min(x for x, _ in cells)
            min_y = min(y for _, y in cells)
            norm = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
            for placement in _SHAPE_INDEX.get((first["type"], norm), []):
                candidates.append((placement.x - min_x, placement.y - min_y, turned))
        rng.shuffle(candidates)
        examined = 0
        for ox, oy, turned in candidates:
            if examined >= self.anchors:
                break
            if not self.ledger.charge("guard", 1):
                break
            examined += 1
            steps = translate_steps(turned, ox, oy)
            if macro_fits(env, steps):
                return steps
        return None

    def _place_index(self, env: PackingEnv, index: int) -> None:
        placement = ALL_PLACEMENTS[index]
        env.step(Action.place(placement.piece_type, placement.rotation, placement.x, placement.y))

    def _execute_macro(self, env: PackingEnv, chosen: dict, events: list) -> None:
        self.ledger.macros_invoked += 1
        accepted = 0
        for step in chosen["steps"]:
            if env.terminal:
                break
            params = placement_params(step["type"], step["cells"])
            if params is None:
                env.step(Action.place(step["type"], 0, 0, 0))
                break
            rotation, x, y = params
            result = env.step(Action.place(step["type"], rotation, x, y))
            if not result.accepted:
                break
            accepted += 1
        if accepted == len(chosen["steps"]):
            self.ledger.macros_completed += 1
            self.tabu = None
        else:
            self.ledger.macros_interrupted += 1
        events.append(self._event(env, "macro", None, chosen["op_id"]))

    def _cheap(self, env: PackingEnv, events: list, allow_undo: bool = True) -> None:
        for index, placement in enumerate(ALL_PLACEMENTS):
            if env.terminal:
                return
            if not env.inventory.can_take(placement.piece_type):
                continue
            if not self.ledger.charge("cheap", 1, reserve=True):
                env.force_terminal("compute_budget")
                events.append(self._event(env, "compute_budget", None, None))
                return
            if placement.mask & env.mask:
                continue
            signature = (placement.piece_type, placement.rotation, placement.x, placement.y)
            if signature == self.tabu:
                continue
            self.ledger.cheap_actions += 1
            self._place_index(env, index)
            self.tabu = None
            events.append(self._event(env, "cheap", index, None))
            return
        if (
            allow_undo
            and not env.terminal
            and env.stack
            and env.undos < self.undo_budget
            and env.actions_used < env.budget
        ):
            top = env.stack[-1]
            self.tabu = (top.piece_type, top.rotation, top.x, top.y)
            env.step(Action.undo())
            events.append(self._event(env, "undo", None, None))
            return
        if not env.terminal:
            env.force_terminal("no_legal")
            events.append(self._event(env, "no_legal", None, None))
