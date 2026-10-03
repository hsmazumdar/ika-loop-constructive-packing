"""Item 2: piece-P usage / piece area for (a) uniform natural, (b) hand contact/hole/area rule, (c) learner frozen memories.
All on the same 1,200 held-out episodes (rng seeds 7,700,000+j) and the same 14-piece natural-placing task.
Baseline functions replicate Expt_22d/src/learner_ref.py and Expt_21/src/learner.py::hand_box RNG usage exactly; the script
asserts that S1 reproduces learner_ref's values before reporting anything."""
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import D21, D22B, D22C, D22D, EVAL_SEED, RUN, SRC22D, ld, streams, write_csv
sys.path.insert(0, str(SRC22D))
import engine as E  # noqa: E402
from config import VARIANTS, Cfg  # noqa: E402
from learner_ref import hand_ref, uniform_ref  # noqa: E402
from agent import Agent  # noqa: E402
from net import MLP  # noqa: E402
import feat as F  # noqa: E402

PID = E.TYPE_ID["P"]
N = 1200
BUD = 14


def stats_of(boxes, tag, n_eval=None):
    s1 = np.array([b.s1 for b in boxes]); n = np.array([b.n for b in boxes])
    nP = np.array([sum(1 for t in b.types if t == PID) for b in boxes])
    area = s1 / n
    usedP = nP > 0
    r = dict(policy=tag, n_boxes=len(boxes), S1=s1.mean(), mean_pieces=n.mean(), mean_piece_area=area.mean(),
             area_pooled=s1.sum() / n.sum(), frac_boxes_with_P=usedP.mean(), mean_P_per_box=nP.mean(),
             mean_P_given_used=nP[usedP].mean() if usedP.any() else float("nan"), max_P=int(nP.max()),
             frac_boxes_2plusP=(nP >= 2).mean(),
             S1_P_used=s1[usedP].mean() if usedP.any() else float("nan"), n_P_used=int(usedP.sum()),
             S1_P_not_used=s1[~usedP].mean() if (~usedP).any() else float("nan"), n_P_not_used=int((~usedP).sum()),
             frac_S1_ge_90=(s1 >= 90).mean(), frac_cells_in_P=(7 * nP).sum() / s1.sum())
    for k in range(0, 14):
        sel = nP == k
        r[f"n_boxes_P={k}"] = int(sel.sum()); r[f"S1_P={k}"] = s1[sel].mean() if sel.any() else float("nan")
    return r, s1, nP


def uniform_boxes(n):
    out = []
    for j in range(n):
        rng = np.random.default_rng(EVAL_SEED + j)
        b = E.Box(budget=BUD)
        while True:
            c, _ = E.natural_candidates(b, 0)
            if c.size == 0:
                break
            b.place(int(c[rng.integers(c.size)]))
        out.append(b)
    return out


def hand_boxes(n):
    out = []
    for j in range(n):
        rng = np.random.default_rng(EVAL_SEED + j)
        b = E.Box(budget=BUD)
        while True:
            c, f = E.natural_candidates(b, 0)
            if c.size == 0:
                break
            sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * E.AREA[c] + rng.random(c.size) * 0.5
            b.place(int(c[int(np.argmax(sc))]))
        out.append(b)
    return out


def load_agent(mem_path, seed=0):
    m = ld(mem_path)
    cfg = Cfg(); cfg.eval_boxes = N
    ag = Agent(cfg, VARIANTS["full"], seed, hidden=m["hidden"])
    ag.slow = MLP(F.D, m["hidden"], np.random.default_rng(0)); ag.slow.p = {k: v.copy() for k, v in m["slow"].items()}
    ag.fast = MLP(F.D, m["hidden"], np.random.default_rng(0)); ag.fast.p = {k: v.copy() for k, v in m["fast"].items()}
    ag.lib.keys, ag.lib.val = m["concepts"]
    return ag, cfg


def learner_boxes(ag, cfg, n):
    out = []
    for j in range(n):
        b, _ = ag.play(np.random.default_rng(EVAL_SEED + j), cfg.tau_eval, 0.0, BUD, net=ag.memory_net(), record=False)
        out.append(b)
    return out


if __name__ == "__main__":
    rows, per_box = [], {}
    cfg = Cfg(); cfg.eval_boxes = N
    # ---- reference policies on 1,200 boxes, with reproduction checks against the saved reference functions
    ub = uniform_boxes(N)
    ref_u = uniform_ref(cfg, BUD, N)["S1"]
    assert np.array_equal(ref_u, np.array([b.s1 for b in ub])), "uniform replication differs from learner_ref.uniform_ref"
    hb = hand_boxes(N)
    ref_h = hand_ref(cfg, BUD, N)
    assert np.array_equal(ref_h, np.array([b.s1 for b in hb])), "hand replication differs from learner_ref.hand_ref"
    r, s, p = stats_of(ub, "uniform natural (1200)"); rows.append(r); per_box["uniform"] = (s, p)
    r, s, p = stats_of(hb, "hand contact/hole/area rule (1200)"); rows.append(r); per_box["hand"] = (s, p)
    h1000 = ref_h[:1000].mean()
    print("hand S1 on 1200:", ref_h.mean(), "on first 1000 (the 89.61 convention):", h1000, "uniform 1200:", ref_u.mean())
    meta = dict(hand_S1_1200=float(ref_h.mean()), hand_S1_first1000=float(h1000), uniform_S1_1200=float(ref_u.mean()),
                uniform_S1_first1000=float(ref_u[:1000].mean()), replication_asserts="passed")
    # ---- learner: stored memories (22b seed0 @20k, 22c seed100 @32k) and re-run 22d memories (if present)
    mems = [("22b full s0 @20k boxes", D22B / "ltm_full_seed0.pkl", D22B / "streams" / "full_s0.pkl", 20000),
            ("22c full s100 @32k boxes", D22C / "ltm_full_seed0.pkl", D22C / "streams" / "full_s100.pkl", 32000)]
    for s in range(300, 306):
        mp = RUN / "memory_reruns" / f"full_s{s}_final_memory.pkl"
        if mp.exists():
            mems.append((f"22d full s{s} @60k boxes (rerun, saved memory)", mp, RUN / "memory_reruns" / f"full_s{s}_stream.pkl", 60000))
    for name, mp, sp, k in mems:
        ag, c = load_agent(mp)
        lb = learner_boxes(ag, c, N)
        saved = ld(sp)["evals"][k]["S1"]
        mine = np.array([b.s1 for b in lb])
        same = bool(np.array_equal(saved, mine))
        r, s_, p_ = stats_of(lb, name); r["reproduces_saved_heldout_exactly"] = same
        r["saved_heldout_S1"] = float(saved.mean()); r["n_boxes_differing_from_saved"] = int((saved != mine).sum())
        rows.append(r); per_box[name] = (s_, p_)
        print(name, "S1", r["S1"], "saved", saved.mean(), "exact", same, "P frac", r["frac_boxes_with_P"], flush=True)
    write_csv(RUN / "item2_piece_P_usage.csv", rows)
    json.dump(meta, open(RUN / "item2_meta.json", "w"), indent=1)
    np.savez_compressed(RUN / "item2_per_box.npz", **{f"{k}_S1": v[0] for k, v in per_box.items()}, **{f"{k}_nP": v[1] for k, v in per_box.items()})
