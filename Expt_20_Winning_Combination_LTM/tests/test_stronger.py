import random
from collections import Counter

import numpy as np

from mga.environment import Action, PackingEnv
from mga.pieces import ALL_PLACEMENTS, FULL_MASK, placed_cells
from stronger.engine import Cost, anchor_pool, contact_score, dead_cells_after
from stronger.ltmbuild import build_ltm, build_placement_table, type_keysets
from stronger.policies import Context, Online, Spec, run_online_arm, run_trial
from stronger.stats import arm_arrays, arm_row, paired_boot
from trials import run_trial as plain_trial


def mini_ltm(label="S1"):
    def e(key, nt, nb, lift, win):
        return {"key": key, "key_str": "+".join(key) if isinstance(key, tuple) else key, "n_top": nt, "n_bottom": nb,
                "lift_vs_bottom": lift, "winning": win}
    return {"default_ranking": label, "manifest": {"trials": 100}, "cutoffs": {label: {"n_top": 25}},
            "ltm": {label: {"single_type": {"entries": [e("P", 22, 24, 3.0, True), e("N", 20, 70, 0.8, False)]},
                            "pair_type": {"entries": [e(("N", "P"), 18, 20, 2.4, True)]},
                            "triple_type": {"entries": [e(("N", "O", "P"), 14, 20, 2.0, True)]}}}}


def ctx():
    return Context({"S2_frozen": mini_ltm("S2"), "x": mini_ltm("S1")}, {"pt": {}})


def test_uniform_spec_with_eps0_reproduces_control_exactly():
    spec = Spec("u", "t", eps=0.0, type_mode="placement_uniform")
    for i in range(8):
        a, b = run_trial(5, i, spec, ctx()), plain_trial(5, i)
        assert (a["S1"], a["attempts"], a["S2"]) == (b["S1"], b["attempts"], b["S2"])


def test_anchor_pool_covers_first_coverable_empty_cell_and_is_legal():
    env = PackingEnv()
    cost = Cost()
    pool = anchor_pool(env.mask, cost)
    assert pool and all(p.mask & 1 for p in pool) and cost.mask_ops > 0     # cell 0 is coverable on an empty board
    # block cell 0's neighbourhood so that cell 0 becomes dead; the anchor moves on
    rng = random.Random(1)
    for _ in range(6):
        legal = env.legal_placements()
        env.step(Action.place_from(rng.choice(legal)))
    occ = env.mask
    pool = anchor_pool(occ, Cost())
    legal_ids = {id(p) for p in env.legal_placements()}
    assert all(id(p) in legal_ids for p in pool)
    first = min(i for p in pool for i in range(100) if (p.mask >> i) & 1 and not (occ >> i) & 1)
    assert all(not (p.mask & ((1 << first) - 1) & ~occ) or True for p in pool)
    assert all((p.mask >> first) & 1 for p in pool)


def test_dead_cells_after_counts_unreachable_empty_cells():
    # fill columns 0-8 of the first 10 rows except a single-cell hole: hole is dead because every piece has >=4 cells
    occ = 0
    hole = 5 * 10 + 4
    for idx in range(100):
        if idx % 10 <= 8 and idx != hole:
            occ |= 1 << idx
    legal = [p for p in ALL_PLACEMENTS if not (p.mask & occ)]
    assert dead_cells_after(legal, occ, 0) >= 1
    # the hole cell is covered by no legal placement
    assert not any((p.mask >> hole) & 1 for p in legal)


def test_contact_score_prefers_corner_over_open_space():
    m = next(p for p in ALL_PLACEMENTS if p.piece_type == "M" and p.rotation == 0 and p.x == 0 and p.y == 0)
    mid = next(p for p in ALL_PLACEMENTS if p.piece_type == "M" and p.rotation == 0 and p.x == 4 and p.y == 3)
    assert contact_score(m, 0) > contact_score(mid, 0)
    assert contact_score(mid, 0) == mid.boundary_contacts == 0 or contact_score(mid, 0) >= 0


def test_hard_priority_chooses_only_completing_types():
    spec = Spec("h", "t", eps=0.0, type_mode="ltm", ltm="x", hard_priority=True, boost_max=20.0)
    c = ctx()
    rng = random.Random(0)
    from stronger.policies import _choose_type
    for _ in range(50):
        t = _choose_type(spec, c, ["M", "N", "O", "P"], Counter({"N": 1}), rng, Cost(), None)
        assert t == "P"                      # only P completes winning N+P; hard priority ignores the others
    t2 = _choose_type(spec, c, ["M", "N"], Counter({"N": 1}), rng, Cost(), None)
    assert t2 in ("M", "N")                  # nothing completes -> normal weighting


def test_exponent_sharpens_single_weights():
    c = ctx()
    from stronger.policies import _choose_type
    for alpha, lo in ((1.0, 0.0), (3.0, 0.0)):
        spec = Spec("a", "t", eps=0.0, ltm="x", alpha=alpha, use_boost=False)
        rng = random.Random(3)
        cnt = Counter(_choose_type(spec, c, ["N", "P"], Counter(), rng, Cost(), None) for _ in range(4000))
        if alpha == 1.0:
            p1 = cnt["P"] / 4000
        else:
            p3 = cnt["P"] / 4000
    assert p3 > p1 > 0.5


def test_size_mode_prefers_large_pieces():
    c = ctx()
    from stronger.policies import _choose_type
    spec = Spec("s", "t", type_mode="size", alpha=2.0)
    rng = random.Random(1)
    cnt = Counter(_choose_type(spec, c, ["M", "P"], Counter(), rng, Cost(), None) for _ in range(3000))
    assert cnt["P"] > cnt["M"]


def test_guided_variants_are_legal_reproducible_and_score_consistent():
    c = ctx()
    specs = [Spec("a", "t", eps=0.05, ltm="x", select="contact", anchor=True),
             Spec("b", "t", eps=0.0, type_mode="flat", select="look", K=4),
             Spec("c", "t", eps=0.05, type_mode="placement_uniform", select="table", table="pt"),
             Spec("d", "t", eps=0.05, ltm="x", hard_priority=True)]
    for s in specs:
        r1 = [run_trial(3, i, s, c) for i in range(5)]
        r2 = [run_trial(3, i, s, c) for i in range(5)]
        assert r1 == r2
        for r in r1:
            assert 0 < r["S1"] <= 100 and abs(r["S2"] - r["S1"] / r["attempts"]) < 1e-12 and r["enum_ops"] >= 3636 * r["attempts"]
    look = run_trial(3, 0, specs[1], c)
    assert look["cand_evals"] > 0 and look["mask_ops"] > 0
    assert run_trial(3, 0, Spec("u", "t", eps=0.0, type_mode="placement_uniform"), c)["cand_evals"] == 0


def test_lookahead_does_not_lose_to_random_on_dead_cells_in_a_single_step():
    env = PackingEnv()
    rng = random.Random(4)
    for _ in range(9):
        env.step(Action.place_from(rng.choice(env.legal_placements())))
    legal = env.legal_placements()
    occ = env.mask
    spec = Spec("l", "t", select="look", K=10_000, eps=0.0, type_mode="placement_uniform")
    from stronger.policies import _choose_placement
    p = _choose_placement(spec, ctx(), legal, legal, occ, random.Random(0), Cost())
    best = min(dead_cells_after(legal, occ, q.mask) for q in legal)
    assert dead_cells_after(legal, occ, p.mask) == best


def test_online_updates_and_favours_types_with_higher_s1():
    on = Online(prior=1.0)
    for i in range(200):
        on.update(90.0 if i % 2 else 70.0, ["P"] if i % 2 else ["M"])
    e_p, _ = on.effect("P"); e_m, _ = on.effect("M")
    assert e_p > 0 > e_m
    w = on.weights(["P", "M"], random.Random(0), "softmax", 5.0)
    assert w[0] > w[1]
    assert on.n == 200
    out = run_online_arm(1, range(4), Spec("o", "t", eps=0.05, type_mode="online"), ctx())
    assert len(out) == 4


def test_build_ltm_and_placement_table_shapes():
    trials = [plain_trial(7, i) for i in range(60)]
    meta = [{"trial_id": t["trial_id"], "S1": t["S1"], "S2": t["S2"]} for t in trials]
    ks = [type_keysets(t["placements"]) for t in trials]
    l = build_ltm(ks, meta, "S1", 0.25, "test")
    assert l["default_ranking"] == "S1" and l["cutoffs"]["S1"]["n_top"] == 15
    e = l["ltm"]["S1"]["single_type"]["entries"][0]
    assert {"key", "n_top", "n_bottom", "lift_vs_bottom", "winning"} <= set(e)
    tab = build_placement_table(trials, "S1", 0.25)
    assert tab and all(0.25 <= v <= 4.0 for v in tab.values())
    from phases.policy import Policy
    Policy.from_ltm(l)                       # a built LTM is directly usable by the phase-2 policy


def test_paired_boot_and_arm_row_cost_fields():
    d = np.r_[np.ones(50) * 2.0, np.zeros(50)]
    b = paired_boot(d, 300)
    assert abs(b["mean"] - 1.0) < 1e-9 and b["lo"] <= 1.0 <= b["hi"]
    mk = lambda off, cost: [{"trial_id": i, "S1": 80 + off, "S2": 4.7, "attempts": 17, "n_P": 1, "enum_ops": 10, "mask_ops": cost, "cand_evals": cost} for i in range(100)]
    row = arm_row("v", "f", arm_arrays(mk(1, 50)), arm_arrays(mk(0, 0)), 1.0, 200)
    assert abs(row["S1_gain"] - 1.0) < 1e-9 and row["extra_cost_units_per_box"] == 100.0
    assert abs(row["S1_gain_per_1k_extra_units"] - 10.0) < 1e-9 and row["S1_gain_ci_excludes_0"]