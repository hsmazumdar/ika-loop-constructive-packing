"""Reference table: per (variant, condition, split) mean normalised scores of the reference policies. Writes results/ref_table.csv/.md"""
import sys, pathlib, csv, glob
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[1]
rows = []
for f in sorted(glob.glob(str(ROOT / "results" / "refs" / "refs_*.csv"))):
    for r in csv.DictReader(open(f)):
        rows.append(r)
keys = sorted({(r["variant"], r["cond"], r["split"]) for r in rows})
out = []
for k in keys:
    R = [r for r in rows if (r["variant"], r["cond"], r["split"]) == k]
    g = lambda c: np.array([float(r[c]) for r in R])
    ref = g("ref")
    beam = np.maximum.reduce([g("beam64_s0"), g("beam64_s1"), g("beam64_s2")])
    d = dict(variant=k[0], cond=k[1], split=k[2], n=len(R), free=g("free").mean(), ref=ref.mean())
    for name, v in (("uniform", g("uniform")), ("hand", g("hand")), ("cemhand", g("cemhand")), ("beam64", beam), ("rollout_beam", g("rollout_beam"))):
        d[name + "_S1"] = v.mean(); d[name + "_norm"] = (v / ref).mean()
    d["hand_lt_090"] = float((g("hand") / ref < 0.90).mean())
    d["t_beam"] = g("t_beam").mean(); d["t_rollout"] = g("t_rollout").mean()
    out.append(d)
cols = list(out[0].keys())
with open(ROOT / "results" / "ref_table.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, cols); w.writeheader(); w.writerows(out)
L = ["| variant | cond | split | n | ref S1 | uniform | hand | CEM-hand | beam64 | rollout-beam | share hand<0.90 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for d in out:
    L.append("| %s | %s | %s | %d | %.1f | %.3f | %.3f | %.3f | %.3f | %.3f | %.2f |" % (d["variant"], d["cond"], d["split"], d["n"], d["ref"], d["uniform_norm"], d["hand_norm"], d["cemhand_norm"], d["beam64_norm"], d["rollout_beam_norm"], d["hand_lt_090"]))
(ROOT / "results" / "ref_table.md").write_text("\n".join(L))
print("\n".join(L))