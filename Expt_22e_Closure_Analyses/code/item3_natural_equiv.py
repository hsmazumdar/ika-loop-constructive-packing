"""Item 3 check: is the learner's natural filter (feat.step_features) identical to engine.natural_candidates (used by uniform/hand/V21)?
Compared on every decision state visited by uniform-random, hand-rule and 22c-learner play (300 episodes each)."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import D22C, EVAL_SEED, RUN
import item2_piece_P as P2
import engine as E
import feat as F

def check_state(b):
    c1, _ = E.natural_candidates(b, 0)
    r = F.step_features(b, 14)
    c2 = np.empty(0, np.int64) if r is None else r[0]
    return np.array_equal(np.sort(c1), np.sort(c2)), c1.size

tot = bad = 0
by = {}
ag, cfg = P2.load_agent(D22C / "ltm_full_seed0.pkl")
for name in ("uniform", "hand", "learner"):
    n_states = n_bad = 0
    for j in range(300):
        rng = np.random.default_rng(EVAL_SEED + j)
        b = E.Box(budget=14)
        while True:
            ok, k = check_state(b)
            n_states += 1; n_bad += (not ok)
            if k == 0:
                break
            c, f = E.natural_candidates(b, 0)
            if name == "uniform":
                i = c[rng.integers(c.size)]
            elif name == "hand":
                sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * E.AREA[c] + rng.random(c.size) * 0.5
                i = c[int(np.argmax(sc))]
            else:
                i = c[rng.integers(c.size)] if j % 2 else c[int(np.argmax(f["contact"] + E.AREA[c]))]
            b.place(int(i))
    by[name] = dict(states=n_states, mismatching_states=n_bad)
# learner-driven trajectories
n_states = n_bad = 0
for j in range(300):
    bx, _ = ag.play(np.random.default_rng(EVAL_SEED + j), cfg.tau_eval, 0.0, 14, net=ag.memory_net(), record=True)
    b = E.Box(budget=14)
    for i in bx.placed:
        ok, k = check_state(b); n_states += 1; n_bad += (not ok); b.place(int(i))
    ok, k = check_state(b); n_states += 1; n_bad += (not ok)
by["learner_trajectories"] = dict(states=n_states, mismatching_states=n_bad)
json.dump(by, open(RUN / "item3_natural_filter_equivalence.json", "w"), indent=1)
print(by)
