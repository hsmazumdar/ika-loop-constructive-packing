"""Expt-22b report: tables (markdown/csv) and paper figures (PNG + PDF) from <run>/streams/*.pkl."""

from __future__ import annotations

import csv
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from config import Cfg

V21 = 83.70  # Expt-21 final held-out S1 (Expt_21 results/20260930_233539_run, 12 replicates, 2000 boxes)


def load(out: Path):
    runs = defaultdict(list)
    for p in sorted((out / "streams").glob("*.pkl")):
        with open(p, "rb") as fh:
            r = pickle.load(fh)
        runs[r["variant"]].append(r)
    return runs


def boot(v, n=4000, seed=0):
    v = np.asarray([x for x in v if not np.isnan(x)], float)
    if v.size == 0:
        return np.nan, np.nan, np.nan
    if v.size < 3:
        return float(v.mean()), np.nan, np.nan
    rng = np.random.default_rng(seed)
    m = v[rng.integers(0, v.size, (n, v.size))].mean(1)
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def boot_diff(a, b, n=5000, seed=1):
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(seed)
    d = a[rng.integers(0, a.size, (n, a.size))].mean(1) - b[rng.integers(0, b.size, (n, b.size))].mean(1)
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def welch_p(a, b):
    from math import erfc, sqrt
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.size < 2 or b.size < 2:
        return np.nan
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
    if se == 0:
        return 0.0 if a.mean() != b.mean() else 1.0
    return float(erfc(abs((a.mean() - b.mean()) / se) / sqrt(2)))  # normal approximation, two-sided


def save(fig, out: Path, name: str):
    fig.savefig(out / f"{name}.png", dpi=150)
    fig.savefig(out / f"{name}.pdf")


def rolling(x, w):
    c = np.cumsum(np.insert(np.asarray(x, float), 0, 0.0))
    return (c[w:] - c[:-w]) / w


def _errs(rows):
    return [[r["S1"] - r["lo"] if not np.isnan(r["lo"]) else 0 for r in rows], [r["hi"] - r["S1"] if not np.isnan(r["hi"]) else 0 for r in rows]]


def build_report(out: Path, cfg: Cfg) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
    from learner_ref import hand_ref, uniform_ref

    runs = load(out)
    man = json.loads((out / "manifest.json").read_text())
    full = runs["full"]
    N = man["boxes"]
    NA = man["abl_boxes"]
    hand14 = float(hand_ref(cfg, cfg.budget, min(cfg.eval_boxes, 1000)).mean())
    unif14 = float(np.mean([r["evals"][0]["S1"].mean() for r in full]))
    L: list[str] = []
    A = L.append

    # ---- training curve ---------------------------------------------------------------------------------------
    W, STEP = 500, 250
    grid = np.arange(W, N + 1, STEP)
    M = np.array([[rolling(r["S1"], W)[g - W] for g in grid] for r in full])
    mu = M.mean(0)
    se = M.std(0, ddof=1) / np.sqrt(len(full)) if len(full) > 1 else np.zeros_like(mu)
    with open(out / "learning_curve_full.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["box", "train_S1_roll500", "ci_lo", "ci_hi"])
        for g, m_, s_ in zip(grid, mu, se):
            w.writerow([int(g), f"{m_:.3f}", f"{m_ - 2.2*s_:.3f}", f"{m_ + 2.2*s_:.3f}"])

    # ---- held-out checkpoints ---------------------------------------------------------------------------------
    def ck_table(v):
        rs = runs[v]
        ks = sorted(set.intersection(*[set(r["evals"]) for r in rs]))
        rows = []
        for k in ks:
            vals = [r["evals"][k]["S1"].mean() for r in rs]
            m, lo, hi = boot(vals)
            rows.append(dict(variant=v, box=k, n=len(vals), S1=m, lo=lo, hi=hi,
                             attempts=float(np.mean([r["evals"][k]["attempts"].mean() for r in rs])),
                             frac90=float(np.mean([(r["evals"][k]["S1"] >= 90).mean() for r in rs])),
                             hidden=float(np.mean([r["evals"][k]["hidden"] for r in rs])),
                             concepts=float(np.mean([r["evals"][k]["concepts"] for r in rs]))))
        return rows

    allck = {v: ck_table(v) for v in runs}
    with open(out / "heldout_checkpoints.csv", "w", newline="") as fh:
        rows = [r for v in allck.values() for r in v]
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    fin = [r["evals"][N]["S1"].mean() for r in full]
    fm, flo, fhi = boot(fin)
    # paired-by-replicate-index is not meaningful (independent streams): report difference of means with bootstrap
    d21 = boot_diff(fin, [V21] * 2) if False else (fm - V21, flo - V21, fhi - V21)

    # fig 1
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for i in range(len(full)):
        ax[0].plot(grid, M[i], color="tab:blue", alpha=0.12, lw=0.7)
    ax[0].plot(grid, mu, color="tab:blue", lw=2, label=f"V22b training S1 (mean of {len(full)} reps)")
    ax[0].fill_between(grid, mu - 2.2 * se, mu + 2.2 * se, color="tab:blue", alpha=0.3)
    for a_ in ax:
        a_.axhline(unif14, color="gray", ls="--", label=f"uniform natural ({unif14:.1f})")
        a_.axhline(V21, color="tab:orange", ls="-.", label=f"V21 final held-out ({V21})")
        a_.axhline(hand14, color="tab:green", ls=":", label=f"hand rule, reference only ({hand14:.1f})")
    rows = allck["full"]
    x = [r["box"] for r in rows]
    ax[1].plot(x, [r["S1"] for r in rows], "o-", ms=3, color="tab:blue", label="V22b full (frozen memory)")
    ax[1].fill_between(x, [r["lo"] if not np.isnan(r["lo"]) else r["S1"] for r in rows],
                       [r["hi"] if not np.isnan(r["hi"]) else r["S1"] for r in rows], color="tab:blue", alpha=0.3)
    ax[1].set_xscale("symlog", linthresh=1000)
    ax[0].set_title("training curve (exploring)"); ax[1].set_title(f"held-out ({cfg.eval_boxes} fresh boxes), 95% CI over replicates")
    ax[0].set_xlabel("boxes"); ax[1].set_xlabel("boxes of learning before freezing")
    ax[0].set_ylabel("S1"); ax[1].set_ylabel("S1"); ax[1].legend(fontsize=7, loc="lower right")
    fig.tight_layout(); save(fig, out, "fig1_learning_curves"); plt.close(fig)

    # ---- ablations ----------------------------------------------------------------------------------------------
    abl = []
    fh_ = [r["evals"][NA]["S1"].mean() for r in full if NA in r["evals"]]
    for v, rs in runs.items():
        ho = [r["evals"][NA]["S1"].mean() for r in rs if NA in r["evals"]]
        m, lo, hi = boot(ho)
        d = boot_diff(fh_, ho) if v != "full" and len(ho) > 1 else (np.nan,) * 3
        abl.append(dict(variant=v, n=len(ho), boxes=NA, S1=m, lo=lo, hi=hi, full_minus=d[0], d_lo=d[1], d_hi=d[2],
                        p=welch_p(fh_, ho) if v != "full" else np.nan,
                        train_last3k=float(np.mean([r["S1"][max(0, NA - 3000):NA].mean() for r in rs])),
                        min_per_stream=float(np.mean([r["runtime_s"] for r in rs]) / 60)))
    abl.sort(key=lambda d: -d["S1"])
    with open(out / "leaderboard_ablations.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(abl[0])); w.writeheader(); w.writerows(abl)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.barh([d["variant"] for d in abl], [d["S1"] for d in abl], xerr=_errs(abl), color="tab:blue", alpha=0.8)
    ax.axvline(V21, color="tab:orange", ls="-.", label="V21"); ax.axvline(hand14, color="tab:green", ls=":", label="hand rule (ref)")
    ax.axvline(unif14, color="gray", ls="--", label="uniform")
    ax.set_xlim(60, max(max(d["S1"] for d in abl), hand14) + 2)
    ax.invert_yaxis(); ax.legend(fontsize=7); ax.set_xlabel(f"held-out S1 after {NA} boxes (mean, 95% CI over replicates)")
    fig.tight_layout(); save(fig, out, "fig3_ablation_bars"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for v in runs:
        rr = [r for r in allck[v] if r["box"] <= NA]
        if rr:
            ax.plot([r["box"] for r in rr], [r["S1"] for r in rr], marker="o", ms=2.5, label=f"{v} (n={rr[0]['n']})")
    ax.axhline(V21, color="tab:orange", ls="-.", lw=1); ax.axhline(hand14, color="tab:green", ls=":", lw=1)
    ax.set_xscale("symlog", linthresh=1000); ax.set_xlabel("boxes"); ax.set_ylabel("held-out S1"); ax.legend(fontsize=6.5, ncol=2)
    fig.tight_layout(); save(fig, out, "fig4_ablation_curves"); plt.close(fig)

    # ---- self-modification --------------------------------------------------------------------------------------
    ev_count = Counter(); ev_dir = defaultdict(lambda: [0, 0]); cap_tests = []
    for r in full:
        for e in r["events"]:
            if e["kind"] == "hyper":
                ev_count[e["param"]] += 1
                ev_dir[e["param"]][0 if e["new"] > e["old"] else 1] += 1
            else:
                cap_tests.append(e)
    keys = ["tau", "eps", "lr", "lam", "dream", "sleep_every", "stm", "concepts"]
    fig, axs = plt.subplots(2, 4, figsize=(13, 5.5))
    T = min(len(r["hyper_log"]) for r in full)
    for ax, k in zip(axs.ravel(), keys):
        for r in full:
            hl = r["hyper_log"]
            ax.plot([h["box"] for h in hl], [h[k] for h in hl], alpha=0.25, lw=0.8, color="tab:blue")
        ax.plot([full[0]["hyper_log"][i]["box"] for i in range(T)], [np.mean([r["hyper_log"][i][k] for r in full]) for i in range(T)], color="k", lw=1.8)
        ax.set_title(k); ax.set_xlabel("boxes")
    fig.suptitle("Self-modification timeline: values chosen online by the meta-controller (thin = replicate, thick = mean)")
    fig.tight_layout(); save(fig, out, "fig2_self_modification"); plt.close(fig)
    with open(out / "self_modification_events.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["seed", "box", "kind", "param", "old", "new", "reason"])
        for r in full:
            for e in r["events"]:
                w.writerow([r["seed"], e["box"], e["kind"], e.get("param", "capacity"), e.get("old", e.get("from")), e.get("new", e.get("to")), e["reason"]])

    # sample efficiency
    def boxes_to(frac, r):
        ks = sorted(r["evals"]); s = np.array([r["evals"][k]["S1"].mean() for k in ks])
        target = s[0] + frac * (s[-1] - s[0])
        return next((k for k, v in zip(ks, s) if v >= target), ks[-1])
    eff = {v: {f: [boxes_to(f, r) for r in runs[v]] for f in (0.5, 0.9)} for v in runs if v != "frozen"}

    # transfer
    trows = []
    bs = cfg.transfer_budgets
    uref = {b: float(uniform_ref(cfg, b, cfg.transfer_boxes)["S1"].mean()) for b in bs}
    for v in ("full", "no_meta", "frozen"):
        if v in runs and runs[v][0].get("transfer"):
            for b in bs:
                m, lo, hi = boot([r["transfer"][b]["S1"].mean() for r in runs[v]])
                trows.append(dict(variant=v, budget=b, S1=m, lo=lo, hi=hi, uniform=uref[b]))
    if trows:
        with open(out / "transfer.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(trows[0])); w.writeheader(); w.writerows(trows)
        fig, ax = plt.subplots(figsize=(6.5, 4))
        for v in ("full", "no_meta"):
            rr = [t for t in trows if t["variant"] == v]
            if rr:
                ax.errorbar([t["budget"] for t in rr], [t["S1"] for t in rr], yerr=_errs(rr), marker="o", label=v)
        ax.plot(bs, [uref[b] for b in bs], "k--", label="uniform natural (untrained)")
        ax.axvline(cfg.budget, color="k", ls=":", lw=1)
        ax.set_xlabel("pieces allowed per box at test (trained at 14)"); ax.set_ylabel("held-out S1"); ax.legend(fontsize=8)
        fig.tight_layout(); save(fig, out, "fig5_transfer"); plt.close(fig)

    # ---- summary.md ---------------------------------------------------------------------------------------------------
    A("# Expt-22b - organic self-improving value learner\n")
    A(f"Run `{out.name}` | code hash `{man['code_hash']}` | wall {man.get('wall_s', 0)/60:.0f} min | {len(full)} full replicates x {N} boxes (equal length); ablations {man['abl_reps']} replicates x {NA} boxes | eval set {cfg.eval_boxes} fresh boxes (seeds never used in training)\n")
    A("## Headline\n")
    A(f"- Uniform natural placing (untrained): held-out S1 **{unif14:.2f}**. V21 (additive tables, Expt-21, 12 reps, ~60-98k boxes): **{V21}**. Hand contact/hole rule (reference only; never used by the learner): **{hand14:.2f}**.")
    A(f"- **V22b full, frozen memory after {N} boxes: S1 {fm:.2f} (95% CI {flo:.2f}-{fhi:.2f}, {len(full)} replicates)**; difference to V21 final {d21[0]:+.2f} (CI {d21[1]:+.2f}, {d21[2]:+.2f}; V21 treated as a constant).")
    m10 = [r for r in allck['full'] if r['box'] == 10000]
    if m10:
        A(f"- At only 10,000 boxes: {m10[0]['S1']:.2f} ({m10[0]['lo']:.2f}-{m10[0]['hi']:.2f}) vs V21 at 10,000 boxes: 82.52 (82.37-82.66).")
    A(f"- Held-out fraction with S1>=90: {allck['full'][-1]['frac90']:.3f}; mean pieces used {allck['full'][-1]['attempts']:.2f} of 14.\n")
    A("![fig1](fig1_learning_curves.png)\n")
    A("## Held-out S1 of the frozen memory (full variant)\n")
    A("| boxes learned | S1 | 95% CI | pieces | frac S1>=90 | hidden | concepts | replicates |\n|---|---|---|---|---|---|---|---|")
    for r in allck["full"]:
        A(f"| {r['box']} | {r['S1']:.2f} | {r['lo']:.2f} - {r['hi']:.2f} | {r['attempts']:.1f} | {r['frac90']:.3f} | {r['hidden']:.0f} | {r['concepts']:.0f} | {r['n']} |")
    A(f"\n## Ablations (held-out S1 after {NA} boxes; 'full minus variant' = bootstrap over replicate means; p = Welch/normal approx.)\n")
    A("| variant | n | S1 | 95% CI | full minus variant | 95% CI | p | train S1 (last 3k) | min/stream |\n|---|---|---|---|---|---|---|---|---|")
    for d in abl:
        dd = "-" if np.isnan(d["full_minus"]) else f"{d['full_minus']:+.2f}"
        dci = "-" if np.isnan(d["full_minus"]) or np.isnan(d["d_lo"]) else f"{d['d_lo']:+.2f}, {d['d_hi']:+.2f}"
        pp = "-" if np.isnan(d["p"]) else f"{d['p']:.3g}"
        A(f"| {d['variant']} | {d['n']} | {d['S1']:.2f} | {d['lo']:.2f} - {d['hi']:.2f} | {dd} | {dci} | {pp} | {d['train_last3k']:.2f} | {d['min_per_stream']:.1f} |")
    A("\n![fig3](fig3_ablation_bars.png)\n![fig4](fig4_ablation_curves.png)\n")
    A("Variants: `full`; `no_meta` fixed hyperparameters + V21-style tau/eps anneal, no capacity test; `no_sleep` online TD only (no replay/dreams/slow-weight LTM, no concepts; memory = fast net); `no_dream`; `no_concepts`; `td095` bootstrapped lambda-return targets (lambda 0.95, the V22a setting) instead of Monte-Carlo returns; `badinit_meta` / `badinit_fixed` deliberately poor initial hyperparameters (lr 8e-3, tau 0.3, eps 0, lambda 0.5, no dreams, sleep 800, STM 300) with / without the meta-controller; `frozen` untrained.\n")
    A("## Self-modification (full variant)\n")
    tot = sum(ev_count.values())
    A(f"- {tot} hyperparameter changes over {len(full)} replicates ({tot/len(full):.0f} per replicate) and {len(cap_tests)} capacity tests.")
    A("| parameter | changes | up | down |\n|---|---|---|---|")
    for k, c in ev_count.most_common():
        A(f"| {k} | {c} | {ev_dir[k][0]} | {ev_dir[k][1]} |")
    grown = [e for e in cap_tests if e["grow"]]
    med = np.median([e["ratio"] for e in cap_tests]) if cap_tests else float("nan")
    A(f"- Capacity tests: {len(cap_tests)}; widening accepted in {len(grown)}; median validation-loss ratio widened/control {med:.3f} (<0.93 is needed to grow). Final hidden widths: {dict(Counter(int(r['evals'][N]['hidden']) for r in full))}.")
    A("- Every event (box, parameter, old, new, reason) is in `self_modification_events.csv`; trajectories in `fig2_self_modification`.\n")
    A("![fig2](fig2_self_modification.png)\n")
    A("## Sample efficiency (boxes of learning until frozen held-out S1 reaches 50% / 90% of that stream's own total gain; checkpoint resolution)\n")
    A("| variant | 50% (median boxes) | 90% (median boxes) |\n|---|---|---|")
    for v, d in eff.items():
        A(f"| {v} | {np.median(d[0.5]):.0f} | {np.median(d[0.9]):.0f} |")
    if trows:
        A("\n## Transfer / robustness (trained at 14 pieces per box, memory frozen; 1,000 fresh boxes per budget)\n")
        A("| variant | " + " | ".join(f"budget {b}" for b in bs) + " |\n|---|" + "---|" * len(bs))
        for v in ("full", "no_meta", "frozen"):
            rr = [t for t in trows if t["variant"] == v]
            if rr:
                A(f"| {v} | " + " | ".join(f"{t['S1']:.1f} ({t['lo']:.1f}-{t['hi']:.1f})" if not np.isnan(t['lo']) else f"{t['S1']:.1f}" for t in rr) + " |")
        A("| uniform natural (same boxes) | " + " | ".join(f"{uref[b]:.1f}" for b in bs) + " |")
        A("\n![fig5](fig5_transfer.png)\n")
    A("## Files\n`summary.md`, `fig1..fig5` (PNG+PDF), `learning_curve_full.csv`, `heldout_checkpoints.csv`, `leaderboard_ablations.csv`, `self_modification_events.csv`, `transfer.csv`, `ltm_full_seed0.pkl`, `streams/*.pkl`, `progress.log`, `manifest.json`.\n")
    (out / "summary.md").write_text("\n".join(L), encoding="utf-8")