"""Item 1: paired statistics and multiplicity control for Expt-22d (saved data only)."""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from common import D22C, D22D, RUN, ho, streams, write_csv

rng = np.random.default_rng(20261001)
full = streams(D22D, "full")
assert len(full) == 6 and all(r["n_boxes"] == 60000 for r in full), "expect 6 finished 60k streams"
ref22c = streams(D22C, "full")
assert len(ref22c) == 12
CK = [20000, 24000, 28000, 32000, 36000, 40000, 44000, 48000, 52000, 56000, 60000]
M = {k: ho(full, k) for k in CK}
assert all(v.size == 6 for v in M.values())
seeds = [r["seed"] for r in full]


def boot_mean(x, n=20000):
    return x[rng.integers(0, x.size, (n, x.size))].mean(1)


def signflip_p(d):
    """exact two-sided sign-flip permutation test of mean(d)=0 (2^n flips)"""
    n = d.size
    signs = np.array(list(itertools.product([-1, 1], repeat=n)))
    m = np.abs((signs * d).mean(1))
    return float((m >= abs(d.mean()) - 1e-12).mean())


rows = []
pairs = [(CK[i], CK[i + 1]) for i in range(len(CK) - 1)] + [(20000, 60000), (32000, 60000), (48000, 60000), (52000, 60000)]
for a, b in pairs:
    d = M[b] - M[a]
    bs = boot_mean(d)
    tcrit = stats.t.ppf(0.975, d.size - 1)
    se = d.std(ddof=1) / np.sqrt(d.size)
    ind = M[b].mean() - M[a].mean()
    # independent-sample bootstrap (what summary.md used) for comparison
    ib = boot_mean(M[b]) - boot_mean(M[a])
    rows.append(dict(from_boxes=a, to_boxes=b, n_streams=d.size, mean_diff=d.mean(), sd_diff=d.std(ddof=1),
                     boot_lo=np.percentile(bs, 2.5), boot_hi=np.percentile(bs, 97.5),
                     t_lo=d.mean() - tcrit * se, t_hi=d.mean() + tcrit * se,
                     p_t_paired=float(stats.ttest_1samp(d, 0).pvalue), p_signflip_exact=signflip_p(d),
                     n_streams_up=int((d > 0).sum()),
                     indep_boot_lo=np.percentile(ib, 2.5), indep_boot_hi=np.percentile(ib, 97.5),
                     per_stream_diffs=";".join(f"{x:+.2f}" for x in d)))
write_csv(RUN / "item1a_paired_saturation.csv", rows)
per_stream = [dict(seed=s, **{f"S1@{k}": float(M[k][i]) for k in CK}) for i, s in enumerate(seeds)]
write_csv(RUN / "item1a_per_stream_heldout.csv", per_stream)

# ---------- (b) multiplicity across the five 22d ablations ----------
AB = ["no_concepts", "no_meta", "no_dream", "no_meta_matched_floor", "no_sleep"]
ab = {v: ho(streams(D22D, v), 32000) for v in AB}
assert all(x.size == 4 for x in ab.values())
r22c = ho(ref22c, 32000)
r22d_at32 = M[32000]
pooled = np.concatenate([r22c, r22d_at32])


def welch_normal(a, b):
    from math import erfc, sqrt
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
    return float(erfc(abs((a.mean() - b.mean()) / se) / sqrt(2)))


def welch_t(a, b):
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)


def perm_exact(ref, var):
    """exact two-sided permutation test of difference of means: enumerate every assignment of len(var) of the pooled values"""
    allv = np.concatenate([ref, var])
    n, k = allv.size, var.size
    obs = abs(ref.mean() - var.mean())
    tot = allv.sum()
    cnt = 0
    num = 0
    for idx in itertools.combinations(range(n), k):
        vs = allv[list(idx)].sum()
        diff = abs((tot - vs) / (n - k) - vs / k)
        num += 1
        cnt += diff >= obs - 1e-12
    return cnt / num


def mw(ref, var):
    return float(stats.mannwhitneyu(ref, var, alternative="two-sided").pvalue)


def adjust(p):
    p = np.asarray(p, float)
    m = p.size
    order = np.argsort(p)
    holm = np.empty(m); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i]); holm[i] = min(1.0, run)
    bonf = np.minimum(1.0, p * m)
    bh = np.empty(m); prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]; prev = min(prev, p[i] * m / (rank + 1)); bh[i] = prev
    return holm, bonf, bh


out = []
for refname, ref in (("22c_full_n12", r22c), ("pooled_22c+22d_full_n18", pooled)):
    tests = {"welch_normal(as in summary.md)": welch_normal, "welch_t(df Satterthwaite)": welch_t,
             "permutation_exact": perm_exact, "mannwhitney_U": mw}
    for tname, f in tests.items():
        ps = [f(ref, ab[v]) for v in AB]
        holm, bonf, bh = adjust(ps)
        for i, v in enumerate(AB):
            diff = ref.mean() - ab[v].mean()
            bs = boot_mean(ref) - boot_mean(ab[v])
            out.append(dict(reference=refname, test=tname, variant=v, n_variant=ab[v].size, ref_mean=ref.mean(), var_mean=ab[v].mean(),
                            ref_minus_var=diff, boot_lo=np.percentile(bs, 2.5), boot_hi=np.percentile(bs, 97.5), p_raw=ps[i],
                            p_holm=holm[i], p_bonferroni=bonf[i], p_BH=bh[i],
                            survives_holm_05=holm[i] < 0.05, survives_bonf_05=bonf[i] < 0.05, survives_BH_05=bh[i] < 0.05))
write_csv(RUN / "item1b_ablation_multiplicity.csv", out)
# also: Holm on a six-comparison family would not change the conclusion; report the nominal-vs-adjusted picture for the key tests
json.dump({"ref22c_values": r22c.tolist(), "ref22d_full_at32k": r22d_at32.tolist(),
           "ablation_values": {v: ab[v].tolist() for v in AB}, "saturation_streams": seeds}, open(RUN / "item1_inputs.json", "w"), indent=1)
print("done")
for r in rows:
    print(f"{r['from_boxes']}->{r['to_boxes']}: {r['mean_diff']:+.2f} boot[{r['boot_lo']:+.2f},{r['boot_hi']:+.2f}] t[{r['t_lo']:+.2f},{r['t_hi']:+.2f}] p_t={r['p_t_paired']:.3f} p_sf={r['p_signflip_exact']:.3f} up={r['n_streams_up']}/6 indepCI[{r['indep_boot_lo']:+.2f},{r['indep_boot_hi']:+.2f}]")
for r in out:
    if r["test"] in ("welch_normal(as in summary.md)", "permutation_exact", "welch_t(df Satterthwaite)") and r["reference"].startswith("22c"):
        print(f"{r['reference'][:4]} {r['test'][:12]:12s} {r['variant']:22s} diff {r['ref_minus_var']:+.2f} p {r['p_raw']:.4f} holm {r['p_holm']:.4f} bonf {r['p_bonferroni']:.4f} BH {r['p_BH']:.4f}")
