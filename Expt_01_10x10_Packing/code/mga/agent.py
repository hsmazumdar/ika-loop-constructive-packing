"""Shared decision policy for the four memory ablations.

All modes share observations, legal-action generation, heuristic, epsilon-greedy
exploration, action budget and computation limits. The heuristic is engineered,
not discovered intelligence. The validator/solver is never imported here.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

from mga.environment import Action, PackingEnv
from mga.memory import (
    EpisodeUpdateBuffer,
    LongTermMemory,
    ShortTermMemory,
    ltm_key,
)
from mga.pieces import ALL_PLACEMENTS, BOARD_SIZE, FULL_MASK, NEIGHBORS, Placement, lookup_placement, min_piece_area


MODES = ("none", "stm", "ltm", "both")


def _flood_component(empty_mask: int, start_bit: int) -> int:
    stack = start_bit
    seen = 0
    while stack:
        bit = stack & -stack
        stack ^= bit
        seen |= bit
        idx = bit.bit_length() - 1
        x = idx % BOARD_SIZE
        y = idx // BOARD_SIZE
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                nb = 1 << (ny * BOARD_SIZE + nx)
                if nb & empty_mask and not (nb & seen):
                    stack |= nb
    return seen


def is_unfillable_area(size: int, min_size: int = 4) -> bool:
    """Empty regions that no combination of 4/5/7-cell pieces can fill."""
    if size <= 0:
        return False
    if size < min_size or size == 6:
        return True
    return False


def small_components_touching(occupancy: int, placement: Placement, min_size: int) -> int:
    """Count newly touched empty components that cannot be tiled by the catalogue."""
    after = occupancy | placement.mask
    empty = FULL_MASK ^ after
    seeds = placement.neighbor_mask & empty
    counted = 0
    visited = 0
    while seeds:
        bit = seeds & -seeds
        seeds ^= bit
        if bit & visited:
            continue
        comp = _flood_component(empty, bit)
        visited |= comp
        seeds &= ~comp
        if is_unfillable_area(comp.bit_count(), min_size):
            counted += 1
    return counted


def contact_count(occupancy: int, placement: Placement) -> int:
    return placement.boundary_contacts + (placement.neighbor_mask & occupancy).bit_count()


@dataclass(slots=True)
class Heuristic:
    w_fill: float = 1.0
    w_contact: float = 0.45
    w_hole: float = 1.0
    fill_div: float = 7.0
    contact_div: float = 28.0
    hole_div: float = 8.0
    min_piece: int = 4

    def features(self, occupancy: int, placement: Placement) -> tuple[float, int]:
        fill = placement.area / self.fill_div
        contact = contact_count(occupancy, placement) / self.contact_div
        holes = small_components_touching(occupancy, placement, self.min_piece)
        hole = holes / self.hole_div
        score = self.w_fill * fill + self.w_contact * contact - self.w_hole * hole
        return score, holes

    def score(self, occupancy: int, placement: Placement) -> float:
        return self.features(occupancy, placement)[0]


class PackingAgent:
    """One shared policy path; memory modules are enabled or disabled by mode."""

    def __init__(
        self,
        mode: str = "both",
        config: dict[str, Any] | None = None,
        ltm: LongTermMemory | None = None,
    ) -> None:
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode}")
        self.mode = mode
        cfg = config or {}
        self.epsilon = float(cfg.get("epsilon", 0.15))
        self.use_stm = mode in ("stm", "both")
        self.use_ltm = mode in ("ltm", "both")
        weights = cfg.get("heuristic_weights", {})
        norm = cfg.get("heuristic_normalization", {})
        self.heuristic = Heuristic(
            w_fill=float(weights.get("fill", 1.0)),
            w_contact=float(weights.get("contact", 0.45)),
            w_hole=float(weights.get("small_component_penalty", 1.0)),
            fill_div=float(norm.get("fill_divisor", 7.0)),
            contact_div=float(norm.get("contact_divisor", 28.0)),
            hole_div=float(norm.get("small_component_divisor", 8.0)),
            min_piece=int(cfg.get("min_piece_area", min_piece_area())),
        )
        self.stm = ShortTermMemory(capacity=int(cfg.get("stm_capacity", 64)))
        self.ltm = ltm or LongTermMemory(
            capacity=int(cfg.get("ltm_capacity", 4096)),
            coefficient=float(cfg.get("ltm_coefficient", 0.40)),
            shrinkage_k=int(cfg.get("ltm_shrinkage_k", 5)),
        )
        if not self.use_ltm:
            # Keep an isolated dummy so calls stay uniform without writing real LTM.
            pass
        self.avoid_new_holes = bool(cfg.get("avoid_new_holes_if_possible", True))
        self.buffer = EpisodeUpdateBuffer(max_actions=int(cfg.get("action_budget", 100)))
        self.candidate_evaluations = 0
        self._last_dead_end = False
        self._undo_tabu: tuple[int, tuple] | None = None
        self._ltm_hits_episode = 0
        self._ltm_lookups_episode = 0
        self._ltm_evictions_start = self.ltm.evictions

    def begin_box(self) -> None:
        self.stm.clear()
        self.buffer.clear()
        self.candidate_evaluations = 0
        self._last_dead_end = False
        self._undo_tabu = None
        self._ltm_hits_episode = 0
        self._ltm_lookups_episode = 0
        self._ltm_evictions_start = self.ltm.evictions
        self.ltm.reset_episode_counters()

    def memory_stats(self) -> dict[str, int]:
        return {
            "stm_entries": len(self.stm) if self.use_stm else 0,
            "ltm_entries": len(self.ltm.entries) if self.use_ltm else 0,
            "ltm_hits": self._ltm_hits_episode if self.use_ltm else 0,
            "ltm_lookups": self._ltm_lookups_episode if self.use_ltm else 0,
            "ltm_evictions": (self.ltm.evictions - self._ltm_evictions_start) if self.use_ltm else 0,
            "memory_serialized_bytes": self.ltm.serialized_bytes() if self.use_ltm else 0,
            "candidate_evaluations": self.candidate_evaluations,
        }

    def _rank(self, env: PackingEnv) -> list[tuple[float, Placement]]:
        occ = env.mask
        excluded = self.stm.excluded_signatures(occ) if self.use_stm else set()
        scored: list[tuple[float, Placement]] = []
        hole_free: list[tuple[float, Placement]] = []
        lookups_before = self.ltm.lookups
        hits_before = self.ltm.hits
        for p in ALL_PLACEMENTS:
            if p.mask & occ:
                continue
            if p.signature in excluded:
                continue
            value, holes = self.heuristic.features(occ, p)
            if self.use_ltm:
                value += self.ltm.bonus(ltm_key(occ, p))
            item = (round(value, 10), p)
            scored.append(item)
            if holes == 0:
                hole_free.append(item)
            self.candidate_evaluations += 1
        if self.use_ltm:
            self._ltm_lookups_episode += self.ltm.lookups - lookups_before
            self._ltm_hits_episode += self.ltm.hits - hits_before
        if self.avoid_new_holes and hole_free:
            return hole_free
        return scored

    def select(self, env: PackingEnv, rng: random.Random) -> Action:
        scored = self._rank(env)
        if self._undo_tabu is not None and env.mask == self._undo_tabu[0]:
            filtered = [item for item in scored if item[1].signature != self._undo_tabu[1]]
            if filtered:
                scored = filtered
        self._undo_tabu = None
        if not scored:
            self._last_dead_end = True
            if env.can_undo:
                top = env.peek_top()
                if top is not None:
                    preceding = env.mask_without_top()
                    sig = (top.piece_type, top.rotation, top.x, top.y)
                    self._undo_tabu = (preceding, sig)
                    if self.use_stm:
                        self.stm.exclude(preceding, sig)
                return Action.undo()
            return Action.submit()

        self._last_dead_end = False
        if rng.random() < self.epsilon:
            choice = scored[rng.randrange(len(scored))][1]
            return Action.place_from(choice)

        best_h = max(h for h, _ in scored)
        best = [p for h, p in scored if h == best_h]
        best.sort(key=lambda p: (p.piece_type, p.rotation, p.y, p.x))
        choice = best[rng.randrange(len(best))]
        return Action.place_from(choice)

    def after_step(self, env: PackingEnv, action: Action, occupied_before: int, mask_before: int) -> None:
        if action.kind.value != "PLACE" or action.piece_type is None:
            return
        if not self.use_ltm:
            return
        placement = lookup_placement(action.piece_type, action.rotation, action.x, action.y)
        if placement is None:
            return
        key = ltm_key(mask_before, placement)
        self.buffer.add(key, occupied_before, env.actions_used)

    def end_box(self, env: PackingEnv) -> None:
        if self.use_ltm:
            self.buffer.apply(self.ltm, env.occupied, env.actions_used)
        else:
            self.buffer.clear()
        self.stm.clear()
