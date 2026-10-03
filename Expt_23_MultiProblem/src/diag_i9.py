"""Post-hoc DIAGNOSTICS D1-D4 for the Expt_23 full learner F (DESIGN.md amendment A7). NOT pre-registered tests.
New file; imports the running code unchanged and patches it only inside the process of one unit (restored afterwards).

Suites (all on capped_nat, 20,000 episodes, seeds 2300+):
  D1   F (unchanged settings) retrained, std+hard x 4 seeds; at every checkpoint ALSO evaluates the FAST net, at the last three
       checkpoints several tau values for both nets and without the concept column; saves model weights. (Saved F models do not exist from
       the main run, so D1 retrains; with the same seed the 'slow, tau 0.25' evaluation should reproduce the main-run stream: repro check.)
  D2   F with 22d-like net width 64 (instead of 128), std x 8 seeds.        (all other settings of F are already identical to 22d, see START note)
  D2L  port check on the legacy 10x10 A-P problem (the 22d task): arms F (width 128) and F_w64, 4 seeds each, compare with 22d (S1 85.4 at 20k boxes).
  D3   F with sleep interval pinned to 200 (F_s200) vs 1000 (F_s1000): meta bounds for sleep_every pinned, std x 4 seeds.
  D4   F_nometa (meta-controller off, same tau/eps anneal as the plain learner N), std+hard x 4 seeds.
Outputs (one JSON + one CSV per unit, plus models) go to results_i9/<suite>/ ; finished units are skipped on re-run."""
from __future__ import annotations
import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"
import sys, json, time, pathlib, contextlib, argparse, datetime, csv
SRC = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import numpy as np
import variants as V
import generator as G
import learner_full as LF
import meta as M
import run_e_streams as E
from env import Env

ROOT = SRC.parent
DEFAULT_OUT = ROOT / "results_i9"
COND = "capped_nat"
N_EP = 20000
TAUS_FULL = (0.05, 0.1, 0.25, 0.5, 1.0)
_ORIG_AGENT = LF.FullAgent


class DiagAgent(_ORIG_AGENT):
    """FullAgent plus optional hyper-parameter overrides applied right after construction (h_over)."""
    def __init__(self, seed, random=False, h_over=None, **kw):
        super().__init__(seed, random=random, **kw)
        if h_over:
            self.h.update(h_over)


# ---------------------------------------------------------------- unit definitions
def _u(suite, arm, variant, seed, n_ep=N_EP, **kw):
    u = dict(suite=suite, arm=arm, base="F", variant=variant, cond=COND, seed=seed, n_ep=n_ep, arm_kw={}, h_over={}, bounds={}, legacy=False,
             extras="light", models="final", repro=False)
    u.update(kw)
    return u


def units(suite: str, seeds=None):
    L = []
    if suite == "D1":
        for v in ("std", "hard"):
            for s in (seeds or range(2300, 2304)):
                L.append(_u("D1", "F", v, s, extras="full", models="all", repro=True))
    elif suite == "D2":
        for s in (seeds or range(2300, 2308)):
            L.append(_u("D2", "F_w64", "std", s, arm_kw=dict(hidden=64)))
    elif suite == "D2L":
        for s in (seeds or range(2300, 2304)):
            for arm, kw in (("F", {}), ("F_w64", dict(hidden=64))):
                L.append(_u("D2L", arm, "legacy", s, arm_kw=kw, legacy=True))
    elif suite == "D3":
        for s in (seeds or range(2300, 2304)):
            for arm, se in (("F_s200", 200), ("F_s1000", 1000)):
                L.append(_u("D3", arm, "std", s, h_over=dict(sleep_every=se), bounds=dict(sleep_every=(se, se))))
    elif suite == "D4":
        for v in ("std", "hard"):
            for s in (seeds or range(2300, 2304)):
                L.append(_u("D4", "F_nometa", v, s, base="F_nometa"))
    else:
        raise ValueError(suite)
    return L


def unit_name(u):
    return f"{u['suite']}_{u['arm']}_{u['variant']}_{u['cond']}_s{u['seed']}"


def v_variant(u):
    return "std" if u["variant"] == "legacy" else u["variant"]


# ---------------------------------------------------------------- patching (restored after the unit)
@contextlib.contextmanager
def patched(u):
    sv = dict(make=V.make, agent=LF.FullAgent, bounds=dict(M.BOUNDS), arms=dict(E.ARMS), evaluate=E.evaluate)
    try:
        kind, kw, rnd = E.ARMS[u["base"]]
        kw2 = dict(kw); kw2.update(u["arm_kw"])
        if u["h_over"]:
            kw2["h_over"] = dict(u["h_over"])
        E.ARMS[u["arm"]] = (kind, kw2, rnd)
        LF.FullAgent = DiagAgent
        for k, b in u["bounds"].items():
            M.BOUNDS[k] = tuple(b)
        if u["legacy"]:
            def make_legacy(variant, split, index, cond="capped_nat"):
                return G.make_problem("legacy", 0, V.CONDS[cond][0])
            V.make = make_legacy
        yield
    finally:
        V.make = sv["make"]; LF.FullAgent = sv["agent"]; E.evaluate = sv["evaluate"]
        M.BOUNDS.clear(); M.BOUNDS.update(sv["bounds"])
        E.ARMS.clear(); E.ARMS.update(sv["arms"])


# ---------------------------------------------------------------- evaluation helpers
def eval_multi(agent, variant, cond, seed, configs, splits, n_prob, n_rep):
    """configs: name -> (net 'slow'|'fast', tau, use_concepts). Problem-outer loop so each Env is built once. Same rng seeds as the main evaluation."""
    nat = V.natural_of(cond)
    out = {n: {sp: {"S1": [], "free": []} for sp in splits} for n in configs}
    old = agent.flags["concepts"]
    try:
        for sp in splits:
            for j in range(n_prob):
                prob = V.make(variant, sp, j, cond); env, enc = agent.get_env(prob)
                for name, (netn, tau, conc) in configs.items():
                    net = agent.slow if netn == "slow" else agent.fast
                    agent.flags["concepts"] = bool(old and conc)
                    for r in range(n_rep):
                        rng = np.random.default_rng((E.EVAL_SEED, seed, j, r))
                        s, _ = agent.play(env, enc, rng, tau, 0.0, nat, net=net, record=False, random=False)
                        out[name][sp]["S1"].append(int(s.filled)); out[name][sp]["free"].append(int(env.free_cells))
    finally:
        agent.flags["concepts"] = old
    return out


def extras_for(u, ck, final, last3):
    """Extra evaluation configs at checkpoint ck (the standard 'slow_t0.25' evaluation is always done by the main code path)."""
    c = {"fast_t0.25": ("fast", 0.25, True)}
    if u["extras"] == "full" and ck in last3:
        for net in ("slow", "fast"):
            for tau in TAUS_FULL:
                if not (net == "slow" and tau == 0.25):
                    c[f"{net}_t{tau}"] = (net, tau, True)
        c["slow_t0.25_noconc"] = ("slow", 0.25, False)
        c["fast_t0.25_noconc"] = ("fast", 0.25, False)
    elif u["extras"] == "light" and final:
        for net in ("slow", "fast"):
            for tau in (0.1, 0.5):
                c[f"{net}_t{tau}"] = (net, tau, True)
    return c


def save_model(agent, path):
    d = {f"fast_{k}": v for k, v in agent.fast.p.items()}
    d.update({f"slow_{k}": v for k, v in agent.slow.p.items()})
    d["lib_keys"] = agent.lib.keys; d["lib_val"] = agent.lib.val
    d["h"] = np.array(json.dumps(agent.h)); d["flags"] = np.array(json.dumps({k: bool(v) for k, v in agent.flags.items()}))
    np.savez_compressed(path, **d)


def load_model(path):
    z = np.load(path, allow_pickle=False)
    hid = int(z["fast_W1"].shape[1])
    ag = _ORIG_AGENT(0, hidden=hid)
    for k in list(ag.fast.p):
        ag.fast.p[k] = z[f"fast_{k}"].copy(); ag.slow.p[k] = z[f"slow_{k}"].copy()
    ag.lib.keys = z["lib_keys"].copy(); ag.lib.val = z["lib_val"].copy()
    ag.h.update(json.loads(str(z["h"])))
    return ag


# ---------------------------------------------------------------- one unit
def _refs():
    import analyze_baselines as AB
    return AB.load_refs()


def csv_rows(u, evals_by_ck, refs):
    rows = []
    for ck, cfgs in evals_by_ck.items():
        for name, per in cfgs.items():
            netn, rest = name.split("_t", 1)
            tau = float(rest.split("_")[0]); conc = 0 if rest.endswith("noconc") else 1
            for sp, d in per.items():
                S1 = np.array(d["S1"], float); fr = np.array(d["free"], float)
                norm = ""
                try:
                    if u["legacy"]:
                        ref = float(refs[("std", u["cond"], "legacy", 0)]["ref"]); norm = float((S1 / ref).mean())
                    else:
                        n_rep = _NREP["n"]
                        n_prob = len(S1) // n_rep
                        ref = np.array([float(refs[(u["variant"], u["cond"], sp, j)]["ref"]) for j in range(n_prob)])
                        norm = float((S1.reshape(n_prob, n_rep) / ref[:, None]).mean())
                except Exception:
                    norm = ""
                rows.append(dict(suite=u["suite"], arm=u["arm"], variant=u["variant"], cond=u["cond"], seed=u["seed"], ckpt=ck, net=netn, tau=tau,
                                 concepts=conc, split=sp, n=len(S1), mean_S1=float(S1.mean()), mean_free=float(fr.mean()),
                                 mean_frac=float((S1 / fr).mean()), mean_norm=norm))
    return rows


_NREP = {"n": 3}


def run_unit(u, out_dir, tiny=False, log=None):
    out_dir = pathlib.Path(out_dir)
    name = unit_name(u)
    jp = out_dir / u["suite"] / f"{name}.json"
    if jp.exists():
        return name, "exists"
    jp.parent.mkdir(parents=True, exist_ok=True)
    (out_dir / "models").mkdir(exist_ok=True)
    n_ep = u["n_ep"]
    splits = ("test_iid",) if u["legacy"] else V.TEST_SPLITS
    n_prob = 40 if u["legacy"] else 50
    n_rep_old = E.N_REP
    if tiny:
        n_prob = 2; E.N_REP = 1; splits = splits[:1]
    _NREP["n"] = E.N_REP
    ck = sorted(set(c for c in E.CKPTS if c <= n_ep) | {n_ep})
    last3 = tuple(ck[-3:])
    st = dict(i=0, extras={}, h={}, ck=ck)
    t0 = time.time()
    logf = (lambda m: None) if log is None else log

    def make_wrapper(orig):
        def wrapped(agent, kind, variant, cond, seed, splits_=None, n_prob_=None, **kw):
            i = st["i"]; st["i"] += 1
            c = ck[i]
            res = orig(agent, kind, variant, cond, seed, splits=splits, n_prob=n_prob)
            cfgs = extras_for(u, c, c == ck[-1], last3)
            st["extras"][c] = eval_multi(agent, variant, cond, seed, cfgs, splits, n_prob, E.N_REP) if cfgs else {}
            st["h"][c] = dict(agent.h, hidden=int(agent.fast.h), concepts=int(agent.lib.keys.size), sleeps=int(agent.sleeps))
            if u["models"] == "all" or c == ck[-1]:
                save_model(agent, out_dir / "models" / f"{name}_ck{c}.npz")
            logf(f"[{name}] ckpt {c} extra evals {sorted(st['extras'][c])} {time.time()-t0:.0f}s")
            return res
        return wrapped

    try:
        with patched(u):
            E.evaluate = make_wrapper(E.evaluate)
            r = E.run_stream(u["arm"], v_variant(u), u["cond"], u["seed"], n_ep, logf)
    except Exception:
        import traceback
        logf(f"FAILED {name}: {traceback.format_exc()}")
        E.N_REP = n_rep_old
        return name, "failed"
    E.N_REP = n_rep_old
    r["arm"] = u["arm"]; r["variant"] = u["variant"]
    r["diag"] = dict(unit=u, extras={str(k): v for k, v in st["extras"].items()}, h_at_ckpt={str(k): v for k, v in st["h"].items()}, tiny=tiny,
                     splits=list(splits), n_prob=n_prob, versions=dict(python=sys.version, numpy=np.__version__, host=os.environ.get("COMPUTERNAME", "")),
                     started=datetime.datetime.fromtimestamp(t0).isoformat(timespec="seconds"))
    r["diag"]["repro"] = repro_check(u, r) if (u["repro"] and not tiny) else None
    tmp = str(jp) + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(r, fh)
    os.replace(tmp, jp)
    try:
        refs = _refs()
        by = {int(k): dict({"slow_t0.25": {sp: r["evals"][k][sp] for sp in splits}}, **r["diag"]["extras"][k]) for k in r["evals"]}
        rows = csv_rows(u, by, refs)
        with open(out_dir / u["suite"] / f"{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    except Exception as ex:
        logf(f"CSV failed {name}: {ex!r}")
    logf(f"DONE {name} {time.time()-t0:.0f}s")
    return name, "done"


def repro_check(u, r):
    """Compare the retrained stream with the main-run E-stream file of the same arm/seed (D1 only): identical numbers => the retrain is faithful."""
    p = ROOT / "results" / "e_streams" / f"{u['base']}_{u['variant']}_{u['cond']}_s{u['seed']}.json"
    if not p.exists():
        return {"file": str(p), "found": False}
    d = json.load(open(p))
    per = {}
    for ck, ev in d["evals"].items():
        if ck in r["evals"]:
            per[ck] = all(ev[sp]["S1"] == r["evals"][ck][sp]["S1"] for sp in ev)
    return {"file": str(p), "found": True, "per_ckpt_equal": per, "all_equal": bool(per) and all(per.values()), "train_frac_equal": d["train_frac"] == r["train_frac"]}


# ---------------------------------------------------------------- CLI
def skipped(u, out_dir) -> bool:
    """Units / suites listed (one per line) in <out>/skip_units.txt are not run (A7 note: D4 moved to the Vivobook). Read at launch and at unit start."""
    try:
        sk = {x.strip() for x in (pathlib.Path(out_dir) / "skip_units.txt").read_text().split("\n") if x.strip()}
    except Exception:
        return False
    return u["suite"] in sk or unit_name(u) in sk


def _job(a):
    u, out = a
    d = pathlib.Path(out); d.mkdir(parents=True, exist_ok=True)
    if skipped(u, d):
        return unit_name(u), "skipped"
    lf = open(d / "diag_log.txt", "a", encoding="utf-8")
    def log(m):
        lf.write(f"{datetime.datetime.now():%m-%d %H:%M:%S} {m}\n"); lf.flush()
    log(f"START {unit_name(u)}")
    return run_unit(u, d, False, log)


def cmd_run(a):
    from multiprocessing import Pool
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    seeds = list(range(a.seed0, a.seed0 + a.n_seeds)) if a.n_seeds else None
    L = []
    for s in a.suites:
        for u in units(s, seeds):
            if a.n_ep: u["n_ep"] = a.n_ep
            L.append(u)
    todo = [u for u in L if not (out / u["suite"] / f"{unit_name(u)}.json").exists() and not skipped(u, out)]
    with open(out / "run_log.txt", "a") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} run suites={a.suites} nw={a.nw} units={len(L)} todo={len(todo)} cmd={' '.join(sys.argv)}\n")
    print(f"{len(todo)} of {len(L)} units to run with {a.nw} workers", flush=True)
    with Pool(a.nw, maxtasksperchild=1) as pool:
        for name, st in pool.imap_unordered(_job, [(u, str(out)) for u in todo]):
            print(name, st, flush=True)


def cmd_status(a):
    out = pathlib.Path(a.out)
    for s in ("D1", "D2", "D2L", "D3", "D4"):
        L = units(s)
        done = sum((out / s / f"{unit_name(u)}.json").exists() for u in L)
        print(f"{s}: {done}/{len(L)} done")


def cmd_list(a):
    for s in a.suites:
        for u in units(s):
            print(unit_name(u))


def cmd_reeval(a):
    ag = load_model(a.model)
    splits = ("test_iid",) if a.variant == "legacy" else V.TEST_SPLITS
    cfgs = {f"{n}_t{t}" + ("" if c else "_noconc"): (n, t, c) for n in a.nets for t in a.taus for c in ((True, False) if a.noconc else (True,))}
    res = eval_multi(ag, "std" if a.variant == "legacy" else a.variant, a.cond, a.seed, cfgs, splits, a.n_prob, E.N_REP)
    json.dump(res, open(a.save, "w"))
    for k, v in res.items():
        fr = np.mean([np.mean(np.array(d["S1"]) / np.array(d["free"])) for d in v.values()])
        print(k, f"S1/free {fr:.4f}")


def main():
    p = argparse.ArgumentParser(); sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--suites", nargs="+", required=True); r.add_argument("--nw", type=int, required=True)
    r.add_argument("--out", default=str(DEFAULT_OUT)); r.add_argument("--n-ep", type=int, default=0)
    r.add_argument("--seed0", type=int, default=2300); r.add_argument("--n-seeds", type=int, default=0); r.set_defaults(f=cmd_run)
    s = sp.add_parser("status"); s.add_argument("--out", default=str(DEFAULT_OUT)); s.set_defaults(f=cmd_status)
    l = sp.add_parser("list"); l.add_argument("--suites", nargs="+", default=["D1", "D2", "D2L", "D3", "D4"]); l.set_defaults(f=cmd_list)
    e = sp.add_parser("reeval"); e.add_argument("--model", required=True); e.add_argument("--variant", default="std"); e.add_argument("--cond", default=COND)
    e.add_argument("--seed", type=int, default=2300); e.add_argument("--nets", nargs="+", default=["slow", "fast"]); e.add_argument("--taus", nargs="+", type=float, default=[0.25])
    e.add_argument("--noconc", action="store_true"); e.add_argument("--n-prob", type=int, default=50); e.add_argument("--save", default="reeval.json"); e.set_defaults(f=cmd_reeval)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()