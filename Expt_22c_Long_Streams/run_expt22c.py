"""Expt-22b entry point (value learner, Monte-Carlo returns, organic meta-controller).
  python run_expt22b.py --workers 10 --reps 8 --abl-reps 4 --boxes 20000 --abl-boxes 10000
"""

from __future__ import annotations

import os

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from config import VARIANTS, Cfg  # noqa: E402

ABLS = ("no_meta", "no_sleep", "no_dream", "no_concepts", "td095", "badinit_meta", "badinit_fixed", "frozen")


def _worker(job):
    from stream import evaluate, run_stream
    variant, seed, n_boxes, out_dir, over = job
    cfg = Cfg()
    for k, v in over.items():
        setattr(cfg, k, v)
    out = Path(out_dir)
    logf = open(out / "progress.log", "a", buffering=1)
    log = lambda m: logf.write(f"{datetime.now():%H:%M:%S} {m}\n")
    r = run_stream(variant, seed, cfg, n_boxes, log=log)
    ag = r.pop("agent")
    tr = {}
    if variant in ("full", "no_meta", "frozen"):
        for b in cfg.transfer_budgets:
            e = evaluate(ag, cfg, cfg.transfer_boxes, b)
            tr[b] = {"S1": e["S1"], "attempts": e["attempts"]}
    r["transfer"] = tr
    if variant == "full" and seed == 100:
        with open(out / "ltm_full_seed0.pkl", "wb") as fh:
            pickle.dump({"slow": ag.slow.p, "fast": ag.fast.p, "concepts": (ag.lib.keys, ag.lib.val), "h": ag.h,
                         "hidden": ag.hidden}, fh)
    with open(out / "streams" / f"{variant}_s{seed}.pkl", "wb") as fh:
        pickle.dump(r, fh)
    log(f"DONE {variant} s{seed}: {r['runtime_s']:.0f}s held-out@{n_boxes} {float(r['evals'][n_boxes]['S1'].mean()):.2f}")
    return variant, seed


def code_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "src").glob("*.py")) + [Path(__file__)]:
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--report-only", default=None)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--abl-reps", type=int, default=4)
    ap.add_argument("--boxes", type=int, default=20_000)
    ap.add_argument("--abl-boxes", type=int, default=10_000)
    ap.add_argument("--eval-boxes", type=int, default=1200)
    ap.add_argument("--variants", default=",".join(ABLS))
    ap.add_argument("--tag", default="run")
    ap.add_argument("--seed-offset", type=int, default=100)
    ap.add_argument("--skip-tests", action="store_true")
    a = ap.parse_args()
    from report import build_report
    if a.report_only:
        build_report(Path(a.report_only), Cfg())
        return 0
    if not a.skip_tests and not a.smoke:
        rc = subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")], cwd=ROOT)
        if rc:
            return rc
    over = {"eval_boxes": a.eval_boxes}
    if a.smoke:
        over = dict(eval_boxes=60, epoch=300, probe_boxes=20, transfer_boxes=40, grow_min_box=600, grow_every_epochs=1,
                    anneal_boxes=800, checkpoints=(0, 600, 1200))
        a.reps, a.abl_reps, a.boxes, a.abl_boxes, a.tag = 2, 1, 1200, 1200, "smoke"
        a.variants = "no_meta,frozen"
    over["n_boxes"] = a.boxes
    out = ROOT / "results" / f"{datetime.now():%Y%m%d_%H%M%S}_{a.tag}"
    (out / "streams").mkdir(parents=True)
    cfg = Cfg()
    for k, v in over.items():
        setattr(cfg, k, v)
    names = [x for x in a.variants.split(",") if x]
    man = {"created": datetime.now().isoformat(timespec="seconds"), "code_hash": code_hash(), "cfg": cfg.as_dict(),
           "variants": {k: VARIANTS[k] for k in ["full"] + names}, "reps": a.reps, "abl_reps": a.abl_reps, "boxes": a.boxes,
           "abl_boxes": a.abl_boxes, "workers": a.workers, "python": sys.version, "abl_names": names}
    (out / "manifest.json").write_text(json.dumps(man, indent=2, default=str), encoding="utf-8")
    jobs = [("full", s + a.seed_offset, a.boxes, str(out), over) for s in range(a.reps)]
    for v in names:
        jobs += [(v, s + a.seed_offset, a.abl_boxes, str(out), over) for s in range(a.abl_reps)]
    print(f"output: {out}\n{len(jobs)} streams on {a.workers} workers", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(_worker, j) for j in jobs]):
            v, s = f.result()
            print(f"[{time.time()-t0:7.0f}s] finished {v} s{s}", flush=True)
    man["wall_s"] = time.time() - t0
    (out / "manifest.json").write_text(json.dumps(man, indent=2, default=str), encoding="utf-8")
    build_report(out, cfg)
    print(f"report written to {out / 'summary.md'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())