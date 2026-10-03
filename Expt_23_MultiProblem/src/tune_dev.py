"""DQN/PPO tuning on the DEV split only (DESIGN.md amendment A6). Usage: python tune_dev.py DQN|PPO. One factor at a time from the default.
Score = mean S1/free over dev problems 0..29 (1 rep) after 3,000 training episodes (10 problems at 1,000)."""
import os
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
import sys, json, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
import variants as V
import learner as Lr
import nn_agents as NN
from env import Env
from encode import Encoder

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED, N_EP, TRAIN_POOL, ANNEAL = 5100, 3000, 20000, 5000
CFG = {
    "DQN": [("default", {}), ("lr1e-3", dict(lr=1e-3)), ("lr2.5e-4", dict(lr=2.5e-4)), ("updates8", dict(updates=8))],
    "PPO": [("default", {}), ("lr1e-3", dict(lr=1e-3)), ("lr1.5e-4", dict(lr=1.5e-4)), ("per_update8", dict(per_update=8)), ("epochs4", dict(epochs=4))],
}


def sched(i):
    f = min(1.0, i / ANNEAL)
    return 2.0 + (0.25 - 2.0) * f, 0.10 + (0.01 - 0.10) * f


def dev_score(arm, agent, n):
    out = []
    for j in range(n):
        prob = V.make("std", "dev", j, "capped_nat"); env = Env(prob); enc = Encoder(env)
        rng = np.random.default_rng((8_100_000, j))
        sel = NN.softmax_select(0.25, 0.0) if arm == "DQN" else NN.sample_select
        s, _ = NN.rollout(env, enc, agent.score, sel, rng, True)
        out.append(s.filled / env.free_cells)
    return float(np.mean(out))


def run(arm, name, kw, log):
    agent = NN.DQN(SEED, **kw) if arm == "DQN" else NN.PPO(SEED, **kw)
    rng = np.random.default_rng(SEED * 7919 + 13); t0 = time.time(); res = {"arm": arm, "cfg": name, "kw": kw}
    for i in range(N_EP + 1):
        if i == 1000:
            res["dev_1000_first10"] = dev_score(arm, agent, 10)
        if i == N_EP:
            res["dev_3000"] = dev_score(arm, agent, 30); break
        tau, eps = sched(i)
        prob = V.make("std", "train", int(rng.integers(TRAIN_POOL)), "capped_nat"); env = Env(prob); enc = Encoder(env)
        sel = NN.softmax_select(tau, eps) if arm == "DQN" else NN.sample_select
        s, steps = NN.rollout(env, enc, agent.score, sel, rng, True)
        if steps:
            agent.observe(steps, (s.filled / max(env.free_cells, 1) - Lr.MU) / Lr.SD)
    res["runtime_s"] = time.time() - t0
    log(json.dumps(res))
    return res


if __name__ == "__main__":
    arm = sys.argv[1]
    d = ROOT / "results" / "tune"; d.mkdir(parents=True, exist_ok=True)
    f = open(d / f"tune_{arm}.jsonl", "a")
    def log(m):
        f.write(m + "\n"); f.flush()
    for name, kw in CFG[arm]:
        run(arm, name, kw, log)