"""Expt-20 entry. 10,000 random legal fills -> rank -> top 25% -> winning combinations -> LTM files.

Does not build or run the next phase (filling the box with winning combinations)."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "Expt_01_10x10_Packing" / "code"))
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
from config import Config, DEFAULT_SEED, DEFAULT_TRIALS  # noqa: E402
from extract import KINDS, RANKINGS, frequency_table, mean_copies, rank_order, trial_keysets  # noqa: E402
from ltm import build_ltm, code_hash, save_ltm  # noqa: E402
from mga.pieces import PIECE_TYPES, catalogue_hash  # noqa: E402
from trials import run_trials  # noqa: E402

MIN_ALL_FOR_CSV_ORIENTED = 5   # oriented connected tables are huge and mostly singletons


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unavailable (not a git repository)"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def fmt(x, nd=4):
    return "" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def md_table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    out = ["| rank | " + " | ".join(h for h, _ in cols) + " |", "|---:|" + "|".join(["---"] * len(cols)) + "|"]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | " + " | ".join(fmt(r[k]) for _, k in cols) + " |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--skip-validation", action="store_true")
    args = ap.parse_args()
    config = Config(seed=args.seed, trials=args.trials)

    validation = "skipped"
    if not args.skip_validation:
        rc = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode
        validation = "passed" if rc == 0 else "failed"
        if rc != 0:
            raise SystemExit("unit tests failed; run aborted")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / "results" / f"{stamp}_{args.tag}"
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    trials = run_trials(config.seed, config.trials)
    t_trials = time.perf_counter() - t0
    print(f"trials done in {t_trials:.1f}s", flush=True)

    n = len(trials)
    n_top = int(round(n * config.top_fraction))
    by_id = {t["trial_id"]: t for t in trials}
    ranks, top_sets, cutoffs = {}, {}, {}
    for r in RANKINGS:
        order = rank_order(trials, r)
        ranks[r] = {tid: i + 1 for i, tid in enumerate(order)}
        top_sets[r] = set(order[:n_top])
        last = by_id[order[n_top - 1]]
        nxt = by_id[order[n_top]] if n_top < n else None
        cutoffs[r] = {
            "n_top": n_top,
            "last_selected_trial_id": last["trial_id"],
            "cutoff_S1_at_boundary": last["S1"],
            "cutoff_S2_at_boundary": last["S2"],
            "first_excluded_S1": nxt["S1"] if nxt else None,
            "first_excluded_S2": nxt["S2"] if nxt else None,
            "n_with_primary_equal_to_boundary": sum(1 for t in trials if t[r] == last[r]),
            "n_selected_with_primary_equal_to_boundary": sum(1 for tid in top_sets[r] if by_id[tid][r] == last[r]),
        }

    # trial csv
    rows = []
    for t in trials:
        tid = t["trial_id"]
        rows.append({
            **{k: t[k] for k in ("trial_id", "trial_seed", "S1", "empty_cells", "attempts", "S2", "invalid_attempts", "termination_reason")},
            "rank_S1": ranks["S1"][tid], "rank_S2": ranks["S2"][tid],
            "in_top25_S1": int(tid in top_sets["S1"]), "in_top25_S2": int(tid in top_sets["S2"]),
            "placements_json": json.dumps(t["placements"], separators=(",", ":")),
        })
    tfields = list(rows[0].keys())
    write_csv(out / "trials.csv", rows, tfields)
    for r in RANKINGS:
        sel = sorted((x for x in rows if x[f"in_top25_{r}"]), key=lambda x: x[f"rank_{r}"])
        write_csv(out / f"top25_by_{r}.csv", sel, tfields)

    # extraction
    t1 = time.perf_counter()
    keysets = [trial_keysets(t["placements"]) for t in trials]
    t_extract_keys = time.perf_counter() - t1
    tables = {}
    for r in RANKINGS:
        is_top = [t["trial_id"] in top_sets[r] for t in trials]
        tables[r] = {k: frequency_table(keysets, is_top, k, config) for k in KINDS}
        cols = ["freq_rank", "kind", "key_str", "n_top", "n_bottom", "n_all", "frac_top", "frac_bottom", "frac_all",
                "lift_vs_bottom", "lift_vs_all", "z", "winning"]
        for k in KINDS:
            rws = tables[r][k]
            if k.endswith("_oriented") and k.startswith(("pair_conn", "triple_conn")):
                rws = [x for x in rws if x["n_all"] >= MIN_ALL_FOR_CSV_ORIENTED]
            write_csv(out / "frequency_tables" / f"rank_{r}" / f"{k}.csv", rws, cols)
    mc = {r: mean_copies(trials, [t["trial_id"] in top_sets[r] for t in trials]) for r in RANKINGS}

    # distribution summary
    s1 = np.array([t["S1"] for t in trials], float)
    s2 = np.array([t["S2"] for t in trials], float)
    att = np.array([t["attempts"] for t in trials], float)

    def desc(a):
        return {"mean": float(a.mean()), "std": float(a.std()), "min": float(a.min()), "p25": float(np.percentile(a, 25)),
                "median": float(np.median(a)), "p75": float(np.percentile(a, 75)), "max": float(a.max())}
    dist = {"S1": desc(s1), "S2": desc(s2), "attempts": desc(att),
            "S1_p75_value": float(np.percentile(s1, 75)), "S2_p75_value": float(np.percentile(s2, 75)),
            "corr_S1_S2": float(np.corrcoef(s1, s2)[0, 1]),
            "top_overlap_S1_vs_S2": len(top_sets["S1"] & top_sets["S2"]),
            "top_overlap_fraction": len(top_sets["S1"] & top_sets["S2"]) / n_top}
    dist["top25_groups"] = {r: {"S1_mean": float(np.mean([by_id[i]["S1"] for i in top_sets[r]])),
                                "S2_mean": float(np.mean([by_id[i]["S2"] for i in top_sets[r]])),
                                "S1_mean_bottom": float(np.mean([by_id[i]["S1"] for i in by_id if i not in top_sets[r]])),
                                "S2_mean_bottom": float(np.mean([by_id[i]["S2"] for i in by_id if i not in top_sets[r]]))} for r in RANKINGS}

    # figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    ax[0].hist(s1, bins=np.arange(s1.min() - .5, s1.max() + 1.5, 1), color="#5B8DEF")
    ax[0].axvline(cutoffs["S1"]["cutoff_S1_at_boundary"] - 0.5, color="k", ls="--", label="top-25% boundary (S1 rank, secondary)")
    ax[0].set(title="S1 = 100 - empty cells", xlabel="S1", ylabel="trials"); ax[0].legend(fontsize=8)
    ax[1].hist(s2, bins=40, color="#F5A623")
    ax[1].axvline(cutoffs["S2"]["cutoff_S2_at_boundary"], color="k", ls="--", label="top-25% boundary (S2 rank, DEFAULT)")
    ax[1].set(title="S2 = S1 / attempts", xlabel="S2", ylabel="trials"); ax[1].legend(fontsize=8)
    ax[2].scatter(att + np.random.default_rng(0).uniform(-.25, .25, n), s1 + np.random.default_rng(1).uniform(-.25, .25, n), s=3, alpha=.25)
    ax[2].set(title="S1 vs attempts (jittered)", xlabel="attempts (placed pieces)", ylabel="S1")
    fig.suptitle(f"Expt-20: {n} random legal fills, seed {config.seed}")
    fig.tight_layout()
    fig.savefig(out / "score_distributions.png", dpi=130)
    plt.close(fig)

    total_runtime = time.perf_counter() - t0
    manifest = {
        "schema": "expt20_manifest_v1", "created": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seed": config.seed, "trials": n, "per_trial_seed_rule": "seed*1_000_000 + trial_id; random.Random(that)",
        "top_fraction": config.top_fraction, "n_top": n_top, "default_ranking": config.default_ranking,
        "ranking_definitions": {
            "S1": "SECONDARY: sort by S1 desc, tie-break S2 desc, then trial_id asc",
            "S2": "DEFAULT/PRIMARY: sort by S2 desc, tie-break S1 desc, then trial_id asc"},
        "score_definitions": {"S1": "100 - empty cells (asserted equal to env.occupied every trial)", "S2": "S1 / attempts; attempts = env.placements_count (accepted placements; every attempt is legal)"},
        "definitions": {
            "piece": "piece type id A..P; oriented variant = (type, canonical rotation)",
            "combination": "unordered multiset of piece types among one trial's placements",
            "connected_combination": "same, but the pieces form an edge-connected group (4-neighbour contact); oriented variant is translation-normalised ((type,rotation,dx,dy)...) as in Expt-17",
            "counting": "each key counted once per trial",
            "frequency": "n_top / n_top_trials",
            "lift_vs_bottom": "frac_top / frac_bottom (bottom = other 75%)",
            "lift_vs_all": "frac_top / frac_all",
            "winning_flag": f"n_top >= {config.win_min_top_count} and lift_vs_bottom > {config.win_min_lift} and two-proportion z >= {config.win_min_z} (or absent from bottom with n_top >= {config.win_min_top_count})",
            "kinds": list(KINDS)},
        "config": config.as_dict(),
        "catalogue_hash": catalogue_hash(), "piece_types": list(PIECE_TYPES),
        "code_hash": code_hash(ROOT), "git_commit": _git_commit(),
        "python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(),
        "python_executable": sys.executable, "unit_tests_before_run": validation,
        "runtime_seconds": {"trials": round(t_trials, 2), "key_extraction": round(t_extract_keys, 2), "total": round(total_runtime, 2)},
    }
    ltm = build_ltm(tables, cutoffs, manifest, config)
    ltm["mean_copies_per_trial"] = mc
    save_ltm(ltm, out / "ltm")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "distribution_summary.json").write_text(json.dumps({"distribution": dist, "cutoffs": cutoffs}, indent=2), encoding="utf-8")

    # summary md
    cols = [("key", "key_str"), ("n_top", "n_top"), ("frac_top", "frac_top"), ("n_bottom", "n_bottom"), ("frac_bottom", "frac_bottom"),
            ("lift_vs_bottom", "lift_vs_bottom"), ("lift_vs_all", "lift_vs_all"), ("z", "z"), ("winning", "winning")]
    L = [f"# Expt-20 summary ({stamp})", "",
         f"- trials: {n}; seed: {config.seed}; top 25% = {n_top} trials; runtime total {total_runtime:.1f}s (trials {t_trials:.1f}s)",
         f"- **Default (primary) ranking: {config.default_ranking}** (S2 desc, tie-break S1 desc, then trial_id). The S1 ranking (S1 desc, tie-break S2 desc, then trial_id) is also saved and labelled SECONDARY.",
         f"- S1 mean {dist['S1']['mean']:.3f}, max {dist['S1']['max']:.0f}, min {dist['S1']['min']:.0f}; S2 mean {dist['S2']['mean']:.4f}, max {dist['S2']['max']:.4f}, min {dist['S2']['min']:.4f}",
         f"- corr(S1,S2) = {dist['corr_S1_S2']:.3f}; overlap of the two top-25% sets: {dist['top_overlap_S1_vs_S2']} trials ({dist['top_overlap_fraction']:.1%})", "",
         "## Top-25% cutoffs", "```json", json.dumps(cutoffs, indent=2), "```", "",
         "## Distribution", "```json", json.dumps(dist, indent=2), "```", ""]
    for r in RANKINGS:
        L += [f"## Ranking by {r} - {'DEFAULT / PRIMARY' if r == config.default_ranking else 'SECONDARY (alternative ranking)'}", ""]
        for title, kind in (("Single pieces (type)", "single_type"), ("Single pieces (type+rotation)", "single_oriented"),
                            ("Pairs (type multiset, any positions)", "pair_type"), ("Triples (type multiset, any positions)", "triple_type"),
                            ("Connected pairs (type)", "pair_conn_type"), ("Connected triples (type)", "triple_conn_type")):
            L += [f"### {title}", "", md_table(tables[r][kind][:10], cols), ""]
    (out / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print(out)
    print(f"total {total_runtime:.1f}s")


if __name__ == "__main__":
    main()