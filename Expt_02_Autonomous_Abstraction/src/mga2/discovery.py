"""Bounded proposal generation and paired utility checks.

No preferred shape class, no witness access, and no preloaded macros.
"""

from __future__ import annotations

import copy

from mga2.budgets import BudgetLedger, UtilityWeights, utility
from mga2.environment import PackingEnv
from mga2.features import zero_weights
from mga2.interpreter import Interpreter
from mga2.ltm import LongTermMemory
from mga2.ops import (
    Operation,
    anchor_after_rotation,
    call,
    expand_spatial,
    is_connected,
    make_operation,
    place_rel,
    seq,
    spatial_from_absolute,
    validate_program,
)
from mga2.pieces import piece_area
from mga2.simulation import primitive_rollout
from mga2.stm import ShortTermMemory

# Adjacent offsets, every direction paired with its opposite.
OFFSETS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
    (2, 0),
    (-2, 0),
    (0, 2),
    (0, -2),
    (1, 1),
    (1, -1),
    (-1, 1),
    (-1, -1),
)


def _limits(cfg: dict) -> dict:
    lang = cfg.get("language", {})
    return {
        "max_nodes": int(lang.get("max_nodes", 24)),
        "max_call_depth": int(lang.get("max_call_depth", 4)),
        "repeat_range": lang.get("repeat_range", [1, 4]),
        "lookahead_depth": lang.get("lookahead_depth", [1, 3]),
        "lookahead_width": lang.get("lookahead_width", [1, 4]),
    }


def mine_trace(trace: list[dict], episode: int, provenance: str) -> list[tuple[Operation, str]]:
    actions = []
    for item in trace:
        if "type" in item and "x" in item:
            actions.append((item["type"], int(item["rotation"]), int(item["x"]), int(item["y"])))
    found: list[tuple[Operation, str]] = []
    n = len(actions)
    for length in (2, 3, 4):
        if n < length:
            continue
        # Mine the most recent windows only, not every historical window.
        start = max(0, n - length)
        window = actions[start : start + length]
        if len(window) != length:
            # also the latest aligned window of this length
            window = actions[n - length :]
        built = spatial_from_absolute(window)
        if built is None:
            continue
        ast, primitive = built
        op = make_operation(ast, primitive, [], "mine", provenance, episode)
        found.append((op, "mine"))
    # One older window of length 2 if the trace is long, still bounded.
    if n >= 6:
        window = actions[-6:-4]
        built = spatial_from_absolute(window)
        if built is not None:
            ast, primitive = built
            op = make_operation(ast, primitive, [], "mine", provenance, episode)
            found.append((op, "mine"))
    return found


def _cells_of(sequence: list[dict], ox: int, oy: int, k: int) -> list[tuple[int, int]] | None:
    cells: list[tuple[int, int]] = []
    for step in sequence:
        ax, ay, rot = anchor_after_rotation(
            step["type"], int(step["rotation"]), int(step["dx"]), int(step["dy"]), k, ox, oy
        )
        from mga2.pieces import placed_cells

        for c in placed_cells(step["type"], rot, ax, ay):
            cells.append((int(c[0]), int(c[1])))
    if len(cells) != len(set(cells)):
        return None
    return cells


def fits(sequence: list[dict], env: PackingEnv, ox: int, oy: int, k: int) -> bool:
    if not sequence:
        return False
    needed: dict[str, int] = {}
    for step in sequence:
        needed[step["type"]] = needed.get(step["type"], 0) + 1
    if not env.inventory.unlimited:
        for t, n in needed.items():
            if env.inventory.counts.get(t, 0) < n:
                return False
    cells = _cells_of(sequence, ox, oy, k)
    if cells is None:
        return False
    for x, y in cells:
        if not (0 <= x < env.size and 0 <= y < env.size):
            return False
        if env.cells[y][x] is not None:
            return False
    return True


def legal_origins(op: Operation, env: PackingEnv, ledger: BudgetLedger, max_trials: int) -> list[tuple[int, int, int]]:
    sequence = op.primitive_sequence
    origins: list[tuple[int, int, int]] = []
    trials = 0
    with ledger.tally("guard"):
        for k in range(4):
            for y in range(env.size):
                for x in range(env.size):
                    if ledger.charge_eval(1) <= 0:
                        return origins
                    trials += 1
                    if fits(sequence, env, x, y, k):
                        origins.append((x, y, k))
                    if max_trials and trials >= max_trials:
                        return origins
    return origins


def _sequence_from_op(op: Operation, library: dict[str, Operation]) -> list[dict] | None:
    if op.primitive_sequence:
        return op.primitive_sequence
    return expand_spatial(op.ast, library)


def compose(existing: list[Operation], rng, episode: int, hierarchical: bool, library: dict[str, Operation]) -> list[tuple[Operation, str]]:
    if len(existing) < 2:
        return []
    proposals = []
    attempts = min(4, len(existing) * (len(existing) - 1))
    for _ in range(attempts):
        a, b = rng.sample(existing, 2)
        seq_a = _sequence_from_op(a, library)
        seq_b = _sequence_from_op(b, library)
        if not seq_a or not seq_b:
            continue
        dx, dy = OFFSETS[rng.randrange(len(OFFSETS))]
        if hierarchical:
            ast = seq([call(a.op_id, 0, 0, 0), call(b.op_id, dx, dy, 0)])
            expanded = expand_spatial(ast, {**library, a.op_id: a, b.op_id: b})
            if expanded is None:
                continue
            primitive = expanded
            parents = [a.op_id, b.op_id]
        else:
            # Flat form is primitive-only. Children are provenance, not CALLs.
            shifted = []
            children = []
            for step in seq_a:
                children.append(place_rel(step["type"], step["rotation"], step["dx"], step["dy"]))
                shifted.append(dict(step))
            for step in seq_b:
                ndx, ndy = int(step["dx"]) + dx, int(step["dy"]) + dy
                children.append(place_rel(step["type"], step["rotation"], ndx, ndy))
                cells = []
                from mga2.ops import sequence_cells

                cells = sequence_cells(step["type"], step["rotation"], ndx, ndy)
                shifted.append(
                    {"type": step["type"], "rotation": step["rotation"], "dx": ndx, "dy": ndy, "cells": cells}
                )
            primitive = shifted
            ast = seq(children)
            parents = [a.op_id, b.op_id]
        occupied = []
        overlap = False
        seen = set()
        for step in primitive:
            for c in step["cells"]:
                tup = (c[0], c[1])
                if tup in seen:
                    overlap = True
                seen.add(tup)
                occupied.append(tup)
        if overlap or not occupied:
            continue
        if not is_connected(occupied):
            continue
        op = make_operation(ast, primitive, parents, "compose", "simulated", episode)
        proposals.append((op, "compose"))
    return proposals


def mutate(existing: list[Operation], rng, episode: int, allow_calls: bool) -> list[tuple[Operation, str]]:
    if not existing:
        return []
    base = existing[rng.randrange(len(existing))]
    ast = copy.deepcopy(base.ast)
    kind = ast.get("kind")
    if kind == "SEQ" and ast.get("children"):
        child = ast["children"][rng.randrange(len(ast["children"]))]
        if child.get("kind") == "PLACE_REL":
            which = rng.choice(["dx", "dy", "rotation"])
            if which == "rotation":
                child["rotation"] = (int(child["rotation"]) + rng.choice([-1, 1])) % 4
            else:
                child[which] = int(child[which]) + rng.choice([-1, 1])
        elif len(ast["children"]) >= 2 and rng.random() < 0.5:
            i, j = rng.sample(range(len(ast["children"])), 2)
            ast["children"][i], ast["children"][j] = ast["children"][j], ast["children"][i]
    elif kind == "CHOOSE":
        weights = dict(ast.get("weights") or zero_weights())
        feat = rng.choice(list(weights.keys()) or ["norm_area"])
        weights[feat] = float(weights.get(feat, 0.0)) + rng.choice([-0.1, 0.1])
        ast["weights"] = weights
    else:
        return []
    if (not allow_calls) and any(n.get("kind") == "CALL" for n in _walk(ast)):
        return []
    errors = validate_program(ast, {"max_nodes": 24, "max_call_depth": 4}, allow_calls=allow_calls)
    if errors:
        return []
    expanded = expand_spatial(ast, {})
    primitive = expanded or []
    if ast.get("kind") == "SEQ" and primitive:
        seen = set()
        for step in primitive:
            for c in step["cells"]:
                tup = (int(c[0]), int(c[1]))
                if tup in seen:
                    return []
                seen.add(tup)
    op = make_operation(ast, primitive, [base.op_id], "mutate", "simulated", episode)
    if op.op_id == base.op_id:
        return []
    return [(op, "mutate")]


def _walk(ast: dict):
    yield ast
    kind = ast.get("kind")
    if kind == "SEQ":
        for c in ast.get("children", []):
            yield from _walk(c)
    elif kind == "REPEAT":
        yield from _walk(ast["child"])
    elif kind == "IF":
        yield from _walk(ast["then"])
        yield from _walk(ast["else"])


def compress(trace: list[dict], library: dict[str, Operation], episode: int) -> list[tuple[Operation, str]]:
    """Replace a repeated spatial subsequence with CALL, hierarchical only."""
    actions = [(it["type"], int(it["rotation"]), int(it["x"]), int(it["y"])) for it in trace if "type" in it]
    proposals = []
    for op in library.values():
        seqs = op.primitive_sequence
        if len(seqs) < 2 or len(actions) < len(seqs):
            continue
        # Match the latest window only.
        window = actions[-len(seqs) :]
        built = spatial_from_absolute(window)
        if built is None:
            continue
        _ast, prim = built
        if [(p["type"], p["rotation"], p["dx"], p["dy"]) for p in prim] != [
            (p["type"], p["rotation"], p["dx"], p["dy"]) for p in seqs
        ]:
            continue
        ast = seq([call(op.op_id, 0, 0, 0)])
        parent = make_operation(ast, list(seqs), [op.op_id], "compress", "real", episode)
        proposals.append((parent, "compress"))
        break
    return proposals


def propose(
    stm: ShortTermMemory,
    ltm: LongTermMemory,
    config: dict,
    rng,
    mode: str,
    episode: int,
) -> list[tuple[Operation, str, str]]:
    """Return (operation, source, reject_reason). reject_reason empty if kept."""
    cap = int(config.get("discovery", {}).get("max_candidates", 8))
    raw: list[tuple[Operation, str]] = []
    raw.extend(mine_trace(stm.trace, episode, "real"))
    for sim in stm.sim_traces:
        raw.extend(mine_trace(sim, episode, "simulated"))
    existing = list(stm.candidates.values()) + list(ltm.ops.values())
    library = {op.op_id: op for op in existing}
    if mode == "hierarchical_library":
        raw.extend(compose(list(ltm.ops.values()), rng, episode, True, library))
        raw.extend(compress(stm.trace, {k: v for k, v in library.items() if k in ltm.ops}, episode))
        raw.extend(mutate(existing, rng, episode, allow_calls=True))
    elif mode == "flat_library":
        raw.extend(compose(existing, rng, episode, False, library))
        raw.extend(mutate(existing, rng, episode, allow_calls=False))
    rng.shuffle(raw)
    kept: list[tuple[Operation, str, str]] = []
    seen = set(ltm.ops)
    for op, source in raw:
        if op.op_id in seen:
            kept.append((op, source, "duplicate"))
            continue
        errors = validate_program(op.ast, _limits(config), known_ids=set(library), allow_calls=(mode == "hierarchical_library"))
        if "call_forbidden" in errors:
            kept.append((op, source, "call_forbidden"))
            continue
        if "nested_lookahead" in errors or "node_limit" in errors:
            kept.append((op, source, errors[0]))
            continue
        if mode == "flat_library" and any(n.get("kind") == "CALL" for n in _walk(op.ast)):
            kept.append((op, source, "call_forbidden"))
            continue
        seen.add(op.op_id)
        kept.append((op, source, ""))
        if sum(1 for item in kept if item[2] == "") >= cap:
            break
    return kept


def paired_validate(
    op: Operation,
    env: PackingEnv,
    ledger: BudgetLedger,
    rng,
    config: dict,
    library: dict[str, Operation],
) -> dict | None:
    """Compare the candidate with the primitive controller from the same state.

    Both branches are charged. The real environment is not modified.
    """
    weights = UtilityWeights.from_config(config)
    horizon = weights.horizon
    exam = int(config.get("exam_limit", 0))
    max_origins = int(config.get("discovery", {}).get("max_origin_trials", 64))
    remaining_eval = ledger.eval_limit() - ledger.candidate_evals
    remaining_model = ledger.model_limit() - ledger.model_transitions
    share_e = remaining_eval // 2
    share_m = remaining_model // 2
    if share_e <= 0 or share_m <= 0:
        return None
    mask_before = env.mask
    inv_before = env.inventory.as_dict()
    score_before = env.score

    def one_branch(use_op: bool, branch_rng) -> dict:
        prev = ledger.push_ceilings(share_e, share_m)
        model0 = ledger.model_transitions
        clone = env.clone()
        legal_op = True
        expanded = 0
        origin = None
        if use_op:
            origins = legal_origins(op, clone, ledger, max_origins)
            if not origins:
                legal_op = False
            else:
                origin = origins[branch_rng.randrange(len(origins))]
                interp = Interpreter(config, library)
                result = interp.execute(op.ast, clone, ledger, branch_rng, simulate=True, origin=origin)
                legal_op = bool(result.ok and result.expanded > 0)
                expanded = result.expanded
        steps_left = max(0, horizon - expanded)
        roll = primitive_rollout(clone, ledger, branch_rng, steps_left, exam)
        out = {
            "delta_filled": clone.score - score_before,
            "physical": clone.actions_used - env.actions_used,
            "model": ledger.model_transitions - model0,
            "legal_op": legal_op,
            "expanded": expanded,
            "origin": origin,
            "roll_delta": roll["delta_filled"],
        }
        ledger.pop_ceilings(prev)
        return out

    # Identical starting RNG state for the two branches.
    state = rng.getstate()
    with ledger.tally("paired"):
        cand = one_branch(True, rng)
        rng.setstate(state)
        base = one_branch(False, rng)
    if env.mask != mask_before or env.score != score_before or env.inventory.as_dict() != inv_before:
        raise RuntimeError("paired validation mutated the real environment")
    uc = utility(cand["delta_filled"], cand["physical"], cand["model"], weights)
    up = utility(base["delta_filled"], base["physical"], base["model"], weights)
    return {
        "U": uc - up,
        "U_candidate": uc,
        "U_primitive": up,
        "candidate": cand,
        "primitive": base,
        "legal": cand["legal_op"],
        "delta_filled": cand["delta_filled"] - base["delta_filled"],
        "physical_actions": cand["physical"] + base["physical"],
        "model_transitions": cand["model"] + base["model"],
    }


def observational_utility(delta_filled: int, physical: int, model: int, config: dict) -> float:
    return utility(delta_filled, physical, model, UtilityWeights.from_config(config))


def area_of(op: Operation) -> int:
    return sum(piece_area(step["type"]) for step in op.primitive_sequence)
