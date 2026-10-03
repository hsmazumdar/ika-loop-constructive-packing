"""Mine recurring subsequences. Promotion policy is applied elsewhere.

A 4-connected footprint is required so one decision is one coherent action.
That is a documented prior, not a rectangle preference.
"""

from __future__ import annotations

import json
import random

from pieces import is_connected

from memory import Episode, LearnedOperation, OperationMemory


def _rot_point(x: int, y: int, k: int) -> tuple[int, int]:
    for _ in range(k % 4):
        x, y = -y, x
    return x, y


def rotate_steps(steps: list[dict], k: int) -> list[dict]:
    rotated = []
    for step in steps:
        rotated.append({"type": step["type"], "cells": [_rot_point(int(x), int(y), k) for x, y in step["cells"]]})
    flat = [c for step in rotated for c in step["cells"]]
    min_x = min(x for x, _ in flat)
    min_y = min(y for _, y in flat)
    out = []
    for step in rotated:
        cells = tuple(sorted((x - min_x, y - min_y) for x, y in step["cells"]))
        out.append({"type": step["type"], "cells": cells})
    return out


def steps_from_absolute(placements: list[dict]) -> list[dict]:
    flat = [tuple(c) for p in placements for c in p["cells"]]
    min_x = min(x for x, _ in flat)
    min_y = min(y for _, y in flat)
    steps = []
    for p in placements:
        cells = tuple(sorted((int(x) - min_x, int(y) - min_y) for x, y in p["cells"]))
        steps.append({"type": p["type"], "cells": cells})
    return steps


def canonical_form(steps: list[dict]) -> tuple[list[dict], str]:
    best: str | None = None
    best_steps: list[dict] | None = None
    for k in range(4):
        turned = rotate_steps(steps, k)
        payload = json.dumps(turned, separators=(",", ":"))
        if best is None or payload < best:
            best = payload
            best_steps = turned
    assert best is not None and best_steps is not None
    return best_steps, best


def connected_steps(steps: list[dict]) -> bool:
    cells = [tuple(c) for step in steps for c in step["cells"]]
    if len(cells) != len(set(cells)):
        return False
    return is_connected(cells)


def nbytes_of(steps: list[dict], children: list[str]) -> int:
    payload = {"children": children, "steps": [{"type": s["type"], "cells": [list(c) for c in s["cells"]]} for s in steps]}
    return len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def expand_primitives(op: LearnedOperation) -> list[dict]:
    return [{"type": step["type"], "cells": tuple(step["cells"])} for step in op.steps]


class AbstractionMiner:
    def __init__(self, config, memory: OperationMemory) -> None:
        self.config = config
        self.memory = memory
        self.support: dict[str, set[int]] = {}
        self.pending: dict[str, dict] = {}

    def observe(self, episode: Episode) -> list[LearnedOperation]:
        if not episode.acceptable:
            return []
        self.memory.remember_episode(episode)
        found: list[LearnedOperation] = []
        decisions = episode.decisions
        for length in range(self.config.min_len, self.config.max_len + 1):
            if len(found) >= self.config.max_promotions_per_episode:
                break
            for start in range(0, len(decisions) - length + 1):
                if len(found) >= self.config.max_promotions_per_episode:
                    break
                created = self._consider(decisions[start : start + length], episode)
                if created is not None:
                    found.append(created)
        return found

    def _consider(self, window: list[dict], episode: Episode) -> LearnedOperation | None:
        child_depths = [int(item["depth"]) for item in window]
        if not self.memory.hierarchical and (not child_depths or max(child_depths) >= 1):
            return None
        depth = 1 + max(child_depths)
        if depth > self.config.max_depth:
            return None
        placements = [p for item in window for p in item["placements"]]
        if len(placements) < 2:
            return None
        if not connected_steps(steps_from_absolute(placements)):
            return None
        steps, geometry = canonical_form(steps_from_absolute(placements))
        children = [item["op_id"] for item in window]
        key = json.dumps({"children": children, "geometry": geometry}, separators=(",", ":"))
        self.support.setdefault(key, set()).add(episode.episode_id)
        if key not in self.pending:
            self.pending[key] = {
                "steps": steps,
                "children": children,
                "depth": depth,
                "features": list(window[0]["features"]),
            }
        if len(self.support[key]) < self.config.min_support:
            return None
        if self.memory.contains_canonical(key):
            return None
        slot = self.pending[key]
        op = LearnedOperation(
            op_id=self.memory.next_name(),
            depth=depth,
            children=list(slot["children"]),
            steps=[{"type": s["type"], "cells": tuple(s["cells"])} for s in slot["steps"]],
            nbytes=nbytes_of(slot["steps"], slot["children"]),
            canonical=key,
            context=list(slot["features"]),
            created_at=episode.episode_id,
            last_used=episode.episode_id,
            status="provisional",
        )
        op.ensure_rule(len(op.context), self.config.applicability_min)
        if self.memory.add_operation(op, episode.episode_id):
            return op
        return None
