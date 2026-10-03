"""Mine recurring action subsequences and promote them to executable operations.

Promotion uses support, reuse, and estimated attempt savings. It does not
score rectangles, corners, rows, or piece size. A candidate must be a
4-connected footprint so that one decision is one spatially coherent action.
That contiguity check is a documented prior, not a shape preference.
"""

from __future__ import annotations

import json
import random

from pieces import PIECES, is_connected, orientation

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
    """Primitive placements stored on the operation, in execution order."""
    return [{"type": step["type"], "cells": tuple(step["cells"])} for step in op.steps]


class AbstractionMiner:
    def __init__(self, config, memory: OperationMemory, control: bool = False) -> None:
        self.config = config
        self.memory = memory
        self.control = control
        self.support: dict[str, set[int]] = {}
        self.pending: dict[str, dict] = {}

    def observe(self, episode: Episode, rng: random.Random) -> list[str]:
        if not episode.acceptable:
            return []
        self.memory.remember_episode(episode)
        promoted: list[str] = []
        decisions = episode.decisions
        for length in range(self.config.min_len, self.config.max_len + 1):
            if len(promoted) >= self.config.max_promotions_per_episode:
                break
            for start in range(0, len(decisions) - length + 1):
                if len(promoted) >= self.config.max_promotions_per_episode:
                    break
                window = decisions[start : start + length]
                created = self._consider(window, episode, rng)
                if created:
                    promoted.append(created)
        self.memory.age(episode.episode_id)
        self.memory.enforce_pressure(episode.episode_id)
        return promoted

    def _consider(self, window: list[dict], episode: Episode, rng: random.Random) -> str | None:
        child_depths = [int(item["depth"]) for item in window]
        if not self.memory.hierarchical and max(child_depths) >= 1:
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
        slot = self.pending.get(key)
        if slot is None:
            slot = {"steps": steps, "children": children, "depth": depth, "features": list(window[0]["features"])}
            self.pending[key] = slot
        if len(self.support[key]) < self.config.min_support:
            return None
        if self.memory.contains_canonical(key):
            return None
        stored_steps = steps
        stored_children = children
        stored_key = key
        if self.control:
            replacement = _random_sequence(len(placements), rng)
            if replacement is None or not connected_steps(replacement):
                return None
            stored_steps, _geo = canonical_form(replacement)
            stored_children = [f"R_{step['type']}_{index}" for index, step in enumerate(stored_steps)]
            stored_key = json.dumps({"control": stored_steps, "salt": key}, separators=(",", ":"), default=list)
            if stored_key == key or self.memory.contains_canonical(stored_key):
                return None
        saved = float(len(placements) - 1)
        op = LearnedOperation(
            op_id=self.memory.next_name(),
            depth=depth,
            children=stored_children,
            steps=[{"type": s["type"], "cells": tuple(s["cells"])} for s in stored_steps],
            nbytes=nbytes_of(stored_steps, stored_children),
            canonical=stored_key,
            context=list(slot["features"]),
            created_at=episode.episode_id,
            last_used=episode.episode_id,
            successes=len(self.support[key]),
            attempts_saved=saved,
            q_sum=float(episode.q) * len(self.support[key]),
        )
        op.recompute(self.memory.fail_penalty, self.memory.storage_weight)
        if self.memory.add_operation(op, episode.episode_id):
            return op.op_id
        return None


def _random_sequence(length: int, rng: random.Random) -> list[dict] | None:
    """A connected sequence that is not taken from the observed trace."""
    names = list(PIECES)
    rng.shuffle(names)
    placed: list[dict] = []
    mask = 0
    for _ in range(length * 8):
        if len(placed) >= length:
            break
        piece = names[len(placed) % len(names)]
        rotation = rng.randrange(4)
        shape = orientation(PIECES[piece], rotation)
        w = max(x for x, _ in shape) + 1
        h = max(y for _, y in shape) + 1
        xs = list(range(10 - w + 1))
        ys = list(range(10 - h + 1))
        rng.shuffle(xs)
        rng.shuffle(ys)
        found = False
        for y in ys:
            for x in xs:
                cells = tuple((x + dx, y + dy) for dx, dy in shape)
                bit = 0
                touch = 0
                for cx, cy in cells:
                    bit |= 1 << (cy * 10 + cx)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < 10 and 0 <= ny < 10:
                            touch |= 1 << (ny * 10 + nx)
                if bit & mask:
                    continue
                if mask and not (touch & mask):
                    continue
                mask |= bit
                placed.append({"type": piece, "cells": cells})
                found = True
                break
            if found:
                break
    if len(placed) < length:
        return None
    return steps_from_absolute(placed[:length])
