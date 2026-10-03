"""Expt-20 phases. Phase 1: 10,000 uniform random fills -> STM. Phase 2: 10,000 fills guided by the frozen LTM,
plus a same-seed uniform control (and two ablations). Does not modify earlier results; writes results/<ts>_phases/.

The LTM is read only. The next phase that *uses* winning combinations as macro-actions is not built here."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
from config import Config  # noqa: E402
from ltm import code_hash, load_ltm  # noqa: E402
from mga.pieces import catalogue_hash  # noqa: E402
from phases.compare import (arm_arrays, boot_diff_unpaired, paired_diff, stm_vs_ltm_rows, summarize_arm)  # noqa: E402
from phases.policy import DEFAULT_EPSILON, Policy, run_guided_trials  # noqa: E402
from phases.stm import STM, STM_KINDS, save_stm  # noqa: E402
from trials import run_trials  # noqa: E402

PHASE1_SEED = 20261001
PHASE2_SEED = 20261002
DEFAULT_LTM = ROOT / "results" / "20260930_131353_run_S2default" / "ltm" / "ltm.pkl"
SNAP_EVERY = 1000


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def trial_rows(trials: list[dict]) -> list[dict]:
    return [{**{k: t[k] for k in ("trial_id", "trial_seed", "S1", "empty_cells", "attempts", "S2", "invalid_attempts", "termination_reason")},
             **{k: t[k] for k in ("n_explore_steps", "n_guided_steps", "n_boosted_steps") if k in t},
             "uses_P": int(any(p[0] == "P" for p in t["placements"])),
             "placements_json": json.dumps(t["placements"], separators=(",", ":"))} for t in trials]


def fill_stm(trials: list[dict], label: str) -> tuple[STM, float]:
    t0 = time.perf_counter()
    stm = STM("S2", 0.25, Config())
    for i, t in enumerate(trials, 1):
        stm.observe(t)
        if i % SNAP_EVERY == 0:
            stm.snapshot()
            print(f"  [{label}] STM snapshot at {i} trials", flush=True)
    if len(trials) % SNAP_EVERY:
        stm.snapshot()   # final partial snapshot (only when the trial count is not a multiple of SNAP_EVERY)
    return stm, time.perf_counter() - t0


def merged_stm(a: STM, b: STM, offset: int) -> STM:
    m = STM("S2", 0.25, Config())
    for t, ks in zip(a.trials, a.keysets):
        m.trials.append(dict(t)); m.keysets.append(ks)
    for t, ks in zip(b.trials, b.keysets):
        m.trials.append({**t, "trial_id": t["trial_id"] + offset}); m.keysets.append(ks)
    for k in STM_KINDS:
        m.running_n_all[k].update(a.running_n_all[k]); m.running_n_all[k].update(b.running_n_all[k])
    m.snapshot()
    return m


def md_rows(rows, cols):
    out = ["| " + " | ".join(h for h, _ in cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if r.get(k) is None else (f"{r[k]:.4f}" if isinstance(r[k], float) else str(r[k])) for _, k in cols) + " |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=10_000)
    ap.add_argument("--phase1-seed", type=int, default=PHASE1_SEED)
    ap.add_argument("--phase2-seed", type=int, default=PHASE2_SEED)
    ap.add_argument("--epsilon", type=float, default=DEFAULT_EPSILON)
    ap.add_argument("--ltm", default=str(DEFAULT_LTM))
    ap.add_argument("--tag", default="phases")
    ap.add_argument("--skip-validation", action="store_true")
    args = ap.parse_args()

    if not args.skip_validation:
        if subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode != 0:
            raise SystemExit("unit tests failed; run aborted")
    ltm_path = Path(args.ltm)
    ltm = load_ltm(ltm_path)
    assert ltm["default_ranking"] == "S2", "LTM default ranking must be S2"
    n = args.trials
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / "results" / f"{stamp}_{args.tag}"
    out.mkdir(parents=True, exist_ok=True)
    T0 = time.perf_counter()
    rt: dict = {}

    # ---- Phase 1 ----
    t0 = time.perf_counter(); p1 = run_trials(args.phase1_seed, n); rt["phase1_trials"] = time.perf_counter() - t0
    print(f"phase 1 trials {rt['phase1_trials']:.1f}s", flush=True)
    stm1, rt["phase1_stm"] = fill_stm(p1, "phase1")
    # ---- Phase 2 ----
    policy = Policy.from_ltm(ltm, epsilon=args.epsilon)
    arms = {}
    for label, pol in (("guided", policy), ("ablation_single_only", policy.variant("single_only", True, False)),
                       ("ablation_boost_only", policy.variant("boost_only", False, True))):
        t0 = time.perf_counter(); arms[label] = run_guided_trials(args.phase2_seed, n, pol); rt[f"phase2_{label}"] = time.perf_counter() - t0
        print(f"phase 2 {label} {rt[f'phase2_{label}']:.1f}s", flush=True)
    t0 = time.perf_counter(); control = run_trials(args.phase2_seed, n); rt["phase2_control"] = time.perf_counter() - t0
    print(f"phase 2 control {rt['phase2_control']:.1f}s", flush=True)
    stm2, rt["phase2_stm"] = fill_stm(arms["guided"], "phase2-guided")
    stm12 = merged_stm(stm1, stm2, offset=n)

    # ---- STM files ----
    meta1 = {"seed": args.phase1_seed, "trials": n, "selection": "uniform random legal placement"}
    meta2 = {"seed": args.phase2_seed, "trials": n, "selection": "LTM-guided", "policy": policy.describe(), "ltm_path": str(ltm_path), "ltm_sha256": sha256(ltm_path)}
    stm_dir = out / "stm"
    files = {}
    files["stm_after_phase1"] = save_stm(stm1.export("STM after Phase 1 (uniform random)", "phase1", meta1), stm_dir, "stm_after_phase1")
    files["stm_after_phase2_guided"] = save_stm(stm2.export("STM over Phase 2 guided trials only", "phase2_guided", meta2), stm_dir, "stm_after_phase2_guided")
    files["stm_cumulative_phase1_plus_phase2"] = save_stm(
        stm12.export("STM cumulative: Phase 1 + Phase 2 guided (20,000 trials; phase-2 ids offset by trials)", "phase1+phase2_guided", {"phase1": meta1, "phase2": meta2}), stm_dir, "stm_cumulative_phase1_plus_phase2")
    stm1_d = stm1.export("x", "phase1", meta1); stm2_d = stm2.export("x", "phase2", meta2)
    for name, d in (("stm1_vs_ltm", stm1_d), ("stm2guided_vs_ltm", stm2_d)):
        rows = stm_vs_ltm_rows(d, ltm)
        write_csv(out / f"{name}.csv", rows, list(rows[0].keys()))

    # ---- trial csvs ----
    for name, tr in (("phase1_uniform", p1), ("phase2_guided", arms["guided"]), ("phase2_control_uniform_same_seeds", control),
                     ("phase2_ablation_single_only", arms["ablation_single_only"]), ("phase2_ablation_boost_only", arms["ablation_boost_only"])):
        rs = trial_rows(tr)
        write_csv(out / f"trials_{name}.csv", rs, list(rs[0].keys()))

    # ---- comparison ----
    summ = {"phase1_uniform": summarize_arm("phase1_uniform", p1, rt["phase1_trials"]),
            "phase2_control_uniform_same_seeds": summarize_arm("phase2_control", control, rt["phase2_control"]),
            "phase2_guided": summarize_arm("phase2_guided", arms["guided"], rt["phase2_guided"]),
            "phase2_ablation_single_only": summarize_arm("single_only", arms["ablation_single_only"], rt["phase2_ablation_single_only"]),
            "phase2_ablation_boost_only": summarize_arm("boost_only", arms["ablation_boost_only"], rt["phase2_ablation_boost_only"])}
    paired = {}
    for lab, tr in (("guided", arms["guided"]), ("ablation_single_only", arms["ablation_single_only"]), ("ablation_boost_only", arms["ablation_boost_only"])):
        paired[lab] = {k: paired_diff(control, tr, k) for k in ("S1", "S2", "attempts", "empty_cells")}
        paired[lab]["uses_P"] = paired_diff([{**t, "uses_P": float(any(p[0] == "P" for p in t["placements"]))} for t in control],
                                            [{**t, "uses_P": float(any(p[0] == "P" for p in t["placements"]))} for t in tr], "uses_P")
    unpaired = {k: boot_diff_unpaired(p1, arms["guided"], k) for k in ("S1", "S2")}
    # S1 effect inside the P/no-P strata is reported through summarize_arm; also seed-level P usage transitions
    cp = np.array([any(p[0] == "P" for p in t["placements"]) for t in control]); gp = np.array([any(p[0] == "P" for p in t["placements"]) for t in arms["guided"]])
    transitions = {"P_both": int((cp & gp).sum()), "P_control_only": int((cp & ~gp).sum()), "P_guided_only": int((~cp & gp).sum()), "P_neither": int((~cp & ~gp).sum())}
    # S1 paired difference restricted to same-P-status pairs
    c1 = np.array([t["S1"] for t in control], float); g1 = np.array([t["S1"] for t in arms["guided"]], float)
    strata = {}
    for name, m in (("P_in_both", cp & gp), ("P_guided_only", ~cp & gp), ("P_control_only", cp & ~gp), ("P_in_neither", ~cp & ~gp)):
        strata[name] = {"n": int(m.sum()), "mean_S1_diff": float((g1[m] - c1[m]).mean()) if m.any() else None}
    c2 = np.array([t["S2"] for t in control], float); g2 = np.array([t["S2"] for t in arms["guided"]], float)
    # top-25% pooled over control+guided (same rule), share coming from guided
    pooled = [{**t, "arm": "c"} for t in control] + [{**t, "trial_id": t["trial_id"] + n, "arm": "g"} for t in arms["guided"]]
    from extract import rank_order
    def share(key):
        order = rank_order(pooled, key)[: len(pooled) // 4]
        byid = {t["trial_id"]: t["arm"] for t in pooled}
        return sum(1 for i in order if byid[i] == "g") / len(order)
    pooled_share = {"S1": share("S1"), "S2": share("S2")}
    comp = {"summaries": summ, "paired_guided_minus_control_same_seeds": paired, "unpaired_guided_minus_phase1": unpaired,
            "P_transitions_control_to_guided": transitions, "paired_S1_diff_by_P_stratum": strata,
            "guided_share_of_pooled_top25_between_guided_and_control": pooled_share}
    (out / "comparison.json").write_text(json.dumps(comp, indent=2), encoding="utf-8")

    # ---- figure ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.3))
    a1, ac, ag = arm_arrays(p1), arm_arrays(control), arm_arrays(arms["guided"])
    bins = np.arange(60.5, 100.5, 1)
    for a, lab, col in ((ac, "uniform control", "#888"), (ag, "LTM-guided", "#D4537E")):
        ax[0].hist(a["S1"], bins=bins, alpha=.55, label=lab, color=col)
    ax[0].set(title="S1 = 100 - empty (Phase 2 seeds)", xlabel="S1", ylabel="trials"); ax[0].legend(fontsize=8)
    for a, lab, col in ((ac, "uniform control", "#888"), (ag, "LTM-guided", "#D4537E")):
        ax[1].hist(a["S2"], bins=40, alpha=.55, label=lab, color=col)
    ax[1].set(title="S2 = S1/attempts (Phase 2 seeds)", xlabel="S2"); ax[1].legend(fontsize=8)
    xs = [s["n_trials"] for s in stm1.snapshots]
    for key, lab in (("single_type:P", "P"), ("pair_type:N+P", "N+P"), ("pair_type:E+P", "E+P"), ("triple_type:N+O+P", "N+O+P"), ("triple_type:E+N+P", "E+N+P")):
        ax[2].plot(xs, [s["focus"][key]["frac_top"] if s["focus"][key] else np.nan for s in stm1.snapshots], marker="o", ms=3, label=lab)
    ax[2].set(title="STM (Phase 1): frac of top-25% (by S2) containing key", xlabel="trials seen", ylim=(0, 1)); ax[2].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "phases_comparison.png", dpi=130); plt.close(fig)

    total = time.perf_counter() - T0
    manifest = {"schema": "expt20_phases_manifest_v1", "created": datetime.now().astimezone().isoformat(timespec="seconds"),
                "phase1": meta1, "phase2": {k: v for k, v in meta2.items() if k != "policy"}, "policy": policy.describe(),
                "ranking": "S2 desc, tie-break S1 desc, then trial_id asc", "stm_snapshot_every": SNAP_EVERY, "stm_files": files,
                "control": "same phase-2 seed and trial ids, uniform random picking (Phase 1 style)",
                "code_hash": {**code_hash(ROOT), "phases": {f.name: sha256(f) for f in sorted((ROOT / "src" / "phases").glob("*.py"))},
                              "run_expt20_phases.py": sha256(Path(__file__))},
                "catalogue_hash": catalogue_hash(), "python": platform.python_version(), "numpy": np.__version__,
                "python_executable": sys.executable, "platform": platform.platform(),
                "runtime_seconds": {**{k: round(v, 2) for k, v in rt.items()}, "total": round(total, 2)}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # ---- summary md ----
    sc = [("arm", "arm"), ("S1 mean", "s1m"), ("S1 median", "s1med"), ("S1 max", "s1max"), ("S1 top25 cutoff", "s1cut"),
          ("S2 mean", "s2m"), ("S2 median", "s2med"), ("S2 max", "s2max"), ("S2 top25 cutoff", "s2cut"),
          ("frac trials w/ P", "fp"), ("mean attempts", "att"), ("frac S1>=85", "f85"), ("runtime s", "rt")]
    srows = [{"arm": k, "s1m": v["S1"]["mean"], "s1med": v["S1"]["median"], "s1max": v["S1"]["max"], "s1cut": v["top25_cutoff_by_S1"]["cutoff_S1"],
              "s2m": v["S2"]["mean"], "s2med": v["S2"]["median"], "s2max": v["S2"]["max"], "s2cut": v["top25_cutoff_by_S2"]["cutoff_S2"],
              "fp": v["frac_trials_using_P"], "att": v["mean_attempts"], "f85": v["frac_S1_ge_85"], "rt": round(v["runtime_s"], 1)} for k, v in summ.items()]
    pr = [{"comparison": f"{lab} - control", "metric": k, "mean_diff": d["mean_diff"], "se": d["se"], "ci_low": d["ci95_boot_low"], "ci_high": d["ci95_boot_high"],
           "better": d["frac_other_better"], "worse": d["frac_other_worse"]} for lab, dd in paired.items() for k, d in dd.items()]
    pc = [("comparison", "comparison"), ("metric", "metric"), ("mean diff", "mean_diff"), ("SE", "se"), ("95% boot low", "ci_low"), ("95% boot high", "ci_high"), ("frac better", "better"), ("frac worse", "worse")]
    L = [f"# Expt-20 phases summary ({stamp})", "",
         f"- Phase 1 seed {args.phase1_seed}, Phase 2 seed {args.phase2_seed}, {n} trials per arm, epsilon {args.epsilon}; LTM = `{ltm_path}` (default ranking S2)",
         f"- total runtime {total:.1f}s", "",
         "S2 = S1/attempts is the mean piece area in the box, so it rewards the only 7-cell piece P. Read the S1 rows to judge actual packing.", "",
         "## Arms", "", md_rows(srows, sc), "", "## Paired difference (same seeds; guided/ablation minus uniform control)", "", md_rows(pr, pc), "",
         "## Unpaired: Phase 2 guided minus Phase 1 (different seeds)", "", "```json", json.dumps(unpaired, indent=1), "```", "",
         "## P usage transitions (control -> guided, same seeds)", "", "```json", json.dumps(transitions), "```", "",
         "## Paired S1 difference by P status", "", "```json", json.dumps(strata, indent=1), "```", "",
         f"Guided share of the pooled top-25% (guided+control): by S1 {pooled_share['S1']:.3f}, by S2 {pooled_share['S2']:.3f} (0.5 = no effect)", "",
         "## STM after Phase 1: final cutoff", "", "```json", json.dumps(stm1_d["final_cutoff"]), "```", ""]
    tc = [("key", "key_str"), ("n_top", "n_top"), ("frac_top", "frac_top"), ("n_bottom", "n_bottom"), ("lift_vs_bottom", "lift_vs_bottom"), ("winning", "winning")]
    for kind in ("single_type", "pair_type", "triple_type", "pair_conn_type", "triple_conn_type"):
        L += [f"### STM Phase 1 top 10: {kind}", "", md_rows(stm1_d["stm"][kind]["entries"][:10], tc), ""]
    L += ["## STM focus keys over snapshots (Phase 1, frac of top-25% containing key / lift)", ""]
    for key in stm1.snapshots[0]["focus"]:
        L.append(f"- {key}: " + "; ".join(f"{s['n_trials']}: {s['focus'][key]['frac_top']:.3f}/{s['focus'][key]['lift_vs_bottom']:.2f}" if s["focus"][key] and s["focus"][key]["lift_vs_bottom"] is not None else f"{s['n_trials']}: n/a" for s in stm1.snapshots))
    for kind in ("single_type", "pair_type", "triple_type", "triple_conn_type"):
        L += ["", f"### STM Phase 2 guided top 10: {kind}", "", md_rows(stm2_d["stm"][kind]["entries"][:10], tc)]
    (out / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print(out); print(f"total {total:.1f}s")


if __name__ == "__main__":
    main()