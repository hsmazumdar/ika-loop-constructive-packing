"""Baseline-day analysis (DESIGN.md section 6, amendment A1): stream-level normalised held-out scores.
Per stream and checkpoint: mean over the four test splits (equal weight) of mean(S1/ref) over the 50 problems x 3 reps.
ref = frozen per-(problem, condition) reference from results/refs. Tests (per variant x condition family, Holm over the family):
learner arms vs each other (Welch-t primary, exact/MC permutation and Mann-Whitney sensitivity) and each learner arm vs the hand rule and CEM-hand rule
(one-sample Welch-style t on per-stream means vs the reference's mean over the same problems). Writes results/baseline_streams.csv, baseline_summary.csv/.md."""
import sys, pathlib, csv, glob, json, itertools
import numpy as np
from scipy import stats
ROOT = pathlib.Path(__file__).resolve().parents[1]
SPLITS = ("test_iid", "test_size", "test_piece", "test_both")
RNG = np.random.default_rng(20261002)


def load_refs():
    refs = {}
    for f in glob.glob(str(ROOT / "results" / "refs" / "refs_*.csv")):
        for r in csv.DictReader(open(f)):
            refs[(r["variant"], r["cond"], r["split"], int(r["index"]))] = r
    return refs


def stream_scores(refs):
    rows = []
    for f in sorted(glob.glob(str(ROOT / "results" / "streams" / "*.json"))):
        d = json.load(open(f))
        for ck, ev in d["evals"].items():
            per = {}
            for sp in SPLITS:
                S1 = np.array(ev[sp]["S1"], float).reshape(50, 3)
                ref = np.array([float(refs[(d["variant"], d["cond"], sp, j)]["ref"]) for j in range(50)])
                per[sp] = float((S1 / ref[:, None]).mean())
                if "S1_greedy" in ev[sp]:
                    Sg = np.array(ev[sp]["S1_greedy"], float).reshape(50, 3)
                    per[sp + "_greedy"] = float((Sg / ref[:, None]).mean())
            rows.append(dict(arm=d["arm"], variant=d["variant"], cond=d["cond"], seed=d["seed"], ckpt=int(ck),
                             score=float(np.mean([per[s] for s in SPLITS])), **{s: per[s] for s in SPLITS},
                             greedy=float(np.mean([per[s + "_greedy"] for s in SPLITS])) if "test_iid_greedy" in per else float("nan"),
                             train_frac_last1k=float(np.mean(d["train_frac"][-1000:]))))
    return rows


def boot_ci(x, n=10000):
    x = np.asarray(x, float)
    if len(x) < 2:
        return (float("nan"),) * 2
    m = x[RNG.integers(0, len(x), (n, len(x)))].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def iqm(x):
    x = np.sort(np.asarray(x)); k = len(x) // 4
    return float(x[k:len(x) - k].mean()) if len(x) - 2 * k > 0 else float(x.mean())


def perm_p(a, b, n=20000):
    a, b = np.asarray(a), np.asarray(b)
    obs = abs(a.mean() - b.mean()); pool = np.concatenate([a, b]); c = 0
    from math import comb
    if comb(len(pool), len(a)) <= 20000:
        for idx in itertools.combinations(range(len(pool)), len(a)):
            m = np.zeros(len(pool), bool); m[list(idx)] = True
            c += abs(pool[m].mean() - pool[~m].mean()) >= obs - 1e-12
        return c / comb(len(pool), len(a))
    for _ in range(n):
        RNG.shuffle(pool); c += abs(pool[:len(a)].mean() - pool[len(a):].mean()) >= obs - 1e-12
    return (c + 1) / (n + 1)


def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * ps[i]); adj[i] = min(run, 1.0)
    return adj


def main():
    refs = load_refs()
    rows = stream_scores(refs)
    if not rows:
        print("no streams yet"); return
    with open(ROOT / "results" / "baseline_streams.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # reference means on the same problems (normalised by the same ref), equal split weights
    def refmean(variant, cond, col):
        v = []
        for sp in SPLITS:
            v.append(np.mean([float(refs[(variant, cond, sp, j)][col]) / float(refs[(variant, cond, sp, j)]["ref"]) for j in range(50)]))
        return float(np.mean(v))
    out, md = [], []
    fams = sorted({(r["variant"], r["cond"]) for r in rows})
    for variant, cond in fams:
        R = [r for r in rows if r["variant"] == variant and r["cond"] == cond]
        ck_final = max(r["ckpt"] for r in R)
        refv = {c: refmean(variant, cond, c) for c in ("uniform", "hand", "cemhand", "rollout_beam")}
        md.append(f"\n### {variant} / {cond}  (final checkpoint {ck_final}; reference means on the same test problems: uniform {refv['uniform']:.3f}, hand {refv['hand']:.3f}, CEM-hand {refv['cemhand']:.3f}, rollout-beam {refv['rollout_beam']:.3f})\n")
        md.append("| arm | streams | " + " | ".join(f"{c//1000}k" if c else "0" for c in sorted({r['ckpt'] for r in R})) + " | final mean [95% CI] | median | IQM | frac. test_iid..test_both (final) |")
        md.append("|---|---|" + "---|" * (len(sorted({r['ckpt'] for r in R})) + 3))
        finals = {}
        for arm in ("N", "DQN", "PPO"):
            A = [r for r in R if r["arm"] == arm]
            if not A:
                continue
            cks = sorted({r["ckpt"] for r in R})
            means = []
            for c in cks:
                v = [r["score"] for r in A if r["ckpt"] == c]
                means.append(f"{np.mean(v):.3f}" if v else "-")
            fv = np.array([r["score"] for r in A if r["ckpt"] == ck_final])
            if len(fv) == 0:
                md.append(f"| {arm} | 0 | " + " | ".join(means) + " | (no final yet) | | | |"); continue
            finals[arm] = fv
            if arm == "PPO":
                ppo4 = [r["score"] for r in A if r["ckpt"] == ck_final and r["seed"] <= 2303]
            lo, hi = boot_ci(fv)
            sp = ", ".join(f"{np.mean([r[s] for r in A if r['ckpt']==ck_final]):.3f}" for s in SPLITS)
            md.append(f"| {arm} | {len(fv)} | " + " | ".join(means) + f" | {fv.mean():.3f} [{lo:.3f}, {hi:.3f}] | {np.median(fv):.3f} | {iqm(fv):.3f} | {sp} |")
            out.append(dict(variant=variant, cond=cond, arm=arm, n=len(fv), final_ckpt=ck_final, mean=fv.mean(), lo=lo, hi=hi, median=float(np.median(fv)), iqm=iqm(fv)))
        ppo4 = locals().get("ppo4") if "PPO" in finals else None
        if ppo4 is not None and 1 < len(ppo4) < len(finals["PPO"]):
            md.append(f"\nPPO pre-declared 4-seed subset (seeds 2300-2303; A4): mean {np.mean(ppo4):.3f} (n={len(ppo4)}) vs all-streams mean {finals[chr(80)+chr(80)+chr(79)].mean():.3f} (n={len(finals[chr(80)+chr(80)+chr(79)])})")
        # family of comparisons
        comps = []
        for a, b in itertools.combinations(finals, 2):
            comps.append((f"{a} vs {b}", finals[a], finals[b], None))
        for a in finals:
            for rc in ("uniform", "hand", "cemhand"):
                comps.append((f"{a} vs {rc} (ref mean {refv[rc]:.3f})", finals[a], None, refv[rc]))
        if comps:
            pw, pp, pm = [], [], []
            for name, x, y, c in comps:
                if y is not None and len(x) > 1 and len(y) > 1:
                    pw.append(stats.ttest_ind(x, y, equal_var=False).pvalue); pp.append(perm_p(x, y)); pm.append(stats.mannwhitneyu(x, y, alternative="two-sided").pvalue)
                elif y is not None:
                    pw.append(float("nan")); pp.append(float("nan")); pm.append(float("nan"))
                else:
                    pw.append(stats.ttest_1samp(x, c).pvalue if len(x) > 1 else float("nan")); pp.append(float("nan")); pm.append(float("nan"))
            hw = holm(np.nan_to_num(np.array(pw), nan=1.0))
            md.append("\n| comparison (final ckpt) | mean diff | Welch-t p | Holm(Welch) | permutation p | Mann-Whitney p |\n|---|---|---|---|---|---|")
            for (name, x, y, c), a, b, m_, h in zip(comps, pw, pp, pm, hw):
                diff = x.mean() - (y.mean() if y is not None else c)
                md.append(f"| {name} | {diff:+.3f} | {a:.4g} | {h:.4g} | {b:.4g} | {m_:.4g} |")
                out.append(dict(variant=variant, cond=cond, comparison=name, diff=diff, p_welch=a, p_holm=h, p_perm=b, p_mwu=m_))
    keys = sorted({k for d in out for k in d})
    with open(ROOT / "results" / "baseline_summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(out)
    (ROOT / "results" / "baseline_summary.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()