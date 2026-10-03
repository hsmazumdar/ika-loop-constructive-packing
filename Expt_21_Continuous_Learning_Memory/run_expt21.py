"""Expt-21 entry point: continuous learning streams, controls/ablations, report.

  python run_expt21.py                      full protocol (12 full replicates, 5 ablation variants x 6 replicates)
  python run_expt21.py --smoke              tiny end-to-end run
  python run_expt21.py --report-only DIR    rebuild summary/figures from DIR/streams
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from config import VARIANTS, Cfg  # noqa: E402


def _worker(job):
    from stream import run_stream
    variant, seed, max_boxes, out_dir, cfg_over = job
    cfg = Cfg()
    for k, v in cfg_over.items():
        setattr(cfg, k, v)
    t0 = time.time()
    logf = open(Path(out_dir) / "progress.log", "a", buffering=1)

    def log(msg):
        logf.write(f"{datetime.now():%H:%M:%S} {msg}\n")

    r = run_stream(variant, seed, max_boxes, cfg, log=log)
    mem = r.pop("mem_obj")
    if variant == "full" and seed == 0:
        mem.dump(Path(out_dir) / "ltm_full_seed0.pkl")
    with open(Path(out_dir) / "streams" / f"{variant}_s{seed}.pkl", "wb") as fh:
        pickle.dump(r, fh)
    log(f"DONE {variant} s{seed}: {r['n_boxes']} boxes, {r['stop_reason']}, {time.time()-t0:.0f}s")
    return variant, seed


def code_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "src").glob("*.py")) + [Path(__file__)]:
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--report-only", default=None)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--full-reps", type=int, default=12)
    ap.add_argument("--abl-reps", type=int, default=6)
    ap.add_argument("--abl-boxes", type=int, default=60_000)
    ap.add_argument("--max-boxes", type=int, default=None)
    ap.add_argument("--skip-tests", action="store_true")
    a = ap.parse_args()
    from report import build_report

    if a.report_only:
        build_report(Path(a.report_only), Cfg())
        return 0
    if not a.skip_tests and not a.smoke:
        rc = subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")], cwd=ROOT)
        if rc != 0:
            print("tests failed; aborting")
            return rc
    cfg_over: dict = {}
    if a.smoke:
        cfg_over = dict(anneal_boxes=1500, sat_window=500, check_every=250, max_stage_boxes=1200, min_boxes=3000,
                        eval_boxes=100, checkpoints=(0, 1000, 2000, 3500), rehearse=50, sleep_every=100)
        a.full_reps, a.abl_reps, a.abl_boxes, a.max_boxes = 2, 1, 2500, a.max_boxes or 3500
        tag = "smoke"
    else:
        tag = "run"
    out = ROOT / "results" / f"{datetime.now():%Y%m%d_%H%M%S}_{tag}"
    (out / "streams").mkdir(parents=True)
    cfg = Cfg()
    for k, v in cfg_over.items():
        setattr(cfg, k, v)
    max_boxes = a.max_boxes or cfg.max_boxes
    cfg_over["checkpoints"] = tuple(sorted(set(cfg_over.get("checkpoints", cfg.checkpoints)) | {a.abl_boxes}))
    cfg.checkpoints = cfg_over["checkpoints"]
    manifest = {"created": datetime.now().isoformat(timespec="seconds"), "code_hash": code_hash(), "git_commit": git_commit(),
                "cfg": cfg.as_dict(), "variants": {k: list(v) for k, v in VARIANTS.items()},
                "full_reps": a.full_reps, "abl_reps": a.abl_reps, "abl_boxes": a.abl_boxes, "max_boxes": max_boxes,
                "workers": a.workers, "python": sys.version}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    jobs = [("full", s, max_boxes, str(out), cfg_over) for s in range(a.full_reps)]
    for v in VARIANTS:
        if v != "full":
            jobs += [(v, s, a.abl_boxes, str(out), cfg_over) for s in range(a.abl_reps)]
    print(f"output: {out}\n{len(jobs)} streams on {a.workers} workers", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(_worker, j) for j in jobs]
        for f in as_completed(futs):
            v, s = f.result()
            print(f"[{time.time()-t0:7.0f}s] finished {v} s{s}", flush=True)
    manifest["wall_s"] = time.time() - t0
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    build_report(out, cfg)
    print(f"report written to {out / 'summary.md'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())