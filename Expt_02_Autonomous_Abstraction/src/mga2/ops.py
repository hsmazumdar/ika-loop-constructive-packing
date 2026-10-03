"""Typed, serializable operation language. Programs are data, never eval'd Python."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from mga2.pieces import PIECE_TYPES, is_connected, piece_area

KIND_SET = {"PLACE_REL", "SEQ", "CALL", "CHOOSE", "REPEAT", "IF", "LOOKAHEAD"}
COMPARISONS = {"<", "<=", ">", ">=", "=="}


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_bytes(obj: Any) -> int:
    return len(canonical_dumps(obj).encode("utf-8"))


def place_rel(piece_type: str, rotation: int, dx: int, dy: int) -> dict:
    return {
        "kind": "PLACE_REL",
        "type": piece_type,
        "rotation": int(rotation) % 4,
        "dx": int(dx),
        "dy": int(dy),
    }


def seq(children: list[dict]) -> dict:
    return {"kind": "SEQ", "children": list(children)}


def call(op_id: str, dx: int = 0, dy: int = 0, rotation: int = 0) -> dict:
    return {"kind": "CALL", "id": op_id, "dx": int(dx), "dy": int(dy), "rotation": int(rotation) % 4}


def choose(weights: dict[str, float]) -> dict:
    return {"kind": "CHOOSE", "weights": {k: float(v) for k, v in sorted(weights.items())}}


def repeat(k: int, child: dict) -> dict:
    return {"kind": "REPEAT", "k": int(k), "child": child}


def if_node(feature: str, comparison: str, threshold: float, then_child: dict, else_child: dict) -> dict:
    return {
        "kind": "IF",
        "feature": feature,
        "comparison": comparison,
        "threshold": float(threshold),
        "then": then_child,
        "else": else_child,
    }


def lookahead(depth: int, width: int, selector: str = "weights") -> dict:
    return {"kind": "LOOKAHEAD", "depth": int(depth), "width": int(width), "selector": selector}


def node_count(ast: dict) -> int:
    kind = ast.get("kind")
    if kind == "SEQ":
        return 1 + sum(node_count(c) for c in ast.get("children", []))
    if kind in {"REPEAT"}:
        return 1 + node_count(ast["child"])
    if kind == "IF":
        return 1 + node_count(ast["then"]) + node_count(ast["else"])
    return 1


def call_ids(ast: dict) -> list[str]:
    found: list[str] = []
    kind = ast.get("kind")
    if kind == "CALL":
        found.append(ast["id"])
    elif kind == "SEQ":
        for c in ast.get("children", []):
            found.extend(call_ids(c))
    elif kind == "REPEAT":
        found.extend(call_ids(ast["child"]))
    elif kind == "IF":
        found.extend(call_ids(ast["then"]))
        found.extend(call_ids(ast["else"]))
    return found


def contains_lookahead(ast: dict) -> bool:
    if ast.get("kind") == "LOOKAHEAD":
        return True
    if ast.get("kind") == "SEQ":
        return any(contains_lookahead(c) for c in ast.get("children", []))
    if ast.get("kind") == "REPEAT":
        return contains_lookahead(ast["child"])
    if ast.get("kind") == "IF":
        return contains_lookahead(ast["then"]) or contains_lookahead(ast["else"])
    return False


def lookahead_nested(ast: dict, inside: bool = False) -> bool:
    kind = ast.get("kind")
    if kind == "LOOKAHEAD":
        if inside:
            return True
        inside = True
    kids = []
    if kind == "SEQ":
        kids = list(ast.get("children", []))
    elif kind == "REPEAT":
        kids = [ast["child"]]
    elif kind == "IF":
        kids = [ast["then"], ast["else"]]
    return any(lookahead_nested(c, inside) for c in kids)


def structural_hash(ast: dict) -> str:
    return hashlib.sha256(canonical_dumps(ast).encode("utf-8")).hexdigest()[:16]


def rotate_offset(dx: int, dy: int, k: int) -> tuple[int, int]:
    """Clockwise screen rotation, matching piece rotation (x, y) -> (-y, x)."""
    x, y = int(dx), int(dy)
    for _ in range(int(k) % 4):
        x, y = -y, x
    return x, y


def effective_depth(ast: dict) -> int:
    """Depth after dropping single-child SEQ aliases. PLACE_REL is depth 0."""
    kind = ast.get("kind")
    if kind == "PLACE_REL" or kind == "CHOOSE" or kind == "LOOKAHEAD":
        return 1 if kind != "PLACE_REL" else 0
    if kind == "CALL":
        return 1
    if kind == "REPEAT":
        return effective_depth(ast["child"])
    if kind == "IF":
        return 1 + max(effective_depth(ast["then"]), effective_depth(ast["else"]))
    if kind == "SEQ":
        kids = list(ast.get("children", []))
        if len(kids) == 1:
            return effective_depth(kids[0])
        if not kids:
            return 0
        return 1 + max(effective_depth(c) for c in kids)
    return 0


def validate_program(ast: dict, limits: dict, known_ids: set[str] | None = None, allow_calls: bool = True) -> list[str]:
    errors: list[str] = []
    if node_count(ast) > int(limits.get("max_nodes", 24)):
        errors.append("node_limit")
    if lookahead_nested(ast):
        errors.append("nested_lookahead")
    _walk_validate(ast, limits, known_ids, allow_calls, errors, depth=0)
    return errors


def _walk_validate(ast, limits, known_ids, allow_calls, errors, depth: int) -> None:
    kind = ast.get("kind")
    if kind not in KIND_SET:
        errors.append("bad_kind")
        return
    if depth > int(limits.get("max_call_depth", 4)):
        errors.append("call_depth")
        return
    if kind == "PLACE_REL":
        if ast.get("type") not in PIECE_TYPES:
            errors.append("bad_type")
        rot = ast.get("rotation", 0)
        if not isinstance(rot, int) or rot < 0 or rot > 3:
            errors.append("bad_rotation")
    elif kind == "SEQ":
        for c in ast.get("children", []):
            _walk_validate(c, limits, known_ids, allow_calls, errors, depth)
    elif kind == "CALL":
        if not allow_calls:
            errors.append("call_forbidden")
        if known_ids is not None and ast.get("id") not in known_ids:
            errors.append("dangling_id")
        if depth + 1 > int(limits.get("max_call_depth", 4)):
            errors.append("call_depth")
    elif kind == "REPEAT":
        k = int(ast.get("k", 0))
        lo, hi = limits.get("repeat_range", [1, 4])
        if k < int(lo) or k > int(hi):
            errors.append("repeat_range")
        _walk_validate(ast["child"], limits, known_ids, allow_calls, errors, depth)
    elif kind == "IF":
        if ast.get("comparison") not in COMPARISONS:
            errors.append("bad_comparison")
        _walk_validate(ast["then"], limits, known_ids, allow_calls, errors, depth)
        _walk_validate(ast["else"], limits, known_ids, allow_calls, errors, depth)
    elif kind == "LOOKAHEAD":
        dlo, dhi = limits.get("lookahead_depth", [1, 3])
        wlo, whi = limits.get("lookahead_width", [1, 4])
        if not (int(dlo) <= int(ast.get("depth", 0)) <= int(dhi)):
            errors.append("lookahead_depth")
        if not (int(wlo) <= int(ast.get("width", 0)) <= int(whi)):
            errors.append("lookahead_width")


def fresh_stats() -> dict[str, Any]:
    return {
        "support": 0,
        "successes": 0,
        "failures": 0,
        "real_uses": 0,
        "sim_uses": 0,
        "real_task_ids": [],
        "origins": [],
        "utility_sum": 0.0,
        "utility_sq_sum": 0.0,
        "paired_utility_sum": 0.0,
        "physical_cost_sum": 0,
        "model_cost_sum": 0,
        "use_count": 0,
        "boxes_since_benefit": 0,
        "last_utility": 0.0,
        "eviction_reason": None,
    }


def mean_utility(stats: dict) -> float:
    n = int(stats.get("support", 0))
    if n <= 0:
        return 0.0
    return float(stats.get("utility_sum", 0.0)) / n


def utility_uncertainty(stats: dict) -> float:
    n = int(stats.get("support", 0))
    if n <= 1:
        return 1.0
    mean = mean_utility(stats)
    second = float(stats.get("utility_sq_sum", 0.0)) / n
    var = max(0.0, second - mean * mean)
    return var ** 0.5


class Operation:
    """Immutable AST plus mutable performance context."""

    def __init__(
        self,
        op_id: str,
        ast: dict,
        parents: list[str],
        source: str,
        provenance: str,
        created_episode: int,
        primitive_sequence: list[dict],
        status: str = "candidate",
    ) -> None:
        self.op_id = op_id
        self.ast = ast
        self.parents = list(parents)
        self.source = source
        self.provenance = provenance
        self.created_episode = int(created_episode)
        self.primitive_sequence = list(primitive_sequence)
        self.status = status
        self.stats = fresh_stats()
        self.confirmation_scope = ""
        self.depth = effective_depth(ast)
        inv: dict[str, int] = {}
        cells: list[tuple[int, int]] = []
        for step in primitive_sequence:
            inv[step["type"]] = inv.get(step["type"], 0) + 1
            for cx, cy in step.get("cells", []):
                cells.append((int(cx), int(cy)))
        self.inventory_counts = inv
        self.footprint = [list(c) for c in cells]
        self.guards = {
            "inventory": dict(inv),
            "footprint": self.footprint,
            "connected": bool(cells) and is_connected(cells),
        }

    def record_utility(self, value: float, real: bool, task_id: str | None, origin: tuple | None, success: bool) -> None:
        self.stats["last_utility"] = float(value)
        if real:
            self.stats["support"] += 1
            self.stats["utility_sum"] += float(value)
            self.stats["utility_sq_sum"] += float(value) * float(value)
            self.stats["real_uses"] += 1
            self.stats["use_count"] += 1
            if task_id and task_id not in self.stats["real_task_ids"]:
                self.stats["real_task_ids"].append(task_id)
            if origin is not None:
                key = [int(origin[0]), int(origin[1]), int(origin[2]) if len(origin) > 2 else 0]
                if key not in self.stats["origins"]:
                    self.stats["origins"].append(key)
            if success and value > 0:
                self.stats["successes"] += 1
                self.stats["boxes_since_benefit"] = 0
            else:
                self.stats["failures"] += 1
        else:
            self.stats["sim_uses"] += 1
            self.stats["paired_utility_sum"] += float(value)

    def storage_dict(self) -> dict:
        return {
            "op_id": self.op_id,
            "parents": list(self.parents),
            "ast": self.ast,
            "source": self.source,
            "provenance": self.provenance,
            "created_episode": self.created_episode,
            "primitive_sequence": self.primitive_sequence,
            "inventory_counts": self.inventory_counts,
            "footprint": self.footprint,
            "guards": self.guards,
            "stats": self.stats,
            "status": self.status,
            "confirmation_scope": self.confirmation_scope,
            "depth": self.depth,
            "structural_hash": structural_hash(self.ast),
        }

    def logical_bytes(self) -> int:
        return canonical_bytes(self.storage_dict())

    @staticmethod
    def from_dict(data: dict) -> "Operation":
        op = Operation(
            op_id=data["op_id"],
            ast=data["ast"],
            parents=list(data.get("parents", [])),
            source=data.get("source", ""),
            provenance=data.get("provenance", ""),
            created_episode=int(data.get("created_episode", 0)),
            primitive_sequence=list(data.get("primitive_sequence", [])),
            status=data.get("status", "candidate"),
        )
        op.stats = dict(data.get("stats", fresh_stats()))
        op.confirmation_scope = data.get("confirmation_scope", "")
        return op


def sequence_cells(piece_type: str, rotation: int, dx: int, dy: int) -> list[list[int]]:
    from mga2.pieces import placed_cells as pc

    cells = pc(piece_type, rotation, dx, dy)
    return [[int(c[0]), int(c[1])] for c in cells]


def anchor_after_rotation(
    piece_type: str, rotation: int, dx: int, dy: int, k: int, ox: int, oy: int
) -> tuple[int, int, int]:
    """Map a relative piece anchor through a clockwise frame rotation.

    Piece anchors are min-corners of the normalized orientation, so the anchor
    shifts by the min corner of the rotated local cells.
    """
    from mga2.pieces import PIECES, orientation

    base = orientation(PIECES[piece_type], rotation)
    rotated = [rotate_offset(x, y, k) for x, y in base]
    minx = min(p[0] for p in rotated)
    miny = min(p[1] for p in rotated)
    rdx, rdy = rotate_offset(dx, dy, k)
    return ox + rdx + minx, oy + rdy + miny, (int(rotation) + int(k)) % 4


def spatial_from_absolute(actions: list[tuple[str, int, int, int]]) -> tuple[dict, list[dict]] | None:
    """Normalize a window relative to the first placement. Order is preserved.

    Translations of the same sequence share an AST. Rotations and reflections
    stay distinct. Overlaps are rejected.
    """
    if len(actions) < 2:
        return None
    x0, y0 = int(actions[0][2]), int(actions[0][3])
    primitive: list[dict] = []
    occupied: set[tuple[int, int]] = set()
    children = []
    for ptype, rot, x, y in actions:
        dx, dy = int(x) - x0, int(y) - y0
        cells = sequence_cells(ptype, int(rot) % 4, dx, dy)
        for c in cells:
            tup = (c[0], c[1])
            if tup in occupied:
                return None
            occupied.add(tup)
        primitive.append(
            {"type": ptype, "rotation": int(rot) % 4, "dx": dx, "dy": dy, "cells": cells}
        )
        children.append(place_rel(ptype, int(rot) % 4, dx, dy))
    return seq(children), primitive


def make_operation(
    ast: dict,
    primitive_sequence: list[dict],
    parents: list[str],
    source: str,
    provenance: str,
    created_episode: int,
) -> Operation:
    op_id = "op_" + structural_hash(ast)
    return Operation(
        op_id=op_id,
        ast=ast,
        parents=parents,
        source=source,
        provenance=provenance,
        created_episode=created_episode,
        primitive_sequence=primitive_sequence,
        status="candidate",
    )


def expand_spatial(ast: dict, library: dict[str, Operation], depth: int = 0) -> list[dict] | None:
    """Expand CALL/SEQ/PLACE_REL into relative placements. None if not purely spatial."""
    if depth > 4:
        return None
    kind = ast.get("kind")
    if kind == "PLACE_REL":
        cells = sequence_cells(ast["type"], ast["rotation"], ast["dx"], ast["dy"])
        return [
            {
                "type": ast["type"],
                "rotation": int(ast["rotation"]) % 4,
                "dx": int(ast["dx"]),
                "dy": int(ast["dy"]),
                "cells": cells,
            }
        ]
    if kind == "SEQ":
        out: list[dict] = []
        for c in ast.get("children", []):
            part = expand_spatial(c, library, depth)
            if part is None:
                return None
            out.extend(part)
        return out
    if kind == "CALL":
        child = library.get(ast["id"])
        if child is None:
            return None
        inner = expand_spatial(child.ast, library, depth + 1)
        if inner is None:
            return None
        k = int(ast.get("rotation", 0)) % 4
        dx0, dy0 = int(ast.get("dx", 0)), int(ast.get("dy", 0))
        shifted = []
        for step in inner:
            ax, ay, rot = anchor_after_rotation(
                step["type"], int(step["rotation"]), int(step["dx"]), int(step["dy"]), k, dx0, dy0
            )
            cells = sequence_cells(step["type"], rot, ax, ay)
            shifted.append(
                {"type": step["type"], "rotation": rot, "dx": ax, "dy": ay, "cells": cells}
            )
        return shifted
    return None


def footprint_area(sequence: list[dict]) -> int:
    return sum(piece_area(step["type"]) for step in sequence)


def has_call_cycle(op_id: str, ast: dict, library: dict[str, Operation], stack: list[str] | None = None) -> bool:
    stack = list(stack or [])
    if op_id in stack:
        return True
    stack.append(op_id)
    for cid in call_ids(ast):
        if cid in stack:
            return True
        child = library.get(cid)
        if child is not None and has_call_cycle(cid, child.ast, library, stack):
            return True
    return False
