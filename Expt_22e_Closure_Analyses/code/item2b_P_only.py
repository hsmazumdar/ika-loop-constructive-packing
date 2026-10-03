"""Item 2 add-on (modest simulation, 1,200 episodes each, same seeds/task): how much of S1 is piece CHOICE (use P) vs spatial PLACEMENT?
  P_only_uniform_natural : always choose a P placement when one exists (uniformly among natural P placements), else uniform natural
  P_only_contact_greedy  : same, but among P placements pick max contact (random tie)
  P_only_hand_score      : P placements only, hand-rule score (contact - 3*holes - notches [+ noise]) - area term constant
Pure references; none of these is used by the learner."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import EVAL_SEED, RUN, write_csv
import item2_piece_P as P2
import engine as E

PID, N, BUD = P2.PID, P2.N, P2.BUD

def run(mode):
    out = []
    for j in range(N):
        rng = np.random.default_rng(EVAL_SEED + j)
        b = E.Box(budget=BUD)
        while True:
            c, f = E.natural_candidates(b, 0)
            if c.size == 0:
                break
            m = E.PTYPE[c] == PID
            if m.any():
                c = c[m]; f = {k: v[m] for k, v in f.items()}
            if mode == "P_only_uniform_natural":
                i = c[rng.integers(c.size)]
            elif mode == "P_only_contact_greedy":
                i = c[int(np.argmax(f["contact"] + rng.random(c.size) * 0.5))]
            else:
                i = c[int(np.argmax(f["contact"] - 3.0 * f["p1"] - f["n3"] + rng.random(c.size) * 0.5))]
            b.place(int(i))
        out.append(b)
    return out

rows = []
for mode in ("P_only_uniform_natural", "P_only_contact_greedy", "P_only_hand_score"):
    r, s, p = P2.stats_of(run(mode), mode); rows.append(r); print(mode, round(r["S1"], 2), round(r["mean_P_per_box"], 2), flush=True)
write_csv(RUN / "item2b_P_only_baselines.csv", rows)
