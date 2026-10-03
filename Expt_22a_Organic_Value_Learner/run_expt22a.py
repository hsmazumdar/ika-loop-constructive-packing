"""Expt-22a entry point: organic afterstate value learner (agent + meta + sleep).

  python run_expt22a.py                 full protocol (12 full + ablations)
  python run_expt22a.py --pilot         short pilot (<=20 min): full vs frozen
  python run_expt22a.py --smoke         tiny end-to-end
  python run_expt22a.py --report-only DIR
"""

from __future__ import annotations

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

MAIN_ABLS = ("no_meta", "no_sleep", "mc_only", "frozen")


def _worker(job):
    from stream import run_stream
    variant, seed, n_boxes, out_dir, cfg_over = job
    cfg = Cfg()
    for k, v in cfg_over.items():
        setattr(cfg, k, v)
    t0 = time.time()
    outp = Path(out_dir)
    # per-stream log avoids Windows multi-process append contention on one progress.log
    log_path = outp / "logs" / f"{variant}_s{seed}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logf = open(log_path, "w", buffering=1)

    def log(msg):
        line = f"{datetime.now():%H:%M:%S} {msg}"
        logf.write(line + "\n")
        # also mirror a one-liner to a shared progress via atomic replace is heavy; skip shared file

    r = run_stream(variant, seed, cfg, n_boxes=n_boxes, log=log, extra_ckpts=(n_boxes,))
    agent = r.pop("agent", None)
    if variant == "full" and seed == 0 and agent is not None:
        with open(outp / "ltm_full_seed0.pkl", "wb") as fh:
            pickle.dump({"h": agent.h, "hidden": agent.hidden, "fast": agent.fast.p, "slow": agent.slow.p,
                         "lib_keys": agent.lib.keys, "lib_val": agent.lib.val, "cfg": cfg.as_dict()}, fh)
    with open(outp / "streams" / f"{variant}_s{seed}.pkl", "wb") as fh:
        pickle.dump(r, fh)
    log(f"DONE {variant} s{seed}: {r['n_boxes']} boxes, {time.time()-t0:.0f}s, "
        f"heldout@{r['n_boxes']}={float(r['evals'][r['n_boxes']]['S1'].mean()):.2f}")
    # append DONE line to shared progress (open briefly)
    with open(outp / "progress.log", "a", buffering=1) as pf:
        pf.write(f"{datetime.now():%H:%M:%S} DONE {variant} s{seed} boxes={r['n_boxes']} "
                 f"heldout={float(r['evals'][r['n_boxes']]['S1'].mean()):.2f} wall={time.time()-t0:.0f}s\n")
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
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--report-only", default=None)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--full-reps", type=int, default=12)
    ap.add_argument("--abl-reps", type=int, default=6)
    ap.add_argument("--abl-boxes", type=int, default=30_000)
    ap.add_argument("--max-boxes", type=int, default=None)
    ap.add_argument("--skip-tests", action="store_true")
    a = ap.parse_args()
    from report import build_report

    if a.report_only:
        build_report(Path(a.report_only), Cfg())
        return 0
    if not a.skip_tests and not a.smoke and not a.pilot:
        rc = subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")], cwd=ROOT)
        if rc != 0:
            print("tests failed; aborting")
            return rc

    cfg_over: dict = {}
    abl_names = list(MAIN_ABLS)
    if a.smoke:
        cfg_over = dict(eval_boxes=40, probe_boxes=20, epoch=100, checkpoints=(0, 200, 400),
                        n_boxes=500, grow_min_box=10**9)
        a.full_reps, a.abl_reps, a.abl_boxes, a.max_boxes = 1, 1, 400, 500
        abl_names = ["frozen", "no_sleep"]
        tag = "smoke"
    elif a.pilot:
        cfg_over = dict(eval_boxes=400, probe_boxes=60, epoch=1000,
                        checkpoints=(0, 500, 1000, 2000, 4000, 6000, 8000),
                        n_boxes=8000, grow_min_box=6000, grow_every_epochs=2)
        a.full_reps, a.abl_reps, a.abl_boxes, a.max_boxes = 1, 1, 8000, 8000
        abl_names = ["frozen"]
        tag = "pilot"
    else:
        cfg_over = dict(eval_boxes=600, n_boxes=20_000,
                        checkpoints=(0, 500, 1000, 2000, 5000, 10000, 15000, 20000))
        tag = "run"

    out = ROOT / "results" / f"{datetime.now():%Y%m%d_%H%M%S}_{tag}"
    (out / "streams").mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    cfg = Cfg()
    for k, v in cfg_over.items():
        setattr(cfg, k, v)
    max_boxes = a.max_boxes or cfg.n_boxes
    cfg_over["n_boxes"] = max_boxes
    cfg.n_boxes = max_boxes
    manifest = {"created": datetime.now().isoformat(timespec="seconds"), "code_hash": code_hash(),
                "git_commit": git_commit(), "cfg": cfg.as_dict(),
                "variants": {k: {kk: vv for kk, vv in VARIANTS[k].items() if kk != "h" or vv}
                             for k in ["full"] + abl_names},
                "full_reps": a.full_reps, "abl_reps": a.abl_reps, "abl_boxes": a.abl_boxes,
                "max_boxes": max_boxes, "workers": a.workers, "python": sys.version, "tag": tag,
                "abl_names": abl_names}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    (out / "progress.log").write_text(f"{datetime.now():%H:%M:%S} starting {len([])} placeholder\n", encoding="utf-8")

    jobs = [("full", s, max_boxes, str(out), cfg_over) for s in range(a.full_reps)]
    for v in abl_names:
        jobs += [(v, s, a.abl_boxes, str(out), cfg_over) for s in range(a.abl_reps)]
    (out / "progress.log").write_text(f"{datetime.now():%H:%M:%S} launching {len(jobs)} streams on {a.workers} workers\n", encoding="utf-8")

    print(f"output: {out}\n{len(jobs)} streams on {a.workers} workers", flush=True)
    t0 = time.time()
    # Use spawn-safe executor; maxtasksperchild avoids leaked state
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


