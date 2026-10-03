import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import D22C, ld
import item2_piece_P as P2
ag, cfg = P2.load_agent(D22C / "ltm_full_seed0.pkl")
lb = P2.learner_boxes(ag, cfg, 1200)
mine = np.array([b.s1 for b in lb]); saved = ld(D22C/"streams"/"full_s100.pkl")["evals"][32000]["S1"]
print("OMP1 check 22c s100: differing episodes", int((mine!=saved).sum()), "mean", mine.mean(), saved.mean())
