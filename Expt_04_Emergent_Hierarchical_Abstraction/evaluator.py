"""Train, freeze, and evaluate. Held-out boxes are never stored or mined.

The objective of this experiment is not to discover a better packing heuristic.
Packing is the observable environment. The experiment asks whether repeated
information can autonomously become compressed reusable knowledge, and whether
that knowledge allows future problems to be solved with less deliberation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

from abstraction_miner import AbstractionMiner, expand_primitives
from controls import ControlAgent, knockout, shift_inventory
from environment import Action, PackingEnv
from flat_memory_agent import FlatMemoryAgent
from hierarchical_agent import HierarchicalAgent
from inventory import Inventory
from memory import Episode, clone_operations
from pieces import ALL_PLACEMENTS, PIECES, orientation, placed_cells
from primitive_agent import PrimitiveAgent, primitive_choice
from retrieval import first_legal_site, retrieve, state_features

ROOT = Path(__file__).resolve().parent


def derive_seed(master: int, task_id: str, phase: str, repetition: int, purpose: str) -> int:
    payload = f"{int(master)}|{task_id}|{phase}|{int(repetition)}|{purpose}"
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def make_rng(master: int, task_id: str, phase: str, repetition: int, purpose: str) -> random.Random:
    return random.Random(derive_seed(master, task_id, phase, repetition, purpose))


def load_split(name: str) -> list[dict]:
    payload = json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))
    return list(payload["tasks"])


def placement_params(piece_type: str, cells) -> tuple[int, int, int] | None:
    rel = tuple(sorted(tuple(c) for c in cells))
    min_x = min(x for x, _ in rel)
    min_y = min(y for _, y in rel)
    norm = tuple(sorted((x - min_x, y - min_y) for x, y in rel))
    for k in range(4):
        if orientation(PIECES[piece_type], k) == norm:
            return k, min_x, min_y
    return None


def build_agent(name: str, config):
    if name == "primitive":
        return PrimitiveAgent(config)
    if name == "flat":
        return FlatMemoryAgent(config)
    if name == "hierarchical":
        return HierarchicalAgent(config, unlimited=False)
    if name == "hierarchical_unlimited":
        return HierarchicalAgent(config, unlimited=True)
    if name == "control":
        return ControlAgent(config)
    raise KeyError(name)


AGENT_NAMES = ("primitive", "flat", "hierarchical", "hierarchical_unlimited", "control")


@dataclass
class Ledger:
    A: int = 0
    primitive_evals: int = 0
    learned_evals: int = 0
    retrieval_cost: int = 0
    failed_attempts: int = 0
    successful_placements: int = 0
    decisions: int = 0
    internal_execution: int = 0
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


def solve_box(config, task: dict, seed: int, phase: str, repetition: int, memory, learn: bool) -> dict:
    """Solve one inventory. A counts candidate evaluations, not committed macro internals."""
    started = time.perf_counter()
    env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
    ledger = Ledger()
    decisions: list[dict] = []
    tabu: set = set()
    select_rng = make_rng(seed, task["task_id"], phase, repetition, "select")
    reason = "quality"
    while not env.terminal and env.occupied < config.q_min and ledger.A < config.eval_cap:
        features = state_features(env)
        acted = False
        if memory is not None and memory.operations and ledger.A < config.eval_cap:
            retrieve_rng = make_rng(seed, task["task_id"], phase, repetition, f"retrieve-{ledger.decisions}")
            ranked, looked = retrieve(memory, features, retrieve_rng, config.retrieval_pool, config.top_k)
            ledger.charge("retrieval", looked)
            chosen = None
            for op, similarity in ranked:
                if ledger.A >= config.eval_cap:
                    break
                if similarity < config.applicability_min:
                    continue
                site_rng = make_rng(seed, task["task_id"], phase, repetition, f"anchor-{ledger.decisions}-{op.op_id}")
                site, examined = first_legal_site(op, env, site_rng, config.anchors)
                ledger.charge("learned", examined)
                if site is None:
                    ledger.failed_attempts += 1
                    if learn:
                        memory.note_use(op, False, 0.0, env.score, repetition)
                    continue
                chosen = (op, site, similarity)
                break
            if chosen is None and ranked:
                ledger.fallbacks += 1
            if chosen is not None:
                op, site, similarity = chosen
                ok, placed, n_internal = _execute(env, site)
                ledger.internal_execution += n_internal
                ledger.decisions += 1
                ledger.note_depth(op.depth)
                if ok:
                    ledger.successful_placements += len(placed)
                    acted = True
                    saved = float(max(0, len(site) - 1))
                    if learn:
                        memory.note_use(op, True, saved, env.score, repetition)
                        if len(op.context) == len(features):
                            op.context = [(1.0 - 0.2) * old + 0.2 * new for old, new in zip(op.context, features)]
                    decisions.append({
                        "op_id": op.op_id,
                        "depth": op.depth,
                        "placements": placed,
                        "features": list(features),
                    })
                else:
                    ledger.failed_attempts += 1
                    if learn:
                        memory.note_use(op, False, 0.0, env.score, repetition)
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
            decisions.append({
                "op_id": f"O_{placement.piece_type}_{placement.rotation}",
                "depth": 0,
                "placements": [{
                    "type": placement.piece_type,
                    "rotation": placement.rotation,
                    "x": placement.x,
                    "y": placement.y,
                    "cells": cells,
                }],
                "features": list(features),
            })
        if env.terminal:
            reason = env.termination_reason or "terminal"
            break
    if env.occupied >= config.q_min:
        reason = "quality"
    elif ledger.A >= config.eval_cap:
        reason = "eval_cap"
    elif env.terminal and reason == "quality":
        reason = env.termination_reason or "terminal"
    q = float(env.score)
    acceptable = q >= config.q_min
    elapsed = time.perf_counter() - started
    return {
        "task_id": task["task_id"],
        "Q": q,
        "A": ledger.A,
        "acceptable": acceptable,
        "efficiency": (q / ledger.A) if ledger.A else None,
        "primitive_evals": ledger.primitive_evals,
        "learned_evals": ledger.learned_evals,
        "retrieval_cost": ledger.retrieval_cost,
        "failed_attempts": ledger.failed_attempts,
        "successful_placements": ledger.successful_placements,
        "decisions": ledger.decisions,
        "internal_execution": ledger.internal_execution,
        "fallbacks": ledger.fallbacks,
        "depth0": ledger.by_depth["0"],
        "depth1": ledger.by_depth["1"],
        "depth2": ledger.by_depth["2"],
        "depth3plus": ledger.by_depth["3plus"],
        "elapsed_s": elapsed,
        "termination": reason,
        "decisions_trace": decisions,
        "library_size": 0 if memory is None else len(memory.operations),
    }


def _phase_pools(train: list[dict], seed: int, probe_count: int) -> tuple[list[dict], list[dict], list[dict]]:
    shifted = []
    for task in train:
        rng = make_rng(seed, task["task_id"], "environment", 0, "shift")
        inventory = shift_inventory(dict(task["inventory"]), rng)
        shifted.append({
            "task_id": "b_" + task["task_id"],
            "family": "shifted_inventory",
            "inventory": inventory,
        })
    probe = shifted[:probe_count]
    phase_b = shifted[probe_count:] or shifted
    return train, phase_b, probe


def run_lifetime(config, agent_name: str, seed: int, train: list[dict], heldout: list[dict], probe: list[dict], phase_b: list[dict]) -> dict:
    agent = build_agent(agent_name, config)
    memory = agent.memory
    miner = None
    if memory is not None:
        miner = AbstractionMiner(config, memory, control=bool(memory.control))
    rows = []
    checkpoints = []

    def evaluate(experience: int, distribution: str, tasks: list[dict], memory_override=None, tag: str = "heldout") -> None:
        used = memory if memory_override is None else memory_override
        for index, task in enumerate(tasks):
            outcome = solve_box(config, task, seed, "heldout" if tag == "heldout" else "probe", index, used, learn=False)
            outcome.pop("decisions_trace", None)
            outcome.update({
                "agent": agent_name,
                "seed": seed,
                "experience": experience,
                "distribution": distribution,
                "split": tag,
            })
            checkpoints.append(outcome)

    def maybe_checkpoint(experience: int) -> None:
        if experience not in set(config.checkpoints):
            return
        evaluate(experience, "A", heldout, tag="heldout")
        evaluate(experience, "B", probe, tag="probe")

    maybe_checkpoint(0)
    sample_rng = make_rng(seed, agent_name, "train", 0, "sample")
    for index in range(config.train_boxes):
        experience = index
        pool = train if experience < config.change_at else phase_b
        distribution = "A" if experience < config.change_at else "B"
        task = pool[sample_rng.randrange(len(pool))]
        outcome = solve_box(config, task, seed, "train", index, memory, learn=memory is not None)
        trace = outcome.pop("decisions_trace")
        if miner is not None and outcome["acceptable"]:
            episode = Episode(
                episode_id=index,
                task_id=task["task_id"],
                inventory=dict(task["inventory"]),
                decisions=trace,
                q=outcome["Q"],
                a=outcome["A"],
                acceptable=True,
            )
            miner.observe(episode, make_rng(seed, task["task_id"], "train", index, "mine"))
        outcome.update({
            "agent": agent_name,
            "seed": seed,
            "experience": index + 1,
            "distribution": distribution,
            "split": "train",
            "library_size": 0 if memory is None else len(memory.operations),
            "memory_bytes": 0 if memory is None else memory.bytes_used(),
            "mean_depth": _mean_depth(memory),
            "max_depth": _max_depth(memory),
        })
        rows.append(outcome)
        maybe_checkpoint(index + 1)
    specials = []
    if agent_name == "hierarchical" and memory is not None:
        transferred = clone_operations(memory)
        for index, task in enumerate(heldout):
            outcome = solve_box(config, task, seed, "heldout", index, transferred, learn=False)
            outcome.pop("decisions_trace", None)
            outcome.update({"agent": agent_name, "seed": seed, "experience": config.train_boxes, "split": "transfer", "distribution": "A"})
            specials.append(outcome)
        for mode in ("all", "highest", "frequent", "random"):
            knocked = knockout(memory, mode, make_rng(seed, mode, "knockout", 0, "remove"))
            for index, task in enumerate(heldout):
                outcome = solve_box(config, task, seed, "heldout", index, knocked, learn=False)
                outcome.pop("decisions_trace", None)
                outcome.update({
                    "agent": agent_name,
                    "seed": seed,
                    "experience": config.train_boxes,
                    "split": "knockout_" + mode,
                    "distribution": "A",
                })
                specials.append(outcome)
    return {
        "agent": agent_name,
        "seed": seed,
        "train_rows": rows,
        "checkpoint_rows": checkpoints,
        "special_rows": specials,
        "memory": memory,
    }


def _mean_depth(memory) -> float:
    if memory is None or not memory.operations:
        return 0.0
    return sum(op.depth for op in memory.operations) / len(memory.operations)


def _max_depth(memory) -> int:
    if memory is None or not memory.operations:
        return 0
    return max(op.depth for op in memory.operations)


def write_tables(run_dir: Path, train_rows: list[dict], checkpoint_rows: list[dict], special_rows: list[dict]) -> None:
    _write_csv(run_dir / "train_boxes.csv", train_rows)
    _write_csv(run_dir / "checkpoints.csv", checkpoint_rows)
    _write_csv(run_dir / "special.csv", special_rows)


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def assert_split_disjoint(train: list[dict], heldout: list[dict], probe: list[dict]) -> None:
    train_ids = {task["task_id"] for task in train}
    held_ids = {task["task_id"] for task in heldout}
    probe_ids = {task["task_id"] for task in probe}
    if train_ids & held_ids:
        raise RuntimeError("training ids leaked into the held-out split")
    if probe_ids & held_ids:
        raise RuntimeError("probe ids overlap the held-out split")
    if any(not task["task_id"].startswith("b_") for task in probe):
        raise RuntimeError("probe tasks must be the shifted distribution")
