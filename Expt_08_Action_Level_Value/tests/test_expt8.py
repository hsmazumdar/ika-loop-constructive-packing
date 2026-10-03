"""Expt-8 tests."""

from __future__ import annotations

from pathlib import Path

from action_features import ACTION_NAMES
from config import QUALITY_LOSS_MARGIN
from pieces import catalogue_hash
from predictors import ConstantModels, remaining_check_cost, selection_metrics, useful_subset, would_accept
from ranker import RANK_NAMES
from experiment import audit_frozen_implementation, expt7_dir

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_saving_sign_is_skip_minus_commit():
    from config import Config

    assert "A_skip - A_commit" in Config().to_dict()["remaining_saving_sign"]
    assert remaining_check_cost(8) == 8
    assert would_accept(-10.0, 0.9, 0.5, 8) is False
    assert would_accept(20.0, 0.9, 0.5, 8) is True
    assert would_accept(20.0, 0.2, 0.5, 8) is False


def test_reject_all_is_zero_coverage_not_success():
    rows = [
        {"seed": 11, "task_id": "a", "remaining_saving": 100, "quality_ok": True, "pred_saving": -50, "p_quality_ok": 0.9, "quality_threshold": 0.5, "examined": 8, "accept": False},
        {"seed": 11, "task_id": "b", "remaining_saving": -400, "quality_ok": True, "pred_saving": -80, "p_quality_ok": 0.9, "quality_threshold": 0.5, "examined": 8, "accept": False},
    ]
    sel = selection_metrics(rows, "pred_saving", "p_quality_ok", 0.5, 8)
    assert sel["zero_coverage"] is True
    assert sel["n_accepted"] == 0
    assert useful_subset(sel) is False


def test_action_vector_has_placement_and_not_only_context():
    assert len(ACTION_NAMES) > len(RANK_NAMES)
    assert "anchor_x" in ACTION_NAMES
    assert "contact_frac" in ACTION_NAMES
    const = ConstantModels(-100.0, 0.9)
    assert const.predict_saving(None) == -100.0
    assert would_accept(const.predict_saving(None), const.probability(None), const.quality_threshold, 8) is False


def test_source_has_no_shape_labels():
    for path in (ROOT / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name


def test_audit_says_first_legal_not_oracle_best():
    audit = audit_frozen_implementation([])
    assert audit["train_deploy_action_mismatch"] is False
    assert "first_legal_site" in audit["training_action"]
    assert audit["cap_mismatch"] is True


def test_expt7_artifacts_exist():
    src = expt7_dir()
    assert src.exists()
    assert (src / "ranker_seed11.json").exists()
    assert (src / "library_seed11.json").exists()
    assert (src / "ranker_labels.csv").exists()
