"""Figure for item 1a: per-stream trajectories and paired consecutive differences (reads saved CSVs only)."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUN = Path(__file__).resolve().parents[1] / "results" / "20261001_122457_run"
ps = list(csv.DictReader(open(RUN / "item1a_per_stream_heldout.csv")))
pd_ = list(csv.DictReader(open(RUN / "item1a_paired_saturation.csv")))
ck = [int(k.split("@")[1]) for k in ps[0] if k.startswith("S1@")]
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for r in ps:
    ax[0].plot([c / 1000 for c in ck], [float(r[f"S1@{c}"]) for c in ck], marker="o", ms=3, lw=1, label=f"s{r['seed']}")
ax[0].set_xlabel("training boxes (k)"); ax[0].set_ylabel("held-out S1 (1,200 episodes)"); ax[0].legend(fontsize=7, ncol=2)
ax[0].set_title("22d full streams (n=6)")
cons = [r for r in pd_ if int(r["to_boxes"]) - int(r["from_boxes"]) == 4000]
x = np.arange(len(cons))
m = np.array([float(r["mean_diff"]) for r in cons])
lo = np.array([float(r["boot_lo"]) for r in cons]); hi = np.array([float(r["boot_hi"]) for r in cons])
ax[1].errorbar(x, m, yerr=[m - lo, hi - m], fmt="o", capsize=3)
for i, r in enumerate(cons):
    d = [float(v) for v in r["per_stream_diffs"].split(";")]
    ax[1].scatter([i] * len(d), d, s=8, c="gray", alpha=.6, zorder=0)
ax[1].axhline(0, c="k", lw=.6)
ax[1].set_xticks(x); ax[1].set_xticklabels([f"{int(r['from_boxes'])//1000}->{int(r['to_boxes'])//1000}k" for r in cons], rotation=45, fontsize=8)
ax[1].set_ylabel("paired difference in S1"); ax[1].set_title("consecutive checkpoints: mean, paired bootstrap 95% CI (grey = streams)")
fig.tight_layout(); fig.savefig(RUN / "fig_item1a_paired_differences.png", dpi=130)
print("saved")