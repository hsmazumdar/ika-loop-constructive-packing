"""Item 5 add-on: third replication of the six 22d `full` streams (Expt-22e memory reruns, HsmPc1, unmodified Expt_22d code)
versus the 22d final streams at every shared checkpoint, and box-by-box divergence of training S1. Run after all six reruns finished."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from common import D22D, RUN, ld, write_csv
rows, div = [], []
for s in range(300, 306):
    a = ld(D22D / "streams" / f"full_s{s}.pkl")
    b = ld(RUN / "memory_reruns" / f"full_s{s}_stream.pkl")
    for k in sorted(set(a["evals"]) & set(b["evals"])):
        x, y = a["evals"][k]["S1"], b["evals"][k]["S1"]
        rows.append(dict(seed=s, ckpt=k, d22d_final_heldout=float(x.mean()), e22e_rerun_heldout=float(y.mean()), diff=float(y.mean() - x.mean()),
                         identical_per_box=bool(np.array_equal(x, y)), frac_same=float((x == y).mean()), hidden_22d=int(a["evals"][k]["hidden"]),
                         hidden_22e=int(b["evals"][k]["hidden"])))
    ne = np.flatnonzero(a["S1"] != b["S1"])
    div.append(dict(seed=s, identical_training_S1=bool(ne.size == 0), n_boxes_differ=int(ne.size), first_diff_box=int(ne[0]) if ne.size else None,
                    final_heldout_22d=float(a["evals"][60000]["S1"].mean()), final_heldout_22e=float(b["evals"][60000]["S1"].mean())))
write_csv(RUN / "item5_third_run_vs_22d.csv", rows)
write_csv(RUN / "item5_third_run_divergence.csv", div)
d = np.array([r["diff"] for r in rows])
fin = np.array([[r["final_heldout_22d"], r["final_heldout_22e"]] for r in div])
out = dict(n_checkpoint_pairs=int(d.size), identical_checkpoints=int(sum(r["identical_per_box"] for r in rows)), max_abs_diff=float(np.abs(d).max()),
           mean_abs_diff=float(np.abs(d).mean()), n_streams_identical_training_S1=int(sum(r["identical_training_S1"] for r in div)),
           mean_final_22d=float(fin[:, 0].mean()), mean_final_22e=float(fin[:, 1].mean()), per_stream_final=fin.tolist())
json.dump(out, open(RUN / "item5_third_run_summary.json", "w"), indent=1)
print(json.dumps(out, indent=1))
