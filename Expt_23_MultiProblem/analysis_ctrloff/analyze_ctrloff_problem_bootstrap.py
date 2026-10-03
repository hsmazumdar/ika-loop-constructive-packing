"""A8 problem-resampling analysis (DESIGN.md section 6: "a second analysis resamples problems (hierarchical bootstrap: streams, then problems)").
DESCRIPTIVE, AFTER-THE-FACT: specified in DESIGN.md before any data, but NOT implemented in analyze_ctrloff.py and run only after the A8 main result
was known (written and run 2026-10-03 IST, after the A8 verdict). It does not change the A8 verdict (which is defined by analyze_ctrloff.py).
Data: per-problem S1 and free-cell lists saved in every A8 stream json (4 test splits x 50 problems x 3 evaluation repeats at the 20,000-episode checkpoint).
Per-problem value = mean over the 3 repeats of S1 / ref (ref = frozen per-problem reference, as in analyze_ctrloff.py).
Primary streams only (first folder wins: results_ctrloff_i9, then results_ctrloff_i7; i9b replicate excluded).
Resampling: (a) streams only (problems fixed) [= usual stream-level bootstrap], (b) problems only (streams fixed), (c) hierarchical: resample streams with
replacement within each arm, and resample the 50 problems within each split with replacement (the same problem draw is applied to both arms of a contrast).
The designs are unpaired over streams (as in A8's Welch tests). 95% percentile intervals; B = 20000; fixed seed.
Usage: python analyze_ctrloff_problem_bootstrap.py [--out DIR]"""
import sys, pathlib, json, glob, argparse
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import analyze_baselines as AB
ROOT = AB.ROOT; SPLITS = AB.SPLITS
FOLDERS = ["results_ctrloff_i9", "results_ctrloff_i7"]
B = 20000


def load_arrays(refs):
    seen, data = set(), {}
    for fo in FOLDERS:
        for f in sorted(glob.glob(str(ROOT / fo / "streams" / "*.json"))):
            d = json.load(open(f)); key = (d["arm"], d["variant"], d["seed"])
            if key in seen: continue
            seen.add(key)
            ev = d["evals"]["20000"]; arr = np.zeros((4, 50))
            for k, sp in enumerate(SPLITS):
                S1 = np.array(ev[sp]["S1"], float).reshape(50, 3)
                ref = np.array([float(refs[(d["variant"], d["cond"], sp, j)]["ref"]) for j in range(50)])
                arr[k] = (S1 / ref[:, None]).mean(axis=1)
            data.setdefault((d["variant"], d["arm"]), []).append((d["seed"], arr))
    return {k: np.stack([a for _, a in sorted(v, key=lambda t: t[0])]) for k, v in data.items()}   # [stream, split, problem]


def boot(X, Y, rng, mode):
    ns, nc = X.shape[0], Y.shape[0]; out = np.empty(B)
    for b in range(B):
        si = rng.integers(0, ns, ns) if mode in ("streams", "hier") else np.arange(ns)
        sj = rng.integers(0, nc, nc) if mode in ("streams", "hier") else np.arange(nc)
        if mode in ("problems", "hier"):
            pi = rng.integers(0, 50, (4, 50))
        else:
            pi = np.tile(np.arange(50), (4, 1))
        rows = np.arange(4)[:, None]
        xs = X[si][:, rows, pi]; ys = Y[sj][:, rows, pi]          # [stream, split, 50]
        out[b] = xs.mean() - ys.mean()
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    refs = AB.load_refs(); D = load_arrays(refs); rng = np.random.default_rng(20261003)
    comps = (("N", "F vs N"), ("NM", "F vs NM"), ("R", "F vs R"))
    md = ["# A8 problem-resampling (hierarchical bootstrap) - descriptive, after-the-fact\n",
          "Specified in DESIGN.md section 6 (second analysis: streams, then problems); not implemented in analyze_ctrloff.py; computed after the A8 verdict (3 Oct 2026 IST). Does not change the A8 decision rule or verdict.\n",
          f"Primary streams only (i9 seeds 2400-2405 + i7 seeds 2406-2407), final checkpoint 20,000, 4 splits x 50 problems (3 repeats averaged per problem). B = {B}, 95% percentile intervals, seed 20261003.\n",
          "| variant | contrast | n | point diff | CI streams only | CI problems only | CI hierarchical | share of hierarchical draws with F higher |", "|---|---|---|---|---|---|---|---|"]
    rows = []
    for v in ("std", "hard"):
        F = D[(v, "F")]
        for arm, name in comps:
            Y = D[(v, arm)]; pt = F.mean() - Y.mean()
            res = {}
            for mode in ("streams", "problems", "hier"):
                d = boot(F, Y, rng, mode); res[mode] = (float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), float((d > 0).mean()))
            f = lambda t: f"[{t[0]:+.4f}, {t[1]:+.4f}]"
            md.append(f"| {v} | {name} | {F.shape[0]} v {Y.shape[0]} | {pt:+.4f} | {f(res['streams'])} | {f(res['problems'])} | {f(res['hier'])} | {res['hier'][2]:.4f} |")
            rows.append(dict(variant=v, contrast=name, point=pt, **{f"{m}_{k}": res[m][i] for m in res for i, k in enumerate(("lo", "hi", "share_pos"))}))
    pathlib.Path(a.out).mkdir(parents=True, exist_ok=True)
    (pathlib.Path(a.out) / "ctrloff_problem_bootstrap.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    import csv
    with open(pathlib.Path(a.out) / "ctrloff_problem_bootstrap.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("\n".join(md))


if __name__ == "__main__":
    main()
