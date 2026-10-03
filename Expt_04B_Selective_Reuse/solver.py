"""Solve one box. A counts candidate evaluations, not committed macro internals."""

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field

from environment import Action, PackingEnv
from inventory import Inventory
from memory import OperationMemory
from pieces import ALL_PLACEMENTS, PIECES, orientation, placed_cells
from primitive_search import primitive_choice
from retrieval import first_legal_site, retrieve, state_features


def derive_seed(master: int, task_id: str, phase: str, repetition: int, purpose: str) -> int:
    payload = f"{int(master)}|{task_id}|{phase}|{int(repetition)}|{purpose}"
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def make_rng(master: int, task_id: str, phase: str, repetition: int, purpose: str) -> random.Random:
    return random.Random(derive_seed(master, task_id, phase, repetition, purpose))


def placement_params(piece_type: str, cells) -> tuple[int, int, int] | None:
    rel = tuple(sorted(tuple(c) for c in cells))
    min_x = min(x for x, _ in rel)
    min_y = min(y for _, y in rel)
    norm = tuple(sorted((x - min_x, y - min_y) for x, y in rel))
    for k in range(4):
        if orientation(PIECES[piece_type], k) == norm:
            return k, min_x, min_y
    return None


@dataclass
class Ledger:
    A: int = 0
    primitive_evals: int = 0
    learned_evals: int = 0
    retrieval_cost: int = 0
    applicability_cost: int = 0
    failed_attempts: int = 0
    successful_placements: int = 0
    decisions: int = 0
    internal_execution: int = 0
    abstentions: int = 0
    fallbacks: int = 0
    by_depth: dict = field(default_factory=lambda: {"0": 0, "1": 0, "2": 0, "3plus": 0})

    def charge(self, bucket: str, n: int) -> None:
        self.A += n
        if bucket == "primitive":
            self.primitive_evals += n
        elif bucket == "learned":
            self.learned_evals += n
        elif bucket == "retrieval":
            self.retrieval_cost += n
        elif bucket == "applicability":
            self.applicability_cost += n

    def note_depth(self, depth: int) -> None:
        if depth <= 0:
            self.by_depth["0"] += 1
        elif depth == 1:
            self.by_depth["1"] += 1
        elif depth == 2:
            self.by_depth["2"] += 1
        else:
            self.by_depth["3plus"] += 1


def _execute(env: PackingEnv, steps: list[dict]) -> tuple[bool, list[dict], int]:
    placed = []
    for step in steps:
        params = placement_params(step["type"], step["cells"])
        if params is None:
            return False, placed, len(placed)
        rotation, x, y = params
        result = env.step(Action.place(step["type"], rotation, x, y))
        if not result.accepted:
            return False, placed, len(placed)
        cells = placed_cells(step["type"], rotation, x, y)
        placed.append({"type": step["type"], "rotation": rotation, "x": x, "y": y, "cells": cells})
    return True, placed, len(placed)


def solve_box(config, task: dict, seed: int, phase: str, repetition: int, memory: OperationMemory | None, *, learn: bool, abstention: bool, eval_cap: int | None = None) -> dict:
    cap = int(eval_cap if eval_cap is not None else config.eval_cap)
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    decisions: list[dict] = []
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < cap:
        features = state_features(env)
        acted = False
        active = [] if memory is None else memory.active()
        if active and ledger.A < cap:
            retrieve_rng = make_rng(seed, task["task_id"], phase, repetition, f"retrieve-{ledger.decisions}")
            ranked, looked = retrieve(active, features, retrieve_rng, config.retrieval_pool, config.top_k)
            ledger.charge("retrieval", looked)
            for op, _sim in ranked:
                if learn:
                    memory.note_retrieval(op)
            eligible = []
            if abstention:
                for op, similarity in ranked:
                    if ledger.A >= cap:
                        break
                    ledger.charge("applicability", 1)
                    rule = op.ensure_rule(len(features), config.applicability_min)
                    useful, score = rule.useful_here(features)
                    if (not useful) or score < config.abstention_margin:
                        if learn:
                            memory.note_applicability_failure(op)
                        continue
                    eligible.append((op, score))
                if not eligible:
                    ledger.abstentions += 1
            else:
                for op, similarity in ranked:
                    if similarity < config.applicability_min:
                        if learn:
                            memory.note_applicability_failure(op)
                        continue
                    eligible.append((op, similarity))
            chosen = None
            for op, _score in eligible:
                if ledger.A >= cap:
                    break
                site_rng = make_rng(seed, task["task_id"], phase, repetition, f"anchor-{ledger.decisions}-{op.op_id}")
                site, examined = first_legal_site(op, env, site_rng, config.anchors)
                ledger.charge("learned", examined)
                if site is None:
                    ledger.failed_attempts += 1
                    if learn:
                        memory.note_use(op, False, 0.0, env.score, repetition, features)
                    continue
                chosen = (op, site)
                break
            if chosen is None and ranked:
                ledger.fallbacks += 1
            if chosen is not None:
                op, site = chosen
                ok, placed, n_internal = _execute(env, site)
                ledger.internal_execution += n_internal
                ledger.decisions += 1
                ledger.note_depth(op.depth)
                if ok:
                    ledger.successful_placements += len(placed)
                    acted = True
                    saved = float(max(0, len(site) - 1))
                    if learn:
                        memory.note_use(op, True, saved, env.score, repetition, features)
                        if len(op.context) == len(features):
                            op.context = [(0.8) * old + 0.2 * new for old, new in zip(op.context, features)]
                    decisions.append(
                        {
                            "op_id": op.op_id,
                            "depth": op.depth,
                            "placements": placed,
                            "features": list(features),
                        }
                    )
                else:
                    ledger.failed_attempts += 1
                    if learn:
                        memory.note_use(op, False, 0.0, env.score, repetition, features)
        if not acted:
            index = None
            for _attempt in range(4):
                found, evaluated, failed = primitive_choice(
                    env, select_rng, config.scan, config.score_area, config.score_contact, config.score_boundary, tabu
                )
                ledger.charge("primitive", evaluated)
                ledger.failed_attempts += failed
                if found is not None:
                    index = found
                    break
            if index is None:
                found, evaluated, failed = primitive_choice(
                    env, select_rng, 10**6, config.score_area, config.score_contact, config.score_boundary, tabu
                )
                ledger.charge("primitive", evaluated)
                ledger.failed_attempts += failed
                index = found
            if index is None:
                if env.stack and env.undos < config.undo_budget and env.actions_used < env.budget and not env.terminal:
                    top = env.stack[-1]
                    tabu.add((top.piece_type, top.rotation, top.x, top.y))
                    env.step(Action.undo())
                    continue
                reason = "no_progress"
                break
            tabu.clear()
            placement = ALL_PLACEMENTS[index]
            result = env.step(Action.place(placement.piece_type, placement.rotation, placement.x, placement.y))
            ledger.decisions += 1
            ledger.note_depth(0)
            if not result.accepted:
                ledger.failed_attempts += 1
                reason = "no_progress"
                break
            ledger.successful_placements += 1
            cells = placed_cells(placement.piece_type, placement.rotation, placement.x, placement.y)
            decisions.append(
                {
                    "op_id": f"O_{placement.piece_type}_{placement.rotation}",
                    "depth": 0,
                    "placements": [
                        {
                            "type": placement.piece_type,
                            "rotation": placement.rotation,
                            "x": placement.x,
                            "y": placement.y,
                            "cells": cells,
                        }
                    ],
                    "features": list(features),
                }
            )
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    if env.occupied >= config.q_min:
        reason = "quality"
    elif ledger.A >= cap:
        reason = "eval_cap"
    elif env.terminal and reason == "quality":
        reason = env.termination_reason or "terminal"
    q = float(env.score)
    elapsed = time.perf_counter() - started
    return {
        "task_id": task["task_id"],
        "Q": q,
        "A": ledger.A,
        "acceptable": q >= config.q_min,
        "efficiency": (q / ledger.A) if ledger.A else None,
        "primitive_evals": ledger.primitive_evals,
        "learned_evals": ledger.learned_evals,
        "retrieval_cost": ledger.retrieval_cost,
        "applicability_cost": ledger.applicability_cost,
        "failed_attempts": ledger.failed_attempts,
        "successful_placements": ledger.successful_placements,
        "decisions": ledger.decisions,
        "internal_execution": ledger.internal_execution,
        "abstentions": ledger.abstentions,
        "fallbacks": ledger.fallbacks,
        "depth0": ledger.by_depth["0"],
        "depth1": ledger.by_depth["1"],
        "depth2": ledger.by_depth["2"],
        "depth3plus": ledger.by_depth["3plus"],
        "elapsed_s": elapsed,
        "termination": reason,
        "decisions_trace": decisions,
        "library_size": 0 if memory is None else len(memory.active()),
        "memory_bytes": 0 if memory is None else memory.bytes_used(),
    }
