"""Item 3 add-on: V21 code path vs Expt-22 reference code path on the same evaluation seeds.
Run as:  python item3_v21_vs_22_refs.py v21   |   python item3_v21_vs_22_refs.py v22   (separate processes: both src folders define modules named engine/learner...)"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import EVAL_SEED, RUN, SRC21, SRC22D
which = sys.argv[1]
N = 2000
if which == "v21":
    sys.path.insert(0, str(SRC21))
    from learner import play_box, hand_box
    u = np.array([play_box(None, np.random.default_rng(EVAL_SEED + j), 0.3, 0.0, budget=14).s1 for j in range(N)])
    h = np.array([hand_box(np.random.default_rng(EVAL_SEED + j), 14).s1 for j in range(N)])
else:
    sys.path.insert(0, str(SRC22D))
    from config import Cfg
    from learner_ref import hand_ref, uniform_ref
    c = Cfg(); u = uniform_ref(c, 14, N)["S1"]; h = hand_ref(c, 14, N)
np.savez(RUN / f"item3_refs_{which}.npz", uniform=u, hand=h)
out = {k: dict(mean_2000=float(v.mean()), mean_first1200=float(v[:1200].mean()), mean_first1000=float(v[:1000].mean())) for k, v in (("uniform", u), ("hand", h))}
print(which, json.dumps(out))
