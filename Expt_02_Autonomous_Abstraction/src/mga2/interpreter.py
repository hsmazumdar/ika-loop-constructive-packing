"""Bounded interpreter for the designer-supplied AST language."""

from __future__ import annotations

from dataclasses import dataclass, field

from mga2.budgets import BudgetLedger
from mga2.environment import Action, PackingEnv
from mga2.features import FEATURE_NAMES, board_features, candidate_features, dot, zero_weights
from mga2.ops import Operation, anchor_after_rotation, rotate_offset
from mga2.pieces import ALL_PLACEMENTS


@dataclass
class ExecResult:
    ok: bool
    reason: str
    expanded: int = 0
    nodes: int = 0
    actions: list[dict] = field(default_factory=list)
    proposal: dict | None = None


def _limits(cfg: dict) -> dict:
    lang = cfg.get("language", {})
    return {
        "max_nodes": int(lang.get("max_nodes", 24)),
        "max_expanded": int(lang.get("max_expanded", 12)),
        "max_call_depth": int(lang.get("max_call_depth", 4)),
    }


def _compare(value: float, op: str, threshold: float) -> bool:
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "==":
        return value == threshold
    return False


class Interpreter:
    def __init__(self, config: dict, library: dict[str, Operation]) -> None:
        self.config = config
        self.library = library
        self.limits = _limits(config)
        self.exam_limit = int(config.get("exam_limit", 0))

    def execute(
        self,
        ast: dict,
        env: PackingEnv,
        ledger: BudgetLedger,
        rng,
        simulate: bool,
        origin: tuple[int, int, int] = (0, 0, 0),
        in_lookahead: bool = False,
    ) -> ExecResult:
        ctx = {
            "ox": int(origin[0]),
            "oy": int(origin[1]),
            "rot": int(origin[2]) % 4,
            "depth": 0,
            "expanded": 0,
            "nodes": 0,
            "in_lookahead": in_lookahead,
            "simulate": simulate,
        }
        result = ExecResult(ok=True, reason="ok")
        self._exec(ast, env, ledger, rng, ctx, result)
        result.expanded = ctx["expanded"]
        result.nodes = ctx["nodes"]
        if ctx["nodes"] > self.limits["max_nodes"]:
            result.ok = False
            result.reason = "node_limit"
        return result

    def _exec(self, ast, env, ledger, rng, ctx, result: ExecResult) -> None:
        if not result.ok or env.terminal:
            if env.terminal and result.ok:
                result.ok = False
                result.reason = "terminal"
            return
        ctx["nodes"] += 1
        if ctx["nodes"] > self.limits["max_nodes"]:
            result.ok = False
            result.reason = "node_limit"
            return
        kind = ast.get("kind")
        if kind == "PLACE_REL":
            self._place_rel(ast, env, ledger, ctx, result)
        elif kind == "SEQ":
            for child in ast.get("children", []):
                if not result.ok or env.terminal:
                    break
                self._exec(child, env, ledger, rng, ctx, result)
        elif kind == "CALL":
            self._call(ast, env, ledger, rng, ctx, result)
        elif kind == "REPEAT":
            k = int(ast.get("k", 1))
            for _ in range(k):
                if not result.ok or env.terminal:
                    break
                before = env.actions_used
                self._exec(ast["child"], env, ledger, rng, ctx, result)
                if env.actions_used == before:
                    break
        elif kind == "IF":
            feats = self._quick_feats(env, ledger)
            value = float(feats.get(ast.get("feature", ""), 0.0))
            branch = ast["then"] if _compare(value, ast.get("comparison", "=="), float(ast.get("threshold", 0))) else ast["else"]
            self._exec(branch, env, ledger, rng, ctx, result)
        elif kind == "CHOOSE":
            self._choose(ast, env, ledger, rng, ctx, result)
        elif kind == "LOOKAHEAD":
            if ctx["in_lookahead"]:
                result.ok = False
                result.reason = "nested_lookahead"
                return
            self._lookahead(ast, env, ledger, rng, ctx, result)
        else:
            result.ok = False
            result.reason = "bad_kind"

    def _place_rel(self, ast, env, ledger, ctx, result: ExecResult) -> None:
        if ctx["expanded"] >= self.limits["max_expanded"]:
            result.ok = False
            result.reason = "expansion_limit"
            return
        x, y, rot = anchor_after_rotation(
            ast["type"], int(ast["rotation"]), int(ast["dx"]), int(ast["dy"]), ctx["rot"], ctx["ox"], ctx["oy"]
        )
        action = Action.place(ast["type"], rot, x, y)
        self._apply(action, env, ledger, ctx, result)

    def _apply(self, action: Action, env, ledger, ctx, result: ExecResult) -> None:
        if ctx["simulate"]:
            if ledger.charge_model(1) <= 0:
                result.ok = False
                result.reason = "compute_budget"
                return
        step = env.step(action)
        if not ctx["simulate"]:
            ledger.physical = env.actions_used
        ctx["expanded"] += 1
        result.actions.append(action.as_dict())
        if not step.accepted:
            result.ok = False
            result.reason = step.reason

    def _call(self, ast, env, ledger, rng, ctx, result: ExecResult) -> None:
        if ctx["depth"] >= self.limits["max_call_depth"]:
            result.ok = False
            result.reason = "call_depth"
            return
        op = self.library.get(ast.get("id"))
        if op is None:
            result.ok = False
            result.reason = "dangling_id"
            return
        saved = (ctx["ox"], ctx["oy"], ctx["rot"], ctx["depth"])
        sx, sy = rotate_offset(int(ast.get("dx", 0)), int(ast.get("dy", 0)), ctx["rot"])
        ctx["ox"] = ctx["ox"] + sx
        ctx["oy"] = ctx["oy"] + sy
        ctx["rot"] = (ctx["rot"] + int(ast.get("rotation", 0))) % 4
        ctx["depth"] = ctx["depth"] + 1
        self._exec(op.ast, env, ledger, rng, ctx, result)
        ctx["ox"], ctx["oy"], ctx["rot"], ctx["depth"] = saved

    def _quick_feats(self, env, ledger) -> dict[str, float]:
        return board_features(env, ledger, candidate_count=0)

    def _choose(self, ast, env, ledger, rng, ctx, result: ExecResult) -> None:
        weights = ast.get("weights") or zero_weights()
        legal = self._legal(env, ledger)
        if not legal:
            result.ok = False
            result.reason = "no_legal" if ledger.can_eval() else "compute_budget"
            return
        board = board_features(env, ledger, len(legal))
        scored = []
        for idx in legal:
            feats = candidate_features(env, idx, board)
            scored.append((dot(weights, feats), idx))
        if not scored:
            result.ok = False
            result.reason = "compute_budget"
            return
        best = max(s for s, _ in scored)
        tied = [i for s, i in scored if s == best]
        pick = tied[rng.randrange(len(tied))]
        placement = ALL_PLACEMENTS[pick]
        action = Action.place_from(placement)
        result.proposal = action.as_dict()
        if ctx["expanded"] >= self.limits["max_expanded"]:
            result.ok = False
            result.reason = "expansion_limit"
            return
        self._apply(action, env, ledger, ctx, result)

    def _legal(self, env: PackingEnv, ledger: BudgetLedger) -> list[int]:
        from mga2.pieces import P_MASKS, P_TYPES

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
            if self.exam_limit and len(legal) >= self.exam_limit:
                break
        return legal

    def _lookahead(self, ast, env, ledger, rng, ctx, result: ExecResult) -> None:
        from mga2.simulation import lookahead_first_action

        depth = int(ast.get("depth", 1))
        width = int(ast.get("width", 1))
        weights = zero_weights()
        action = lookahead_first_action(
            env, ledger, rng, depth, width, weights, self.exam_limit, simulate_parent=ctx["simulate"]
        )
        if action is None:
            result.ok = False
            result.reason = "lookahead_empty"
            return
        result.proposal = action.as_dict()
        if ctx["expanded"] >= self.limits["max_expanded"]:
            result.ok = False
            result.reason = "expansion_limit"
            return
        self._apply(action, env, ledger, ctx, result)


def select_primitive(env: PackingEnv, ledger: BudgetLedger, rng, exam_limit: int) -> Action | None:
    """Neutral primitive: uniform among examined legal placements. No undo tabu."""
    from mga2.pieces import P_MASKS, P_TYPES

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
    if not legal:
        return None
    pick = legal[rng.randrange(len(legal))]
    return Action.place_from(ALL_PLACEMENTS[pick])
