"""Build curves, figures, tables and summary.md from <run>/streams/*.pkl for Expt-22a."""

from __future__ import annotations

import csv
import json
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

import engine as E
from analysis import boot_mean_ci, rolling_mean
from config import Cfg

W_CURVE = 500
STEP = 250


def hand_box(rng: np.random.Generator, budget: int, w_area: float = 2.0) -> E.Box:
    """Reference ONLY: hand-written contact/hole/area heuristic under the same handicap."""
    box = E.Box(budget=budget)
    while True:
        cand, f = E.natural_candidates(box, 0)
        if cand.size == 0:
            return box
        sc = f["contact"] - 3.0 * f["p1"] - f["n3"] + w_area * E.AREA[cand] + rng.random(cand.size) * 0.5
        box.place(int(cand[int(np.argmax(sc))]))


def load(out: Path) -> dict:
    runs = defaultdict(list)
    for p in sorted((out / "streams").glob("*.pkl")):
        with open(p, "rb") as fh:
            r = pickle.load(fh)
        runs[r["variant"]].append(r)
    return runs


def curve_grid(reps: list, n_max: int):
    grid = np.arange(W_CURVE, n_max + 1, STEP)
    M = np.full((len(reps), grid.size), np.nan)
    for i, r in enumerate(reps):
        rm = rolling_mean(r["S1"], W_CURVE)
        for j, g in enumerate(grid):
            if g <= r["n_boxes"]:
                M[i, j] = rm[g - W_CURVE]
    return grid, M


def band(M: np.ndarray):
    mean = np.nanmean(M, axis=0)
    n = np.sum(~np.isnan(M), axis=0)
    sd = np.nanstd(M, axis=0, ddof=1)
    half = 2.26 * sd / np.sqrt(np.maximum(n, 1))
    half[n < 3] = np.nan
    return mean, mean - half, mean + half, n


def rep_ci(vals) -> tuple[float, float, float]:
    v = np.asarray([x for x in vals if not np.isnan(x)], dtype=float)
    if v.size == 0:
        return (np.nan,) * 3
    if v.size < 3:
        return float(v.mean()), np.nan, np.nan
    m, lo, hi = boot_mean_ci(v, 4000, 1)
    return m, lo, hi


def at_box(r: dict, n: int, w: int = 500) -> float:
    if r["n_boxes"] < n:
        return np.nan
    return float(r["S1"][n - w:n].mean())


def build_report(out: Path, cfg: Cfg) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    runs = load(out)
    man = json.loads((out / "manifest.json").read_text())
    full = runs.get("full", [])
    if not full:
        raise SystemExit("no full-variant streams found")
    n_max = max(r["n_boxes"] for r in full)
    budget = man["cfg"]["budget"]

    hand = np.array([hand_box(np.random.default_rng(cfg.eval_seed + j), budget).s1
                     for j in range(min(cfg.eval_boxes, 800))])
    base_eval = np.mean([r["evals"][0]["S1"].mean() for r in full if 0 in r["evals"]])
    base_train = np.mean([r["S1"][:W_CURVE].mean() for r in full])

    grid, M = curve_grid(full, n_max)
    mean, lo, hi, cnt = band(M)
    with open(out / "learning_curve_full.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["box", "mean_S1_rolling500", "ci_lo", "ci_hi", "n_replicates"])
        for row in zip(grid, mean, lo, hi, cnt):
            w.writerow([int(row[0])] + [f"{x:.4f}" for x in row[1:4]] + [int(row[4])])

    fig, ax = plt.subplots(1, 2, figsize=(15, 5.2))
    for a, xs in zip(ax, (None, "log")):
        for i in range(len(full)):
            a.plot(grid, M[i], color="tab:blue", alpha=0.12, lw=0.8)
        a.plot(grid, mean, color="tab:blue", lw=2, label=f"value learner (n={len(full)}, rolling {W_CURVE})")
        a.fill_between(grid, lo, hi, color="tab:blue", alpha=0.25, label="95% CI across replicates")
        a.axhline(base_eval, color="gray", ls="--", label=f"held-out @0 ({base_eval:.1f})")
        a.axhline(hand.mean(), color="tab:green", ls=":", label=f"hand rule ({hand.mean():.1f}; ref)")
        a.axhline(93, color="tab:red", ls="-.", lw=1, label="target 93")
        a.axhline(83.70, color="tab:orange", ls="--", alpha=0.7, label="V21 held-out 83.70")
        a.set_xlabel("boxes seen")
        a.set_ylabel("training S1")
        if xs:
            a.set_xscale("log")
            a.set_xlim(W_CURVE, max(n_max, W_CURVE + 1))
        a.grid(alpha=0.3)
    ax[0].set_title("Expt-22a organic afterstate value learner")
    ax[1].set_title("same, log x-axis")
    ax[0].legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "learning_curve.png", dpi=140)
    plt.close(fig)

    ck_rows = []
    for v, reps in runs.items():
        cks = sorted(set(k for r in reps for k in r["evals"]))
        for k in cks:
            vals = [r["evals"][k]["S1"].mean() for r in reps if k in r["evals"]]
            att = [r["evals"][k]["attempts"].mean() for r in reps if k in r["evals"]]
            m, l, h = rep_ci(vals)
            ck_rows.append({"variant": v, "box": k, "n_replicates": len(vals), "heldout_S1": m, "ci_lo": l, "ci_hi": h,
                            "attempts": float(np.mean(att)),
                            "frac_S1_ge_90": float(np.mean([(r["evals"][k]["S1"] >= 90).mean() for r in reps if k in r["evals"]])),
                            "hidden": float(np.mean([r["evals"][k].get("hidden", 0) for r in reps if k in r["evals"]])),
                            "concepts": float(np.mean([r["evals"][k].get("concepts", 0) for r in reps if k in r["evals"]]))})
    with open(out / "heldout_checkpoints.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ck_rows[0]))
        w.writeheader()
        w.writerows(ck_rows)

    fig, ax = plt.subplots(figsize=(8, 5))
    for v in runs:
        rows = [r for r in ck_rows if r["variant"] == v]
        x = [r["box"] for r in rows]
        ax.plot(x, [r["heldout_S1"] for r in rows], marker="o", ms=3, label=f"{v} (n={rows[0]['n_replicates']})")
        if v == "full" and len(rows) >= 1:
            ax.fill_between(x, [r["ci_lo"] if not np.isnan(r["ci_lo"]) else r["heldout_S1"] for r in rows],
                            [r["ci_hi"] if not np.isnan(r["ci_hi"]) else r["heldout_S1"] for r in rows], alpha=0.25)
    ax.axhline(hand.mean(), color="tab:green", ls=":", label="hand rule (ref)")
    ax.axhline(93, color="tab:red", ls="-.", lw=1)
    ax.axhline(83.70, color="tab:orange", ls="--", alpha=0.7, label="V21 83.70")
    ax.set_xscale("symlog", linthresh=500)
    ax.set_xlabel("boxes of learning before freeze")
    ax.set_ylabel(f"held-out S1 ({cfg.eval_boxes} fresh boxes, slow net)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("Held-out checkpoints (Expt-22a)")
    fig.tight_layout()
    fig.savefig(out / "heldout_checkpoints.png", dpi=140)
    plt.close(fig)

    N_CMP = min(int(man.get("abl_boxes", n_max)), min(r["n_boxes"] for r in full))
    lb = []
    for v, reps in runs.items():
        tr = [at_box(r, N_CMP, min(5000, N_CMP)) for r in reps]
        ho = []
        for r in reps:
            if N_CMP in r["evals"]:
                ho.append(r["evals"][N_CMP]["S1"].mean())
            else:
                ks = [k for k in r["evals"] if k <= N_CMP]
                ho.append(r["evals"][max(ks)]["S1"].mean() if ks else np.nan)
        m, l, h = rep_ci(ho)
        tm, tl, th = rep_ci(tr)
        lb.append({"variant": v, "replicates": len(reps), "boxes_compared": N_CMP, "heldout_S1": m, "ci_lo": l, "ci_hi": h,
                   "train_S1_last5000": tm, "train_ci_lo": tl, "train_ci_hi": th,
                   "runtime_min_per_stream": float(np.mean([r["runtime_s"] for r in reps]) / 60),
                   "hidden": float(np.mean([r["evals"][max(r["evals"])].get("hidden", 0) for r in reps])),
                   "concepts": float(np.mean([r["evals"][max(r["evals"])].get("concepts", 0) for r in reps])),
                   "_ho": ho})
    lb.sort(key=lambda d: -d["heldout_S1"] if not np.isnan(d["heldout_S1"]) else -1e9)
    fv = next(d for d in lb if d["variant"] == "full")
    rng = np.random.default_rng(5)
    for d in lb:
        a = np.array(fv["_ho"], dtype=float); b = np.array(d["_ho"], dtype=float)
        a, b = a[~np.isnan(a)], b[~np.isnan(b)]
        if d["variant"] == "full" or a.size < 2 or b.size < 2:
            d["full_minus_variant"] = d["diff_lo"] = d["diff_hi"] = np.nan
            continue
        bs = a[rng.integers(0, a.size, (5000, a.size))].mean(1) - b[rng.integers(0, b.size, (5000, b.size))].mean(1)
        d["full_minus_variant"] = float(a.mean() - b.mean())
        d["diff_lo"], d["diff_hi"] = map(float, np.percentile(bs, [2.5, 97.5]))
    with open(out / "leaderboard_ablations.csv", "w", newline="") as fh:
        keys = [k for k in lb[0] if k != "_ho"]
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows([{k: d[k] for k in keys} for d in lb])

    fig, ax = plt.subplots(figsize=(9, 5))
    for v, reps in runs.items():
        g, Mv = curve_grid(reps, min(N_CMP, max(r["n_boxes"] for r in reps)))
        m, l, h, n = band(Mv)
        ax.plot(g, m, label=f"{v} (n={len(reps)})")
        if v in ("full", "frozen") and len(reps) >= 3:
            ax.fill_between(g, l, h, alpha=0.2)
    ax.axhline(93, color="tab:red", ls="-.", lw=1)
    ax.set_xlabel("boxes")
    ax.set_ylabel(f"training S1 (rolling {W_CURVE})")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("Expt-22a ablations")
    fig.tight_layout()
    fig.savefig(out / "ablation_curves.png", dpi=140)
    plt.close(fig)

    # meta / hyperparameter trajectory for full seed 0 if present
    full0 = next((r for r in full if r["seed"] == 0), full[0])
    if full0.get("hyper_log"):
        with open(out / "hyper_trajectory_full_s0.csv", "w", newline="") as fh:
            keys = list(full0["hyper_log"][0].keys())
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(full0["hyper_log"])

    def s1_at(n):
        v = [at_box(r, n) for r in full]
        m, l, h = rep_ci(v)
        return m, l, h, int(np.sum(~np.isnan(v)))

    lines = []
    A = lines.append
    final_tr = [float(r["S1"][-min(5000, r["n_boxes"]):].mean()) for r in full]
    fm, fl, fh_ = rep_ci(final_tr)
    last_k = {r["seed"]: max(r["evals"]) for r in full}
    fin_ho = [r["evals"][last_k[r["seed"]]]["S1"].mean() for r in full]
    hm, hl, hh = rep_ci(fin_ho)
    A("# Expt-22a — Organic Afterstate Value Learner\n")
    A(f"Run folder: `{out.name}` | code hash `{man['code_hash']}` | wall time {man.get('wall_s', 0)/60:.1f} min | "
      f"{len(full)} full replicates, abl_reps={man.get('abl_reps')} × abl_boxes={man.get('abl_boxes')}\n")
    A("## Headline (full system)\n")
    A(f"- **Baseline held-out @0**: handicap ≤{budget} pieces/box, natural placing: **{base_eval:.2f}** "
      f"(first {W_CURVE} training boxes: {base_train:.2f}).")
    A(f"- **Final training (last ≤5000)**: S1 **{fm:.2f}** (95% CI {fl:.2f}-{fh_:.2f}).")
    A(f"- **Final held-out (slow net)**: S1 **{hm:.2f}** ({hl:.2f}-{hh:.2f}).")
    A(f"- Target 93: **{'reached' if hm >= 93 else 'NOT reached'}**. Hand rule (ref): {hand.mean():.2f}. "
      f"V21 held-out: 83.70. Beat V21: **{'YES' if hm > 83.70 else 'NO'}**. "
      f"Beat hand: **{'YES' if hm > hand.mean() else 'NO'}**.")
    A(f"- Stream lengths: min {min(r['n_boxes'] for r in full)}, max {n_max}.\n")
    A("## Learning curve (training S1)\n")
    A("| boxes | S1 mean | 95% CI | n |\n|---|---|---|---|")
    A(f"| 0 (held-out) | {base_eval:.2f} | - | {len(full)} |")
    for n in (1000, 2000, 5000, 10000, 20000, 30000, 40000, 60000, 80000):
        m, l, h, k = s1_at(n)
        if k:
            A(f"| {n} | {m:.2f} | {l:.2f}-{h:.2f} | {k} |")
    A("\n![curve](learning_curve.png)\n")
    A("## Held-out checkpoints (full)\n")
    A("| boxes | held-out S1 | 95% CI | attempts | frac≥90 | hidden | concepts | n |\n|---|---|---|---|---|---|---|---|")
    for r in ck_rows:
        if r["variant"] == "full":
            A(f"| {r['box']} | {r['heldout_S1']:.2f} | {r['ci_lo']:.2f}-{r['ci_hi']:.2f} | {r['attempts']:.1f} | "
              f"{r['frac_S1_ge_90']:.2f} | {r['hidden']:.0f} | {r['concepts']:.0f} | {r['n_replicates']} |")
    A("\n![heldout](heldout_checkpoints.png)\n")
    A(f"## Ablations (compared near {N_CMP} boxes)\n")
    A("| variant | n | held-out S1 | 95% CI | train last5k | full−var (CI) | hidden | concepts | min/stream |\n|---|---|---|---|---|---|---|---|---|")
    for d in lb:
        diff = "-" if np.isnan(d["full_minus_variant"]) else f"{d['full_minus_variant']:+.2f} ({d['diff_lo']:+.2f},{d['diff_hi']:+.2f})"
        A(f"| {d['variant']} | {d['replicates']} | {d['heldout_S1']:.2f} | {d['ci_lo']:.2f}-{d['ci_hi']:.2f} | "
          f"{d['train_S1_last5000']:.2f} | {diff} | {d['hidden']:.0f} | {d['concepts']:.0f} | {d['runtime_min_per_stream']:.1f} |")
    A("\nVariants: `full` value+lookahead+sleep+dream+meta+concepts+shadow-growth; `no_meta` fixed anneal; "
      "`no_sleep` online only; `no_dream`; `no_concepts`; `mc_only` λ=1; `frozen` no learning.\n")
    A("![ablation](ablation_curves.png)\n")
    A("## Design\n")
    A("- Afterstate features D=29 (28 board + 1 concept column); MLP 2×ReLU; placement = softmax V(afterstate)/τ.")
    A("- λ-returns vs slow net; online Adam on fast net; sleep = prioritised replay + dreams; slow EMA of fast; concept library.")
    A("- Meta adapts τ/ε/lr/λ/dream/sleep/STM from probe EMA gain + sleep loss diagnostics; growth only if shadow-widen wins.\n")
    A("## Files\n`learning_curve.png/.csv`, `heldout_checkpoints.png/.csv`, `leaderboard_ablations.csv`, "
      "`ablation_curves.png`, `hyper_trajectory_full_s0.csv`, `ltm_full_seed0.pkl`, `streams/*.pkl`, `progress.log`, `manifest.json`.")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
