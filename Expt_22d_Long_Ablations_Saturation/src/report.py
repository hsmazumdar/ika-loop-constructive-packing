"""Expt-22d report: long-horizon ablations (32k) vs the 22c full reference (n=12) and the 60k-box saturation run.
Works on finished streams (streams/*.pkl) AND on partial snapshots (streams_partial/*.pkl) so it can be run while the long
streams are still going; the summary says which numbers are partial."""
from __future__ import annotations

import csv
import json
import pickle
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

from config import Cfg
from report_utils import boot, boot_diff, welch_p, rolling, save

V21 = 83.70
REF22C = Path(__file__).resolve().parents[2] / "Expt_22c_Long_Streams" / "results" / "20261001_044425_run" / "streams"


def _ld(p):
    with open(p, "rb") as fh:
        return pickle.load(fh)


def load(out: Path):
    runs = defaultdict(list)
    done = {p.stem for p in (out / "streams").glob("*.pkl")}
    for p in sorted((out / "streams").glob("*.pkl")):
        r = _ld(p); r["partial"] = False; runs[r["variant"]].append(r)
    for p in sorted((out / "streams_partial").glob("*.pkl")):
        if p.stem in done:
            continue
        try:
            r = _ld(p)
        except Exception:
            continue
        runs[r["variant"]].append(r)
    return runs


def load_ref():
    rs = []
    for p in sorted(REF22C.glob("full_*.pkl")):
        r = _ld(p); r["partial"] = False; rs.append(r)
    return rs


def at(rs, k):
    return [r["evals"][k]["S1"].mean() for r in rs if k in r["evals"]]


def build_report(out: Path, cfg: Cfg) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
    from learner_ref import hand_ref, uniform_ref

    runs = load(out)
    ref = load_ref()
    man = json.loads((out / "manifest.json").read_text())
    NL, NA = man["long_boxes"], man["abl_boxes"]
    full = runs.get("full", [])
    nfin = sum(1 for v in runs.values() for r in v if not r["partial"])
    ntot = len([x for x in (out / "streams_partial").glob("*.pkl")] + [x for x in (out / "streams").glob("*.pkl") if not (out / "streams_partial" / x.name).exists()])
    hand14 = float(hand_ref(cfg, cfg.budget, min(cfg.eval_boxes, 1000)).mean())
    unif14 = float(np.mean([r["evals"][0]["S1"].mean() for r in (ref or full)]))
    L: list[str] = []
    A = L.append
    status = f"{nfin} streams finished, {ntot - nfin} still running (partial snapshots)" if ntot > nfin else f"all {nfin} streams finished"
    prog = {v: (min(r["n_boxes"] for r in rs), max(r["n_boxes"] for r in rs)) for v, rs in runs.items()}

    # ---------------- ablations at the long horizon -------------------------------------------------------------------------
    ref_v = at(ref, NA)
    full22d_v = at(full, NA)
    pooled = ref_v + full22d_v
    abl = []
    for v, rs in runs.items():
        ho = at(rs, NA)
        if not ho or v == "full":
            continue
        m, lo, hi = boot(ho)
        d = boot_diff(ref_v, ho) if ref_v and len(ho) > 1 else (np.nan,) * 3
        dp = boot_diff(pooled, ho) if pooled and len(ho) > 1 else (np.nan,) * 3
        abl.append(dict(variant=v, n=len(ho), n_running=len(rs) - len(ho), boxes=NA, S1=m, lo=lo, hi=hi, ref_minus=d[0], r_lo=d[1], r_hi=d[2],
                        p_ref=welch_p(ref_v, ho) if ref_v else np.nan, pooled_minus=dp[0], p_lo=dp[1], p_hi=dp[2],
                        train_last3k=float(np.mean([r["S1"][NA - 3000:NA].mean() for r in rs if r["n_boxes"] >= NA])),
                        frac90=float(np.mean([(r["evals"][NA]["S1"] >= 90).mean() for r in rs if NA in r["evals"]]))))
    abl.sort(key=lambda d: -d["S1"])
    if abl:
        with open(out / "leaderboard_long_ablations.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(abl[0])); w.writeheader(); w.writerows(abl)
    fm22c = boot(ref_v) if ref_v else (np.nan,) * 3
    fm22d = boot(full22d_v) if full22d_v else (np.nan,) * 3
    fmp = boot(pooled) if pooled else (np.nan,) * 3
    bars = ([dict(variant="full (22c, n=%d)" % len(ref_v), S1=fm22c[0], lo=fm22c[1], hi=fm22c[2])] if ref_v else []) + \
           ([dict(variant="full (22d 60k-stream @%d, n=%d)" % (NA, len(full22d_v)), S1=fm22d[0], lo=fm22d[1], hi=fm22d[2])] if full22d_v else []) + \
           [dict(variant=f"{d['variant']} (n={d['n']})", S1=d["S1"], lo=d["lo"], hi=d["hi"]) for d in abl]
    if bars:
        fig, ax = plt.subplots(figsize=(8, 4.4))
        err = [[b["S1"] - b["lo"] if not np.isnan(b["lo"]) else 0 for b in bars], [b["hi"] - b["S1"] if not np.isnan(b["hi"]) else 0 for b in bars]]
        ax.barh([b["variant"] for b in bars], [b["S1"] for b in bars], xerr=err, color=["tab:blue"] * (1 + bool(full22d_v) if ref_v else 0) + ["tab:gray"] * len(abl), alpha=0.85)
        ax.axvline(V21, color="tab:orange", ls="-.", label="V21 final"); ax.axvline(hand14, color="tab:green", ls=":", label="hand rule (ref only)")
        ax.axvline(unif14, color="gray", ls="--", label="uniform")
        ax.set_xlim(60, max(hand14, max(b["S1"] for b in bars)) + 2); ax.invert_yaxis(); ax.legend(fontsize=7, loc="lower left")
        ax.set_xlabel(f"held-out S1 after {NA} boxes (mean, 95% CI over replicate streams)")
        fig.tight_layout(); save(fig, out, "fig_long_ablation_bars"); plt.close(fig)

    # ablation learning curves
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    groups = [("full 22c", ref, "k")] + [(v, rs, None) for v, rs in runs.items()]
    for name, rs, col in groups:
        if not rs:
            continue
        ks = sorted(set.intersection(*[set(r["evals"]) for r in rs]))
        if not ks:
            continue
        mm = [np.mean([r["evals"][k]["S1"].mean() for r in rs]) for k in ks]
        ax.plot(ks, mm, marker="o", ms=2.5, color=col, lw=2 if col else 1.2, label=f"{name} (n={len(rs)})")
    ax.axhline(V21, color="tab:orange", ls="-.", lw=1); ax.axhline(hand14, color="tab:green", ls=":", lw=1)
    ax.set_xlabel("boxes of learning before freezing"); ax.set_ylabel("held-out S1"); ax.legend(fontsize=6.5, ncol=2)
    fig.tight_layout(); save(fig, out, "fig_long_ablation_curves"); plt.close(fig)

    # ---------------- saturation (full, 60k) ------------------------------------------------------------------------------------
    sat_rows = []
    if full:
        ks_all = sorted(set().union(*[set(r["evals"]) for r in full]))
        for k in ks_all:
            vals = at(full, k)
            m, lo, hi = boot(vals)
            sat_rows.append(dict(box=k, n=len(vals), S1=m, lo=lo, hi=hi,
                                 frac90=float(np.mean([(r["evals"][k]["S1"] >= 90).mean() for r in full if k in r["evals"]])),
                                 hidden=float(np.mean([r["evals"][k]["hidden"] for r in full if k in r["evals"]])),
                                 concepts=float(np.mean([r["evals"][k]["concepts"] for r in full if k in r["evals"]]))))
        with open(out / "saturation_checkpoints.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(sat_rows[0])); w.writeheader(); w.writerows(sat_rows)
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
        for r in full:
            ks = sorted(r["evals"])
            ax[0].plot(ks, [r["evals"][k]["S1"].mean() for k in ks], color="tab:blue", alpha=0.25, lw=0.8)
        full_ref_ks = sorted(set.intersection(*[set(r["evals"]) for r in ref])) if ref else []
        if ref:
            m22 = [np.mean(at(ref, k)) for k in full_ref_ks]
            ax[0].plot(full_ref_ks, m22, color="tab:purple", lw=1.4, ls="--", label=f"22c full mean (n={len(ref)})")
        ax[0].plot([r["box"] for r in sat_rows], [r["S1"] for r in sat_rows], "o-", color="tab:blue", ms=3, lw=2, label="22d full (60k streams) mean")
        ax[0].fill_between([r["box"] for r in sat_rows], [r["lo"] if not np.isnan(r["lo"]) else r["S1"] for r in sat_rows],
                           [r["hi"] if not np.isnan(r["hi"]) else r["S1"] for r in sat_rows], color="tab:blue", alpha=0.25)
        for yv, c, lb in ((V21, "tab:orange", f"V21 final ({V21})"), (hand14, "tab:green", f"hand rule, ref only ({hand14:.1f})"), (unif14, "gray", f"uniform ({unif14:.1f})")):
            ax[0].axhline(yv, color=c, ls=":", label=lb)
        ax[0].set_xlabel("boxes of learning before freezing"); ax[0].set_ylabel("held-out S1")
        ax[0].set_title("saturation: held-out (frozen) S1, thin = replicate, band = 95% CI"); ax[0].legend(fontsize=7, loc="lower right")
        nmax = max(r["n_boxes"] for r in full)
        W = 2000
        grid = np.arange(W, nmax + 1, 500)
        Mx = [[rolling(r["S1"], W)[g - W] for g in grid if g <= r["n_boxes"]] for r in full]
        for row in Mx:
            ax[1].plot(grid[:len(row)], row, color="tab:blue", alpha=0.25, lw=0.8)
        T = min(len(row) for row in Mx)
        if T:
            mu = np.mean([row[:T] for row in Mx], 0)
            ax[1].plot(grid[:T], mu, color="tab:blue", lw=2, label="22d full mean (rolling 2k boxes)")
        ax[1].axhline(hand14, color="tab:green", ls=":"); ax[1].set_xlabel("boxes"); ax[1].set_ylabel("training S1 (exploring)")
        ax[1].set_title("training curve"); ax[1].legend(fontsize=7)
        fig.tight_layout(); save(fig, out, "fig_saturation"); plt.close(fig)

    # self-modification timeline for the long streams
    if full:
        keys = ["tau", "eps", "lr", "dream", "sleep_every", "stm", "concepts", "hidden"]
        fig, axs = plt.subplots(2, 4, figsize=(13, 5.5))
        for ax, k in zip(axs.ravel(), keys):
            for r in full:
                hl = r["hyper_log"]
                ax.plot([h["box"] for h in hl], [h[k] for h in hl], alpha=0.3, lw=0.8, color="tab:blue")
            T = min(len(r["hyper_log"]) for r in full)
            if T:
                ax.plot([full[0]["hyper_log"][i]["box"] for i in range(T)], [np.mean([r["hyper_log"][i][k] for r in full]) for i in range(T)], "k", lw=1.8)
            ax.set_title(k); ax.set_xlabel("boxes")
        fig.suptitle("Self-modification timeline, long streams (thin = replicate, thick = mean)")
        fig.tight_layout(); save(fig, out, "fig_self_modification_long"); plt.close(fig)
    ev_count = Counter(); ev_dir = defaultdict(lambda: [0, 0]); cap = []
    for r in full:
        for e in r["events"]:
            if e["kind"] == "hyper":
                ev_count[e["param"]] += 1; ev_dir[e["param"]][0 if e["new"] > e["old"] else 1] += 1
            else:
                cap.append(e)
    if full:
        with open(out / "self_modification_events_long.csv", "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["seed", "box", "kind", "param", "old", "new", "reason"])
            for r in full:
                for e in r["events"]:
                    w.writerow([r["seed"], e["box"], e["kind"], e.get("param", "capacity"), e.get("old", e.get("from")), e.get("new", e.get("to")), e["reason"]])

    # matched-floor diagnostic: training S1 and tau of full/no_meta/matched in the last blocks
    def tr_block(rs, a, b):
        v = [r["S1"][a:b].mean() for r in rs if r["n_boxes"] >= b]
        return (float(np.mean(v)), len(v)) if v else (np.nan, 0)

    # ---------------- summary -----------------------------------------------------------------------------------------------------
    A("# Expt-22d - long-horizon ablations and saturation of the organic value learner\n")
    A(f"Run `{out.name}` | code hash `{man['code_hash']}` | generated {datetime.now():%Y-%m-%d %H:%M} IST | **{status}**\n")
    A(f"Design: `full` x {man['long_reps']} streams of {NL} boxes (seeds {man['seed_long']}+; held-out checkpoints every 4k boxes after 20k); ablations x {man['abl_reps']} streams of {NA} boxes (seeds {man['seed_abl']}+): {', '.join(man['abl_names'])}. Reference = Expt-22c `full`, 12 streams (seeds 100-111) at {NA} boxes. Held-out = frozen memory on {man["cfg"]["eval_boxes"]} fresh boxes (same boxes as 22b/22c). Progress (min-max boxes done per variant): " + ", ".join(f"{v} {a}-{b}" for v, (a, b) in prog.items()) + ".\n")
    A("Reminder: `no_meta` = fixed hyperparameters + V21-style anneal (tau 2.0->0.35, eps 0.10->0.01 over 15k boxes, then constant); `no_meta_matched_floor` = fixed hyperparameters, tau 2.0->0.25 and eps 0.10->0.0077 linearly over 32k boxes (the floors the meta-controller reached in 22c; the meta-controller's own tau trajectory is shown in fig_self_modification_long). `no_sleep` = online TD only; `no_dream`; `no_concepts`.\n")
    A(f"## 1. Long-horizon ablations (held-out S1 after {NA} boxes)\n")
    if ref_v:
        A(f"- Reference `full` (22c, n={len(ref_v)}): **{fm22c[0]:.2f} ({fm22c[1]:.2f}-{fm22c[2]:.2f})**." + (f" `full` streams of this run at the same 32k checkpoint (n={len(full22d_v)}): {fm22d[0]:.2f} ({fm22d[1]:.2f}-{fm22d[2]:.2f}); pooled n={len(pooled)}: {fmp[0]:.2f} ({fmp[1]:.2f}-{fmp[2]:.2f})." if full22d_v else ""))
    A("\n| variant | n finished (+running) | S1 | 95% CI | full(22c) minus variant | 95% CI | p (Welch) | full(pooled) minus variant (95% CI) | frac S1>=90 | train S1 last 3k |\n|---|---|---|---|---|---|---|---|---|---|")
    for d in abl:
        A(f"| {d['variant']} | {d['n']} (+{d['n_running']}) | {d['S1']:.2f} | {d['lo']:.2f} - {d['hi']:.2f} | {d['ref_minus']:+.2f} | {d['r_lo']:+.2f}, {d['r_hi']:+.2f} | {d['p_ref']:.3g} | {d['pooled_minus']:+.2f} ({d['p_lo']:+.2f}, {d['p_hi']:+.2f}) | {d['frac90']:.3f} | {d['train_last3k']:.2f} |")
    if not abl:
        A("| (no variant has reached the long-horizon checkpoint yet) |||||||||")
    A(f"\n![bars](fig_long_ablation_bars.png)\n![curves](fig_long_ablation_curves.png)\n")
    if "no_meta_matched_floor" in runs and "no_meta" in runs:
        a, b = tr_block(runs["no_meta"], NA - 3000, NA)[0], tr_block(runs["no_meta_matched_floor"], NA - 3000, NA)[0]
        A(f"Floor diagnostic: training S1 over boxes {NA-3000}-{NA}: no_meta {a:.2f}, no_meta_matched_floor {b:.2f}, full(22c) {np.mean([r['S1'][NA-3000:NA].mean() for r in ref]):.2f}.\n")
    A("## 2. Saturation run (full, long streams)\n")
    if sat_rows:
        A("| boxes learned | S1 | 95% CI | frac S1>=90 | hidden | concepts | replicates |\n|---|---|---|---|---|---|---|")
        for r in sat_rows:
            A(f"| {r['box']} | {r['S1']:.2f} | {r['lo']:.2f} - {r['hi']:.2f} | {r['frac90']:.3f} | {r['hidden']:.0f} | {r['concepts']:.0f} | {r['n']} |")
        A("\n![sat](fig_saturation.png)\n")
        cks = [r for r in sat_rows if r["n"] == len(full) and r["box"] >= 28000]
        if len(cks) >= 2:
            k0, k1 = cks[-2]["box"], cks[-1]["box"]
            diff = boot_diff(at(full, k1), at(full, k0))
            A(f"Last common interval {k0}->{k1}: change in held-out S1 {diff[0]:+.2f} (95% CI {diff[1]:+.2f}, {diff[2]:+.2f}) over {len(full)} replicates (independent-sample bootstrap; replicate streams are the same across checkpoints so a paired estimate would be tighter).\n")
    else:
        A("(no checkpoints yet)\n")
    A("## 3. Self-modification in the long streams (full)\n")
    if full:
        tot = sum(ev_count.values())
        A(f"{tot} hyperparameter changes over {len(full)} streams so far ({tot/len(full):.0f}/stream), {len(cap)} capacity tests ({sum(1 for e in cap if e['grow'])} accepted). " +
          "; ".join(f"{k}: {c} (up {ev_dir[k][0]}, down {ev_dir[k][1]})" for k, c in ev_count.most_common()) + ". Full event list: `self_modification_events_long.csv`.\n")
        A("![sm](fig_self_modification_long.png)\n")
    # ---------------- findings (generated strictly from the numbers) -----------------------------------------------------------------
    A("## 4. Paper-ready findings (auto-generated from the numbers above; PARTIAL if runs unfinished)\n")
    sig, nsig = [], []
    for d in abl:
        txt = f"`{d['variant']}` (n={d['n']}): 22c-full minus variant {d['ref_minus']:+.2f} (CI {d['r_lo']:+.2f}, {d['r_hi']:+.2f})"
        if d["n"] < 3:
            nsig.append(txt + " - too few finished replicates to judge")
        elif d["r_lo"] > 0:
            sig.append(txt + " -> full is significantly better")
        elif d["r_hi"] < 0:
            sig.append(txt + " -> the ABLATED variant is significantly BETTER than full (component not helping at this horizon)")
        else:
            nsig.append(txt + " -> not distinguishable (CI includes 0)")
    A("**Supported (CI excludes 0):**\n" + ("\n".join("- " + s for s in sig) if sig else "- none yet"))
    A("\n**Not supported / inconclusive:**\n" + ("\n".join("- " + s for s in nsig) if nsig else "- none"))
    if sat_rows:
        last = sat_rows[-1]
        A(f"\n**Saturation:** latest long-stream checkpoint {last['box']} boxes: S1 {last['S1']:.2f} ({last['lo']:.2f}-{last['hi']:.2f}), n={last['n']}; frac S1>=90 {last['frac90']:.3f}. " +
          ("The long streams have completed; a plateau claim requires the final intervals' CIs to include 0 (see section 2)." if last["box"] >= NL else "The long streams are NOT finished; no saturation claim can be made yet."))
    A("\n**Caveats:** ablations use 4 replicates (low power; CIs are over replicate streams only; the 1,200 evaluation boxes are fixed and shared by all variants); the reference full(22c) used different seeds (100-111) than the ablations (200-203), which is valid but not paired; V21 CI treats V21 as a constant; hand rule is a reference only.")
    (out / "summary.md").write_text("\n".join(L), encoding="utf-8")

