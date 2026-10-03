"""Expt-22e helper: re-run ONE Expt-22d `full` stream (same code, same seed) for 60k boxes and SAVE the final agent
(slow/LTM net, fast net, concept library, hyperparameters) because the Expt-22d run did not keep final memories.
Uses the unmodified Expt_22d src/ (imported in place; hash-identical).  Usage: python rerun_full_for_memory.py <seed> <outdir>"""
import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
import pickle, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Expt_22d_Long_Ablations_Saturation" / "src"
sys.path.insert(0, str(SRC))
from config import Cfg  # noqa: E402
from stream import run_stream  # noqa: E402

seed, out = int(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
cfg = Cfg()
cfg.eval_boxes = 1200          # as in Expt-22d
cfg.n_boxes = 60000
logf = open(out / "progress.log", "a", buffering=1)
log = lambda m: logf.write(f"{datetime.now():%H:%M:%S} {m}\n")
def on_eval(ag, snap):
    log(f"CKPT full s{seed} box {snap['n_boxes']} held-out {float(snap['evals'][snap['n_boxes']]['S1'].mean()):.2f}")
r = None
def _on_eval(snap):
    on_eval(None, snap)
t0 = time.time()
r = run_stream("full", seed, cfg, 60000, log=log, on_eval=_on_eval)
ag = r.pop("agent")
mem = {"slow": ag.slow.p, "fast": ag.fast.p, "concepts": (ag.lib.keys, ag.lib.val), "h": ag.h, "hidden": ag.hidden}
with open(out / f"full_s{seed}_final_memory.pkl", "wb") as fh:
    pickle.dump(mem, fh)
with open(out / f"full_s{seed}_stream.pkl", "wb") as fh:
    pickle.dump(r, fh)
log(f"DONE full s{seed}: {r['runtime_s']:.0f}s held-out@60000 {float(r['evals'][60000]['S1'].mean()):.2f}")
