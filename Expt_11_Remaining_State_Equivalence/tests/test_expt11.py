"""Expt-11 tests. Declared isometries; no invented transforms."""

from __future__ import annotations

from config import QUALITY_LOSS_MARGIN
from continuation import ContinuationTable, state_key
from environment import Action, PackingEnv
from inventory import Inventory
from pieces import catalogue_hash
from transforms import CANDIDATES, TransformSelector, inverse, transform_mask, transform_placement, transform_suffix

FORBIDDEN = ("RECTANGLE_AVAILABLE", "GOOD_CORNER", "ROW_PATTERN")


def test_catalogue():
    assert QUALITY_LOSS_MARGIN == 1.0
    assert catalogue_hash() == "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"


def test_d4_inverses_restore_mask():
    env = PackingEnv(budget=80, inventory=Inventory({"A": 2, "M": 4}))
    env.step(Action.place("A", 0, 0, 0))
    env.step(Action.place("M", 0, 5, 0))
    mask = int(env.mask)
    for name in CANDIDATES:
        mapped = transform_mask(name, mask)
        back = transform_mask(inverse(name), mapped)
        assert back == mask, name


def test_rotation_maps_placement_when_orientations_exist():
    mapped = transform_placement("rot90", "M", 0, 0, 0)
    assert mapped is not None
    assert mapped[0] == "M"


def test_selector_requires_success_and_no_fail():
    sel = TransformSelector()
    sel.observe("rot90", transformed_ok=True, validation_ok=True, acceptable=True)
    sel.observe("refl_x", transformed_ok=True, validation_ok=False, acceptable=False)
    chosen = sel.freeze()
    assert "rot90" in chosen
    assert "refl_x" not in chosen


def test_transform_suffix_all_or_nothing():
    suffix = [("M", 0, 0, 0), ("M", 0, 2, 0)]
    out = transform_suffix("rot180", suffix)
    assert out is not None
    assert len(out) == 2


def test_lookup_key_and_state_key_agree():
    env = PackingEnv(budget=80, inventory=Inventory({"A": 1, "B": 2}))
    table = ContinuationTable()
    table.entries[state_key(env)] = [("A", 0, 0, 0)]
    assert table.lookup(env) == table.lookup_key(env.mask, state_key(env)[1])


def test_source_has_no_shape_labels():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for path in (root / "src").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, path.name
