"""Deterministic RNG streams.

A stream depends on master seed, task id, phase, repetition and purpose.
It does not depend on mode order or on how many other episodes have run.
"""

from __future__ import annotations

import hashlib
import random


def derive_seed(master: int, task_id: str, phase: str, repetition: int, purpose: str) -> int:
    payload = f"{int(master)}|{task_id}|{phase}|{int(repetition)}|{purpose}"
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def make_rng(master: int, task_id: str, phase: str, repetition: int, purpose: str) -> random.Random:
    return random.Random(derive_seed(master, task_id, phase, repetition, purpose))
