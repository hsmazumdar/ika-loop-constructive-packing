"""E1-E4 analysis for packing (DESIGN.md section 6). Per-stream value = mean over the 4 test splits of mean(S1/ref) (as analyze_baselines.py).
Arms F, R, RN from results/e_streams; N, DQN, PPO from results/streams (same condition, same seeds 2300+).
Family per (variant, cond): F-R (E1), F-N (E2), F-RN, F-DQN, F-PPO, F-hand, F-CEMhand (one-sample); Holm over the family.
Supported only if Welch-Holm < 0.05 AND permutation and Mann-Whitney Holm-adjusted p < 0.10. Writes results/e_summary.md/.csv, e_streams_scores.csv."""
import sys, pathlib, csv, glob, json, itertools
import numpy as np
from scipy import stats
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analyze_baselines as AB
ROOT = AB.ROOT; SPLITS = AB.SPLITS; RNG = np.random.default_rng(20261003)


def scores(folder, refs):
    rows = []
    for f in sorted(glob.glob(str(ROOT / "results" / folder / "*.json"))):
        d = json.load(open(f))
        for ck, ev in d["evals"].items():
            per = {}
            for sp in SPLITS:
                S1 = np.array(ev[sp]["S1"], float).reshape(50, 3)
                ref = np.array([float(refs[(d["variant"], d["cond"], sp, j)]["ref"]) for j in range(50)])
                per[sp] = float((S1 / ref[:, None]).mean())
            rows.append(dict(arm=d["arm"], variant=d["variant"], cond=d["cond"], seed=d["seed"], ckpt=int(ck), score=float(np.mean(list(per.values()))),
                             **per, train_frac=d["train_frac"], n_ep=d["n_ep"]))
    return rows


def refmean(refs, variant, cond, col):
    return float(np.mean([np.mean([float(refs[(variant, cond, sp, j)][col]) / float(refs[(variant, cond, sp, j)]['ref']) for j in range(50)]) for sp in SPLITS]))


def boot_diff(a, b, n=10000):
    d = a.mean() - b.mean()
    bs = [RNG.choice(a, len(a)).mean() - RNG.choice(b, len(b)).mean() for _ in range(n)]
    return d, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    refs = AB.load_refs()
    E = scores("e_streams", refs); B = scores("streams", refs)
    if not E:
        print("no E streams yet"); return
    allr = E + [r for r in B if r["arm"] in ("N", "DQN", "PPO")]
    with open(ROOT / "results" / "e_streams_scores.csv", "w", newline="") as fh:
        keys = [k for k in allr[0] if k not in ("train_frac",)]
        w = csv.DictWriter(fh, keys, extrasaction="ignore"); w.writeheader(); w.writerows(allr)
    md, out = [], []
    for variant, cond in sorted({(r["variant"], r["cond"]) for r in E}):
        R = [r for r in allr if r["variant"] == variant and r["cond"] == cond]
        ckf = max(r["ckpt"] for r in E if r["variant"] == variant and r["cond"] == cond)
        cks = sorted({r["ckpt"] for r in R})
        md.append(f"\n### {variant} / {cond}  (final checkpoint {ckf})\n")
        md.append("| arm | streams | " + " | ".join(f"{c}" for c in cks) + " | final mean [95% CI] | median | IQM | final by split |\n|---|---|" + "---|" * (len(cks) + 3))
        fin, byseed = {}, {}
        for arm in ("F", "R", "RN", "NM", "NMs", "N", "DQN", "PPO"):
            A = [r for r in R if r["arm"] == arm]
            if not A: continue
            means = [f"{np.mean([r['score'] for r in A if r['ckpt']==c]):.3f}" if any(r['ckpt']==c for r in A) else "-" for c in cks]
            F = sorted([r for r in A if r["ckpt"] == ckf], key=lambda r: r["seed"])
            if not F:
                md.append(f"| {arm} | 0 | " + " | ".join(means) + " | | | | |"); continue
            fv = np.array([r["score"] for r in F]); fin[arm] = fv; byseed[arm] = {r["seed"]: r["score"] for r in F}
            lo, hi = AB.boot_ci(fv)
            sp = ", ".join(f"{np.mean([r[s] for r in F]):.3f}" for s in SPLITS)
            md.append(f"| {arm} | {len(fv)} | " + " | ".join(means) + f" | {fv.mean():.3f} [{lo:.3f}, {hi:.3f}] | {np.median(fv):.3f} | {AB.iqm(fv):.3f} | {sp} |")
            out.append(dict(variant=variant, cond=cond, arm=arm, n=len(fv), mean=fv.mean(), lo=lo, hi=hi, median=float(np.median(fv)), iqm=AB.iqm(fv)))
        if "F" in fin:
            refv = {c: refmean(refs, variant, cond, c) for c in ("uniform", "hand", "cemhand")}
            comps = [(f"F vs {o}" + (" (E1)" if o == "R" else " (E2)" if o == "N" else " (matched compute)" if o == "NM" else ""), fin["F"], fin[o], None) for o in ("R", "N", "RN", "NM", "DQN", "PPO") if o in fin]
            comps += [(f"F vs {k} (ref mean {refv[k]:.3f})", fin["F"], None, refv[k]) for k in ("hand", "cemhand")]
            pw, pp, pm = [], [], []
            for name, x, y, c in comps:
                if y is not None and len(x) > 1 and len(y) > 1:
                    pw.append(stats.ttest_ind(x, y, equal_var=False).pvalue); pp.append(AB.perm_p(x, y)); pm.append(stats.mannwhitneyu(x, y, alternative="two-sided").pvalue)
                else:
                    pw.append(stats.ttest_1samp(x, c).pvalue if len(x) > 1 else 1.0); pp.append(float("nan")); pm.append(float("nan"))
            hw = AB.holm(np.array(pw)); hp = AB.holm(np.nan_to_num(np.array(pp), nan=1.0)); hm = AB.holm(np.nan_to_num(np.array(pm), nan=1.0))
            md.append("\n| comparison (final ckpt) | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | MWU p | verdict |\n|---|---|---|---|---|---|---|---|")
            for (name, x, y, c), a, b, m_, h, h2, h3 in zip(comps, pw, pp, pm, hw, hp, hm):
                if y is not None:
                    d, lo, hi = boot_diff(x, y); ci = f"[{lo:+.3f}, {hi:+.3f}]"
                    ver = "supported" if (h < 0.05 and h2 < 0.10 and h3 < 0.10) else "survives Welch only" if h < 0.05 else "not supported"
                else:
                    d = x.mean() - c; ci = ""; ver = "supported" if h < 0.05 else "not supported"
                md.append(f"| {name} | {d:+.3f} | {ci} | {a:.4g} | {h:.4g} | {b:.4g} | {m_:.4g} | {ver} |")
                out.append(dict(variant=variant, cond=cond, comparison=name, diff=d, p_welch=a, p_holm=h, p_perm=b, p_mwu=m_, verdict=ver))
            # E1 x E2 interaction (needs F, R, N, RN with shared seeds)
            if all(a in fin for a in ("F", "R", "N", "RN")):
                xs = {a: np.array(fin[a]) for a in ("F", "R", "N", "RN")}
                did = (xs["F"].mean() - xs["R"].mean()) - (xs["N"].mean() - xs["RN"].mean())
                bs = [(RNG.choice(xs["F"], len(xs["F"])).mean() - RNG.choice(xs["R"], len(xs["R"])).mean()) - (RNG.choice(xs["N"], len(xs["N"])).mean() - RNG.choice(xs["RN"], len(xs["RN"])).mean()) for _ in range(10000)]
                md.append(f"\nE1xE2 interaction (F-R)-(N-RN) = {did:+.3f} [95% boot CI {np.percentile(bs,2.5):+.3f}, {np.percentile(bs,97.5):+.3f}]")
            # E4: change between checkpoints (within-stream bootstrap) for F
            Fs = {}
            for r in R:
                if r["arm"] == "F": Fs.setdefault(r["seed"], {})[r["ckpt"]] = r["score"]
            for c0, c1 in ((0, ckf), (2000, ckf), (ckf // 2, ckf)):
                dd = np.array([v[c1] - v[c0] for v in Fs.values() if c0 in v and c1 in v])
                if len(dd) > 1:
                    bs = [RNG.choice(dd, len(dd)).mean() for _ in range(10000)]
                    md.append(f"E4 F change ckpt {c0}->{c1}: {dd.mean():+.3f} [95% boot CI {np.percentile(bs,2.5):+.3f}, {np.percentile(bs,97.5):+.3f}], n={len(dd)}")
            # generated-data quality per round of 1000 (F vs R), training outcome frac
            for arm in ("F", "R", "RN"):
                T = [r["train_frac"] for r in E if r["arm"] == arm and r["variant"] == variant and r["cond"] == cond]
                if T:
                    n = min(len(t) for t in T); k = n // 1000
                    if k: md.append(f"gen. data quality {arm} (mean S1/free of generated episodes per 1000-round): " + ", ".join(f"{np.mean([np.mean(t[i*1000:(i+1)*1000]) for t in T]):.3f}" for i in range(k)))
    keys = sorted({k for d in out for k in d})
    with open(ROOT / "results" / "e_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(out)
    (ROOT / "results" / "e_summary.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()