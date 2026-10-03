"""Item 5: provenance table of every Expt-22b/22c/22d stream, and run-to-run reproducibility (22d run 1 vs rerun)."""
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import D22B, D22C, D22D, RUN, ld, write_csv

def done_lines(log):
    out = {}
    for ln in open(log, encoding="utf-8", errors="replace"):
        m = re.match(r"(\d\d:\d\d:\d\d) DONE (\S+) s(\d+): (\d+)s", ln)
        if m:
            out.setdefault((m.group(2), int(m.group(3))), []).append((m.group(1), int(m.group(4))))
    return out

def hhmmss_minus(t, secs):
    h, m, s = map(int, t.split(":")); x = h * 3600 + m * 60 + s - int(secs)
    x %= 86400
    return f"{x//3600:02d}:{x%3600//60:02d}:{x%60:02d}"

def man(d, name="manifest.json"):
    return json.load(open(d / name))

rows = []
def add_run(d, label, machine, workers, hash_, cfgnote, rerun_set=frozenset(), run1_done=None, extra=None):
    dl = done_lines(d / "progress.log")
    for p in sorted((d / "streams").glob("*.pkl")):
        r = ld(p)
        key = (r["variant"], r["seed"])
        dn = dl.get(key, [])
        # rerun streams: use the LAST DONE line (the rerun); first-run streams: the only DONE line
        t_fin, rt = (dn[-1] if dn else (None, None))
        rows.append(dict(run_folder=label, variant=r["variant"], seed=r["seed"], n_boxes=r["n_boxes"],
                         machine=machine if key not in rerun_set else "HsmPc1 (rerun from box 0)",
                         first_run_machine=machine if key in rerun_set else "",
                         workers_in_run=workers if key not in rerun_set else 13,
                         start_IST=hhmmss_minus(t_fin, r["runtime_s"]) if t_fin else "", finish_IST=t_fin or "",
                         runtime_s_pickle=round(r["runtime_s"], 1), code_hash=hash_ if key not in rerun_set else extra["rerun_hash"],
                         rerun_after_0709_stop=key in rerun_set, final_heldout_S1=float(r["evals"][r["n_boxes"]]["S1"].mean()),
                         hidden_final=int(r["evals"][r["n_boxes"]]["hidden"]), config_note=cfgnote))

# 22b and 22c (single run each, Vivobook; numpy version not recorded in manifest)
m = man(D22B)
add_run(D22B, "Expt_22b/results/20261001_034445_run", "Vivobook (1c7a0169)", 10, m["code_hash"],
        "OMP/BLAS=1; eval 1200 boxes; full 12x20k; ablations 4x10k; seeds 0-11 / 0-3")
m = man(D22C)
add_run(D22C, "Expt_22c/results/20261001_044425_run", "Vivobook (1c7a0169)", 12, m["code_hash"],
        "OMP/BLAS=1; eval 1200 boxes; full 12x32k; seeds 100-111")
# 22d
m1 = man(D22D); m2 = man(D22D, "manifest_rerun.json")
run1_log = D22D / "progress_run1_stopped_0709.log"
d1 = done_lines(run1_log)
finished_run1 = set(d1)
all_streams = {(ld(p)["variant"], ld(p)["seed"]) for p in (D22D / "streams").glob("*.pkl")}
rerun = frozenset(all_streams - finished_run1)
assert len(rerun) == 13, len(rerun)
add_run(D22D, "Expt_22d/results/20261001_060654_main", "Vivobook (1c7a0169)", 26, m1["code_hash"],
        "OMP/BLAS=1; eval 1200 boxes; full 6x60k seeds 300-305; ablations 4x32k seeds 200-203", rerun,
        extra={"rerun_hash": m2["code_hash"]})
# the 13 first-run DONE streams: start/finish come from the run-1 log (progress.log also contains them)
write_csv(RUN / "item5_stream_provenance.csv", rows)
print(len(rows), "streams;", sum(r["rerun_after_0709_stop"] for r in rows), "rerun")
print("rerun streams:", sorted(rerun))

# ---- run-to-run reproducibility: run1 snapshots (backup) vs final rerun streams
BK = D22D / "streams_partial_run1_stopped_0709"
rep = []
div = []
for (v, s) in sorted(rerun):
    snap = ld(BK / f"{v}_s{s}.pkl")
    fin = ld(D22D / "streams" / f"{v}_s{s}.pkl")
    ks = sorted(set(snap["evals"]) & set(fin["evals"]))
    n1 = snap["n_boxes"]
    # first box at which the training S1 sequences differ
    a, b = snap["S1"], fin["S1"][: len(snap["S1"])]
    neq = np.flatnonzero(a != b)
    first_div = int(neq[0]) if neq.size else None
    div.append(dict(variant=v, seed=s, run1_boxes_reached=n1, run1_last_ckpt=max(snap["evals"]), first_training_S1_divergence_box=first_div,
                    train_S1_identical_over_run1_boxes=neq.size == 0,
                    frac_train_S1_equal=float((a == b).mean())))
    for k in ks:
        x, y = snap["evals"][k]["S1"], fin["evals"][k]["S1"]
        rep.append(dict(variant=v, seed=s, ckpt=k, run1_heldout=float(x.mean()), rerun_heldout=float(y.mean()), diff_rerun_minus_run1=float(y.mean() - x.mean()),
                        identical_per_box=bool(np.array_equal(x, y)), frac_boxes_same_S1=float((x == y).mean()),
                        hidden_run1=int(snap["evals"][k]["hidden"]), hidden_rerun=int(fin["evals"][k]["hidden"])))
write_csv(RUN / "item5_rerun_vs_run1_checkpoints.csv", rep)
write_csv(RUN / "item5_rerun_divergence.csv", div)
d = np.array([r["diff_rerun_minus_run1"] for r in rep if r["ckpt"] >= 5000])
dd = np.array([r["diff_rerun_minus_run1"] for r in rep if r["ckpt"] >= 20000])
summ = dict(n_pairs_ckpt_ge5000=int(d.size), mean_abs_diff=float(np.abs(d).mean()), sd_diff=float(d.std(ddof=1)), mean_diff=float(d.mean()),
            n_pairs_ckpt_ge20000=int(dd.size), mean_abs_diff_ge20000=float(np.abs(dd).mean()) if dd.size else None,
            sd_diff_ge20000=float(dd.std(ddof=1)) if dd.size > 1 else None, mean_diff_ge20000=float(dd.mean()) if dd.size else None,
            max_abs_diff=float(np.abs(d).max()), identical_checkpoints=int(sum(r["identical_per_box"] for r in rep)), n_checkpoints=len(rep))
json.dump(summ, open(RUN / "item5_reproducibility_summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
for r in div:
    print(r)
