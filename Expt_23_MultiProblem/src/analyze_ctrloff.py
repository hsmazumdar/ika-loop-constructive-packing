"""Analysis of the controller-off confirmation run (DESIGN.md Amendment A8). Pre-registered; written before any A8 data existed.
Merges one or more result folders (default results_ctrloff_i9 results_ctrloff_i7), stream level, same scoring as analyze_e.py
(per-stream value = mean over the 4 test splits of mean(S1/ref), final checkpoint 20,000 episodes; frozen refs).
PRIMARY family per condition (std, hard): F-N, F-NM, F-R; Welch t (two-sided) with Holm over the 3; sensitivities: exact/MC permutation and Mann-Whitney U, Holm-adjusted.
'supported' = Welch-Holm < 0.05 AND permutation-Holm < 0.10 AND MWU-Holm < 0.10 AND F > comparator; 'survives Welch only' = Welch-Holm < 0.05 only;
a significant result with F < comparator is reported as 'opposite direction'; otherwise 'not supported'.
SECONDARY family per condition (Holm over 5): F-RN, F-DQN, F-PPO (earlier baseline run, seeds 2300+), F-hand, F-CEMhand (one-sample).
Also: E1xE2 interaction, E3 transfer (per-split gap to test_iid), E4 (change between checkpoints, per-stream slope), generated-data quality,
machine-nuisance check, i9-only sensitivity of the primary family.
Usage: python src\analyze_ctrloff.py [--folders results_ctrloff_i9 results_ctrloff_i7] [--out analysis_ctrloff]"""
import sys, pathlib, csv, glob, json, argparse
import numpy as np
from scipy import stats
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analyze_baselines as AB
import analyze_e as AE
ROOT = AB.ROOT; SPLITS = AB.SPLITS; RNG = np.random.default_rng(20261004)
ARMS = ("F", "R", "RN", "NM", "N")
PRIMARY = (("F vs N (E2, consolidation vs plain)", "N"), ("F vs NM (E2, matched compute)", "NM"), ("F vs R (E1, guided vs random data)", "R"))


def load(folders, refs):
    rows = []
    for fo in folders:
        for f in sorted(glob.glob(str(ROOT / fo / "streams" / "*.json"))):
            d = json.load(open(f))
            for ck, ev in d["evals"].items():
                per = {}
                for sp in SPLITS:
                    S1 = np.array(ev[sp]["S1"], float).reshape(50, 3)
                    ref = np.array([float(refs[(d["variant"], d["cond"], sp, j)]["ref"]) for j in range(50)])
                    per[sp] = float((S1 / ref[:, None]).mean())
                rows.append(dict(arm=d["arm"], variant=d["variant"], cond=d["cond"], seed=d["seed"], ckpt=int(ck), score=float(np.mean(list(per.values()))),
                                 machine=d.get("machine", fo), folder=fo, pyv=d.get("python", "?"), npv=d.get("numpy", "?"), train_frac=d["train_frac"], **per))
    return rows


def bdiff(a, b, n=10000):
    bs = [RNG.choice(a, len(a)).mean() - RNG.choice(b, len(b)).mean() for _ in range(n)]
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def tests(x, y):
    return (stats.ttest_ind(x, y, equal_var=False).pvalue, AB.perm_p(x, y), stats.mannwhitneyu(x, y, alternative="two-sided").pvalue)


def verdict(hw, hp, hm, d):
    if hw < 0.05 and d < 0:
        return "opposite direction (F worse), Welch-Holm < 0.05"
    if hw < 0.05 and hp < 0.10 and hm < 0.10:
        return "supported"
    return "survives Welch only" if hw < 0.05 else "not supported"


def family(title, items, md, out, variant):
    """items: (name, x, y or None, c or None)"""
    pw, pp, pm = [], [], []
    for name, x, y, c in items:
        if y is not None and len(x) > 1 and len(y) > 1:
            a, b, m = tests(x, y)
        else:
            a, b, m = (stats.ttest_1samp(x, c).pvalue if len(x) > 1 else 1.0), float("nan"), float("nan")
        pw.append(a); pp.append(b); pm.append(m)
    if not items:
        return
    hw = AB.holm(np.array(pw)); hp = AB.holm(np.nan_to_num(np.array(pp), nan=1.0)); hm = AB.holm(np.nan_to_num(np.array(pm), nan=1.0))
    md.append(f"\n**{title}** (Holm over {len(items)})\n\n| comparison | n | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | Holm(perm) | MWU p | Holm(MWU) | verdict |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for (name, x, y, c), a, b, m, h, h2, h3 in zip(items, pw, pp, pm, hw, hp, hm):
        if y is not None:
            d = x.mean() - y.mean(); lo, hi = bdiff(x, y); ci = f"[{lo:+.3f}, {hi:+.3f}]"; n = f"{len(x)} v {len(y)}"
            ver = verdict(h, h2, h3, d)
        else:
            d = x.mean() - c; ci = ""; n = f"{len(x)} v ref"; ver = "supported (one-sample)" if (h < 0.05 and d > 0) else "opposite direction (F worse)" if (h < 0.05) else "not supported"
        md.append(f"| {name} | {n} | {d:+.4f} | {ci} | {a:.4g} | {h:.4g} | {b:.4g} | {h2:.4g} | {m:.4g} | {h3:.4g} | {ver} |")
        out.append(dict(variant=variant, family=title, comparison=name, diff=d, p_welch=a, p_holm_welch=h, p_perm=b, p_holm_perm=h2, p_mwu=m, p_holm_mwu=h3, verdict=ver))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--folders", nargs="+", default=["results_ctrloff_i9", "results_ctrloff_i7", "results_ctrloff_i9b"]); ap.add_argument("--out", default="analysis_ctrloff")
    a = ap.parse_args()
    refs = AB.load_refs()
    E = load([f for f in a.folders if (ROOT / f / "streams").exists()], refs)
    if not E:
        print("no A8 streams yet"); return
    # A8 implementation note: folders are taken in the given order; a stream (arm, variant, seed) present in several folders counts ONCE (first folder) in every test;
    # later copies (e.g. i7 streams for seeds that were re-run on the i9) are machine-nuisance replicates only.
    seen, prim, repl = {}, [], []
    for r in E:
        k = (r["arm"], r["variant"], r["seed"], r["ckpt"])
        if k in seen and seen[k] != r["folder"]:
            repl.append(r)
        else:
            seen[k] = r["folder"]; prim.append(r)
    E = prim
    B = AE.scores("streams", refs)                       # earlier baseline run (N, DQN, PPO; seeds 2300+; reused as references, not rerun)
    O = AE.scores("e_streams", refs)                     # earlier controller-ON E-streams (context only, never tested here)
    outd = ROOT / a.out; outd.mkdir(exist_ok=True)
    md, out = [], []
    ms = sorted({(r["machine"], r["pyv"], r["npv"]) for r in E})
    md.append("# A8 controller-off confirmation - analysis (stream level)\n")
    md.append("Machines/libraries present: " + "; ".join(f"{m} (python {p}, numpy {n})" for m, p, n in ms) + f"\n\nStreams loaded: {len({(r['arm'], r['variant'], r['seed']) for r in E})}\n")
    for variant in ("std", "hard"):
        cond = "capped_nat"
        R = [r for r in E if r["variant"] == variant]
        if not R: continue
        ckf = max(r["ckpt"] for r in R)
        cks = sorted({r["ckpt"] for r in R})
        md.append(f"\n## {variant} / {cond}  (final checkpoint {ckf})\n")
        md.append("| arm | streams | " + " | ".join(str(c) for c in cks) + " | final mean [95% CI] | median | IQM | final by split (" + ", ".join(SPLITS) + ") |\n|---|---|" + "---|" * (len(cks) + 3))
        fin, finm = {}, {}
        for arm in ARMS:
            A = [r for r in R if r["arm"] == arm]
            if not A: continue
            means = [f"{np.mean([r['score'] for r in A if r['ckpt'] == c]):.3f}" if any(r['ckpt'] == c for r in A) else "-" for c in cks]
            F = sorted([r for r in A if r["ckpt"] == ckf], key=lambda r: r["seed"])
            if not F:
                md.append(f"| {arm} | 0 | " + " | ".join(means) + " | | | | |"); continue
            v = np.array([r["score"] for r in F]); fin[arm] = v; finm[arm] = [r["machine"] for r in F]
            lo, hi = AB.boot_ci(v)
            md.append(f"| {arm} | {len(v)} | " + " | ".join(means) + f" | {v.mean():.4f} [{lo:.4f}, {hi:.4f}] | {np.median(v):.4f} | {AB.iqm(v):.4f} | " + ", ".join(f"{np.mean([r[s] for r in F]):.3f}" for s in SPLITS) + " |")
            out.append(dict(variant=variant, arm=arm, n=len(v), mean=v.mean(), lo=lo, hi=hi, median=float(np.median(v)), iqm=AB.iqm(v)))
        # references (earlier baseline run, reused)
        refrows = []
        for arm in ("N", "DQN", "PPO"):
            Bv = np.array([r["score"] for r in B if r["arm"] == arm and r["variant"] == variant and r["cond"] == cond and r["ckpt"] == ckf])
            if len(Bv): refrows.append((arm, Bv))
        refv = {c: AE.refmean(refs, variant, cond, c) for c in ("uniform", "hand", "cemhand")}
        md.append("\nReferences from the EARLIER runs (not rerun, not part of the A8 tests unless stated): " + "; ".join(f"{k} {v:.3f}" for k, v in refv.items()) + "; " +
                  "; ".join(f"{n} (earlier baseline, seeds 2300+, n={len(v)}) {v.mean():.4f}" for n, v in refrows) + "; " +
                  "; ".join(f"{arm} (earlier controller-ON E-run, n={len([r for r in O if r['arm']==arm and r['variant']==variant and r['ckpt']==ckf])}) {np.mean([r['score'] for r in O if r['arm']==arm and r['variant']==variant and r['ckpt']==ckf]):.4f}" for arm in ("F", "NM", "R", "RN") if any(r['arm']==arm and r['variant']==variant and r['ckpt']==ckf for r in O)))
        if "F" in fin:
            prim = [(n, fin["F"], fin[o], None) for n, o in PRIMARY if o in fin]
            family("PRIMARY family (pre-registered)", prim, md, out, variant)
            sec = [(f"F vs {o}", fin["F"], fin[o], None) for o in ("RN",) if o in fin]
            ref_arms = {n: v for n, v in refrows}
            sec += [(f"F vs {o} (earlier run, seeds 2300+)", fin["F"], ref_arms[o], None) for o in ("DQN", "PPO") if o in ref_arms]
            sec += [(f"F vs {k} (ref mean {refv[k]:.3f})", fin["F"], None, refv[k]) for k in ("hand", "cemhand")]
            family("SECONDARY family (Holm over 5)", sec, md, out, variant)
            if len({m for ms_ in finm.values() for m in ms_}) > 1:
                keep = {arm: np.array([s for s, m in zip(fin[arm], finm[arm]) if m == "i9Win10"]) for arm in fin}
                prim9 = [(n + " [i9 streams only]", keep["F"], keep[o], None) for n, o in PRIMARY if o in keep and len(keep[o]) > 1 and len(keep["F"]) > 1]
                family("SENSITIVITY: primary family on i9Win10 streams only (Holm over 3)", prim9, md, out, variant)
        # descriptive, unadjusted contrasts
        desc = []
        for n1, n2 in (("R", "RN"), ("NM", "N")):
            if n1 in fin and n2 in fin:
                d = fin[n1].mean() - fin[n2].mean(); lo, hi = bdiff(fin[n1], fin[n2]); desc.append(f"{n1}-{n2} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]")
        if all(x in fin for x in ARMS[:4]) and "N" in fin:
            xs = fin
            did = (xs["F"].mean() - xs["R"].mean()) - (xs["N"].mean() - xs["RN"].mean())
            bs = [(RNG.choice(xs["F"], len(xs["F"])).mean() - RNG.choice(xs["R"], len(xs["R"])).mean()) - (RNG.choice(xs["N"], len(xs["N"])).mean() - RNG.choice(xs["RN"], len(xs["RN"])).mean()) for _ in range(10000)]
            desc.append(f"E1xE2 interaction (F-R)-(N-RN) {did:+.4f} [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")
        if desc: md.append("\nDescriptive contrasts (no tests, 95% bootstrap CI): " + "; ".join(desc))
        # E3 transfer
        md.append("\n**E3 transfer (final checkpoint): split score and gap to test_iid, mean [95% CI over streams]**\n\n| arm | " + " | ".join(SPLITS) + " | gap size | gap piece | gap both |\n|---|---|---|---|---|---|---|---|")
        for arm in ARMS:
            F = [r for r in R if r["arm"] == arm and r["ckpt"] == ckf]
            if len(F) < 2: continue
            cells = [f"{np.mean([r[s] for r in F]):.3f}" for s in SPLITS]
            gaps = []
            for s in SPLITS[1:]:
                g = np.array([r[s] - r["test_iid"] for r in F]); lo, hi = AB.boot_ci(g); gaps.append(f"{g.mean():+.3f} [{lo:+.3f}, {hi:+.3f}]")
            md.append(f"| {arm} | " + " | ".join(cells) + " | " + " | ".join(gaps) + " |")
        if "F" in fin and "N" in fin:
            line = []
            for s in SPLITS:
                x = np.array([r[s] for r in R if r["arm"] == "F" and r["ckpt"] == ckf]); y = np.array([r[s] for r in R if r["arm"] == "N" and r["ckpt"] == ckf])
                lo, hi = bdiff(x, y); line.append(f"{s} {x.mean()-y.mean():+.3f} [{lo:+.3f}, {hi:+.3f}]")
            md.append("\nF minus N per split (descriptive): " + "; ".join(line))
        # E4
        md.append("\n**E4 improvement across iterations (checkpoints), within-stream**")
        for arm in ("F", "N", "NM", "R"):
            Fs = {}
            for r in R:
                if r["arm"] == arm: Fs.setdefault(r["seed"], {})[r["ckpt"]] = r["score"]
            for c0, c1 in ((0, ckf), (2000, ckf), (ckf // 2, ckf)):
                dd = np.array([v[c1] - v[c0] for v in Fs.values() if c0 in v and c1 in v])
                if len(dd) > 1:
                    bs = [RNG.choice(dd, len(dd)).mean() for _ in range(10000)]
                    md.append(f"- {arm} change ckpt {c0}->{c1}: {dd.mean():+.4f} [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}], n={len(dd)}")
            sl = []
            for v in Fs.values():
                ks = [c for c in (2000, 5000, 10000, 20000) if c in v]
                if len(ks) == 4: sl.append(np.polyfit(np.array(ks, float) / 1000.0, [v[c] for c in ks], 1)[0])
            if len(sl) > 1:
                sl = np.array(sl); bs = [RNG.choice(sl, len(sl)).mean() for _ in range(10000)]
                md.append(f"- {arm} stream-level slope over ckpts 2k..20k: {sl.mean():+.5f} per 1000 episodes [{np.percentile(bs,2.5):+.5f}, {np.percentile(bs,97.5):+.5f}], n={len(sl)}")
        for arm in ("F", "R", "RN", "N", "NM"):
            T = [r["train_frac"] for r in R if r["arm"] == arm and r["ckpt"] == ckf]
            if T:
                k = min(len(t) for t in T) // 1000
                md.append(f"- generated-data quality {arm} (mean S1/free of training episodes per 1000-episode round): " + ", ".join(f"{np.mean([np.mean(t[i*1000:(i+1)*1000]) for t in T]):.3f}" for i in range(k)))
    # machine nuisance check
    md.append("\n## Machine as a nuisance factor (final checkpoint)\n")
    machines = sorted({r["machine"] for r in E})
    if len(machines) < 2:
        md.append("Only one machine present - no check possible.")
    else:
        ref_m = "i9Win10" if "i9Win10" in machines else machines[0]
        offs = []
        md.append("| variant | arm | machine | n | mean | " + ref_m + " mean (n) | offset (this - " + ref_m + ") | in units of " + ref_m + " SD |\n|---|---|---|---|---|---|---|---|")
        for variant in ("std", "hard"):
            ckf = max(r["ckpt"] for r in E if r["variant"] == variant)
            for arm in ARMS:
                A = [r for r in E if r["variant"] == variant and r["arm"] == arm and r["ckpt"] == ckf]
                base = np.array([r["score"] for r in A if r["machine"] == ref_m])
                for m in machines:
                    if m == ref_m: continue
                    o = np.array([r["score"] for r in A if r["machine"] == m])
                    if len(o) and len(base) > 1:
                        off = o.mean() - base.mean(); z = off / max(base.std(ddof=1), 1e-9); offs.append(off)
                        md.append(f"| {variant} | {arm} | {m} | {len(o)} | {o.mean():.4f} | {base.mean():.4f} ({len(base)}) | {off:+.4f} | {z:+.2f} |")
        if len(offs) > 1:
            offs = np.array(offs); t = stats.ttest_1samp(offs, 0.0)
            md.append(f"\nMean offset over the {len(offs)} (arm x condition) cells: {offs.mean():+.4f} (SD {offs.std(ddof=1):.4f}); one-sample t p = {t.pvalue:.3g}. "
                      "Reading rule (declared in A8): machine counts as a nuisance factor if |mean offset| > 0.004 normalised units (about half a stream SD) or p < 0.05; "
                      "then the i9-only sensitivity family above is the one to quote alongside the full analysis.")
    if repl:
        md.append("\n### Replicate streams (same arm, condition and seed run on another machine/folder; NOT used in any test)\n")
        pm = {(r["arm"], r["variant"], r["seed"], r["ckpt"]): r for r in E}
        ds = []
        md.append("| variant | arm | seed | replicate machine/folder | replicate score | primary score (machine) | difference |\n|---|---|---|---|---|---|---|")
        for r in sorted(repl, key=lambda r: (r["variant"], r["arm"], r["seed"], r["ckpt"])):
            ckf = max(x["ckpt"] for x in E if x["variant"] == r["variant"])
            if r["ckpt"] != ckf: continue
            p = pm.get((r["arm"], r["variant"], r["seed"], r["ckpt"]))
            if p is None: continue
            ds.append(r["score"] - p["score"])
            md.append(f"| {r['variant']} | {r['arm']} | {r['seed']} | {r['machine']} / {r['folder']} | {r['score']:.4f} | {p['score']:.4f} ({p['machine']}) | {r['score']-p['score']:+.4f} |")
        if len(ds) > 1:
            ds = np.array(ds); t = stats.ttest_1samp(ds, 0.0)
            md.append(f"\nPaired replicate difference (replicate - primary) over {len(ds)} streams: mean {ds.mean():+.4f}, SD {ds.std(ddof=1):.4f}, one-sample t p = {t.pvalue:.3g}; max |difference| {np.abs(ds).max():.4f}. Same reading rule as above (|mean| > 0.004 or p < 0.05 = nuisance).")
    (outd / "ctrloff_summary.md").write_text("\n".join(md), encoding="utf-8")
    keys = sorted({k for d in out for k in d})
    with open(outd / "ctrloff_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(out)
    with open(outd / "ctrloff_stream_scores.csv", "w", newline="") as fh:
        keys = [k for k in E[0] if k != "train_frac"]; w = csv.DictWriter(fh, keys, extrasaction="ignore"); w.writeheader(); w.writerows(E)
    print("\n".join(md))


if __name__ == "__main__":
    main()