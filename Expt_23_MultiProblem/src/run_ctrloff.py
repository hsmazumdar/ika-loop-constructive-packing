"""Amendment A8: clean controller-OFF re-run of the loop experiments E1-E4 (packing, capped_nat, std + hard) on NEW seeds.
Arms (all with the SAME settings; F and R run with meta=False, i.e. tau/eps annealed 2.0->0.25 / 0.10->0.01 over 5,000 episodes exactly as in N,
lr 1e-3 (online lr 5e-4), sleep every 200, 40 steps x 256 rows, dream ratio 0.5, STM 1000 fixed):
  F  full learner, guided, controller off      R  same with random data generation     RN random data, online-only (plain)
  NM compute-matched plain learner (A5, rows)  N  plain online-MC control (guided, online-only)
Same code path as src/run_e_streams.py (imported unchanged; only its ARMS table is replaced in this process).
Resumable and idempotent: finished streams (json present) are skipped; json written atomically.

  python src\run_ctrloff.py run    --out results_ctrloff_i9 --machine i9Win10 --seeds 2400-2406 --nw 16
  python src\run_ctrloff.py status --out results_ctrloff_i9 [results_ctrloff_i7 ...] --seeds 2400-2407
  python src\run_ctrloff.py bench  --arm F --variant hard --seed 2300 --n-ep 1000
"""
import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"   # must be set BEFORE numpy is imported (otherwise BLAS oversubscribes the cores)
import sys, json, time, pathlib, platform, argparse, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
import run_e_streams as E

ROOT = E.ROOT
E.ARMS.clear()
E.ARMS.update({
    "F": ("full", dict(meta=False), False),
    "R": ("full", dict(meta=False), True),
    "RN": ("plain", dict(), True),
    "NM": ("matched", dict(mode="rows"), False),
    "N": ("plain", dict(), False),
})
ARMS = ("F", "R", "RN", "NM", "N")
VARIANTS = ("std", "hard")
COND = "capped_nat"
N_EP = 20000
COST = {("std", "F"): 5.4, ("std", "N"): 5.4, ("std", "NM"): 5.0, ("std", "R"): 4.5, ("std", "RN"): 2.0,
        ("hard", "NM"): 2.3, ("hard", "F"): 2.2, ("hard", "R"): 1.8, ("hard", "N"): 1.4, ("hard", "RN"): 1.0}  # relative cost (main-run runtimes /1000 s) for longest-first order


def parse_seeds(s):
    out = []
    for part in s.replace(",", " ").split():
        if "-" in part:
            a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def path_of(out, arm, variant, seed):
    return pathlib.Path(out) / "streams" / f"{arm}_{variant}_{COND}_s{seed}.json"


def job_list(seeds, arms=ARMS, variants=VARIANTS):
    jobs = [(a, v, COND, s) for v in variants for s in seeds for a in arms]
    return sorted(jobs, key=lambda j: (-COST[(j[1], j[0])], j[3]))


def machine_info(tag):
    import scipy
    return {"machine": tag, "node": platform.node(), "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "platform": platform.platform(), "cpu_count": os.cpu_count(), "controller": "off", "amendment": "A8"}


def job(args):
    (arm, variant, cond, seed), out, tag, n_ep = args
    p = path_of(out, arm, variant, seed)
    if p.exists():
        return arm, variant, seed, "exists"
    p.parent.mkdir(parents=True, exist_ok=True)
    lf = open(pathlib.Path(out) / "log.txt", "a")
    def log(m):
        lf.write(f"{datetime.datetime.now():%m-%d %H:%M:%S} {m}\n"); lf.flush()
    log(f"START {arm} {variant} s{seed}")
    try:
        r = E.run_stream(arm, variant, cond, seed, n_ep, log)
    except Exception:
        import traceback
        log(f"FAILED {arm} {variant} s{seed}: {traceback.format_exc()}"); lf.close()
        return arm, variant, seed, "failed"
    r.update(machine_info(tag))
    with open(str(p) + ".tmp", "w") as fh:
        json.dump(r, fh)
    os.replace(str(p) + ".tmp", p)
    log(f"DONE {arm} {variant} s{seed} {r['runtime_s']:.0f}s"); lf.close()
    return arm, variant, seed, "done"


def status_text(outs, seeds):
    lines, tot_done, tot = [], 0, 0
    for arm in ARMS:
        row = []
        for v in VARIANTS:
            d = sum(1 for s in seeds if any(path_of(o, arm, v, s).exists() for o in outs))
            row.append(f"{v} {d}/{len(seeds)}"); tot_done += d; tot += len(seeds)
        lines.append(f"{arm:3s} " + "  ".join(row))
    return tot_done, tot, "\n".join(lines)


def write_status(out, seeds):
    d, t, txt = status_text([out], seeds)
    (pathlib.Path(out) / "status.txt").write_text(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} IST: {d}/{t} streams done in this folder\n{txt}\n")


def cmd_run(a):
    seeds = parse_seeds(a.seeds); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    arms = tuple(a.arms.split()) if a.arms else ARMS
    jobs = [j for j in job_list(seeds, arms) if not path_of(out, j[0], j[1], j[3]).exists()]
    info = machine_info(a.machine); info.update(seeds=seeds, arms=list(arms), nw=a.nw, n_ep=a.n_ep, started=f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}", cmd=" ".join(sys.argv))
    mf = out / "manifest.json"
    hist = json.loads(mf.read_text()) if mf.exists() else []
    hist.append(info); mf.write_text(json.dumps(hist, indent=1))
    print(f"{len(jobs)} streams to run of {len(seeds) * len(arms) * len(VARIANTS)}; nw={a.nw}", flush=True)
    from multiprocessing import Pool
    write_status(out, seeds)
    with Pool(a.nw, maxtasksperchild=1) as pool:
        for arm, v, s, st in pool.imap_unordered(job, [(j, str(out), a.machine, a.n_ep) for j in jobs]):
            print(arm, v, s, st, flush=True); write_status(out, seeds)
    write_status(out, seeds)
    print("finished", flush=True)


def cmd_status(a):
    d, t, txt = status_text(a.out, parse_seeds(a.seeds)); print(f"{d}/{t} done (summed over {len(a.out)} folder(s))\n{txt}")


def cmd_bench(a):
    t = time.time(); r = E.run_stream(a.arm, a.variant, COND, a.seed, a.n_ep, print)
    print(f"BENCH {a.arm} {a.variant} s{a.seed} {a.n_ep} episodes: {time.time()-t:.0f}s total; {machine_info('bench')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="c", required=True)
    r = sp.add_parser("run"); r.add_argument("--out", required=True); r.add_argument("--machine", required=True); r.add_argument("--seeds", required=True)
    r.add_argument("--nw", type=int, required=True); r.add_argument("--arms", default=""); r.add_argument("--n-ep", type=int, default=N_EP); r.set_defaults(f=cmd_run)
    s = sp.add_parser("status"); s.add_argument("--out", nargs="+", required=True); s.add_argument("--seeds", default="2400-2407"); s.set_defaults(f=cmd_status)
    b = sp.add_parser("bench"); b.add_argument("--arm", default="F"); b.add_argument("--variant", default="hard"); b.add_argument("--seed", type=int, default=2300)
    b.add_argument("--n-ep", type=int, default=1000); b.set_defaults(f=cmd_bench)
    a = ap.parse_args(); a.f(a)
