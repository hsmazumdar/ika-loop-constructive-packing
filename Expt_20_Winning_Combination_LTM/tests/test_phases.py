from collections import Counter

import numpy as np

from phases.compare import paired_diff, summarize_arm
from phases.policy import Policy, run_guided_trial, run_guided_trials, smoothed_single_weights
from phases.stm import STM, save_stm, load_stm
from trials import run_trial, run_trials


def fake_ltm():
    def e(key, nt, nb, lift, win):
        return {"key": key, "key_str": "+".join(key) if isinstance(key, tuple) else key, "n_top": nt, "n_bottom": nb,
                "lift_vs_bottom": lift, "winning": win}
    return {"default_ranking": "S2", "manifest": {"trials": 100}, "cutoffs": {"S2": {"n_top": 25}},
            "ltm": {"S2": {
                "single_type": {"entries": [e("P", 22, 24, 3.0, True), e("N", 20, 70, 0.8, False), e("M", 10, 30, 1.0, False)]},
                "pair_type": {"entries": [e(("N", "P"), 18, 20, 2.4, True), e(("M", "N"), 18, 50, 0.9, False)]},
                "triple_type": {"entries": [e(("N", "O", "P"), 14, 20, 2.0, True), e(("N", "N", "M"), 10, 10, 1.5, True)]},
            }}}


def test_smoothed_single_weights_clip_and_direction():
    w = smoothed_single_weights(fake_ltm()["ltm"]["S2"]["single_type"]["entries"], 25, 75)
    assert w["P"] > 1.0 > w["N"]
    assert 0.25 <= min(w.values()) and max(w.values()) <= 4.0


def test_policy_boost_only_for_winning_combinations_completed():
    pol = Policy.from_ltm(fake_ltm())
    assert pol.boosts(Counter()) == {}                        # nothing placed -> nothing completed
    b = pol.boosts(Counter({"N": 1}))
    assert b.get("P") == 2.4 and "M" not in b                 # winning N+P completed by P; non-winning M+N ignored
    b2 = pol.boosts(Counter({"N": 1, "P": 1}))
    assert "P" not in b2                                      # N+P already complete
    assert b2.get("O") == 2.0                                 # N+O+P completed by O
    b3 = pol.boosts(Counter({"N": 1, "M": 1}))
    assert b3.get("N") is None or b3["N"] >= 1.0


def test_policy_multiset_triple_with_repeated_type():
    pol = Policy.from_ltm(fake_ltm())
    assert pol.boosts(Counter({"N": 1, "M": 1})).get("N") == 1.5     # N+N+M needs a second N
    assert "N" not in pol.boosts(Counter({"N": 2, "M": 1}))          # already complete


def test_weights_follow_switches():
    pol = Policy.from_ltm(fake_ltm())
    types = ["N", "P"]
    full = pol.weights(types, Counter({"N": 1}))
    single_only = pol.variant("s", True, False).weights(types, Counter({"N": 1}))
    boost_only = pol.variant("b", False, True).weights(types, Counter({"N": 1}))
    assert boost_only == [1.0, 2.4]
    assert full[1] > single_only[1] > single_only[0]


def test_epsilon_one_reproduces_nothing_special_and_zero_is_valid():
    pol1 = Policy.from_ltm(fake_ltm(), epsilon=1.0)
    t = run_guided_trial(3, 4, pol1)
    assert t["n_guided_steps"] == 0 and t["n_explore_steps"] == t["attempts"]
    pol0 = Policy.from_ltm(fake_ltm(), epsilon=0.0)
    t0 = run_guided_trial(3, 4, pol0)
    assert t0["n_explore_steps"] == 0 and t0["n_guided_steps"] == t0["attempts"]


def test_guided_trial_is_legal_reproducible_and_s1_consistent():
    pol = Policy.from_ltm(fake_ltm())
    a, b = run_guided_trials(9, 6, pol), run_guided_trials(9, 6, pol)
    assert a == b
    for t in a:
        assert t["S1"] == 100 - t["empty_cells"]
        assert abs(t["S2"] - t["S1"] / t["attempts"]) < 1e-12
        assert t["invalid_attempts"] == 0 and t["termination_reason"] == "no_legal_placement"
        cells = [c for p in t["placements"] for c in __import__("mga.pieces", fromlist=["x"]).placed_cells(*p)]
        assert len(cells) == len(set(cells)) == t["S1"]


def test_control_uses_same_seeds_as_phase1_style_trials():
    assert [t["trial_seed"] for t in run_trials(11, 4)] == [t["trial_seed"] for t in run_guided_trials(11, 4, Policy.from_ltm(fake_ltm()))]


def test_stm_counts_once_per_trial_and_roundtrip(tmp_path):
    stm = STM("S2", 0.25)
    # P has 7 cells: two trials with a P (one with two Ps), six without.
    mk = lambda i, s1, s2, pl: {"trial_id": i, "S1": s1, "S2": s2, "placements": pl}
    stm.observe(mk(0, 80, 5.0, [("P", 0, 0, 0), ("P", 0, 4, 0), ("N", 0, 0, 5)]))
    stm.observe(mk(1, 80, 4.8, [("P", 0, 0, 0), ("M", 0, 4, 0)]))
    for i in range(2, 8):
        stm.observe(mk(i, 70, 4.0, [("M", 0, 0, 0), ("M", 0, 2, 0)]))
    assert stm.running_n_all["single_type"]["P"] == 2          # once per trial, not per piece
    assert stm.running_n_all["pair_type"][("P", "P")] == 1
    is_top, cut = stm.top_split()
    assert cut["n_top"] == 2 and sum(is_top) == 2 and cut["cutoff_S2"] == 4.8
    snap = stm.snapshot()
    assert snap["focus"]["single_type:P"]["n_top"] == 2 and snap["focus"]["single_type:P"]["frac_top"] == 1.0
    d = stm.export("t", "phase1", {"seed": 1})
    info = save_stm(d, tmp_path, "stm")
    assert load_stm(info["pkl"])["final_cutoff"] == d["final_cutoff"]
    import json
    j = json.loads((tmp_path / "stm.json").read_text(encoding="utf-8"))
    assert j["ranking"] == "S2" and j["n_trials"] == 8


def test_paired_diff_same_ids_and_sign():
    base = [{"trial_id": i, "S1": 80.0} for i in range(50)]
    other = [{"trial_id": i, "S1": 82.0 + (i % 2)} for i in range(50)]
    d = paired_diff(base, other, "S1", n_boot=200)
    assert d["n_pairs"] == 50 and abs(d["mean_diff"] - 2.5) < 1e-9 and d["frac_other_better"] == 1.0
    assert d["ci95_boot_low"] <= 2.5 <= d["ci95_boot_high"]


def test_summarize_arm_p_fraction():
    tr = run_trials(2, 30)
    s = summarize_arm("x", tr)
    expect = np.mean([any(p[0] == "P" for p in t["placements"]) for t in tr])
    assert abs(s["frac_trials_using_P"] - expect) < 1e-12
    assert s["S1"]["max"] >= s["S1"]["median"] >= s["S1"]["min"]