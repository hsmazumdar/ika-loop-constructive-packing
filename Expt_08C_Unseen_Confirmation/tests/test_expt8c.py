"""Expt-8C tests."""

from __future__ import annotations

from pathlib import Path

from config import QUALITY_LOSS_MARGIN
from pieces import catalogue_hash
from predictors import remaining_check_cost, would_accept
from provenance import CACHE_KEY, EIGHT_B_HOLDOUT, LABEL_BUDGET, build_audit
from experiment import audit_frozen_implementation, expt7_dir

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_holdout_is_reused_development():
    audit = build_audit()
    assert audit["n_holdout_with_prior_use"] == len(EIGHT_B_HOLDOUT)
    assert audit["fit_label_comparison"]["n_y_changed"] == 0
    assert audit["val_label_comparison"]["n_y_changed"] == 0
    assert audit["cache_includes_budget"] is True
    assert LABEL_BUDGET in audit["label_remaining_budget"]
    assert "remaining_cap" in CACHE_KEY
    for item in audit["expt8b_holdout"]:
        assert item["fresh"] is False
        assert any("development.json" in p for p in item["prior_uses"])


def test_admit_bar_unchanged():
    assert remaining_check_cost(8) == 8
    assert would_accept(-10.0, 0.9, 0.5, 8) is False
    assert would_accept(20.0, 0.9, 0.5, 8) is True


def test_source_has_no_shape_labels():
    for path in (ROOT / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name


def test_expt7_artifacts_exist():
    src = expt7_dir()
    assert src.exists()
    assert (src / "ranker_seed11.json").exists()


def test_audit_marks_historical_and_reused_holdout():
    audit = audit_frozen_implementation([])
    assert audit["frozen_expt7_historical"] is True
    assert "reused" in audit["expt8b_holdout_status"]
    assert audit["expt8_used_pair_cap_for_remaining_pair"] is False
