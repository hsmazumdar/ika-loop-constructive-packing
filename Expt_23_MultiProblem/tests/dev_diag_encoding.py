"""DEV-only diagnostic (never reports test splits): can the problem-agnostic patch encoding learn at all with online MC updates?
Compares update intensity (steps per episode, lr) for the plain afterstate-MC learner on `dev` problems."""
import os
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"): os.environ[k]="1"
import sys, time, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import variants as V, learner as Lr, baselines as B
from env import Env
from encode import Encoder
steps, lr, n_ep = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
variant = sys.argv[4] if len(sys.argv) > 4 else "std"
ag = Lr.Agent(0, lr=lr)
ag_rng = np.random.default_rng(5)
def heldout():
    fr = []; un = []
    for j in range(20):
        prob = V.make(variant, "dev", j, "capped_nat"); env = Env(prob); enc = Encoder(env)
        for r in range(2):
            s, _ = ag.play(env, enc, np.random.default_rng((77, j, r)), 0.25, 0.0, True, net=ag.memory_net(), record=False)
            fr.append(s.filled / env.free_cells)
            un.append(B.run_uniform(env, np.random.default_rng((78, j, r)), True) / env.free_cells)
    return float(np.mean(fr)), float(np.mean(un))
t0 = time.time(); out = []
for i in range(n_ep + 1):
    if i % 500 == 0:
        h, u = heldout(); out.append((i, round(h, 4), round(u, 4))); print(f"steps={steps} lr={lr} {variant} ep {i} dev frac {h:.4f} (uniform {u:.4f}) {time.time()-t0:.0f}s", flush=True)
    if i == n_ep: break
    f = min(1.0, i / 5000); tau, eps = 2.0 + (0.25 - 2.0) * f, 0.10 + (0.01 - 0.10) * f
    prob = V.make(variant, "train", int(ag_rng.integers(20000)), "capped_nat"); env = Env(prob); enc = Encoder(env)
    s, ep = ag.play(env, enc, ag_rng, tau, eps, True)
    if ep is not None:
        y = np.full(len(ep.X), ep.y, np.float32)
        for _ in range(steps):
            ag.fast.step(ep.X, y, ep.w, lr)