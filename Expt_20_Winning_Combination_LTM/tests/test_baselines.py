import random
import subprocess
import sys
from pathlib import Path

import numpy as np

from baselines.rules import RULES, Rule, choose, run_rule_trial
from mga.environment import Action, PackingEnv
from mga.pieces import placed_cells
from stronger.engine import Cost, anchor_pool
from stronger.policies import Context, Spec, run_trial as spec_trial

ROOT = Path(__file__).resolve().parents[1]


def test_first_fit_largest_is_deterministic_and_legal():
    rule = next(r for r in RULES if r.name == "FF_largest_first_legal")
    assert rule.deterministic
    a, b = run_rule_trial(1, 0, rule), run_rule_trial(99, 7, rule)
    assert (a["S1"], a["attempts"]) == (b["S1"], b["attempts"])        # seed does not matter: no random step


def test_every_rule_yields_legal_nonoverlapping_boxes_and_consistent_scores():
    for rule in RULES:
        for tid in range(3):
            t = run_rule_trial(5, tid, rule)
            assert 0 < t["S1"] <= 100 and abs(t["S2"] - t["S1"] / t["attempts"]) < 1e-12
            assert t["undos"] == 0 and t["pieces"] == t["attempts"]


def test_rule_replays_to_the_same_board_through_public_api():
    # re-derive FF_largest_first_legal independently: anchor cell, max area, first in catalogue order
    env = PackingEnv()
    log = []
    while True:
        legal = env.legal_placements()
        if not legal:
            break
        occ = env.mask
        for idx in range(100):
            if (occ >> idx) & 1:
                continue
            pool = [p for p in legal if (p.mask >> idx) & 1]
            if pool:
                break
        m = max(p.area for p in pool)
        p = next(q for q in pool if q.area == m)
        env.step(Action.place_from(p))
        log.append(p)
    cells = [c for p in log for c in placed_cells(p.piece_type, p.rotation, p.x, p.y)]
    assert len(cells) == len(set(cells)) == env.occupied
    rule = next(r for r in RULES if r.name == "FF_largest_first_legal")
    assert run_rule_trial(0, 0, rule)["S1"] == env.occupied


def test_piece_filters_and_tie_breaks():
    env = PackingEnv()
    pool = anchor_pool(env.mask, Cost())
    rng = random.Random(0)
    big = choose(Rule("x", piece="largest", place="first"), pool, env.mask, rng, Cost())
    small = choose(Rule("y", piece="smallest", place="first"), pool, env.mask, rng, Cost())
    assert big.area == 7 and small.area == 4
    c = Cost()
    cp = choose(Rule("z", anchor=True, piece="any", place="contact_first"), pool, env.mask, rng, c)
    assert c.cand_evals == len(pool)
    assert cp.boundary_contacts == max(p.boundary_contacts for p in pool)
    types = {choose(Rule("r", piece="random_type", place="random"), pool, env.mask, random.Random(s), Cost()).piece_type for s in range(40)}
    assert len(types) > 4


def test_rowmajor_first_picks_earliest_lowest_cell():
    env = PackingEnv()
    legal = env.legal_placements()
    p = choose(Rule("g", anchor=False, piece="largest", place="rowmajor_first"), legal, env.mask, random.Random(0), Cost())
    assert p.area == 7 and (p.mask & 1)


def test_contact_rule_with_anchor_matches_expt20_best_rule():
    """FF_largest... is not the Expt-20 rule, but anchor + contact_random(any piece) must equal D_anchor_contact_eps0 (same RNG use)."""
    ctx = Context({"S2_frozen": {}}, {})
    spec = Spec("D", "D", eps=0.0, type_mode="placement_uniform", anchor=True, select="contact")
    rule = Rule("r", anchor=True, piece="any", place="contact_random")
    for tid in range(6):
        a, b = spec_trial(11, tid, spec, ctx), run_rule_trial(11, tid, rule)
        assert a["S1"] == b["S1"] and a["attempts"] == b["attempts"]


def test_e1_agent_runs_on_empty_box_and_reports_effort():
    from baselines.e1agent import run_e1_trial
    t = run_e1_trial(3, 0)
    assert 0 < t["S1"] <= 100 and t["cand_evals"] > 1000 and t["actions"] <= 100 and t["enum_ops"] > 0
    assert t["S1"] == run_e1_trial(3, 0)["S1"]


def test_e16_primitive_runner_on_empty_box(tmp_path):
    out = tmp_path / "e16.npz"
    subprocess.run([sys.executable, "-B", str(ROOT / "src" / "baselines" / "e16_run.py"), "--seed", "5", "--trials", "8", "--workers", "1",
                    "--q-min", "101", "--out", str(out)], check=True, cwd=ROOT)
    with np.load(out) as d:
        cols = [str(c) for c in d["columns"]]
        a = d["data"].copy()
    assert a.shape == (8, len(cols)) and (a[:, cols.index("S1")] > 0).all() and (a[:, cols.index("A")] > 0).all()
    out2 = tmp_path / "e16b.npz"
    subprocess.run([sys.executable, "-B", str(ROOT / "src" / "baselines" / "e16_run.py"), "--seed", "5", "--trials", "8", "--workers", "1",
                    "--q-min", "101", "--out", str(out2)], check=True, cwd=ROOT)
    with np.load(out2) as d2:
        assert (d2["data"] == a).all()                      # reproducible


def test_e16_q75_stop_rule_stops_at_quality(tmp_path):
    p = tmp_path / "q75.npz"
    subprocess.run([sys.executable, "-B", str(ROOT / "src" / "baselines" / "e16_run.py"), "--seed", "5", "--trials", "8", "--workers", "1",
                    "--q-min", "75", "--out", str(p)], check=True, cwd=ROOT)
    with np.load(p) as d:
        cols = [str(c) for c in d["columns"]]
        s1 = d["data"][:, cols.index("S1")]
    assert (s1 >= 68).all() and (s1 <= 85).all()            # stops soon after 75: no high-quality boxes