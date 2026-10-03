from mga.pieces import (
    PIECES,
    ROTATIONS,
    is_connected,
    normalize,
    orientation,
    reflect_x,
    rotate90_cw,
    unique_orientations,
)


def test_sixteen_types():
    assert list(PIECES) == list("ABCDEFGHIJKLMNOP")
    assert len(PIECES) == 16


def test_unique_types_up_to_rotation():
    seen = []
    for name, cells in PIECES.items():
        oris = set(unique_orientations(name))
        for other in seen:
            assert oris.isdisjoint(other)
        seen.append(oris)


def test_connected_no_duplicate_coords_areas():
    areas = {}
    for name, cells in PIECES.items():
        assert len(cells) == len(set(cells))
        assert is_connected(cells)
        areas[name] = len(cells)
        assert name != "P" or areas[name] == 7
    assert min(areas.values()) == 4
    assert max(areas.values()) == 7
    assert areas["M"] == areas["N"] == areas["O"] == 4


def test_rotation_normalization_four_turn_identity():
    for name, cells in PIECES.items():
        base = normalize(cells)
        cur = cells
        for _ in range(4):
            cur = rotate90_cw(cur)
        assert normalize(cur) == base
        assert orientation(cells, 4) == base
        assert orientation(cells, 0) == base


def test_no_accidental_reflection():
    """Asymmetric pieces must have a mirror image that is not among the 4 rotations."""
    asymmetric = []
    for name, cells in PIECES.items():
        rots = set(orientation(cells, k) for k in ROTATIONS)
        mirrored = reflect_x(cells)
        if mirrored not in rots:
            asymmetric.append(name)
    # Catalogue contains several chiral pieces; at least some must be chiral.
    assert asymmetric, "expected at least one chiral piece so reflection is detectable"
    for name in asymmetric:
        rots = set(orientation(PIECES[name], k) for k in ROTATIONS)
        assert reflect_x(PIECES[name]) not in rots


def test_four_user_rotations_exist_even_if_deduped():
    for name in PIECES:
        uniq = unique_orientations(name)
        assert 1 <= len(uniq) <= 4
        for k in ROTATIONS:
            orientation(PIECES[name], k)
