"""Expt-22d entry point: long-horizon ablations (32k boxes) + saturation run (full, 60k boxes).
  python run_expt22d.py --workers 26 --long-reps 6 --long-boxes 60000 --abl-reps 4 --abl-boxes 32000
  python run_expt22d.py --report-only results/<run>      (safe to run while streams are still running: uses partial snapshots)
"""
from __future__ import annotations

import os

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")

import argparse
import hashlib
import json
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from config import VARIANTS, Cfg  # noqa: E402

ABLS = ("no_meta", "no_meta_matched_floor", "no_dream", "no_concepts", "no_sleep")
SEED_LONG, SEED_ABL = 300, 200  # Expt-22c used seeds 100-111 (distinct)


def _worker(job):
    from stream import evaluate, run_stream
    variant, seed, n_boxes, out_dir, over = job
    cfg = Cfg()
    for k, v in over.items():
        setattr(cfg, k, v)
    out = Path(out_dir)
    logf = open(out / "progress.log", "a", buffering=1)
    log = lambda m: logf.write(f"{datetime.now():%H:%M:%S} {m}\n")
    pdir = out / "streams_partial"

    def on_eval(snap):
        tmp = pdir / f"{variant}_s{seed}.tmp"
        with open(tmp, "wb") as fh:
            pickle.dump(snap, fh)
        os.replace(tmp, pdir / f"{variant}_s{seed}.pkl")
        log(f"CKPT {variant} s{seed} box {snap['n_boxes']} held-out {float(snap['evals'][snap['n_boxes']]['S1'].mean()):.2f}")

    r = run_stream(variant, seed, cfg, n_boxes, log=log, on_eval=on_eval)
    ag = r.pop("agent")
    tr = {}
    if variant in ("full", "no_meta", "no_meta_matched_floor"):
        for b in cfg.transfer_budgets:
            e = evaluate(ag, cfg, cfg.transfer_boxes, b)
            tr[b] = {"S1": e["S1"], "attempts": e["attempts"]}
    r["transfer"] = tr
    with open(out / "streams" / f"{variant}_s{seed}.tmp", "wb") as fh:
        pickle.dump(r, fh)
    os.replace(out / "streams" / f"{variant}_s{seed}.tmp", out / "streams" / f"{variant}_s{seed}.pkl")
    log(f"DONE {variant} s{seed}: {r['runtime_s']:.0f}s held-out@{n_boxes} {float(r['evals'][n_boxes]['S1'].mean()):.2f}")
    return variant, seed


def code_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "src").glob("*.py")) + [Path(__file__)]:
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", default=None)
    ap.add_argument("--workers", type=int, default=26)
    ap.add_argument("--long-reps", type=int, default=6)
    ap.add_argument("--long-boxes", type=int, default=60_000)
    ap.add_argument("--abl-reps", type=int, default=4)
    ap.add_argument("--abl-boxes", type=int, default=32_000)
    ap.add_argument("--eval-boxes", type=int, default=1200)
    ap.add_argument("--variants", default=",".join(ABLS))
    ap.add_argument("--tag", default="run")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--resume-dir", default=None, help="re-run only streams without a final pickle in <dir>/streams (cut streams restart from box 0)")
    a = ap.parse_args()
    from report import build_report
    if a.report_only:
        build_report(Path(a.report_only), Cfg())
        return 0
    over = {"eval_boxes": a.eval_boxes}
    if a.smoke:
        over = dict(eval_boxes=40, epoch=300, probe_boxes=20, transfer_boxes=30, grow_min_box=600, grow_every_epochs=1,
                    anneal_boxes=800, checkpoints=(0, 600, 1200))
        a.long_reps, a.abl_reps, a.long_boxes, a.abl_boxes, a.tag = 1, 1, 1200, 1200, "smoke"
        a.variants = "no_meta_matched_floor,no_sleep"
        a.workers = 3
    over["n_boxes"] = a.long_boxes
    if a.resume_dir:
        out = Path(a.resume_dir).resolve()
    else:
        out = ROOT / "results" / f"{datetime.now():%Y%m%d_%H%M%S}_{a.tag}"
        (out / "streams").mkdir(parents=True)
        (out / "streams_partial").mkdir()
    cfg = Cfg()
    for k, v in over.items():
        setattr(cfg, k, v)
    names = [x for x in a.variants.split(",") if x]
    man = {"created": datetime.now().isoformat(timespec="seconds"), "code_hash": code_hash(), "cfg": cfg.as_dict(),
           "variants": {k: VARIANTS[k] for k in ["full"] + names}, "long_reps": a.long_reps, "abl_reps": a.abl_reps,
           "long_boxes": a.long_boxes, "abl_boxes": a.abl_boxes, "workers": a.workers, "python": sys.version, "abl_names": names,
           "seed_long": SEED_LONG, "seed_abl": SEED_ABL, "ref_run_22c": "../Expt_22c_Long_Streams/results/20261001_044425_run"}
    man_name = "manifest_rerun.json" if a.resume_dir else "manifest.json"
    (out / man_name).write_text(json.dumps(man, indent=2, default=str), encoding="utf-8")
    jobs = [("full", s + SEED_LONG, a.long_boxes, str(out), over) for s in range(a.long_reps)]  # long streams first
    for v in names:
        jobs += [(v, s + SEED_ABL, a.abl_boxes, str(out), over) for s in range(a.abl_reps)]
    if a.resume_dir:
        jobs = [j for j in jobs if not (out / "streams" / f"{j[0]}_s{j[1]}.pkl").exists()]
        print("resume: rerunning", [f"{j[0]}_s{j[1]}" for j in jobs], flush=True)
    print(f"output: {out}\n{len(jobs)} streams on {a.workers} workers (pid {os.getpid()})", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(_worker, j) for j in jobs]):
            v, s = f.result()
            print(f"[{time.time()-t0:7.0f}s] finished {v} s{s}", flush=True)
    man["wall_s"] = time.time() - t0
    (out / man_name).write_text(json.dumps(man, indent=2, default=str), encoding="utf-8")
    try:
        build_report(out, cfg)
    except Exception as e:  # report is re-run separately with --report-only
        print('report failed:', repr(e), flush=True)
    print(f"report written to {out / 'summary.md'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

