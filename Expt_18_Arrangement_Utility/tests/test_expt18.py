"""Sample, billing, and decision rules. The diagnostic run is not a unit test."""

from __future__ import annotations

from collections import Counter

from census import match_pattern
from config import diagnostic_config
from environment import PackingEnv
from experiment import trace_primitive
from inventory import Inventory
from pieces import placed_cells
from solver import Ledger
from utility import (
    box_opportunity,
    commit_pattern,
    decide,
    first_translation,
    sample_indices,
    select_patterns,
)


def _row(saving, pattern, stage, benefit, lost=False, valid=True, replay=True):
    return {
        "effort_saving": saving,
        "pattern_index": pattern,
        "stage": stage,
        "quality_delta": -2.0 if lost else 0.0,
        "quality_loss": lost,
        "quality_preserving_benefit": benefit,
        "valid": valid,
        "replay_ok": replay,
    }


def test_sample_strides_are_fixed_and_do_not_depend_on_fit_counts():
    assert sample_indices(60, 5, 12) == [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    assert sample_indices(60, 10, 6) == [0, 10, 20, 30, 40, 50]
    assert sample_indices(2, 5, 1) == [0]


def test_pattern_sample_keeps_high_support_and_draws_eight_pairs():
    from experiment import load_frozen

    config = diagnostic_config()
    frozen = load_frozen(config)
    chosen = select_patterns(frozen, config)
    assert len(chosen) == 13
    assert sum(1 for item in chosen if item["n_inventories"] >= 3) == 5
    assert sum(1 for item in chosen if item["n_inventories"] == 2) == 8
    assert select_patterns(frozen, config)[0]["pattern_index"] == chosen[0]["pattern_index"]
    assert len({item["pattern_index"] for item in chosen}) == 13


def test_first_translation_matches_the_expt17_scanner_on_a_miss():
    pattern = {"counts": {"M": 2}, "cells": ((0, 0), (1, 0))}
    occupied = {(x, y) for x in range(10) for y in range(10)}
    remaining = Counter({"M": 4})
    checks, origin = first_translation(pattern, occupied, remaining)
    other, fits = match_pattern(pattern, occupied, remaining)
    assert origin is None and fits == 0 and checks == other


def test_commit_charges_every_examined_piece_and_cell():
    env = PackingEnv(budget=80, inventory=Inventory({"M": 4}))
    cells = placed_cells("M", 0, 0, 0)
    height = max(y for _x, y in cells) - min(y for _x, y in cells)
    pattern = {
        "counts": {"M": 2},
        "anchors": (("M", 0, 0, 0), ("M", 0, 0, height + 1)),
        "cells": (),
    }
    ledger = Ledger()
    assert commit_pattern(env, ledger, pattern, (0, 0))
    assert ledger.validation_cost == 2 + 2 * len(cells)
    assert len(env.stack) == 2


def test_box_opportunity_does_not_add_overlapping_savings():
    config = diagnostic_config()
    rows = [
        _row(100, 1, "early", True),
        _row(40, 2, "middle", True),
        _row(500, 3, "early", False, lost=True),
    ]
    opp = box_opportunity(rows, config)
    assert opp["ideal_saving"] == 100
    assert opp["n_quality_preserving"] == 2
    assert opp["largest_valid_saving"] == 500
    assert opp["largest_valid_lost_quality"] is True
    assert opp["counts_as_benefit"] is True


def test_decision_rows():
    config = diagnostic_config()

    def box(benefit, pattern=0, stage="early", saving=100):
        return {"counts_as_benefit": benefit, "ideal_pattern": pattern, "ideal_stage": stage, "ideal_saving": saving}

    stop = decide(config, [box(False), box(False)], [box(False)], 4, 0)
    assert stop["row"] == "stop_pattern_reuse"
    assert stop["cost_gate"] == "not relaxed"
    narrow_count = decide(config, [box(True, 1, "early"), box(False)], [], 4, 0)
    assert narrow_count["row"] == "narrow_retrieval"
    narrow_pattern = decide(
        config,
        [box(True, 1, "early"), box(True, 1, "middle"), box(True, 2, "early")],
        [],
        6,
        0,
    )
    assert narrow_pattern["row"] == "narrow_retrieval"
    narrow_stage = decide(
        config,
        [box(True, 1, "early"), box(True, 2, "early"), box(True, 3, "early")],
        [],
        6,
        0,
    )
    assert narrow_stage["row"] == "narrow_retrieval"
    family_only = decide(config, [box(False), box(False)], [box(True, 4, "middle")], 3, 0)
    assert family_only["row"] == "narrow_retrieval"
    broad = decide(
        config,
        [box(True, 1, "early"), box(True, 2, "middle"), box(True, 3, "early")],
        [],
        6,
        0,
    )
    assert broad["row"] == "build_budgeted_matcher"
    bad = decide(config, [box(False)], [], 4, 3)
    assert bad["row"] == "inconclusive_replay"


def test_primitive_replay_from_the_first_fresh_prefix_reproduces_the_trajectory():
    from experiment import load_manifest
    from utility import replay_branch

    config = diagnostic_config()
    task = load_manifest("applicability_fresh")["tasks"][0]
    traced = trace_primitive(config, task, "expt16-applicability-independent_fresh", 0)
    primitive = replay_branch(config, traced["snaps"][0], None, None)
    assert primitive["Q"] == traced["Q"]
    assert primitive["A"] == traced["A"]
