"""Build curves, figures, tables and summary.md from <run>/streams/*.pkl."""

from __future__ import annotations

import csv
import json
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

from analysis import boot_mean_ci, rolling_mean
from config import Cfg
from learner import hand_box

W_CURVE = 500
STEP = 250


def load(out: Path) -> dict:
    runs = defaultdict(list)
    for p in sorted((out / "streams").glob("*.pkl")):
        with open(p, "rb") as fh:
            r = pickle.load(fh)
        runs[r["variant"]].append(r)
    return runs


def curve_grid(reps: list, n_max: int):
    """Rolling-mean S1 (window W_CURVE, ending at each grid point) per replicate; NaN after a replicate stopped."""
    grid = np.arange(W_CURVE, n_max + 1, STEP)
    M = np.full((len(reps), grid.size), np.nan)
    for i, r in enumerate(reps):
        rm = rolling_mean(r["S1"], W_CURVE)  # rm[k] = mean of S1[k:k+W] ending at box k+W
        for j, g in enumerate(grid):
            if g <= r["n_boxes"]:
                M[i, j] = rm[g - W_CURVE]
    return grid, M


def band(M: np.ndarray):
    mean = np.nanmean(M, axis=0)
    n = np.sum(~np.isnan(M), axis=0)
    sd = np.nanstd(M, axis=0, ddof=1)
    half = 2.26 * sd / np.sqrt(np.maximum(n, 1))  # t(9) ~ 2.26; with n<3 the band is hidden
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

    # reference: hand-written heuristic under the SAME handicap (not available to the learner)
    rng = np.random.default_rng(99)
    hand = np.array([hand_box(np.random.default_rng(cfg.eval_seed + j), man["cfg"]["budget"]).s1
                     for j in range(min(cfg.eval_boxes, 1000))])
    base_eval = np.mean([r["evals"][0]["S1"].mean() for r in full if 0 in r["evals"]])
    base_train = np.mean([r["S1"][:W_CURVE].mean() for r in full])

    # ---- curve csv + main figure -----------------------------------------------------------------------------
    grid, M = curve_grid(full, n_max)
    mean, lo, hi, cnt = band(M)
    with open(out / "learning_curve_full.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["box", "mean_S1_rolling500", "ci_lo", "ci_hi", "n_replicates"])
        for row in zip(grid, mean, lo, hi, cnt):
            w.writerow([int(row[0])] + [f"{x:.4f}" for x in row[1:4]] + [int(row[4])])
    ev_boxes = defaultdict(list)
    for r in full:
        for e in r["events"]:
            if e.get("to_stage") is not None:
                ev_boxes[e["to_stage"]].append(e["box"])
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.2))
    for a, xs in zip(ax, (None, "log")):
        for i in range(len(full)):
            a.plot(grid, M[i], color="tab:blue", alpha=0.12, lw=0.8)
        a.plot(grid, mean, color="tab:blue", lw=2, label=f"learning agent (mean of {len(full)} replicates, rolling {W_CURVE})")
        a.fill_between(grid, lo, hi, color="tab:blue", alpha=0.25, label="95% CI across replicates")
        a.axhline(base_eval, color="gray", ls="--", label=f"baseline: uniform natural placing ({base_eval:.1f})")
        a.axhline(hand.mean(), color="tab:green", ls=":", label=f"hand contact/hole rule, same handicap ({hand.mean():.1f}; reference only)")
        a.axhline(93, color="tab:red", ls="-.", lw=1, label="target 93")
        for st, bx in sorted(ev_boxes.items()):
            a.axvline(np.median(bx), color="k", alpha=0.35, lw=1)
            a.text(np.median(bx), a.get_ylim()[0] + 0.3, f"G{st}", rotation=90, fontsize=8, va="bottom", ha="right")
        a.set_xlabel("boxes seen (continuous stream, one box at a time)")
        a.set_ylabel("training S1 (100 - empty cells)")
        if xs:
            a.set_xscale("log")
            a.set_xlim(W_CURVE, n_max)
        a.grid(alpha=0.3)
    ax[0].set_title("Expt-21 continuous learning curve (vertical lines = median growth event)")
    ax[1].set_title("same, log x-axis")
    ax[0].legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "learning_curve.png", dpi=140)
    plt.close(fig)

    # ---- held-out checkpoints ---------------------------------------------------------------------------------
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
                            "memory_entries": float(np.mean([r["evals"][k]["mem"] for r in reps if k in r["evals"]])),
                            "stage": float(np.mean([r["evals"][k]["stage"] for r in reps if k in r["evals"]]))})
    with open(out / "heldout_checkpoints.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ck_rows[0]))
        w.writeheader()
        w.writerows(ck_rows)
    fig, ax = plt.subplots(figsize=(8, 5))
    for v in runs:
        rows = [r for r in ck_rows if r["variant"] == v]
        x = [r["box"] for r in rows]
        ax.plot(x, [r["heldout_S1"] for r in rows], marker="o", ms=3, label=f"{v} (n={rows[0]['n_replicates']})")
        if v == "full":
            ax.fill_between(x, [r["ci_lo"] for r in rows], [r["ci_hi"] for r in rows], alpha=0.25)
    ax.axhline(hand.mean(), color="tab:green", ls=":", label="hand rule, same handicap (ref)")
    ax.axhline(93, color="tab:red", ls="-.", lw=1, label="target 93")
    ax.set_xscale("symlog", linthresh=500)
    ax.set_xlabel("boxes of learning before the memory was frozen")
    ax.set_ylabel(f"held-out S1 ({cfg.eval_boxes} fresh boxes, frozen memory, no learning)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("Held-out checkpoint evaluation")
    fig.tight_layout()
    fig.savefig(out / "heldout_checkpoints.png", dpi=140)
    plt.close(fig)

    # ---- growth stages ----------------------------------------------------------------------------------------
    stage_rows = []
    by_stage = defaultdict(list)
    for r in full:
        for e in r["events"]:
            by_stage[e["stage_done"]].append(e)
    for st in sorted(by_stage):
        es = by_stage[st]
        g = [e["stage_gain_vs_prev_stage"] for e in es if e["stage_gain_vs_prev_stage"] is not None]
        stage_rows.append({"stage_done": st, "name": cfg.stages[st][0], "n_replicates": len(es),
                           "median_box_at_saturation": float(np.median([e["box"] for e in es])),
                           "frac_saturated_vs_forced": float(np.mean([e["reason"] == "saturated" for e in es])),
                           "train_S1_at_end": float(np.mean([e["mean_at_end_of_stage"] for e in es])),
                           "train_gain_vs_prev_stage": float(np.mean(g)) if g else np.nan,
                           "heldout_S1_at_end": float(np.mean([e["heldout_S1"] for e in es])),
                           "memory_entries": float(np.mean([e["memory_entries"] for e in es]))})
    if stage_rows:
        with open(out / "growth_stages.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(stage_rows[0]))
            w.writeheader()
            w.writerows(stage_rows)

    # ---- ablation leaderboard at a common budget ------------------------------------------------------------
    N_CMP = min(int(man["abl_boxes"]), min(r["n_boxes"] for r in full))
    lb = []
    for v, reps in runs.items():
        tr = [at_box(r, N_CMP, 5000) for r in reps]
        ho = [r["evals"][N_CMP]["S1"].mean() if N_CMP in r["evals"] else np.nan for r in reps]
        m, l, h = rep_ci(ho)
        tm, tl, th = rep_ci(tr)
        lb.append({"variant": v, "replicates": len(reps), "boxes_compared": N_CMP, "heldout_S1": m, "ci_lo": l, "ci_hi": h,
                   "train_S1_last5000": tm, "train_ci_lo": tl, "train_ci_hi": th,
                   "runtime_min_per_stream": float(np.mean([r["runtime_s"] for r in reps]) / 60),
                   "final_stage": float(np.mean([r["final_stage"] for r in reps])),
                   "memory_entries": float(np.mean([r["memory"]["stats"]["entries"] for r in reps])),
                   "_ho": ho})
    lb.sort(key=lambda d: -d["heldout_S1"])
    fv = next(d for d in lb if d["variant"] == "full")
    rng = np.random.default_rng(5)
    for d in lb:
        a = np.array(fv["_ho"]); b = np.array(d["_ho"])
        a, b = a[~np.isnan(a)], b[~np.isnan(b)]
        if d["variant"] == "full" or a.size < 2 or b.size < 2:
            d["full_minus_variant"] = d["diff_lo"] = d["diff_hi"] = np.nan
            continue
        bs = a[rng.integers(0, a.size, (5000, a.size))].mean(1) - b[rng.integers(0, b.size, (5000, b.size))].mean(1)
        d["full_minus_variant"], d["diff_lo"], d["diff_hi"] = float(a.mean() - b.mean()), *np.percentile(bs, [2.5, 97.5])
        d["diff_lo"], d["diff_hi"] = float(d["diff_lo"]), float(d["diff_hi"])
    with open(out / "leaderboard_ablations.csv", "w", newline="") as fh:
        keys = [k for k in lb[0] if k != "_ho"]
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows([{k: d[k] for k in keys} for d in lb])

    # ablation training curves
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
    ax.set_title("Controls / ablations (same handicap, same seeds per replicate index)")
    fig.tight_layout()
    fig.savefig(out / "ablation_curves.png", dpi=140)
    plt.close(fig)

    # ---- summary numbers --------------------------------------------------------------------------------------
    def s1_at(n):
        v = [at_box(r, n) for r in full]
        m, l, h = rep_ci(v)
        return m, l, h, int(np.sum(~np.isnan(v)))

    lines = []
    A = lines.append
    final_tr = [float(r["S1"][-5000:].mean()) for r in full]
    fm, fl, fh_ = rep_ci(final_tr)
    last_k = {r["seed"]: max(r["evals"]) for r in full}
    fin_ho = [r["evals"][last_k[r["seed"]]]["S1"].mean() for r in full]
    hm, hl, hh = rep_ci(fin_ho)
    stops = defaultdict(int)
    for r in full:
        stops[r["stop_reason"]] += 1
    A("# Expt-21 - continuous learning with sleep consolidation and growth on saturation\n")
    A(f"Run folder: `{out.name}` | code hash `{man['code_hash']}` | wall time {man.get('wall_s', 0)/60:.1f} min | "
      f"{len(full)} full replicates, {man['abl_reps']} replicates per ablation x {man['abl_boxes']} boxes\n")
    A("## Headline (full system)\n")
    A(f"- **Baseline (measured)**: uniform natural placing, handicap = at most {man['cfg']['budget']} pieces per box: "
      f"held-out S1 **{base_eval:.2f}** (first {W_CURVE} training boxes: {base_train:.2f}).")
    A(f"- **Final (training stream, last 5000 boxes)**: S1 **{fm:.2f}** (95% CI over replicates {fl:.2f}-{fh_:.2f}).")
    A(f"- **Final held-out (frozen memory, {cfg.eval_boxes} fresh boxes, near-greedy softmax)**: S1 **{hm:.2f}** ({hl:.2f}-{hh:.2f}) at the last checkpoint of each stream.")
    A(f"- Target 93: **{'reached' if hm >= 93 else 'NOT reached'}** (held-out {hm:.2f}). Hand contact/hole rule under the same handicap (reference only, not used by the learner): {hand.mean():.2f}. Expt-20 best hand rule on the unhandicapped box: 96-98 (context only, different task).")
    A(f"- Streams ended by: {dict(stops)}.  Stream lengths: min {min(r['n_boxes'] for r in full)}, max {n_max}.\n")
    A("## Learning curve: S1 at 0 / 1k / 10k / 50k / 100k boxes (training stream, mean of the 500 boxes ending there)\n")
    A("| boxes | S1 mean | 95% CI over replicates | replicates reaching it |\n|---|---|---|---|")
    A(f"| 0 (baseline, held-out) | {base_eval:.2f} | - | {len(full)} |")
    for n in (1000, 2000, 5000, 10000, 20000, 50000, 100000, 150000):
        m, l, h, k = s1_at(n)
        if k:
            A(f"| {n} | {m:.2f} | {l:.2f} - {h:.2f} | {k} |")
    A("\n![curve](learning_curve.png)\n")
    A("## Growth stages (saturation events, full variant)\n")
    A("Saturation = upper 95%-bound of the S1 gain between two consecutive windows is below sat_delta; growth is then applied automatically (a stage that never saturates is forced to grow after max_stage_boxes).\n")
    A("| stage finished | name | replicates | median box | saturated (vs forced) | train S1 at end | gain vs previous stage | held-out S1 at end | memory entries |\n|---|---|---|---|---|---|---|---|---|")
    for s in stage_rows:
        g = "-" if np.isnan(s["train_gain_vs_prev_stage"]) else f"{s['train_gain_vs_prev_stage']:+.2f}"
        A(f"| {s['stage_done']} | {s['name']} | {s['n_replicates']} | {s['median_box_at_saturation']:.0f} | {s['frac_saturated_vs_forced']:.0%} | {s['train_S1_at_end']:.2f} | {g} | {s['heldout_S1_at_end']:.2f} | {s['memory_entries']:.0f} |")
    A("\n## Held-out checkpoints (full variant: memory frozen after N boxes, evaluated on the same fixed fresh boxes)\n")
    A("| boxes learned | held-out S1 | 95% CI (replicates) | attempts | frac S1>=90 | stage | memory entries | replicates |\n|---|---|---|---|---|---|---|---|")
    for r in ck_rows:
        if r["variant"] == "full":
            A(f"| {r['box']} | {r['heldout_S1']:.2f} | {r['ci_lo']:.2f} - {r['ci_hi']:.2f} | {r['attempts']:.1f} | {r['frac_S1_ge_90']:.2f} | {r['stage']:.1f} | {r['memory_entries']:.0f} | {r['n_replicates']} |")
    A("\n![heldout](heldout_checkpoints.png)\n")
    A(f"## Controls and ablations (all compared at {N_CMP} boxes, held-out S1 after freezing)\n")
    A("| variant | replicates | held-out S1 | 95% CI | train S1 (last 5000) | full minus variant (95% CI) | mean final stage | memory entries | min/stream |\n|---|---|---|---|---|---|---|---|---|")
    for d in lb:
        diff = "-" if np.isnan(d["full_minus_variant"]) else f"{d['full_minus_variant']:+.2f} ({d['diff_lo']:+.2f}, {d['diff_hi']:+.2f})"
        A(f"| {d['variant']} | {d['replicates']} | {d['heldout_S1']:.2f} | {d['ci_lo']:.2f} - {d['ci_hi']:.2f} | {d['train_S1_last5000']:.2f} | {diff} | {d['final_stage']:.1f} | {d['memory_entries']:.0f} | {d['runtime_min_per_stream']:.1f} |")
    A("\nVariants: `full` sleep+dream+growth on saturation; `no_sleep` learns online after every box, no STM replay, no dreams (growth on saturation still active); `sleep_no_dream` sleeps (replay of real boxes) but never dreams; `no_growth` fixed stage-0 memory; `all_upfront` every feature and the largest memory from box 0 (no staged growth); `frozen` learning disabled (flatness check). The 'full minus variant' interval is a bootstrap over replicate means (independent replicates).\n")
    A("![ablation](ablation_curves.png)\n")
    A("## Final memory (replicate 0)\n")
    mem0 = full[0]["memory"]
    A(f"- entries {mem0['stats']['entries']} of {mem0['stats']['slots']} slots; active features {mem0['stats']['active']}; sleeps {mem0['stats']['sleeps']}")
    A("- learned piece-type weights (cells of advantage): " + ", ".join(f"{k} {v:+.2f}" for k, v in sorted(mem0['type_weights'].items(), key=lambda kv: -kv[1])))
    if mem0.get("pair_top"):
        A("- best learned piece pairs: " + ", ".join(f"{k} ({w:+.2f}, n={n:.0f})" for k, w, n in mem0["pair_top"][:6]))
        A("- worst learned piece pairs: " + ", ".join(f"{k} ({w:+.2f}, n={n:.0f})" for k, w, n in mem0["pair_bottom"][:6]))
    A("\n## Files\n`learning_curve.png/.csv`, `heldout_checkpoints.png/.csv`, `growth_stages.csv`, `leaderboard_ablations.csv`, `ablation_curves.png`, `ltm_full_seed0.pkl`, `streams/*.pkl` (per-box S1/attempts per stream), `progress.log`, `manifest.json`.")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")