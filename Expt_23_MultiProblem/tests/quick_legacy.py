import sys, time, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import generator as G, baselines as B
from env import Env
p = G.make_problem("legacy", 0)
e = Env(p)
print("legacy placements:", e.N, "(Expt-01 catalogue has 3636)")
t=time.time(); u = B.evaluate_policy(p, B.run_uniform, 300, 7_700_000); print("uniform  n=300 mean %.3f  %.1fs" % (u.mean(), time.time()-t))
t=time.time(); h = B.evaluate_policy(p, B.run_hand, 300, 7_700_000); print("hand     n=300 mean %.3f  %.1fs" % (h.mean(), time.time()-t))
for w in (4, 8, 16):
    t=time.time(); s, nodes = B.run_beam(e, width=w); print("beam w=%d S1=%d nodes=%d %.1fs" % (w, s, nodes, time.time()-t))