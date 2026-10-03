"""Runner invariants: mode order, replay, frozen eval, resume."""

from __future__ import annotations

import json
from pathlib import Path

from mga2.experiment import execute_run, legacy_task, run_episode
from mga2.selection import new_library

ROOT = Path(__file__).resolve().parents[1]


def small_config() -> dict:
    cfg = json.loads((ROOT / "configs" / "default.json").read_text(encoding="utf-8"))
    cfg["budgets"]["physical_actions"] = 6
    cfg["budgets"]["candidate_evals"] = 4000
    cfg["budgets"]["model_transitions"] = 1500
    cfg["exam_limit"] = 10
    cfg["discovery"]["max_paired_trials"] = 1
    cfg["discovery"]["max_origin_trials"] = 8
    cfg["discovery"]["flat_think_interval"] = 3
    cfg["utility"]["horizon"] = 2
    cfg["language"]["default_lookahead_depth"] = 1
    cfg["language"]["default_lookahead_width"] = 1
    cfg["tiny_boxes"] = 2
    cfg["modes"] = ["primitive", "search_only"]
    return cfg


def _actions(rec):
    return [step["action"] for step in rec["trace"]]


def test_primitive_trace_independent_of_other_mode():
    cfg = small_config()
    task = legacy_task(0)
    ltm_a = new_library(cfg)
    first = run_episode("primitive", task, 3, "train", 0, ltm_a, cfg, frozen=False)
    _search = run_episode("search_only", task, 3, "train", 0, new_library(cfg), cfg, frozen=False)
    second = run_episode("primitive", task, 3, "train", 0, new_library(cfg), cfg, frozen=False)
    assert _actions(first) == _actions(second)
    assert first["final_score"] == second["final_score"]
    assert first["best_score"] >= first["final_score"]


def test_replay_matches_score():
    cfg = small_config()
    rec = run_episode("primitive", legacy_task(1), 4, "train", 1, new_library(cfg), cfg, frozen=False)
    from mga2.experiment import assert_replay

    assert_replay(
        {
            "family": "legacy_unlimited",
            "inventory": {},
            "actions": _actions(rec),
            "final_score": rec["final_score"],
        },
        budget=cfg["budgets"]["physical_actions"],
    )


def test_frozen_episode_does_not_mutate_library():
    cfg = small_config()
    ltm = new_library(cfg)
    run_episode("flat_library", legacy_task(0), 5, "train", 0, ltm, cfg, frozen=False)
    before = json.dumps(ltm.to_dict()["ops"], sort_keys=True)
    run_episode("flat_library", legacy_task(0), 5, "eval", 0, ltm, cfg, frozen=True)
    after = json.dumps(ltm.to_dict()["ops"], sort_keys=True)
    assert before == after


def test_resume_after_wall_cap(tmp_path, monkeypatch):
    cfg = small_config()
    cfg["modes"] = ["primitive"]
    cfg["tiny_boxes"] = 2
    import mga2.experiment as experiment

    monkeypatch.setattr(experiment, "RESULTS", tmp_path)
    stopped = experiment.execute_run("tiny", cfg, wall_minutes=0)
    assert stopped["complete"] is False
    assert stopped["stop_reason"] == "wall_cap"
    resumed = experiment.execute_run("tiny", {}, wall_minutes=None, resume=Path(stopped["run_dir"]))
    assert resumed["complete"] is True
    assert len(resumed["completed"]) == 2


def test_zero_cap_without_reserve_submits_compute_budget():
    cfg = small_config()
    cfg["budgets"]["candidate_evals"] = 0
    cfg["budgets"]["cheap_scan_reserve"] = 0
    cfg["exam_limit"] = 0
    rec = run_episode("primitive", legacy_task(0), 11, "train", 0, new_library(cfg), cfg, frozen=False)
    assert rec["termination"] == "compute_budget"
    assert rec["physical_actions"] == 0


def test_reserve_allows_a_cheap_placement_before_compute_budget():
    cfg = small_config()
    cfg["budgets"]["candidate_evals"] = 200
    cfg["budgets"]["cheap_scan_reserve"] = 3636
    cfg["budgets"]["physical_actions"] = 20
    cfg["exam_limit"] = 0
    rec = run_episode("primitive", legacy_task(0), 11, "train", 0, new_library(cfg), cfg, frozen=False)
    assert rec["physical_actions"] >= 1
    assert rec["final_score"] > 0
    assert rec["cheap_actions"] >= 1
    assert rec["termination"] == "compute_budget"


def test_hierarchical_reserve_places_after_deliberation_stops():
    cfg = small_config()
    cfg["budgets"]["candidate_evals"] = 8000
    cfg["budgets"]["model_transitions"] = 10_000
    cfg["budgets"]["physical_actions"] = 20
    cfg["budgets"]["cheap_scan_reserve"] = 3636
    cfg["exam_limit"] = 0
    rec = run_episode(
        "hierarchical_library",
        legacy_task(0),
        11,
        "train",
        0,
        new_library(cfg),
        cfg,
        frozen=False,
    )
    assert rec["physical_actions"] >= 1
    assert rec["final_score"] > 0
    parts = (
        rec["part_think"]
        + rec["part_paired"]
        + rec["part_guard"]
        + rec["part_selection"]
        + rec["part_other"]
    )
    assert parts == rec["candidate_evals"]


def test_decision_trace_partitions_evaluations():
    cfg = small_config()
    cfg["record_decisions"] = True
    cfg["budgets"]["cheap_scan_reserve"] = 0
    cfg["budgets"]["candidate_evals"] = 400
    cfg["exam_limit"] = 0
    rec = run_episode("primitive", legacy_task(0), 11, "train", 0, new_library(cfg), cfg, frozen=False)
    trace = rec["decision_trace"]
    assert trace
    keys = ("candidate", "paired", "library_scan", "lookahead", "placement", "think", "other")
    spent = sum(sum(int(row.get(key, 0)) for key in keys) for row in trace)
    assert spent == rec["candidate_evals"]
    assert trace[-1]["score_after"] == rec["final_score"]
    assert trace[-1]["evals_after"] == rec["candidate_evals"]
    assert any(int(row.get("placement", 0)) > 0 for row in trace)


def test_library_lookup_does_not_think():
    cfg = small_config()
    cfg["budgets"]["allow_think"] = False
    rec = run_episode("flat_library", legacy_task(0), 11, "eval", 0, new_library(cfg), cfg, frozen=True)
    assert rec["think_batches"] == 0


def test_fixed_think_allowance_stops_paired_scans(monkeypatch):
    from mga2.ops import make_operation, place_rel, seq

    cfg = small_config()
    cfg["budgets"]["cheap_scan_reserve"] = 0
    cfg["budgets"]["candidate_evals"] = 5000
    cfg["budgets"]["physical_actions"] = 3
    cfg["exam_limit"] = 0
    cfg["discovery"]["flat_think_interval"] = 1
    cfg["think_eval_allowance"] = 80
    op = make_operation(
        seq([place_rel("M", 0, 0, 0)]),
        [{"type": "M", "rotation": 0, "dx": 0, "dy": 0, "cells": [[0, 0], [0, 1], [0, 2], [0, 3]]}],
        [],
        "test",
        "real",
        0,
    )
    monkeypatch.setattr("mga2.selection.propose", lambda *args, **kwargs: [(op, "mine", "")])
    rec = run_episode("flat_library", legacy_task(0), 11, "eval", 0, new_library(cfg), cfg, frozen=True)
    assert rec["think_batches"] >= 1
    assert 0 < rec["span_think"] <= 80
