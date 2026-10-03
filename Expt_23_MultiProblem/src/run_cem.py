import os
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
import sys, json, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
from multiprocessing import Pool
import variants as V, baselines as B

ROOT = pathlib.Path(__file__).resolve().parents[1]

def job(a):
    variant, cond = a
    out = ROOT / "results" / "cem" / f"cem_{variant}_{cond}.json"
    if out.exists():
        return a, "exists"
    t = time.time()
    probs = [V.make(variant, "train", j, cond) for j in range(60)]
    r = B.cem_tune_hand(probs, natural=V.natural_of(cond), seed=2300)
    r.update(variant=variant, cond=cond, seconds=time.time() - t, train_problems="train[0:60]")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, indent=1))
    return a, r["w"]

if __name__ == "__main__":
    jobs = [(v, c) for v in V.VARIANTS for c in V.CONDS]
    with Pool(8) as p:
        for a, w in p.imap_unordered(job, jobs):
            print(a, w, flush=True)