"""GUI construction and a short offline generation check."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_gui_step_keeps_a_manual_session():
    tk = pytest.importorskip("tkinter")
    from mga2.gui import DemoApp

    cfg = json.loads((ROOT / "configs" / "default.json").read_text(encoding="utf-8"))
    cfg["budgets"]["physical_actions"] = 8
    cfg["budgets"]["candidate_evals"] = 3000
    cfg["budgets"]["model_transitions"] = 800
    cfg["exam_limit"] = 8
    cfg["discovery"]["max_paired_trials"] = 1
    cfg["discovery"]["max_origin_trials"] = 4
    cfg["utility"]["horizon"] = 2
    root = tk.Tk()
    root.withdraw()
    try:
        app = DemoApp(root, config=cfg)
        app.refresh()
        before = app.env.mask
        app.internal_step()
        assert app.env.mask == before
        app.physical_step()
        app.snapshot = lambda: None
        root.update_idletasks()
    finally:
        root.destroy()


def test_generator_finds_a_partial_split(tmp_path, monkeypatch):
    from tools.generate_tasks import generate
    import tools.validate_tasks as validate_tasks

    cfg = {
        "generation": {
            "timeout_seconds": 40,
            "train": 2,
            "development": 1,
            "test": 1,
            "seed": 7,
            "min_types": 4,
            "max_cells_per_type": 40,
        }
    }
    manifest = generate(cfg, root=tmp_path)
    assert manifest["unique"] >= 1
    ids = [i for split in manifest["splits"].values() for i in split]
    assert len(ids) == len(set(ids))
    monkeypatch.setattr(validate_tasks, "ROOT", tmp_path)
    report = validate_tasks.validate(tmp_path / "data" / "runtime" / "manifest.json")
    assert report["status"] == "OK"
    assert report["errors"] == []
