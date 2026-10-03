import os
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
import sys, json, time, pathlib, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
import variants as V
import learner as Lr
import learner_full as LF
import learner_matched as LM
from env import Env
from encode import Encoder

ROOT = pathlib.Path(__file__).resolve().parents[1]
N_PROB, N_REP = 50, 3
CKPTS = (0, 1000, 2000, 5000, 10000, 20000)
TRAIN_POOL, EVAL_SEED, ANNEAL = 20000, 9_500_000, 5000
PROBE_N = 20
ARMS = {  # arm -> (agent kind, kwargs, random data)
    "F": ("full", dict(), False),
    "R": ("full", dict(), True),          # random data generation + all consolidation machinery
    "RN": ("plain", dict(), True),        # random data generation, online-only update
    "NM": ("matched", dict(mode="rows"), False),    # A5: N + extra online steps, gradient rows matched to F per 200 episodes
    "NMs": ("matched", dict(mode="steps"), False),  # A5 (optional): Adam steps matched to F
    "F_nometa": ("full", dict(meta=False), False),
    "F_nodream": ("full", dict(dream=False), False),
    "F_noconcepts": ("full", dict(concepts=False), False),
}


def sched(i):
    f = min(1.0, i / ANNEAL)
    return 2.0 + (0.25 - 2.0) * f, 0.10 + (0.01 - 0.10) * f


def evaluate(agent, kind, variant, cond, seed, splits=V.TEST_SPLITS, n_prob=N_PROB):
    nat = V.natural_of(cond); res = {}
    for sp in splits:
        S1, free = [], []
        for j in range(n_prob):
            prob = V.make(variant, sp, j, cond)
            if kind == "full":
                env, enc = agent.get_env(prob)
            else:
                env = Env(prob); enc = Encoder(env)
            for r in range(N_REP):
                rng = np.random.default_rng((EVAL_SEED, seed, j, r))
                if kind == "full":
                    s, _ = agent.play(env, enc, rng, 0.25, 0.0, nat, net=agent.memory_net(), record=False, random=False)
                else:
                    s, _ = agent.play(env, enc, rng, 0.25, 0.0, nat, net=agent.memory_net(), record=False)
                S1.append(s.filled); free.append(env.free_cells)
        res[sp] = {"S1": S1, "free": free}
    return res


def probe(agent, variant, cond, seed):
    nat = V.natural_of(cond); v = []
    for j in range(PROBE_N):
        prob = V.make(variant, "dev", j, cond); env, enc = agent.get_env(prob)
        s, _ = agent.play(env, enc, np.random.default_rng((8_200_000, seed, j)), 0.25, 0.0, nat, net=agent.memory_net(), record=False, random=False)
        v.append(100.0 * s.filled / max(env.free_cells, 1))   # percent of free cells; meta thresholds were set for S1 on a 100-cell board
    return float(np.mean(v))


def run_stream(arm, variant, cond, seed, n_ep, log=None):
    kind, kw, rnd = ARMS[arm]
    nat = V.natural_of(cond)
    rng = np.random.default_rng(seed * 7919 + 13)
    agent = LF.FullAgent(seed, random=rnd, **kw) if kind == "full" else LM.MatchedAgent(seed, **kw) if kind == "matched" else Lr.Agent(seed)
    ck = sorted(set(c for c in CKPTS if c <= n_ep) | {n_ep})
    evals, train_frac, finals, sleeps_epoch = {}, [], [], []
    t0 = time.time()
    for i in range(n_ep):
        if i in ck:
            evals[i] = evaluate(agent, kind, variant, cond, seed)
            if log:
                m = np.mean([np.mean(np.array(v["S1"]) / np.array(v["free"])) for v in evals[i].values()])
                extra = f" concepts {agent.lib.keys.size} tau {agent.h['tau']:.2f}" if kind == "full" else ""
                log(f"[{arm} {variant} {cond} s{seed}] ep {i} heldout S1/free {m:.4f} {time.time()-t0:.0f}s{extra}")
        if kind == "full":
            if not agent.flags["meta"]:
                tau, eps = sched(i); agent.h["tau"], agent.h["eps"] = tau, eps
            tau, eps = agent.h["tau"], agent.h["eps"]
        else:
            tau, eps = sched(i)
        prob = V.make(variant, "train", int(rng.integers(TRAIN_POOL)), cond)
        if kind == "full":
            env, enc = agent.get_env(prob)
            s, ep = agent.play(env, enc, rng, tau, eps, nat)
            if ep is not None:
                agent.remember(ep); agent.online_step(ep)
                if agent.due():
                    sleeps_epoch.append(agent.sleep())
            if (i + 1) % 1000 == 0:
                pr = probe(agent, variant, cond, seed)
                agent.meta.end_epoch(agent, i + 1, pr, sleeps_epoch); sleeps_epoch = []
        else:
            env = Env(prob); enc = Encoder(env)
            if rnd:
                s = env.new_state()
                Xs = []
                while True:
                    cand, _ = env.candidates(s, nat)
                    if cand.size == 0: break
                    j = int(rng.integers(cand.size)); Xs.append(enc.features(s, cand[j:j+1])[0]); env.place(s, int(cand[j]))
                if Xs:
                    ep = Lr.Episode(np.array(Xs, np.float32), prob, None, (s.filled / max(env.free_cells, 1) - Lr.MU) / Lr.SD)
                    agent.online_step(ep)
            else:
                s, ep = agent.play(env, enc, rng, tau, eps, nat)
                if ep is not None:
                    agent.online_step(ep)
        train_frac.append(s.filled / max(env.free_cells, 1))
        finals.append(hash(s.occ.tobytes()))
    if n_ep not in evals:
        evals[n_ep] = evaluate(agent, kind, variant, cond, seed)
    distinct = [len(set(finals[a:a + 1000])) for a in range(0, len(finals), 1000)]
    out = {"arm": arm, "variant": variant, "cond": cond, "seed": seed, "n_ep": n_ep, "train_frac": train_frac, "distinct_per_1000": distinct,
           "evals": {str(k): v for k, v in evals.items()}, "runtime_s": time.time() - t0, "py": sys.version, "numpy": np.__version__}
    if kind == "full":
        out["meta_events"] = agent.meta.events[-200:]; out["n_meta_events"] = len(agent.meta.events); out["concepts"] = int(agent.lib.keys.size)
        out["sleep_stats_last"] = agent.sleep_stats[-5:]
    return out


def stream_path(arm, variant, cond, seed):
    return ROOT / "results" / "e_streams" / f"{arm}_{variant}_{cond}_s{seed}.json"


def job(a):
    arm, variant, cond, seed, n_ep = a
    p = stream_path(arm, variant, cond, seed)
    if p.exists():
        return a, "exists"
    p.parent.mkdir(parents=True, exist_ok=True)
    logf = open(ROOT / "results" / "e_streams_log.txt", "a")
    def log(m):
        logf.write(m + "\n"); logf.flush()
    try:
        r = run_stream(arm, variant, cond, seed, n_ep, log)
    except Exception:
        import traceback
        log(f"FAILED {a}: {traceback.format_exc()}")
        return a, "failed"
    with open(str(p) + ".tmp", "w") as fh:
        json.dump(r, fh)
    os.replace(str(p) + ".tmp", p)
    log(f"DONE {arm} {variant} {cond} s{seed} {r['runtime_s']:.0f}s")
    return a, "done"


def job_list(arms=("F", "R", "RN", "NM"), seeds=range(8), variants=("std", "hard"), n_ep=20000):
    return [(arm, v, "capped_nat", 2300 + s, n_ep) for v in variants for s in seeds for arm in arms]


if __name__ == "__main__":
    from multiprocessing import Pool
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        for arm in ("F", "R", "RN"):
            t = time.time(); r = run_stream(arm, "std", "capped_nat", 1, 1200, print); print(arm, "1200 eps %.0fs" % (time.time() - t), "meta events", r.get("n_meta_events"), "concepts", r.get("concepts"), flush=True)
        sys.exit()
    nw = int(os.environ.get("NW", "12"))
    with Pool(nw, maxtasksperchild=1) as pool:
        for a, st in pool.imap_unordered(job, job_list()):
            print(a, st, flush=True)