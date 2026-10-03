"""Access rule, billing, and decision. The diagnostic run is separate."""

from __future__ import annotations

from pathlib import Path

from config import diagnostic_config
from experiment import decide, miss_reason
from matcher import Budget, Recogniser, absolute_budget, select_anchors


def _pattern(index, pieces, cells, support=3):
    return {
        "pattern_index": index,
        "n_inventories": support,
        "counts": {piece: 1 for piece in pieces},
        "cells": tuple(cells),
        "anchors": (),
    }


def test_empty_board_anchor_is_the_declared_origin_only():
    config = diagnostic_config()
    anchors, checks, complete = select_anchors(set(), config)
    assert anchors == [(0, 0)]
    assert checks == 1 and complete


def test_frontier_anchors_are_capped_and_deterministic():
    config = diagnostic_config()
    occupied = {(0, 0)}
    first, _, _ = select_anchors(occupied, config)
    second, _, _ = select_anchors(occupied, config)
    assert first == second
    assert len(first) <= config.max_anchors
    assert all(cell not in occupied for cell in first)
    assert (1, 0) in first or (0, 1) in first


def test_budget_stops_consulting_and_does_not_place():
    config = diagnostic_config()
    pattern = _pattern(0, ["M"], ((0, 0), (1, 0)))
    budget = Budget(0)
    recogniser = Recogniser([pattern], budget)
    recogniser.filter_inventory({"M": 2}, None)
    assert recogniser.stopped
    record = recogniser.consult(0, set(), config)
    assert record["exposed"] == []
    assert budget.geometry == 0


def test_inventory_rejection_and_cache_invalidation_are_billed():
    config = diagnostic_config()
    pattern = _pattern(0, ["M"], ((0, 0), (1, 0)))
    budget = Budget(100)
    recogniser = Recogniser([pattern], budget)
    recogniser.filter_inventory({"M": 0}, None)
    assert recogniser.available[0] is False
    assert budget.inventory == 1
    recogniser.available[0] = True
    recogniser.cache[(0, (0, 0))] = True
    recogniser.cache_cells[(0, (0, 0))] = {(0, 0), (1, 0)}
    recogniser.filter_inventory({"M": 0}, {"M"})
    assert (0, (0, 0)) not in recogniser.cache
    assert budget.cache_invalidate == 1


def test_same_pattern_at_another_origin_is_not_a_hit():
    action = {"pattern_index": 3, "origin_x": 0, "origin_y": 0}
    consult = {
        "anchors": [(0, 0), (1, 0)],
        "anchor_complete": True,
        "inventory_rejected": [],
        "unchecked": [],
        "tested": [{"pattern_index": 3, "origin": (1, 0), "fits": True}],
        "exposed": [{"pattern_index": 3, "origin": (1, 0)}],
    }
    assert miss_reason(action, consult) == "budget_during_consult"
    consult["exposed"].append({"pattern_index": 3, "origin": (0, 0)})
    assert miss_reason(action, consult) == "exposed"
    other = {"pattern_index": 3, "origin_x": 4, "origin_y": 4}
    assert miss_reason(other, consult) == "anchor"


def test_absolute_budget_is_a_floor_of_development_effort():
    assert absolute_budget([1000, 2000], 0.10) == 150
    assert absolute_budget([1598], 0.10) == 159


def test_decision_rows_do_not_treat_a_fit_as_commitment():
    config = diagnostic_config()
    expensive = decide(config, {"mean_primitive": 1000, "mean_recognition": 200, "state_recall": 1.0, "mean_retention": 1.0, "n_boxes_with_reference": 5})
    assert expensive["row"] == "recognition_expensive"
    assert expensive["commitment"] == "disabled"
    retains = decide(config, {"mean_primitive": 1000, "mean_recognition": 50, "state_recall": 0.5, "mean_retention": 0.5, "n_boxes_with_reference": 3})
    assert retains["row"] == "retains_opportunities"
    misses = decide(config, {"mean_primitive": 1000, "mean_recognition": 50, "state_recall": 0.2, "mean_retention": 0.9, "n_boxes_with_reference": 4})
    assert misses["row"] == "misses_opportunities"
    none = decide(config, {"mean_primitive": 1000, "mean_recognition": 50, "state_recall": None, "mean_retention": None, "n_boxes_with_reference": 0})
    assert none["row"] == "misses_opportunities"


def test_access_rule_does_not_name_the_expt18_winning_patterns():
    root = Path(__file__).resolve().parents[1] / "src"
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "[0, 2, 4, 6, 24]" not in text
    assert "winning" not in text.lower()
