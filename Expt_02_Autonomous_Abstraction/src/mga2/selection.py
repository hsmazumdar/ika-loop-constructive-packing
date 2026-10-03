"""Dispatchers: primitive, search, flat library, hierarchical library, engineered reference.

The engineered reference is the only mode with a one-step undo tabu and a hard
small-component filter. Autonomous modes do not call those routines.
"""

from __future__ import annotations

import math

from mga2.budgets import BudgetLedger, ledger_from_config
from mga2.discovery import (
    legal_origins,
    observational_utility,
    paired_validate,
    propose,
)
from mga2.environment import Action, PackingEnv
from mga2.features import zero_weights
from mga2.interpreter import Interpreter, select_primitive
from mga2.ltm import LongTermMemory
from mga2.ops import Operation
from mga2.pieces import (
    ALL_PLACEMENTS,
    BOARD_SIZE,
    FULL_MASK,
    NEIGHBORS,
    P_MASKS,
    P_TYPES,
    Placement,
    min_piece_area,
)
from mga2.simulation import lookahead_first_action
from mga2.stm import ShortTermMemory

MODES = (
    "primitive",
    "search_only",
    "flat_library",
    "hierarchical_library",
    "engineered_reference",
)
LIBRARY_MODES = ("flat_library", "hierarchical_library")


def _flood(empty_mask: int, start_bit: int) -> int:
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


def _engineered_unfillable(size: int, min_size: int) -> bool:
    if size <= 0:
        return False
    if size < min_size or size == 6:
        return True
    return False


def _engineered_small_components(occupancy: int, placement: Placement, min_size: int) -> int:
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
        comp = _flood(empty, bit)
        visited |= comp
        seeds &= ~comp
        if _engineered_unfillable(comp.bit_count(), min_size):
            counted += 1
    return counted


class Agent:
    def __init__(self, mode: str, config: dict, ltm: LongTermMemory | None = None, frozen: bool = False) -> None:
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode}")
        self.mode = mode
        self.config = config
        mem = config.get("memory", {})
        self.stm = ShortTermMemory(int(mem.get("stm_bytes", 64 * 1024)))
        self.ltm = ltm if ltm is not None else LongTermMemory(int(mem.get("ltm_bytes", 256 * 1024)))
        self.ltm.frozen = bool(frozen) or self.ltm.frozen
        self.frozen = bool(frozen) or self.ltm.frozen
        bandit = config.get("bandit", {})
        self.ucb_c = float(bandit.get("exploration_c", 0.5))
        self.unseen_mean = float(bandit.get("unseen_mean", 0.0))
        self.unseen_count = float(bandit.get("unseen_count", 1.0))
        self.stm_explore_prob = float(bandit.get("stm_explore_prob", 0.2))
        disc = config.get("discovery", {})
        self.max_consecutive_think = int(disc.get("max_consecutive_think", 2))
        self.flat_think_interval = int(disc.get("flat_think_interval", 5))
        self.search_think_probability = float(disc.get("search_think_probability", 0.25))
        self.max_paired = int(disc.get("max_paired_trials", 2))
        self.max_origins = int(disc.get("max_origin_trials", 64))
        self.exam_limit = int(config.get("exam_limit", 0))
        lang = config.get("language", {})
        self.lookahead_depth = int(lang.get("default_lookahead_depth", 1))
        self.lookahead_width = int(lang.get("default_lookahead_width", 2))
        self.think_horizon = int(config.get("utility", {}).get("horizon", 8))
        self.episode = 0
        self.task_id = ""
        self.decisions = 0
        self.consecutive_think = 0
        self.used_beneficial: set[str] = set()
        self.last_decision: dict = {"source": "none", "reason": "", "ucb": 0.0}
        self.simulation_env: PackingEnv | None = None
        self.events: list[dict] = []
        self._pending_think: dict | None = None
        self._undo_tabu: tuple[int, tuple] | None = None
        self.weights = zero_weights()
        raw_allowance = config.get("think_eval_allowance", None)
        self.think_eval_allowance = None if raw_allowance is None else int(raw_allowance)
        self.record_decisions = bool(config.get("record_decisions", False))
        self.decision_trace: list[dict] = []

    def begin_box(self, episode: int, task_id: str) -> None:
        self.stm.clear()
        self.episode = int(episode)
        self.task_id = task_id
        self.decisions = 0
        self.consecutive_think = 0
        self.used_beneficial = set()
        self.last_decision = {"source": "none", "reason": "begin", "ucb": 0.0}
        self.simulation_env = None
        self.events = []
        self._pending_think = None
        self._undo_tabu = None
        self.stm.sample()

    def finish_box(self) -> dict:
        """Capture STM statistics, then clear. LTM consolidation happens after the snapshot."""
        stats = self.stm.snapshot_stats()
        if self.mode in LIBRARY_MODES and not self.frozen:
            self.ltm.end_box(self.used_beneficial)
        self.stm.clear()
        return stats

    def decide_and_act(self, env: PackingEnv, ledger: BudgetLedger, rng_decision, rng_discovery, rng_eval) -> None:
        if env.terminal:
            return
        if not self.record_decisions:
            self._decide_body(env, ledger, rng_decision, rng_discovery, rng_eval)
            return
        score0 = env.score
        evals0 = ledger.candidate_evals
        span0 = ledger.span_think
        before = dict(ledger.buckets)
        self._decide_body(env, ledger, rng_decision, rng_discovery, rng_eval)
        row = {
            "decision": self.decisions,
            "source": self.last_decision.get("source"),
            "reason": self.last_decision.get("reason"),
            "score_before": score0,
            "score_after": env.score,
            "evals_before": evals0,
            "evals_after": ledger.candidate_evals,
            "think_span": ledger.span_think - span0,
            "termination": env.termination_reason,
        }
        for key, value in ledger.buckets.items():
            row[key] = int(value) - int(before.get(key, 0))
        if self.last_decision.get("action"):
            row["action"] = self.last_decision["action"]
        if self.last_decision.get("op_id"):
            row["op_id"] = self.last_decision["op_id"]
        spent = ledger.candidate_evals - evals0
        accounted = sum(int(row.get(key, 0)) for key in ledger.buckets)
        if accounted != spent:
            raise RuntimeError(f"decision accounting mismatch: buckets {accounted} vs spent {spent}")
        self.decision_trace.append(row)

    def _think_room(self, ledger: BudgetLedger) -> int | None:
        if self.think_eval_allowance is None:
            return None
        return max(0, int(self.think_eval_allowance) - int(ledger.span_think))

    def _run_think(self, env, ledger, rng_discovery, rng_eval) -> None:
        prev = None
        room = self._think_room(ledger)
        if room is not None:
            prev = ledger.push_ceilings(room, max(0, ledger.model_limit() - ledger.model_transitions))
        try:
            if self.mode == "search_only":
                self._think_search(env, ledger, rng_discovery)
            else:
                self._think_library(env, ledger, rng_discovery, rng_eval)
        finally:
            if prev is not None:
                ledger.pop_ceilings(prev)

    def _decide_body(self, env: PackingEnv, ledger: BudgetLedger, rng_decision, rng_discovery, rng_eval) -> None:
        if env.terminal:
            return
        self._settle_think(env, ledger)
        self.stm.sample()
        self.decisions += 1
        if not ledger.can_eval():
            # Deliberation has reached the reserved cap. A cheap legal placement
            # still runs when eligibility evaluations remain.
            if self._cheap_progress(env, ledger, rng_decision):
                return
            if ledger.reserve_remaining():
                self._submit(env, "submit")
            else:
                self._submit(env, "compute_budget")
                self.last_decision = {"source": "primitive", "reason": "compute_budget", "ucb": 0.0}
            return
        if self.mode == "primitive":
            self._act_primitive(env, ledger, rng_decision)
            return
        if self.mode == "engineered_reference":
            self._act_engineered(env, ledger, rng_decision)
            return
        if self.mode == "hierarchical_library":
            arm, score = self._choose_arm(rng_decision, allow_think=True)
            self._log_arm(arm, score)
            if (
                arm == "think"
                and self.consecutive_think < self.max_consecutive_think
                and self._think_room(ledger) != 0
            ):
                self.consecutive_think += 1
                self.last_decision = {"source": "think", "reason": "ucb", "ucb": score}
                self._run_think(env, ledger, rng_discovery, rng_eval)
                return
            self.consecutive_think = 0
            if arm in {"stm", "ltm"} and self._maybe_macro(env, ledger, rng_decision, prefer=arm):
                return
            self._act_primitive(env, ledger, rng_decision)
            return
        if (
            self._wants_think(rng_decision)
            and self.consecutive_think < self.max_consecutive_think
            and self._think_room(ledger) != 0
        ):
            self.consecutive_think += 1
            self._run_think(env, ledger, rng_discovery, rng_eval)
            return
        self.consecutive_think = 0
        if self.mode == "search_only":
            self._act_primitive(env, ledger, rng_decision)
            return
        if self._maybe_macro(env, ledger, rng_decision, prefer=None):
            return
        self._act_primitive(env, ledger, rng_decision)

    def _submit(self, env: PackingEnv, reason: str) -> None:
        if reason == "compute_budget":
            env.force_terminal("compute_budget")
        else:
            env.step(Action.submit())

    def _cheap_progress(self, env, ledger, rng) -> bool:
        """One legal primitive using evaluations deliberation was not allowed to spend."""
        if not ledger.reserve_remaining() or env.terminal:
            return False
        previous = ledger.protect_reserve
        ledger.protect_reserve = False
        try:
            with ledger.tally("placement"):
                with ledger.tally("selection"):
                    action = select_primitive(env, ledger, rng, self.exam_limit)
        finally:
            ledger.protect_reserve = previous
        if action is None:
            return False
        env.step(action)
        ledger.physical = env.actions_used
        ledger.primitive_decisions += 1
        ledger.cheap_actions += 1
        self.last_decision = {
            "source": "primitive",
            "reason": "cheap_legal_at_cap",
            "ucb": 0.0,
            "action": action.as_dict(),
        }
        self.events.append({"type": "cheap_action", "action": action.as_dict(), "evals": ledger.candidate_evals})
        if self.mode in LIBRARY_MODES:
            self._sync_trace(env)
        return True

    def _act_primitive(self, env, ledger, rng) -> None:
        with ledger.tally("placement"):
            with ledger.tally("selection"):
                action = select_primitive(env, ledger, rng, self.exam_limit)
        if action is None:
            # A finished scan with evaluations left means nothing legal remains.
            # The reserved scan runs only after deliberation has stopped.
            if not ledger.can_eval() and self._cheap_progress(env, ledger, rng):
                return
            reason = "compute_budget" if not ledger.reserve_remaining() else "submit"
            self._submit(env, reason)
            self.last_decision = {"source": "primitive", "reason": reason, "ucb": 0.0}
            return
        env.step(action)
        ledger.physical = env.actions_used
        ledger.primitive_decisions += 1
        self.last_decision = {
            "source": "primitive",
            "reason": "uniform_among_examined_legal",
            "ucb": 0.0,
            "action": action.as_dict(),
        }
        if self.mode in LIBRARY_MODES:
            self._sync_trace(env)

    def _sync_trace(self, env: PackingEnv) -> None:
        self.stm.trace = [
            {"type": inst.piece_type, "rotation": inst.rotation, "x": inst.x, "y": inst.y}
            for inst in env.stack
        ]
        self.stm.sample()

    def _wants_think(self, rng) -> bool:
        if not self.config.get("budgets", {}).get("allow_think", True):
            return False
        if self.mode == "search_only":
            return rng.random() < self.search_think_probability
        if self.mode == "flat_library":
            return self.flat_think_interval > 0 and (self.decisions % self.flat_think_interval == 0)
        return False

    def _choose_arm(self, rng, allow_think: bool) -> tuple[str, float]:
        arms = ["primitive", "stm", "ltm"] + (["think"] if allow_think else [])
        scored = [(self._ucb(arm), arm) for arm in arms]
        best = max(s for s, _ in scored)
        tied = [arm for s, arm in scored if s == best]
        # Equal scores tie-break by the decision RNG, not by a fixed preference for thinking.
        pick = tied[rng.randrange(len(tied))]
        return pick, best

    def _arm_row(self, arm: str) -> dict:
        row = self.ltm.selector.get(arm)
        if row is None:
            row = self.stm.selector.get(arm)
        if row is None:
            return {"n": 0, "sum": 0.0}
        return row

    def _ucb_parts(self, arm: str) -> dict:
        row = self._arm_row(arm)
        observed = float(row.get("n", 0))
        n = observed if observed else self.unseen_count
        mean = (float(row.get("sum", 0.0)) / observed) if observed else self.unseen_mean
        total = 1.0 + sum(
            float(item.get("n", 0))
            for item in list(self.ltm.selector.values()) + list(self.stm.selector.values())
        )
        bonus = self.ucb_c * math.sqrt(math.log(total + 1.0) / n)
        return {"mean": mean, "n": observed, "bonus": bonus, "ucb": mean + bonus, "sum": float(row.get("sum", 0.0))}

    def _ucb(self, arm: str) -> float:
        return float(self._ucb_parts(arm)["ucb"])

    def _log_arm(self, arm: str, score: float) -> None:
        parts = {name: self._ucb_parts(name) for name in ("primitive", "stm", "ltm", "think")}
        self.events.append({"type": "arm_choice", "arm": arm, "ucb": score, "parts": parts})

    def _bump(self, arm: str, reward: float) -> None:
        if not self.frozen:
            self.ltm.bump_selector(arm, reward)
        self.stm.bump_selector(arm, reward)

    def _settle_think(self, env, ledger: BudgetLedger) -> None:
        pending = self._pending_think
        if not pending:
            return
        if env.actions_used < pending["actions"] + self.think_horizon and not env.terminal:
            return
        delta = env.score - pending["score"]
        phys = env.actions_used - pending["actions"]
        reward = observational_utility(delta, phys, pending["model"], self.config)
        self._bump("think", reward)
        self.events.append({"type": "think_outcome", "reward": reward, "delta_filled": delta})
        self._pending_think = None

    def _think_search(self, env, ledger, rng) -> None:
        ledger.think_batches += 1
        model0 = ledger.model_transitions
        self.simulation_env = env.clone()
        eval0 = ledger.candidate_evals
        with ledger.tally("think"):
            action = lookahead_first_action(
                env,
                ledger,
                rng,
                self.lookahead_depth,
                self.lookahead_width,
                self.weights,
                self.exam_limit,
            )
        self.events.append(
            {
                "type": "think",
                "mode": "search_only",
                "model": ledger.model_transitions - model0,
                "evals": ledger.candidate_evals - eval0,
            }
        )
        if action is None:
            self._act_primitive(env, ledger, rng)
            return
        # Mental board shows the imagined placement. The real board changes only on commit.
        self.simulation_env.step(action)
        env.step(action)
        ledger.physical = env.actions_used
        ledger.primitive_decisions += 1
        self.last_decision = {
            "source": "think",
            "reason": "lookahead",
            "ucb": self._ucb("think"),
            "action": action.as_dict(),
        }
        self._pending_think = {
            "actions": env.actions_used,
            "score": env.score,
            "model": ledger.model_transitions - model0,
        }

    def _think_library(self, env, ledger, rng_discovery, rng_eval) -> None:
        ledger.think_batches += 1
        model0 = ledger.model_transitions
        eval0 = ledger.candidate_evals
        self.simulation_env = env.clone()
        library = {**self.stm.candidates, **self.ltm.ops}
        plan_bytes = 0
        trials = 0
        with ledger.tally("think"):
            with ledger.tally("candidate"):
                batch = propose(self.stm, self.ltm, self.config, rng_discovery, self.mode, self.episode)
            for op, source, reject in batch:
                self.events.append(
                    {
                        "type": "proposal",
                        "op_id": op.op_id,
                        "source": source,
                        "reject_reason": reject,
                        "depth": op.depth,
                    }
                )
                if reject:
                    continue
                if trials >= self.max_paired:
                    self.events.append({"type": "proposal", "op_id": op.op_id, "source": source, "reject_reason": "trial_cap"})
                    continue
                if not ledger.can_simulate() or not ledger.can_eval():
                    self.events.append({"type": "proposal", "op_id": op.op_id, "source": source, "reject_reason": "compute_budget"})
                    break
                trials += 1
                report = paired_validate(op, env, ledger, rng_eval, self.config, library)
                if report is None:
                    self.events.append({"type": "validation", "op_id": op.op_id, "reject_reason": "no_budget"})
                    break
                promoted = False
                if report["legal"] and report["U"] > 0:
                    self.stm.add_candidate(op)
                    if not self.frozen:
                        promoted = self.ltm.add_provisional(op, self.episode)
                        if promoted:
                            self.ltm.note_paired(op.op_id, report["U"])
                    library[op.op_id] = op
                else:
                    self.stm.note_failure({"op_id": op.op_id, "U": report["U"], "legal": report["legal"]})
                self.events.append(
                    {
                        "type": "validation",
                        "op_id": op.op_id,
                        "source": source,
                        "U": report["U"],
                        "legal": report["legal"],
                        "promoted": promoted,
                        "delta_filled": report["delta_filled"],
                        "physical_actions": report["physical_actions"],
                        "model_transitions": report["model_transitions"],
                    }
                )
                plan_bytes += op.logical_bytes()
                if not ledger.note_planning(plan_bytes):
                    break
        self.events.append(
            {
                "type": "think_batch",
                "trials": trials,
                "evals": ledger.candidate_evals - eval0,
                "span_think": ledger.span_think,
                "span_paired": ledger.span_paired,
                "part_paired": ledger.part_paired,
                "part_guard": ledger.part_guard,
                "part_selection": ledger.part_selection,
            }
        )
        self._pending_think = {
            "actions": env.actions_used,
            "score": env.score,
            "model": ledger.model_transitions - model0,
        }
        self.last_decision = {
            "source": "think",
            "reason": "proposal_batch",
            "ucb": self._ucb("think"),
            "trials": trials,
        }

    def _maybe_macro(self, env, ledger, rng, prefer: str | None) -> bool:
        pools: list[tuple[str, Operation]] = []
        want_stm = prefer in {None, "stm"} and (prefer == "stm" or rng.random() < self.stm_explore_prob)
        want_ltm = prefer in {None, "ltm"}
        if want_stm:
            for op in self.stm.candidates.values():
                pools.append(("stm", op))
        if want_ltm:
            for op in self.ltm.ops.values():
                if op.status == "evicted":
                    continue
                pools.append(("ltm", op))
        if not pools:
            return False
        rng.shuffle(pools)
        # Bound how many operations we try so origin scans cannot consume the box.
        for source, op in pools[:4]:
            if not ledger.can_eval():
                return False
            with ledger.tally("library"):
                origins = legal_origins(op, env, ledger, self.max_origins)
            if not origins:
                continue
            origin = origins[rng.randrange(len(origins))]
            return self._execute_op(op, source, origin, env, ledger, rng)
        return False

    def _execute_op(self, op: Operation, source: str, origin: tuple, env, ledger, rng) -> bool:
        before_score = env.score
        before_actions = env.actions_used
        self.ltm._protected.add(op.op_id)
        interp = Interpreter(self.config, {**self.stm.candidates, **self.ltm.ops})
        with ledger.tally("placement"):
            result = interp.execute(op.ast, env, ledger, rng, simulate=False, origin=origin)
        self.ltm._protected.discard(op.op_id)
        ledger.physical = env.actions_used
        ledger.macro_invocations += 1
        delta = env.score - before_score
        phys = env.actions_used - before_actions
        value = observational_utility(delta, phys, 0, self.config)
        success = bool(result.ok and result.expanded > 0)
        if source == "ltm" or op.op_id in self.ltm.ops:
            self.ltm.note_real_use(op.op_id, value, success, self.task_id, origin)
        self._bump(source, value)
        if success and value > 0:
            self.used_beneficial.add(op.op_id)
        self.last_decision = {
            "source": source,
            "reason": "execute_operation",
            "ucb": self._ucb(source),
            "op_id": op.op_id,
            "origin": list(origin),
            "utility": value,
            "success": success,
            "failure_reason": None if success else result.reason,
        }
        self.events.append(
            {
                "type": "reuse" if success else "failure",
                "op_id": op.op_id,
                "source": source,
                "utility": value,
                "success": success,
                "origin": list(origin),
                "task_id": self.task_id,
                "reason": result.reason,
            }
        )
        self._sync_trace(env)
        if env.terminal:
            return True
        return True

    def _act_engineered(self, env: PackingEnv, ledger: BudgetLedger, rng) -> None:
        """Externally designed Expt-1 heuristic. Not a teacher for other modes."""
        occ = env.mask
        scored: list[tuple[float, int, int]] = []
        hole_free: list[tuple[float, int, int]] = []
        min_size = int(self.config.get("engineered_reference", {}).get("min_piece_area", min_piece_area()))
        w_fill = float(self.config.get("engineered_reference", {}).get("w_fill", 1.0))
        w_contact = float(self.config.get("engineered_reference", {}).get("w_contact", 0.45))
        w_hole = float(self.config.get("engineered_reference", {}).get("w_hole", 1.0))
        for i, pmask in enumerate(P_MASKS):
            if ledger.charge_eval(1) <= 0:
                break
            if pmask & occ:
                continue
            if not env.inventory.can_take(P_TYPES[i]):
                continue
            placement = ALL_PLACEMENTS[i]
            if self._undo_tabu is not None and env.mask == self._undo_tabu[0]:
                if placement.signature == self._undo_tabu[1]:
                    continue
            contacts = placement.boundary_contacts + (placement.neighbor_mask & occ).bit_count()
            holes = _engineered_small_components(occ, placement, min_size)
            value = w_fill * (placement.area / 7.0) + w_contact * (contacts / 28.0) - w_hole * (holes / 8.0)
            item = (value, holes, i)
            scored.append(item)
            if holes == 0:
                hole_free.append(item)
        self._undo_tabu = None
        pool = hole_free if hole_free else scored
        if not pool:
            if not ledger.can_eval() and not scored:
                self._submit(env, "compute_budget")
                return
            if env.can_undo:
                top = env.peek_top()
                if top is not None:
                    preceding = env.mask & ~top.mask
                    sig = (top.piece_type, top.rotation, top.x, top.y)
                    self._undo_tabu = (preceding, sig)
                env.step(Action.undo())
                ledger.physical = env.actions_used
                self.last_decision = {"source": "engineered_reference", "reason": "undo_tabu", "ucb": 0.0}
                return
            self._submit(env, "submit")
            return
        best = max(item[0] for item in pool)
        tied = [item for item in pool if item[0] == best]
        _value, _holes, idx = tied[rng.randrange(len(tied))]
        action = Action.place_from(ALL_PLACEMENTS[idx])
        env.step(action)
        ledger.physical = env.actions_used
        ledger.primitive_decisions += 1
        self.last_decision = {
            "source": "engineered_reference",
            "reason": "designed_heuristic_with_tabu",
            "ucb": 0.0,
            "action": action.as_dict(),
        }


def new_library(config: dict) -> LongTermMemory:
    mem = config.get("memory", {})
    life = config.get("lifecycle", {})
    return LongTermMemory(
        byte_cap=int(mem.get("ltm_bytes", 256 * 1024)),
        confirm_uses=int(life.get("confirm_uses", 3)),
        confirm_tasks=int(life.get("confirm_tasks", 2)),
        expiry_boxes=int(life.get("expiry_boxes", 20)),
    )


def make_ledger(config: dict) -> BudgetLedger:
    ledger = ledger_from_config(config)
    raw = config.get("budgets", {}).get("cheap_scan_reserve", None)
    if raw is None:
        from mga2.pieces import P_MASKS

        raw = len(P_MASKS)
    ledger.cheap_reserve = max(0, int(raw))
    return ledger
