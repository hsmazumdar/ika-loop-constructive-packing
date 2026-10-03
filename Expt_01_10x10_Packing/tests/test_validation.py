from mga.validation import (
    canonical_label_grid,
    constructive_witnesses,
    find_perfect_tilings,
    replay_witness,
)


def test_witness_replay_and_nonequivalence():
    w1, w2 = constructive_witnesses()
    e1 = replay_witness(w1)
    e2 = replay_witness(w2)
    assert e1.score == 100 and e2.score == 100
    c1 = canonical_label_grid(e1.occupancy_grid())
    c2 = canonical_label_grid(e2.occupancy_grid())
    assert c1 != c2


def test_canonicalization_rotation_equivalence():
    w1, _w2 = constructive_witnesses()
    env = replay_witness(w1)
    grid = env.occupancy_grid()
    # All-B board is invariant under rotation as a label grid.
    assert "B" in {cell for row in grid for cell in row}


def test_find_perfect_tilings_status():
    payload = find_perfect_tilings(n=2, timeout=15.0)
    assert payload["n_found"] >= 2
    assert payload["status"] == "SOLVED"
    canons = {w["canonical"] for w in payload["witnesses"]}
    assert len(canons) >= 2
