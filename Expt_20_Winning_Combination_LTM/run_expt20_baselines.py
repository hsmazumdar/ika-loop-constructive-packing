"""Expt-20 baselines: plain first-fit / greedy packers, the Expt-1 agent and the Expt-16 primitive policy, on the same boxes
(held-out seed 20261003, 10,000 trials) as the stronger run, next to the Expt-20 variants. Headless, process-parallel.
Writes results/<timestamp>_baselines/. Nothing existing is modified."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import platform
import subprocess
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PATHS = [str(REPO / "Expt_01_10x10_Packing" / "code"), str(ROOT / "src")]
for _p in PATHS:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402
from baselines import arms_b  # noqa: E402
from baselines.rules import RULES, Rule  # noqa: E402
from ltm import code_hash, load_ltm  # noqa: E402
from stronger import arms as A  # noqa: E402
from stronger.policies import Spec  # noqa: E402
from stronger.stats import arm_arrays, arm_row, paired_boot  # noqa: E402

HELD_SEED = 20261003
STRONGER = ROOT / "results" / "20260930_210213_stronger"
FROZEN_LTM = ROOT / "results" / "20260930_131353_run_S2default" / "ltm" / "ltm.pkl"
EXPT20_ARMS = ("D_anchor_contact_eps0", "D_contact_all_eps0", "E_joint_look_K8_eps0", "A_ltmS2_eps0.05_a3b1")
FAMILY = {"control": "uniform random", "reference_guided": "Expt-20 LTM-guided (earlier)"}


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def init_b(paths, ltms, tables, guard):
    A.init_worker(paths, ltms, tables, guard)


def row_extra(a: dict) -> dict:
    s1 = a["S1"]
    return {"frac_full_box": float((s1 == 100).mean()), "frac_S1_ge_95": float((s1 >= 95).mean()), "S1_std": float(s1.std()),
            "S1_min": float(s1.min()), "distinct_S1_values": int(len(np.unique(s1)))}


def load_e16(path: Path) -> tuple[list[dict], float]:
    d = np.load(path)
    arr, cols = d["data"], [str(c) for c in d["columns"]]
    ix = {c: i for i, c in enumerate(cols)}
    out = []
    for r in arr:
        s1, att = float(r[ix["S1"]]), float(r[ix["attempts"]])
        out.append({"trial_id": int(r[ix["trial_id"]]), "S1": s1, "S2": s1 / att if att else 0.0, "attempts": att, "n_P": float(r[ix["n_P"]]),
                    "enum_ops": float(r[ix["enum_ops"]]), "mask_ops": 0.0, "cand_evals": float(r[ix["A"]]),
                    "eval_cap_hit": float(r[ix["termination"]] == 1)})
    return out, float(d["cpu_seconds"])


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)


def fmt(v, nd=3):
    return "" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=10_000)
    ap.add_argument("--workers", type=int, default=18)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--tag", default="baselines")
    ap.add_argument("--skip-validation", action="store_true")
    ap.add_argument("--skip-e1", action="store_true")
    args = ap.parse_args()
    if not args.skip_validation:
        if subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=ROOT).returncode != 0:
            raise SystemExit("unit tests failed; run aborted")
    n = args.trials
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ROOT / "results" / f"{stamp}_{args.tag}"
    out.mkdir(parents=True, exist_ok=True)
    T0 = time.perf_counter()
    log = open(out / "run_log.txt", "w", encoding="utf-8")

    def say(m):
        line = f"[{time.perf_counter() - T0:7.1f}s] {m}"; print(line, flush=True); log.write(line + "\n"); log.flush()

    frozen = load_ltm(FROZEN_LTM)
    specs_all = json.loads((STRONGER / "specs.json").read_text(encoding="utf-8"))
    xspecs = [Spec(**specs_all[k]) for k in EXPT20_ARMS]
    results: dict = {}; cpu: dict = {}; groups: dict = {}

    def submit(ex, key, job_list, group):
        groups[key] = group
        return [(key, ex.submit(arms_b.run_chunk_b, j)) for j in job_list]

    with ProcessPoolExecutor(args.workers, initializer=init_b, initargs=(PATHS, {"S2_frozen": frozen}, {}, 0)) as ex:
        futs = []
        futs += submit(ex, "uniform_random_control", A.jobs_for("control", HELD_SEED, n), "control")
        futs += submit(ex, "Expt20_LTM_guided_earlier", A.jobs_for("ref", HELD_SEED, n), "Expt-20")
        for s in xspecs:
            futs += submit(ex, f"Expt20_{s.name}", A.jobs_for("spec", HELD_SEED, n, dataclasses.asdict(s)), "Expt-20")
        for r in RULES:
            futs += submit(ex, r.name, A.jobs_for("rule", HELD_SEED, n, r.as_dict(), chunk=500), "plain rule")
        if not args.skip_e1:
            futs += submit(ex, "Expt1_agent_none_eps0.15", A.jobs_for("e1", HELD_SEED, n, None, chunk=50), "earlier expt")
        say(f"submitted {len(futs)} chunks")
        for key, f in futs:
            _, o, secs = f.result()
            results.setdefault(key, []).extend(o); cpu[key] = cpu.get(key, 0.0) + secs
    say(f"main pool done ({time.perf_counter() - T0:.0f}s)")

    # Expt-16 primitive (separate process: module name clashes). Two stopping rules.
    e16 = {}
    for label, qmin in (("Expt16_primitive_recorded_stop_Q75", 75), ("Expt16_primitive_run_to_cap_Q101", 101)):
        p = out / f"_e16_{qmin}.npz"
        rc = subprocess.run([sys.executable, "-B", str(ROOT / "src" / "baselines" / "e16_run.py"), "--seed", str(HELD_SEED), "--trials", str(n),
                             "--workers", str(args.workers), "--q-min", str(qmin), "--out", str(p)], cwd=ROOT).returncode
        if rc != 0:
            raise SystemExit("e16 run failed")
        r, c = load_e16(p); results[label] = r; cpu[label] = c; groups[label] = "earlier expt"
        say(f"{label} done")

    ctrl = arm_arrays(results["uniform_random_control"])
    arrs = {k: arm_arrays(v) for k, v in results.items()}
    rows = []
    for k, r in results.items():
        a = arrs[k]
        row = arm_row(k, groups[k], a, ctrl, cpu[k], args.n_boot, seed=zlib.crc32(k.encode()) % 1000)
        row.update(row_extra(a))
        row["cpu_ms_per_box"] = cpu[k] / n * 1000
        row["deterministic_rule"] = bool(next((x.deterministic for x in RULES if x.name == k), False))
        if "eval_cap_hit" in r[0]:
            row["frac_hit_eval_cap"] = float(np.mean([t["eval_cap_hit"] for t in r]))
        rows.append(row)
    # best plain baseline = highest S1 mean among plain rules (chosen after the fact, reported as such)
    plain = [r for r in rows if r["family"] == "plain rule"]
    best_plain = max(plain, key=lambda r: r["S1_mean"])
    best_random_plain = max((r for r in plain if not r["deterministic_rule"]), key=lambda r: r["S1_mean"])
    best_any_base = max((r for r in rows if r["family"] in ("plain rule", "earlier expt")), key=lambda r: r["S1_mean"])
    for r in rows:
        for label, b in (("best_plain", best_plain), ("best_nondet_plain", best_random_plain)):
            d = paired_boot(arrs[r["variant"]]["S1"] - arrs[b["variant"]]["S1"], args.n_boot, seed=7)
            r[f"S1_gain_vs_{label}"], r[f"S1_gain_vs_{label}_lo"], r[f"S1_gain_vs_{label}_hi"] = d["mean"], d["lo"], d["hi"]
        d = paired_boot(arrs[r["variant"]]["S1"] - arrs["Expt20_D_anchor_contact_eps0"]["S1"], args.n_boot, seed=8)
        r["S1_gain_vs_D_anchor_contact"], r["S1_gain_vs_D_anchor_contact_lo"], r["S1_gain_vs_D_anchor_contact_hi"] = d["mean"], d["lo"], d["hi"]
    rows.sort(key=lambda r: -r["S1_mean"])
    write_csv(out / "leaderboard_baselines.csv", rows)
    np.savez_compressed(out / "arrays.npz", **{k: np.array([[t["S1"], t["S2"], t["attempts"]] for t in sorted(v, key=lambda q: q["trial_id"])]) for k, v in results.items()})
    (out / "rules.json").write_text(json.dumps([r.as_dict() for r in RULES], indent=1), encoding="utf-8")

    # recorded numbers of the earlier experiments (authoritative runs): computed from their saved CSVs
    rec = recorded_earlier()
    (out / "recorded_earlier_experiments.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")

    total = time.perf_counter() - T0
    manifest = {"schema": "expt20_baselines_manifest_v1", "created": datetime.now().astimezone().isoformat(timespec="seconds"), "seed": HELD_SEED,
                "trials": n, "same_boxes_as": str(STRONGER), "workers": args.workers, "n_boot": args.n_boot,
                "best_plain_baseline": best_plain["variant"], "best_nondeterministic_plain": best_random_plain["variant"],
                "code_hash": {**code_hash(ROOT), "baselines": {f.name: sha(f) for f in sorted((ROOT / "src" / "baselines").glob("*.py"))},
                              "stronger": {f.name: sha(f) for f in sorted((ROOT / "src" / "stronger").glob("*.py"))},
                              "phases": {f.name: sha(f) for f in sorted((ROOT / "src" / "phases").glob("*.py"))},
                              "run_expt20_baselines.py": sha(Path(__file__))},
                "python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(),
                "runtime_seconds": round(total, 1)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    cols = [("variant", "variant", 0), ("family", "family", 0), ("S1 mean", "S1_mean", 3), ("S1 std", "S1_std", 2), ("S1 max", "S1_max", 0),
            ("gain vs uniform [95% CI]", None, 0), ("gain vs best plain [95% CI]", None, 0), ("gain vs D_anchor_contact [95% CI]", None, 0),
            ("S2 mean", "S2_mean", 4), ("attempts", "attempts_mean", 2), ("extra units/box", "extra_cost_units_per_box", 0),
            ("enum units/box", "enum_ops_per_box", 0), ("full boxes", "frac_full_box", 4), ("S1>=95", "frac_S1_ge_95", 3), ("cpu ms/box", "cpu_ms_per_box", 2)]
    md = [f"# Expt-20 baselines ({stamp})", "",
          f"- {n} boxes per arm, seed {HELD_SEED} (the held-out seed of the stronger run), paired by per-trial seed id. Bootstrap 95% CI, {args.n_boot} resamples over trial pairs. Total {total:.0f}s.",
          f"- Best plain baseline (picked after seeing results, from {len(plain)} rules): **{best_plain['variant']}** (S1 {best_plain['S1_mean']:.3f}). Best non-deterministic plain rule: {best_random_plain['variant']} ({best_random_plain['S1_mean']:.3f}).",
          "- Rules marked deterministic have no random step: every box is identical, S1 std 0. They are one solution, evaluated 10,000 times; a CI on them is a CI on the control's variation.",
          "- Effort: `extra units` = strategy's own mask tests + scored candidates (rules, Expt-20 arms); for the Expt-1 agent it is its `candidate_evaluations`; for the Expt-16 primitive it is its A (candidates examined). `enum units` = 3,636 placement-visits per decision, where the code enumerates the catalogue. These scales are similar in spirit but not identical.", "",
          "| rank | " + " | ".join(c[0] for c in cols) + " |", "|---:|" + "|".join(["---"] * len(cols)) + "|"]
    for i, r in enumerate(rows, 1):
        cells = []
        for h, k, nd in cols:
            if h.startswith("gain vs uniform"):
                cells.append(f"{r['S1_gain']:+.3f} [{r['S1_gain_lo']:+.3f}, {r['S1_gain_hi']:+.3f}]")
            elif h.startswith("gain vs best plain"):
                cells.append(f"{r['S1_gain_vs_best_plain']:+.3f} [{r['S1_gain_vs_best_plain_lo']:+.3f}, {r['S1_gain_vs_best_plain_hi']:+.3f}]")
            elif h.startswith("gain vs D_anchor"):
                cells.append(f"{r['S1_gain_vs_D_anchor_contact']:+.3f} [{r['S1_gain_vs_D_anchor_contact_lo']:+.3f}, {r['S1_gain_vs_D_anchor_contact_hi']:+.3f}]")
            else:
                cells.append(fmt(r.get(k), nd))
        md.append(f"| {i} | " + " | ".join(cells) + " |")
    md += ["", "## Recorded numbers of the earlier experiments (saved authoritative runs, different tasks)", "", "```json", json.dumps(rec, indent=2), "```"]
    (out / "summary.md").write_text("\n".join(md), encoding="utf-8")
    for p in out.glob("_e16_*.npz"):
        pass
    say(f"done -> {out}")
    log.close()


def recorded_earlier() -> dict:
    import statistics as st
    res = {}
    def rd(p):
        return list(csv.DictReader(open(REPO / p, encoding="utf-8")))
    e1 = rd(r"Expt_01_10x10_Packing\results\episodes.csv")
    for mode in ("none",):
        ev = [x for x in e1 if x["mode"] == mode and x["phase"] == "eval"]
        res["Expt-1 smoke (results/episodes.csv), mode none, eval boxes"] = {
            "n_boxes": len(ev), "mean_terminal_occupied": st.mean(float(x["terminal_score"]) for x in ev), "max": max(float(x["terminal_score"]) for x in ev),
            "mean_candidate_evaluations": st.mean(float(x["candidate_evaluations"]) for x in ev), "mean_actions": st.mean(float(x["actions"]) for x in ev),
            "mean_undos": st.mean(float(x["undos"]) for x in ev), "task": "empty 10x10 box, unlimited pieces, 100-action budget (same task as Expt-20)",
            "note": "run folder pointed to by LATEST_RUN.txt is not the same as this summary file's; this is the repo-root episodes.csv as saved"}
    e2 = rd(r"Expt_02_Autonomous_Abstraction\results\20260929_092518_discovery_smoke\episodes.csv")
    p = [x for x in e2 if x["mode"] == "primitive"]
    res["Expt-2 primitive (authoritative run 20260929_092518_discovery_smoke)"] = {
        "n_boxes": len(p), "mean_final_occupied": st.mean(float(x["final_score"]) for x in p), "max": max(float(x["final_score"]) for x in p),
        "mean_candidate_evals": st.mean(float(x["candidate_evals"]) for x in p), "task": "inventory tasks (limited pieces per box), compute budget 50,000 evals, about 14 placements; different boxes"}
    e16 = rd(r"Expt_16_Search_Acquired_Local_Memory\results\20260930_071552_diagnostic\boxes.csv")
    for wl in ("independent_fresh", "recurring_family"):
        r = [x for x in e16 if x["workload"] == wl]
        res[f"Expt-16 primitive (authoritative 20260930_071552), {wl}"] = {
            "n_boxes": len(r), "mean_Q_occupied": st.mean(float(x["Q"]) for x in r), "min": min(float(x["Q"]) for x in r), "max": max(float(x["Q"]) for x in r),
            "mean_A_candidates": st.mean(float(x["A"]) for x in r), "median_A": st.median(float(x["A"]) for x in r),
            "task": "inventory tasks; the policy stops once occupied >= 75 (q_min) or at eval_cap 8000, so its Q is a floor-stop, not a best effort"}
    return res


if __name__ == "__main__":
    main()