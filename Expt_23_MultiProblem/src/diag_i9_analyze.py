r"""Summary of the post-hoc diagnostics (amendment A7). DESCRIPTIVE ONLY: no p-values, not pre-registered.
Usage: python src\diag_i9_analyze.py [--root results_i9]   -> <root>/diag_all.csv and <root>/diag_summary.md
Reads the per-unit CSVs written by diag_i9.py (so it also works after results_i9 was merged into the Vivobook project) and compares with the
main-run streams in results/e_streams and results/streams of the same seeds (when present)."""
import sys, pathlib, csv, glob, json, argparse, collections
import numpy as np
SRC = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
ROOT = SRC.parent


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", nargs="+", default=[str(ROOT / "results_i9")], help="one or more result folders (e.g. results_i9 results_vivo_diag); outputs go to the first"); a = ap.parse_args()
    roots = [pathlib.Path(x) for x in a.root]; root = roots[0]
    rows = []
    for f in sorted(g for r_ in roots for g in glob.glob(str(r_ / "D*" / "*.csv"))):
        rows += list(csv.DictReader(open(f)))
    if not rows:
        print("no diagnostic CSVs yet"); return
    with open(root / "diag_all.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    def val(r):
        return float(r["mean_norm"]) if r["mean_norm"] not in ("", None) else float(r["mean_frac"])
    # per unit: mean over splits (equal weight) at (ckpt, net, tau, concepts)
    U = collections.defaultdict(list)
    for r in rows:
        U[(r["suite"], r["arm"], r["variant"], r["seed"], int(r["ckpt"]), r["net"], r["tau"], r["concepts"])].append(val(r))
    S = {k: float(np.mean(v)) for k, v in U.items()}
    norm_kind = "normalised to ref (S1/ref)" if any(r["mean_norm"] not in ("", None) for r in rows) else "S1/free cells"

    # main-run reference arms, same variants/seeds, final checkpoint (from results/e_streams, results/streams)
    refarm = {}
    try:
        import analyze_e as AE, analyze_baselines as AB
        refs = AB.load_refs()
        for folder in ("e_streams", "streams"):
            for r in AE.scores(folder, refs):
                if r["ckpt"] == 20000 and r["cond"] == "capped_nat":
                    refarm.setdefault((r["arm"], r["variant"]), {})[r["seed"]] = r["score"]
    except Exception as ex:
        print("reference arms not available:", ex)

    md = ["# POST-HOC DIAGNOSTICS (DESIGN.md amendment A7) - descriptive, not pre-registered, no significance claims",
          f"Score = mean over the four test splits of {norm_kind}; per-unit values then averaged over seeds (n = seeds). Legacy-problem units (D2L) use the single 10x10 A-P problem.\n"]
    suites = sorted({k[0] for k in S})
    for su in suites:
        md.append(f"\n## {su}")
        arms = sorted({(k[1], k[2]) for k in S if k[0] == su})
        for arm, var in arms:
            ck_all = sorted({k[4] for k in S if k[:3] == (su, arm, var)})
            cfgs = sorted({(k[5], k[6], k[7]) for k in S if k[:3] == (su, arm, var)})
            fin = ck_all[-1]
            seeds = sorted({k[3] for k in S if k[:3] == (su, arm, var)})
            md.append(f"\n### {su} / {arm} / {var}  (seeds {','.join(seeds)}; final checkpoint {fin})\n")
            show = [c for c in cfgs]
            md.append("| ckpt | " + " | ".join(f"{n} t{t}{'' if c == '1' else ' noconc'}" for n, t, c in show) + " |")
            md.append("|---|" + "---|" * len(show))
            for ck in ck_all:
                cells = []
                for n, t, c in show:
                    v = [S[(su, arm, var, s, ck, n, t, c)] for s in seeds if (su, arm, var, s, ck, n, t, c) in S]
                    cells.append(f"{np.mean(v):.3f} ({np.min(v):.3f}-{np.max(v):.3f})" if v else "-")
                md.append(f"| {ck} | " + " | ".join(cells) + " |")
        if su != "D2L":
            md.append("\nMain-run reference (same variant, 20k episodes, all available seeds; slow net, tau 0.25):")
            for (arm, var), d in sorted(refarm.items()):
                if arm in ("F", "R", "RN", "NM", "N") and any(k[0] == su and k[2] == var for k in S):
                    md.append(f"- {arm} / {var}: mean {np.mean(list(d.values())):.3f} (n={len(d)}; min {min(d.values()):.3f}, max {max(d.values()):.3f})")
    # hyper-parameters of the meta-controller at the checkpoints (why is the training data poor?)
    md.append("\n## Meta-controller state at checkpoints (mean over units; tau, eps, lr, sleep_every, hidden, concepts)")
    H = collections.defaultdict(list)
    for f in sorted(g for r_ in roots for g in glob.glob(str(r_ / "D*" / "*.json"))):
        d = json.load(open(f))
        for ck, h in d["diag"]["h_at_ckpt"].items():
            H[(d["diag"]["unit"]["suite"], d["arm"], d["variant"], int(ck))].append(h)
    for k in sorted(H):
        hs = H[k]
        md.append(f"- {k[0]} {k[1]} {k[2]} ckpt {k[3]}: " + ", ".join(f"{q} {np.mean([h[q] for h in hs]):.3g}" for q in ("tau", "eps", "lr", "sleep_every", "hidden", "concepts")))
    # D1 reproduction check
    rep = []
    for f in sorted(g for r_ in roots for g in glob.glob(str(r_ / "D1" / "*.json"))):
        d = json.load(open(f)); r = d["diag"].get("repro")
        if r: rep.append((pathlib.Path(f).stem, r.get("found"), r.get("all_equal"), r.get("train_frac_equal")))
    if rep:
        md.append("\n## D1 reproduction check (retrained stream vs main-run stream, identical numbers expected)")
        for n, fnd, eq, tf in rep:
            md.append(f"- {n}: main-run file found={fnd}, all evaluations identical={eq}, training outcomes identical={tf}")
    txt = "\n".join(md)
    (root / "diag_summary.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()