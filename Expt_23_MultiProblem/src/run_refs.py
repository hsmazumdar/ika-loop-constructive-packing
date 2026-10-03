import os
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
import sys, json, time, pathlib, csv
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
from multiprocessing import Pool
import variants as V, baselines as B
from env import Env

ROOT = pathlib.Path(__file__).resolve().parents[1]
N_PROB = 50
EVAL_SEED = 9_300_000   # uniform / hand / CEM-hand evaluation episodes (disjoint from CEM training seeds)
COLS = ["variant", "cond", "split", "index", "pid", "H", "W", "k", "obstacles", "free", "max_area", "uniform", "hand", "cemhand",
        "beam64_s0", "beam64_s1", "beam64_s2", "rollout_beam", "hand_mean60", "ref", "t_beam", "t_rollout"]

def cem_w(variant, cond):
    f = ROOT / "results" / "cem" / f"cem_{variant}_{cond}.json"
    return tuple(json.loads(f.read_text())["w"]) if f.exists() else None

def unit(a):
    variant, cond, split, j = a
    prob = V.make(variant, split, j, cond)
    nat = V.natural_of(cond)
    e = Env(prob)
    n = 100
    uni = np.mean([B.run_uniform(e, np.random.default_rng((EVAL_SEED, j, k)), nat) for k in range(n)])
    hand = np.mean([B.run_hand(e, np.random.default_rng((EVAL_SEED, j, k)), nat) for k in range(n)])
    hand60 = np.mean([B.run_hand(e, np.random.default_rng((EVAL_SEED + 1, j, k)), nat) for k in range(60)])
    w = cem_w(variant, cond)
    cem = np.mean([B.run_hand_w(e, np.random.default_rng((EVAL_SEED, j, k)), nat, w) for k in range(n)]) if w else float("nan")
    t = time.time(); b = [B.run_beam(e, width=64, natural=nat, seed=s)[0] for s in range(3)]; tb = (time.time() - t) / 3
    t = time.time(); rb = B.run_beam_rollout(e, 8, 6, 2, natural=nat)[0]; trb = time.time() - t
    ref = max(max(b), rb, hand60)
    return [variant, cond, split, j, prob.pid, prob.H, prob.W, len(prob.catalogue), len(prob.blocked), e.free_cells, e.max_area,
            round(uni, 3), round(hand, 3), round(cem, 3), b[0], b[1], b[2], rb, round(hand60, 3), round(ref, 3), round(tb, 2), round(trb, 2)]

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "refs"   # 'refs' (all) or 'cem_only'
    outdir = ROOT / "results" / "refs"
    outdir.mkdir(parents=True, exist_ok=True)
    groups = [(v, c, s) for v in V.VARIANTS for c in V.CONDS for s in V.TEST_SPLITS]
    groups += [("std", c, "legacy") for c in V.CONDS]
    with Pool(int(os.environ.get("NW", "12"))) as pool:
        for (v, c, s) in groups:
            f = outdir / f"refs_{v}_{c}_{s}.csv"
            if f.exists():
                continue
            idx = list(range(N_PROB)) if s != "legacy" else [0]
            t = time.time()
            rows = pool.map(unit, [(v, c, s, j) for j in idx])
            with open(str(f) + ".tmp", "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(COLS); w.writerows(rows)
            os.replace(str(f) + ".tmp", f)
            print(f"{v} {c} {s}: {len(rows)} problems {time.time()-t:.0f}s", flush=True)