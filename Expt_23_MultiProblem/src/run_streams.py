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
N_PROB, N_REP = 50, 3
CKPTS = (0, 1000, 2000, 5000, 10000, 20000)
TRAIN_POOL = 20000          # train problem indices drawn uniformly from [0, TRAIN_POOL)
EVAL_SEED = 9_500_000
ANNEAL = 5000


def sched(i):
    f = min(1.0, i / ANNEAL)
    return 2.0 + (0.25 - 2.0) * f, 0.10 + (0.01 - 0.10) * f


def evaluate(arm, agent, variant, cond, seed):
    nat = V.natural_of(cond)
    res = {}
    for sp in V.TEST_SPLITS:
        rows = {"S1": [], "free": [], "S1_greedy": []}
        for j in range(N_PROB):
            prob = V.make(variant, sp, j, cond); env = Env(prob); enc = Encoder(env)
            for r in range(N_REP):
                rng = np.random.default_rng((EVAL_SEED, seed, j, r))
                if arm == "N":
                    s, _ = agent.play(env, enc, rng, 0.25, 0.0, nat, net=agent.memory_net(), record=False)
                    rows["S1"].append(s.filled)
                elif arm == "DQN":
                    s, _ = NN.rollout(env, enc, agent.score, NN.softmax_select(0.25, 0.0), rng, nat)
                    rows["S1"].append(s.filled)
                else:  # PPO: sample at temperature 1 (main) and argmax (secondary)
                    s, _ = NN.rollout(env, enc, agent.score, NN.sample_select, rng, nat)
                    rows["S1"].append(s.filled)
                    s2, _ = NN.rollout(env, enc, agent.score, NN.greedy_select, rng, nat)
                    rows["S1_greedy"].append(s2.filled)
                rows["free"].append(env.free_cells)
        res[sp] = {k: v for k, v in rows.items() if v}
    return res


def run_stream(arm, variant, cond, seed, n_ep, log=None):
    nat = V.natural_of(cond)
    rng = np.random.default_rng(seed * 7919 + 13)
    if arm == "N":
        agent = Lr.Agent(seed)
    elif arm == "DQN":
        agent = NN.DQN(seed)
    else:
        agent = NN.PPO(seed)
    ck = sorted(set(c for c in CKPTS if c <= n_ep) | {n_ep})
    evals, train_y = {}, []
    t0 = time.time()
    for i in range(n_ep):
        if i in ck:
            evals[i] = evaluate(arm, agent, variant, cond, seed)
            if log:
                m = np.mean([np.mean(np.array(v["S1"]) / np.array(v["free"])) for v in evals[i].values()])
                log(f"[{arm} {variant} {cond} s{seed}] ep {i} heldout S1/free {m:.4f} {time.time()-t0:.0f}s")
        tau, eps = sched(i)
        prob = V.make(variant, "train", int(rng.integers(TRAIN_POOL)), cond)
        env = Env(prob); enc = Encoder(env)
        if arm == "N":
            s, ep = agent.play(env, enc, rng, tau, eps, nat)
            if ep is not None:
                agent.online_step(ep)
        else:
            sel = NN.softmax_select(tau, eps) if arm == "DQN" else NN.sample_select
            s, steps = NN.rollout(env, enc, agent.score, sel, rng, nat)
            if steps:
                agent.observe(steps, (s.filled / max(env.free_cells, 1) - Lr.MU) / Lr.SD)
        train_y.append(s.filled / max(env.free_cells, 1))
    if n_ep not in evals:
        evals[n_ep] = evaluate(arm, agent, variant, cond, seed)
    return {"arm": arm, "variant": variant, "cond": cond, "seed": seed, "n_ep": n_ep, "train_frac": train_y, "evals": {str(k): v for k, v in evals.items()},
            "runtime_s": time.time() - t0, "py": sys.version, "numpy": np.__version__}


def stream_path(arm, variant, cond, seed):
    return ROOT / "results" / "streams" / f"{arm}_{variant}_{cond}_s{seed}.json"


def job(a):
    arm, variant, cond, seed, n_ep = a
    p = stream_path(arm, variant, cond, seed)
    try:  # Amendment A4: jobs listed in results/skip_jobs.txt (not yet started when listed) are skipped
        sk = (ROOT / "results" / "skip_jobs.txt").read_text().split("\n")
    except Exception:
        sk = []
    if f"{arm} {variant} {cond} {seed}" in [x.strip() for x in sk]:
        return a, "skipped"
    if p.exists():
        return a, "exists"
    p.parent.mkdir(parents=True, exist_ok=True)
    logf = open(ROOT / "results" / "streams_log.txt", "a")
    def log(m):
        logf.write(m + "\n"); logf.flush()
    try:
        r = run_stream(arm, variant, cond, seed, n_ep, log)
    except Exception as ex:
        import traceback
        log(f"FAILED {a}: {traceback.format_exc()}")
        return a, "failed"
    tmp = str(p) + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(r, fh)
    os.replace(tmp, p)
    log(f"DONE {arm} {variant} {cond} s{seed} {r['runtime_s']:.0f}s")
    return a, "done"


def job_list():
    jobs = []
    for variant in ("std", "hard"):
        for seed in range(8):
            for arm in ("N", "DQN", "PPO"):
                jobs.append((arm, variant, "capped_nat", 2300 + seed, 20000))
    for cond in ("capped_any", "unc_nat", "unc_any"):
        for seed in range(6):
            for arm in ("N", "DQN", "PPO"):
                jobs.append((arm, "std", cond, 2300 + seed, 10000))
    return jobs


if __name__ == "__main__":
    from multiprocessing import Pool
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        for arm in ("N", "DQN", "PPO"):
            t = time.time(); r = run_stream(arm, "std", "capped_nat", 1, 300, print); print(arm, "300 eps total %.0fs" % (time.time() - t))
        sys.exit()
    nw = int(os.environ.get("NW", "12"))
    jobs = job_list()
    with Pool(nw, maxtasksperchild=1) as pool:
        for a, st in pool.imap_unordered(job, jobs):
            print(a, st, flush=True)