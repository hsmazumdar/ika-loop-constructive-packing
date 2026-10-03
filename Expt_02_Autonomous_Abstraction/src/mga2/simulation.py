"""Exact internal clone of the physical transition rules.

Rollouts mutate only the clone. They never touch the real board, inventory,
score, or the environment's decision RNG. Computation is still charged.
"""

from __future__ import annotations

from mga2.budgets import BudgetLedger
from mga2.environment import Action, PackingEnv
from mga2.features import board_features, candidate_features, dot, zero_weights
from mga2.pieces import ALL_PLACEMENTS, P_MASKS, P_TYPES


def clone_env(env: PackingEnv) -> PackingEnv:
    return env.clone()


def _legal(env: PackingEnv, ledger: BudgetLedger, exam_limit: int) -> list[int]:
    legal: list[int] = []
    occ = env.mask
    for i, pmask in enumerate(P_MASKS):
        if ledger.charge_eval(1) <= 0:
            break
        if pmask & occ:
            continue
        if not env.inventory.can_take(P_TYPES[i]):
            continue
        legal.append(i)
        if exam_limit and len(legal) >= exam_limit:
            break
    return legal


def lookahead_first_action(
    env: PackingEnv,
    ledger: BudgetLedger,
    rng,
    depth: int,
    width: int,
    weights: dict | None,
    exam_limit: int,
    simulate_parent: bool = False,
) -> Action | None:
    """Search on clones and return one action. ``env`` is not modified."""
    weights = weights or zero_weights()
    with ledger.tally("lookahead"):
        with ledger.tally("selection"):
            root = env.clone()
            path, _score = _beam(root, ledger, rng, depth, width, weights, exam_limit, [])
    if not path:
        return None
    return path[0]


def _beam(env, ledger, rng, depth, width, weights, exam_limit, path: list[Action]) -> tuple[list[Action], int]:
    if depth <= 0 or env.terminal or not ledger.can_simulate() or not ledger.can_eval():
        return path, env.score
    legal = _legal(env, ledger, exam_limit)
    if not legal:
        return path, env.score
    board = board_features(env, ledger, len(legal))
    scored = []
    for idx in legal:
        feats = candidate_features(env, idx, board)
        scored.append((dot(weights, feats), idx))
    nonzero = any(abs(float(v)) > 0 for v in weights.values())
    if not nonzero:
        rng.shuffle(scored)
        chosen = scored[: max(1, width)]
    else:
        scored.sort(key=lambda item: (-item[0], item[1]))
        chosen = scored[: max(1, width)]
    best_path = path
    best_score = env.score
    for _score, idx in chosen:
        if ledger.charge_model(1) <= 0:
            break
        action = Action.place_from(ALL_PLACEMENTS[idx])
        branch = env.clone()
        step = branch.step(action)
        if not step.accepted:
            continue
        child_path, child_score = _beam(
            branch, ledger, rng, depth - 1, width, weights, exam_limit, path + [action]
        )
        if child_score > best_score or (child_score == best_score and len(child_path) > len(best_path)):
            best_score = child_score
            best_path = child_path
    return best_path, best_score


def primitive_rollout(env: PackingEnv, ledger: BudgetLedger, rng, horizon: int, exam_limit: int) -> dict:
    """Continue a clone with the neutral primitive controller. ``env`` is the clone."""
    start_score = env.score
    start_actions = env.actions_used
    start_model = ledger.model_transitions
    steps = 0
    while steps < horizon and not env.terminal and ledger.can_eval() and ledger.can_simulate():
        legal = _legal(env, ledger, exam_limit)
        if not legal:
            break
        if ledger.charge_model(1) <= 0:
            break
        pick = legal[rng.randrange(len(legal))]
        env.step(Action.place_from(ALL_PLACEMENTS[pick]))
        steps += 1
    return {
        "delta_filled": env.score - start_score,
        "physical": env.actions_used - start_actions,
        "model": ledger.model_transitions - start_model,
        "score": env.score,
    }
