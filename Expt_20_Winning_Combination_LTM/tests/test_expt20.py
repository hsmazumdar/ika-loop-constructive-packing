from collections import Counter

from config import Config, DEFAULT_RANKING
from extract import (connected_groups, frequency_table, multiset_keys, oriented_pattern, rank_order, top_ids,
                     trial_keysets, two_prop_z)
from trials import run_trial, run_trials


def test_s1_equals_100_minus_empty_and_s2_formula():
    for i in range(20):
        t = run_trial(1, i)
        assert t["S1"] == 100 - t["empty_cells"]
        assert abs(t["S2"] - t["S1"] / t["attempts"]) < 1e-12
        assert t["S1"] == sum({"A": 5, "B": 5, "C": 5, "D": 5, "E": 5, "F": 5, "G": 5, "H": 5, "I": 5, "J": 5,
                               "K": 5, "L": 5, "M": 4, "N": 4, "O": 4, "P": 7}[p[0]] for p in t["placements"])


def test_trials_are_reproducible_and_seed_dependent():
    a, b, c = run_trials(5, 5), run_trials(5, 5), run_trials(6, 5)
    assert a == b
    assert a != c


def test_multiset_keys_count_each_combination_once_and_respect_multiplicity():
    types = Counter({"A": 2, "B": 1})
    assert multiset_keys(types, 2) == {("A", "A"), ("A", "B")}
    assert multiset_keys(types, 3) == {("A", "A", "B")}
    assert multiset_keys(Counter({"A": 1}), 2) == set()


def test_connected_groups_pair_and_triple():
    # M at (0,0) rotation 1 is horizontal 4-long; place cells: A,B adjacent, C far away.
    pl = [("M", 1, 0, 0), ("M", 1, 0, 1), ("M", 1, 6, 6)]
    assert connected_groups(pl, 2) == {(0, 1)}
    assert connected_groups(pl, 3) == set()
    chain = [("M", 1, 0, 0), ("M", 1, 0, 1), ("M", 1, 0, 2)]
    assert connected_groups(chain, 3) == {(0, 1, 2)}


def test_oriented_pattern_is_translation_invariant():
    g1 = [("M", 1, 0, 0), ("M", 1, 0, 1)]
    g2 = [("M", 1, 3, 4), ("M", 1, 3, 5)]
    assert oriented_pattern(g1) == oriented_pattern(g2)


def test_ranking_tiebreak_and_top_selection():
    trials = [
        {"trial_id": 0, "S1": 90, "S2": 4.0},
        {"trial_id": 1, "S1": 90, "S2": 5.0},
        {"trial_id": 2, "S1": 95, "S2": 3.0},
        {"trial_id": 3, "S1": 80, "S2": 9.0},
    ]
    assert rank_order(trials, "S1") == [2, 1, 0, 3]
    assert rank_order(trials, "S2") == [3, 1, 0, 2]
    assert top_ids(trials, "S1", 0.25) == [2]
    assert top_ids(trials, "S2", 0.25) == [3]


def test_frequency_table_counts_lift_and_once_per_trial():
    cfg = Config(win_min_top_count=1)
    # trial placements with two A pieces in one trial must still count "A" once
    ks = [
        {"single_type": {"A", "B"}}, {"single_type": {"A"}},  # top
        {"single_type": {"B"}}, {"single_type": {"B"}}, {"single_type": {"A", "B"}}, {"single_type": {"B"}},
        {"single_type": {"B"}}, {"single_type": {"B"}},
    ]
    is_top = [True, True, False, False, False, False, False, False]
    rows = {r["key"]: r for r in frequency_table(ks, is_top, "single_type", cfg)}
    a, b = rows["A"], rows["B"]
    assert (a["n_top"], a["n_bottom"], a["n_all"]) == (2, 1, 3)
    assert abs(a["frac_top"] - 1.0) < 1e-12 and abs(a["frac_bottom"] - 1 / 6) < 1e-12
    assert abs(a["lift_vs_bottom"] - 6.0) < 1e-9
    assert abs(a["lift_vs_all"] - 1.0 / (3 / 8)) < 1e-9
    assert b["lift_vs_bottom"] < 1.0 and not b["winning"]


def test_trial_keysets_single_type_counts_once():
    pl = [("M", 1, 0, 0), ("M", 1, 0, 1), ("M", 1, 6, 6)]
    ks = trial_keysets(pl)
    assert ks["single_type"] == {"M"}
    assert ks["pair_type"] == {("M", "M")}
    assert ks["triple_type"] == {("M", "M", "M")}
    assert ks["pair_conn_type"] == {("M", "M")}
    assert ks["triple_conn_type"] == set()


def test_two_prop_z_sign():
    assert two_prop_z(50, 100, 10, 100) > 0
    assert two_prop_z(10, 100, 50, 100) < 0
    assert two_prop_z(0, 0, 0, 0) == 0.0

def test_default_ranking_is_s2_primary():
    from extract import RANKINGS
    assert DEFAULT_RANKING == "S2"
    assert Config().default_ranking == "S2"
    assert RANKINGS[0] == "S2"
    # S2 primary: higher S2 wins even with lower S1; ties on S2 broken by S1 then trial_id
    trials = [{"trial_id": 0, "S1": 99, "S2": 4.0}, {"trial_id": 1, "S1": 70, "S2": 5.0},
              {"trial_id": 2, "S1": 80, "S2": 5.0}, {"trial_id": 3, "S1": 80, "S2": 5.0}]
    assert rank_order(trials, "S2") == [2, 3, 1, 0]
