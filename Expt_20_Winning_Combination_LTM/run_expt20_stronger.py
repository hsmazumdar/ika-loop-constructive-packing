"""Expt-20 stronger guidance. Headless, seed-paired, process-parallel.

Stages: build (fresh uniform builder run -> S1/S2 LTMs and placement tables) -> dev screen (seed 20261002, the earlier control's
seeds) -> dev combos -> held-out (fresh seed 20261003) for the selected variants. Hyperparameters are chosen on dev only.
Writes results/<timestamp>_stronger/. The frozen S2 LTM is only read."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import pickle
import platform
import subprocess
import sys
import zlib
import time
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
from ltm import code_hash, load_ltm  # noqa: E402
from stronger import arms as A  # noqa: E402
from stronger.ltmbuild import build_ltm, build_placement_table, type_keysets  # noqa: E402
from stronger.policies import Spec  # noqa: E402
from stronger.stats import arm_arrays, arm_row  # noqa: E402

BUILD_SEED, DEV_SEED, HELD_SEED = 20261004, 20261002, 20261003
FROZEN_LTM = ROOT / "results" / "20260930_131353_run_S2default" / "ltm" / "ltm.pkl"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def S(name, family, **kw):
    return Spec(name=name, family=family, **kw)


def stage1_specs() -> list[Spec]:
    L = []
    # A. stronger weights on the frozen S2 LTM (type level, random placement)
    for e in (0.0, 0.05, 0.1, 0.2):
        L.append(S(f"A_ltmS2_eps{e}_a1b1", "A_weights", eps=e))
    L += [S("A_ltmS2_eps0.05_a2b1", "A_weights", eps=0.05, alpha=2.0),
          S("A_ltmS2_eps0.05_a3b1", "A_weights", eps=0.05, alpha=3.0),
          S("A_ltmS2_eps0.05_a2b2", "A_weights", eps=0.05, alpha=2.0, beta=2.0),
          S("A_ltmS2_eps0_a2b2", "A_weights", eps=0.0, alpha=2.0, beta=2.0),
          S("A_ltmS2_single_only_eps0.05_a2", "A_weights", eps=0.05, alpha=2.0, use_boost=False),
          S("A_ltmS2_boost_only_eps0.05_b2", "A_weights", eps=0.05, beta=2.0, use_single=False),
          S("A_size_a1_eps0.05", "A_weights", eps=0.05, type_mode="size", alpha=1.0, note="weight area^alpha, no LTM"),
          S("A_size_a2_eps0.05", "A_weights", eps=0.05, type_mode="size", alpha=2.0),
          S("A_size_a4_eps0", "A_weights", eps=0.0, type_mode="size", alpha=4.0)]
    # B. S1-based LTMs from the fresh builder run
    for lt in ("S1_top25", "S1_top10", "S2_fresh"):
        L.append(S(f"B_{lt}_eps0.05_a1b1", "B_S1ltm", eps=0.05, ltm=lt))
        L.append(S(f"B_{lt}_eps0.05_a2b2", "B_S1ltm", eps=0.05, ltm=lt, alpha=2.0, beta=2.0))
    # C. actively completing winning combinations (hard priority, big boosts)
    L += [S("C_hard_S2_eps0.05_bmax6", "C_complete", eps=0.05, hard_priority=True),
          S("C_hard_S2_eps0.05_bmax20_b2", "C_complete", eps=0.05, hard_priority=True, boost_max=20.0, beta=2.0),
          S("C_hard_S1top25_eps0.05_bmax6", "C_complete", eps=0.05, hard_priority=True, ltm="S1_top25"),
          S("C_hard_S1top10_eps0.05_bmax20_b2", "C_complete", eps=0.05, hard_priority=True, ltm="S1_top10", boost_max=20.0, beta=2.0),
          S("C_hard_S2_a2_eps0.05_bmax6", "C_complete", eps=0.05, hard_priority=True, alpha=2.0)]
    # D. placement-level (no lookahead)
    L += [S("D_anchor_random_eps0", "D_placement", eps=0.0, type_mode="placement_uniform", anchor=True),
          S("D_contact_all_eps0", "D_placement", eps=0.0, type_mode="placement_uniform", select="contact"),
          S("D_anchor_contact_eps0", "D_placement", eps=0.0, type_mode="placement_uniform", anchor=True, select="contact"),
          S("D_flat_anchor_contact_eps0.05", "D_placement", eps=0.05, type_mode="flat", anchor=True, select="contact"),
          S("D_table_S1_g1_joint_eps0.05", "D_placement", eps=0.05, type_mode="placement_uniform", select="table", table="pt_S1", gamma=1.0),
          S("D_table_S1_g2_joint_eps0.05", "D_placement", eps=0.05, type_mode="placement_uniform", select="table", table="pt_S1", gamma=2.0),
          S("D_table_S2_g1_joint_eps0.05", "D_placement", eps=0.05, type_mode="placement_uniform", select="table", table="pt_S2", gamma=1.0),
          S("D_ltmS2_table_S1_g1_eps0.05", "D_placement", eps=0.05, select="table", table="pt_S1", gamma=1.0),
          S("D_ltmS2_contact_eps0.05", "D_placement", eps=0.05, select="contact"),
          S("D_ltmS2_anchor_random_eps0.05", "D_placement", eps=0.05, anchor=True),
          S("D_ltmS2_anchor_contact_eps0.05", "D_placement", eps=0.05, anchor=True, select="contact")]
    # E. one-step lookahead (min dead cells after placing, K sampled candidates)
    L += [S("E_flat_look_K4_eps0", "E_lookahead", eps=0.0, type_mode="flat", select="look", K=4),
          S("E_flat_look_K8_eps0", "E_lookahead", eps=0.0, type_mode="flat", select="look", K=8),
          S("E_flat_look_K16_eps0", "E_lookahead", eps=0.0, type_mode="flat", select="look", K=16),
          S("E_joint_look_K8_eps0", "E_lookahead", eps=0.0, type_mode="placement_uniform", select="look", K=8),
          S("E_ltmS2_look_K8_eps0.05", "E_lookahead", eps=0.05, select="look", K=8),
          S("E_ltmS2_anchor_look_K8_eps0.05", "E_lookahead", eps=0.05, anchor=True, select="look", K=8)]
    # F. online learning of type weights (sequential, bandit-style on observed S1)
    for mode in ("softmax", "thompson"):
        for tau in (1.0, 0.5):
            L.append(S(f"F_online_{mode}_tau{tau}_eps0.05", "F_online", eps=0.05, type_mode="online", online=mode, tau=tau))
    return L


def combo_specs(rows: list[dict], specs: dict) -> list[Spec]:
    """Cross the best two type-level variants (A,B,C,F excluded for F) with the best two placement-level variants (D,E) on dev."""
    typ = [r for r in rows if r["family"] in ("A_weights", "B_S1ltm", "C_complete") and specs[r["variant"]].select == "random" and not specs[r["variant"]].anchor]
    plc = [r for r in rows if r["family"] in ("D_placement", "E_lookahead")]
    typ = sorted(typ, key=lambda r: -r["S1_gain"])[:2]
    plc = sorted(plc, key=lambda r: -r["S1_gain"])[:2]
    out = []
    for tr in typ:
        for pr in plc:
            t, p = specs[tr["variant"]], specs[pr["variant"]]
            out.append(dataclasses.replace(t, name=f"G_combo[{t.name}]+[{p.name}]", family="G_combo", anchor=p.anchor, select=p.select,
                                           K=p.K, table=p.table, gamma=p.gamma, note="type part from first, placement part from second"))
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)


def fmt(v, nd=3):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def leaderboard_md(rows: list[dict], title: str, ctrl_cpu_ms: float) -> str:
    cols = [("variant", "variant", 0), ("family", "family", 0), ("S1 mean", "S1_mean", 3), ("paired S1 gain", "S1_gain", 3), ("95% CI", None, 0),
            ("S2 mean", "S2_mean", 4), ("paired S2 gain", "S2_gain", 4), ("attempts", "attempts_mean", 2), ("frac P", "frac_P", 3),
            ("extra units/box", "extra_cost_units_per_box", 0), ("S1 gain / 1k units", "S1_gain_per_1k_extra_units", 3),
            ("cpu ms/box", "cpu_ms_per_box", 2), ("S1>=85", "frac_S1_ge_85", 3)]
    out = [f"### {title}", "", "| rank | " + " | ".join(c[0] for c in cols) + " |", "|---:|" + "|".join(["---"] * len(cols)) + "|"]
    for i, r in enumerate(rows, 1):
        cells = []
        for h, k, nd in cols:
            if h == "95% CI":
                cells.append(f"[{r['S1_gain_lo']:.3f}, {r['S1_gain_hi']:.3f}]")
            else:
                cells.append(fmt(r.get(k), nd))
        out.append(f"| {i} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=10_000)
    ap.add_argument("--workers", type=int, default=18)
    ap.add_argument("--tag", default="stronger")
    ap.add_argument("--skip-validation", action="store_true")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--n-final", type=int, default=5)
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

    def say(msg):
        line = f"[{time.perf_counter() - T0:7.1f}s] {msg}"
        print(line, flush=True); log.write(line + "\n"); log.flush()

    frozen = load_ltm(FROZEN_LTM)
    assert frozen["default_ranking"] == "S2"
    timings: dict = {}

    # ---------- build stage ----------
    t0 = time.perf_counter()
    with ProcessPoolExecutor(args.workers, initializer=A.init_worker, initargs=(PATHS, {}, {}, 0)) as ex:
        res = list(ex.map(A.run_chunk, A.jobs_for("control_full", BUILD_SEED, n)))
    build = sorted((t for _, o, _ in res for t in o), key=lambda t: t["trial_id"])
    meta = [{"trial_id": t["trial_id"], "S1": t["S1"], "S2": t["S2"]} for t in build]
    ks = [type_keysets(t["placements"]) for t in build]
    ltms = {"S2_frozen": frozen,
            "S1_top25": build_ltm(ks, meta, "S1", 0.25, "S1_top25 (fresh builder run, top 25% by S1, tie-break S2)", extra_manifest={"seed": BUILD_SEED}),
            "S1_top10": build_ltm(ks, meta, "S1", 0.10, "S1_top10 (fresh builder run, top 10% by S1)", extra_manifest={"seed": BUILD_SEED}),
            "S2_fresh": build_ltm(ks, meta, "S2", 0.25, "S2_fresh (fresh builder run, top 25% by S2)", extra_manifest={"seed": BUILD_SEED})}
    tables = {"pt_S1": build_placement_table(build, "S1", 0.25), "pt_S2": build_placement_table(build, "S2", 0.25)}
    with (out / "built_knowledge.pkl").open("wb") as fh:
        pickle.dump({"ltms": {k: v for k, v in ltms.items() if k != "S2_frozen"}, "placement_tables": tables, "build_seed": BUILD_SEED}, fh, protocol=4)
    (out / "built_ltm_summaries.json").write_text(json.dumps({
        k: {"manifest": v["manifest"], "cutoffs": v["cutoffs"],
            "top_singles": [(e["key_str"], round(e["lift_vs_bottom"] or 0, 3), e["winning"]) for e in v["ltm"][v["default_ranking"]]["single_type"]["entries"][:16]],
            "n_winning_pairs": sum(e["winning"] for e in v["ltm"][v["default_ranking"]]["pair_type"]["entries"]),
            "n_winning_triples": sum(e["winning"] for e in v["ltm"][v["default_ranking"]]["triple_type"]["entries"])}
        for k, v in ltms.items() if k != "S2_frozen"}, indent=1, default=str), encoding="utf-8")
    timings["build"] = time.perf_counter() - t0
    say(f"build stage done ({timings['build']:.1f}s); builder S1 mean {np.mean([m['S1'] for m in meta]):.3f}")

    def run_batch(seed: int, specs: list[Spec], with_ref: bool, label: str) -> dict:
        """Returns {variant: (results, cpu_seconds)} including 'control' (and 'reference_guided' if with_ref)."""
        t0 = time.perf_counter()
        results, cpu = {}, {}
        with ProcessPoolExecutor(args.workers, initializer=A.init_worker, initargs=(PATHS, ltms, tables, 0)) as ex:
            futs = []
            kinds = [("control", None, "control")] + ([("ref", None, "reference_guided")] if with_ref else [])
            for kind, payload, key in kinds:
                for job in A.jobs_for(kind, seed, n):
                    futs.append((key, ex.submit(A.run_chunk, job)))
            for s in specs:
                online = s.type_mode == "online"
                for job in A.jobs_for("spec", seed, n, dataclasses.asdict(s), online=online):
                    futs.append((s.name, ex.submit(A.run_chunk, job)))
            for key, f in futs:
                _, o, secs = f.result()
                results.setdefault(key, []).extend(o); cpu[key] = cpu.get(key, 0.0) + secs
        say(f"{label}: {len(specs)} variants x {n} trials done in {time.perf_counter() - t0:.1f}s wall")
        return {k: (results[k], cpu[k]) for k in results}

    def rows_from(batch: dict, specs: dict, fam_override: dict | None = None) -> list[dict]:
        ctrl = arm_arrays(batch["control"][0]); ctrl_ms = batch["control"][1] / n * 1000
        rows = []
        for k, (r, c) in batch.items():
            if k == "control":
                continue
            fam = "REF_earlier_guided" if k == "reference_guided" else specs[k].family
            row = arm_row(k, fam, arm_arrays(r), ctrl, c, args.n_boot, seed=zlib.crc32(k.encode()) % 1000)
            row["cpu_ms_per_box"] = c / n * 1000; row["control_cpu_ms_per_box"] = ctrl_ms
            d = row["cpu_ms_per_box"] - ctrl_ms
            row["S1_gain_per_extra_cpu_ms"] = row["S1_gain"] / d if d > 0.05 else None
            rows.append(row)
        return rows

    # ---------- dev stage 1 ----------
    s1 = stage1_specs()
    spec_by_name = {s.name: s for s in s1}
    dev1 = run_batch(DEV_SEED, s1, True, "dev stage 1")
    dev_rows = rows_from(dev1, spec_by_name)
    ctrl_row = arm_row("control_uniform", "control", arm_arrays(dev1["control"][0]), arm_arrays(dev1["control"][0]), dev1["control"][1], args.n_boot)
    ctrl_row.update(cpu_ms_per_box=dev1["control"][1] / n * 1000, control_cpu_ms_per_box=dev1["control"][1] / n * 1000, S1_gain_per_extra_cpu_ms=None)
    # replicate check against the earlier run (same seed, same control)
    say(f"control dev S1 mean {ctrl_row['S1_mean']:.4f} (earlier Phase 2 control: 79.8561)")

    # ---------- dev combos ----------
    combos = combo_specs(dev_rows, spec_by_name)
    for c in combos:
        spec_by_name[c.name] = c
    dev2 = run_batch(DEV_SEED, combos, False, "dev combos")
    dev_rows += [r for r in rows_from({**dev2, "control": dev1["control"]}, spec_by_name) if r["variant"] != "reference_guided"]
    dev_all = {**{k: v for k, v in dev1.items()}, **{k: v for k, v in dev2.items() if k != "control"}}

    dev_sorted = sorted(dev_rows, key=lambda r: -r["S1_gain"])
    write_csv(out / "leaderboard_dev.csv", [ctrl_row] + dev_sorted)
    np.savez_compressed(out / "dev_arrays.npz", **{k: np.array([[r["S1"], r["S2"], r["attempts"]] for r in sorted(v[0], key=lambda q: q["trial_id"])]) for k, v in dev_all.items()})
    say("dev leaderboard written")

    # ---------- selection on dev ----------
    chosen = []
    def add(name):
        if name in spec_by_name and name not in chosen:
            chosen.append(name)
    for r in dev_sorted:
        if r["family"] == "REF_earlier_guided":
            continue
        if len([c for c in chosen if c in spec_by_name]) >= args.n_final:
            break
        add(r["variant"])
    best_s2 = max((r for r in dev_rows if r["family"] != "REF_earlier_guided"), key=lambda r: r["S2_gain"])
    add(best_s2["variant"])
    eff = [r for r in dev_rows if r["S1_gain"] > 0.5 and r["family"] != "REF_earlier_guided" and r["S1_gain_per_extra_cpu_ms"] is not None]
    if eff:
        add(max(eff, key=lambda r: r["S1_gain_per_extra_cpu_ms"])["variant"])
    cheapest = [r for r in dev_rows if r["extra_cost_units_per_box"] == 0 and r["family"] not in ("REF_earlier_guided", "F_online")]
    if cheapest:
        add(max(cheapest, key=lambda r: r["S1_gain"])["variant"])   # best type-level-only (zero extra unit cost) variant
    # best online variant if any (so the online idea is judged on held-out too)
    onl = [r for r in dev_rows if r["family"] == "F_online"]
    if onl:
        add(max(onl, key=lambda r: r["S1_gain"])["variant"])
    say(f"selected on dev for held-out: {chosen}")

    # ---------- held-out ----------
    held = run_batch(HELD_SEED, [spec_by_name[c] for c in chosen], True, "held-out")
    held_rows = rows_from(held, spec_by_name)
    held_ctrl = arm_row("control_uniform", "control", arm_arrays(held["control"][0]), arm_arrays(held["control"][0]), held["control"][1], args.n_boot)
    held_ctrl.update(cpu_ms_per_box=held["control"][1] / n * 1000, control_cpu_ms_per_box=held["control"][1] / n * 1000, S1_gain_per_extra_cpu_ms=None)
    dev_by = {r["variant"]: r for r in dev_rows}
    for r in held_rows:
        d = dev_by.get(r["variant"])
        r["dev_S1_gain"] = d["S1_gain"] if d else None
        r["dev_S2_gain"] = d["S2_gain"] if d else None
    held_sorted = sorted(held_rows, key=lambda r: -r["S1_gain"])
    write_csv(out / "leaderboard_heldout.csv", [held_ctrl] + held_sorted)
    np.savez_compressed(out / "heldout_arrays.npz", **{k: np.array([[r["S1"], r["S2"], r["attempts"]] for r in sorted(v[0], key=lambda q: q["trial_id"])]) for k, v in held.items()})
    (out / "specs.json").write_text(json.dumps({k: dataclasses.asdict(v) for k, v in spec_by_name.items()}, indent=1), encoding="utf-8")

    # ---------- figure ----------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    fams = sorted({r["family"] for r in dev_rows})
    cm = plt.get_cmap("tab10")
    for i, f in enumerate(fams):
        pts = [r for r in dev_rows if r["family"] == f]
        ax[0].scatter([r["extra_cost_units_per_box"] + 1 for r in pts], [r["S1_gain"] for r in pts], label=f, color=cm(i), s=28)
        ax[1].scatter([r["S2_gain"] for r in pts], [r["S1_gain"] for r in pts], label=f, color=cm(i), s=28)
    ax[0].set(xscale="log", xlabel="extra strategy cost units per box (+1)", ylabel="paired S1 gain vs uniform (dev)", title="Dev: S1 gain vs extra compute")
    ax[1].set(xlabel="paired S2 gain (dev)", ylabel="paired S1 gain (dev)", title="Dev: S1 gain vs S2 gain")
    for a in ax:
        a.axhline(0, color="k", lw=.5)
    ax[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(out / "leaderboard_dev.png", dpi=130); plt.close(fig)

    total = time.perf_counter() - T0
    manifest = {"schema": "expt20_stronger_manifest_v1", "created": datetime.now().astimezone().isoformat(timespec="seconds"),
                "seeds": {"build": BUILD_SEED, "dev": DEV_SEED, "heldout": HELD_SEED}, "trials_per_arm": n,
                "frozen_ltm": {"path": str(FROZEN_LTM), "sha256": sha(FROZEN_LTM)}, "chosen_on_dev": chosen,
                "n_variants_dev_stage1": len(s1), "n_variants_dev_combo": len(combos),
                "code_hash": {**code_hash(ROOT), "phases": {f.name: sha(f) for f in sorted((ROOT / "src" / "phases").glob("*.py"))},
                              "stronger": {f.name: sha(f) for f in sorted((ROOT / "src" / "stronger").glob("*.py"))},
                              "run_expt20_stronger.py": sha(Path(__file__))},
                "workers": args.workers, "n_boot": args.n_boot, "python": platform.python_version(), "numpy": np.__version__,
                "platform": platform.platform(), "cpu_count": __import__("os").cpu_count(),
                "runtime_seconds": {**{k: round(v, 1) for k, v in timings.items()}, "total": round(total, 1)}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    md = [f"# Expt-20 stronger guidance ({stamp})", "",
          f"- seeds: builder {BUILD_SEED} (fresh uniform 10k -> S1/S2 LTMs and placement tables), dev {DEV_SEED} (same seeds as the earlier Phase-2 control), held-out {HELD_SEED}; {n} trials per arm, {args.workers} worker processes, total {total:.0f}s",
          "- Gain = variant minus uniform control on the same per-trial seeds (paired), bootstrap 95% CI over trial pairs. Cost units: see `src/stronger/engine.py`; `cpu ms/box` is measured wall time inside workers under parallel load (noisy).",
          "- Hyperparameters and variants were chosen on the dev seeds only. Dev numbers of the selected variants are optimistically biased (selection); the held-out table is the unbiased estimate.",
          "- S2 = S1/attempts rewards piece P. S1 is the real packing measure.", "",
          leaderboard_md([ctrl_row], "Dev control", 0), "", leaderboard_md(dev_sorted, "Dev leaderboard (sorted by paired S1 gain)", ctrl_row["cpu_ms_per_box"]), "",
          leaderboard_md([held_ctrl], "Held-out control", 0), "", leaderboard_md(held_sorted, "Held-out leaderboard for the variants selected on dev (sorted by S1 gain)", held_ctrl["cpu_ms_per_box"]), "",
          "### Dev vs held-out S1 gain of selected variants", "", "| variant | dev S1 gain | held-out S1 gain [95% CI] | dev S2 gain | held-out S2 gain |", "|---|---|---|---|---|"]
    for r in held_sorted:
        md.append(f"| {r['variant']} | {fmt(r['dev_S1_gain'])} | {r['S1_gain']:.3f} [{r['S1_gain_lo']:.3f}, {r['S1_gain_hi']:.3f}] | {fmt(r['dev_S2_gain'], 4)} | {r['S2_gain']:.4f} |")
    (out / "summary.md").write_text("\n".join(md), encoding="utf-8")
    say(f"done, total {total:.1f}s -> {out}")
    log.close()


if __name__ == "__main__":
    main()