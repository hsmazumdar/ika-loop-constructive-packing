"""Serialize and hash frozen libraries. No learning."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

from memory import ApplicabilityRule, LearnedOperation, OperationMemory, make_memory


def definition_payload(op: LearnedOperation) -> dict:
    return {
        "op_id": op.op_id,
        "depth": op.depth,
        "children": list(op.children),
        "steps": [{"type": s["type"], "cells": [list(c) for c in s["cells"]]} for s in op.steps],
        "canonical": op.canonical,
        "status": op.status,
    }


def definition_hash(op: LearnedOperation) -> str:
    blob = json.dumps(definition_payload(op), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def library_hash(memory: OperationMemory) -> str:
    parts = [definition_hash(op) for op in sorted(memory.operations, key=lambda o: o.op_id)]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def op_to_json(op: LearnedOperation) -> dict:
    rule = None
    if op.applicability is not None:
        rule = {
            "dim": op.applicability.dim,
            "success_sum": list(op.applicability.success_sum),
            "fail_sum": list(op.applicability.fail_sum),
            "success_n": op.applicability.success_n,
            "fail_n": op.applicability.fail_n,
            "threshold": op.applicability.threshold,
        }
    data = definition_payload(op)
    data.update(
        {
            "definition_hash": definition_hash(op),
            "nbytes": op.nbytes,
            "context": list(op.context),
            "created_at": op.created_at,
            "last_used": op.last_used,
            "applicability": rule,
        }
    )
    return data


def op_from_json(data: dict) -> LearnedOperation:
    rule = None
    if data.get("applicability"):
        raw = data["applicability"]
        rule = ApplicabilityRule(
            dim=int(raw["dim"]),
            success_sum=list(raw["success_sum"]),
            fail_sum=list(raw["fail_sum"]),
            success_n=int(raw["success_n"]),
            fail_n=int(raw["fail_n"]),
            threshold=float(raw["threshold"]),
        )
    steps = [{"type": s["type"], "cells": [tuple(c) for c in s["cells"]]} for s in data["steps"]]
    return LearnedOperation(
        op_id=data["op_id"],
        depth=int(data["depth"]),
        children=list(data.get("children") or []),
        steps=steps,
        nbytes=int(data.get("nbytes") or 0),
        canonical=data.get("canonical") or "",
        context=list(data.get("context") or []),
        created_at=int(data.get("created_at") or 0),
        last_used=int(data.get("last_used") or 0),
        status=data.get("status") or "active",
        applicability=rule,
    )


def memory_to_json(memory: OperationMemory) -> dict:
    return {
        "library_hash": library_hash(memory),
        "hierarchical": memory.hierarchical,
        "max_depth": memory.max_depth,
        "_next_id": memory._next_id,
        "operations": [op_to_json(op) for op in memory.operations],
    }


def memory_from_json(data: dict, config) -> OperationMemory:
    memory = make_memory(config, hierarchical=True, selective_retire=False)
    memory._next_id = int(data.get("_next_id") or 1)
    memory.operations = [op_from_json(item) for item in data.get("operations") or []]
    return memory
