import json
from pathlib import Path

from mga.memory import (
    EpisodeUpdateBuffer,
    LongTermMemory,
    ShortTermMemory,
    config_hash,
    ltm_key,
)
from mga.pieces import ALL_PLACEMENTS, catalogue_hash


def test_stm_state_specific_exclusion_eviction_and_clear():
    stm = ShortTermMemory(capacity=3)
    stm.exclude(1, ("A", 0, 0, 0))
    stm.exclude(2, ("A", 0, 0, 0))
    assert stm.is_excluded(1, ("A", 0, 0, 0))
    assert not stm.is_excluded(2, ("B", 0, 0, 0))
    stm.exclude(3, ("C", 0, 0, 0))
    stm.exclude(4, ("D", 0, 0, 0))
    assert len(stm) == 3
    assert not stm.is_excluded(1, ("A", 0, 0, 0))
    stm.clear()
    assert len(stm) == 0


def test_ltm_update_arithmetic_and_empty_zero():
    ltm = LongTermMemory(capacity=8, coefficient=1.0, shrinkage_k=5)
    assert ltm.bonus("missing") == 0.0
    ltm.update("k", 1.0)
    ltm.update("k", 0.0)
    assert ltm.entries["k"].n == 2
    assert abs(ltm.entries["k"].mean - 0.5) < 1e-12
    bonus = 2 / (2 + 5) * 0.5
    assert abs(ltm.bonus("k") - bonus) < 1e-12


def test_ltm_capacity_eviction_deterministic():
    ltm = LongTermMemory(capacity=2, coefficient=1.0, shrinkage_k=1)
    ltm.update("b", 1.0)
    ltm.update("a", 1.0)
    ltm.update("c", 1.0)
    assert "b" not in ltm.entries
    assert set(ltm.entries) == {"a", "c"}
    assert ltm.evictions == 1


def test_checkpoint_roundtrip_and_mismatch(tmp_path: Path):
    ltm = LongTermMemory(capacity=16, coefficient=0.4, shrinkage_k=5)
    ltm.catalogue_hash = catalogue_hash()
    ltm.config_hash = config_hash({"x": 1})
    ltm.update("abc", 0.2)
    path = tmp_path / "ltm.json"
    ltm.save(path)
    loaded = LongTermMemory.load(
        path,
        expected_catalogue_hash=catalogue_hash(),
        expected_config_hash=config_hash({"x": 1}),
    )
    assert loaded.dump_bytes() == ltm.dump_bytes()
    try:
        LongTermMemory.load(path, expected_catalogue_hash="deadbeef")
        assert False, "mismatch should raise"
    except ValueError as exc:
        assert "catalogue" in str(exc)


def test_frozen_eval_byte_for_byte():
    ltm = LongTermMemory(capacity=16)
    ltm.update("k", 0.3)
    ltm.freeze()
    before = ltm.dump_bytes()
    ltm.update("k", 0.9)
    ltm.update("new", 1.0)
    assert ltm.dump_bytes() == before


def test_episode_buffer_formula_and_limit():
    buf = EpisodeUpdateBuffer(max_actions=2)
    buf.add("k", occupied_before=10, action_index=1)
    ltm = LongTermMemory(coefficient=1.0, shrinkage_k=0)
    buf.apply(ltm, terminal_occupied=40, terminal_actions=5)
    expected = (40 - 10) / 100.0 - 0.001 * (5 - 1)
    assert abs(ltm.entries["k"].mean - expected) < 1e-12
    buf.add("a", 0, 1)
    buf.add("b", 0, 2)
    try:
        buf.add("c", 0, 3)
        assert False
    except RuntimeError:
        pass


def test_ltm_key_uses_partial_neighbourhood():
    p = ALL_PLACEMENTS[0]
    k1 = ltm_key(0, p)
    k2 = ltm_key(1, p)
    assert k1 != k2
    assert p.piece_type in k1
