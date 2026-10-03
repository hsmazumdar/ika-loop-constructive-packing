"""Items 3/4 add-on facts from saved data only: (a) what the '~67 uniform natural baseline' in the 22b/c/d summaries really is
(checkpoint-0 evaluation of each stream's randomly initialised value net, tau 0.25) versus true uniform-random natural placing;
(b) numeric seed disjointness of evaluation / probe seeds vs training generators; (c) list of Expt-20 baseline rules."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from common import D21, D22B, D22C, D22D, ROOT, RUN, EVAL_SEED, streams, ld, write_csv

rows = []
for lab, d in (("22b full (12 streams, seeds 0-11)", D22B), ("22c full (12, seeds 100-111)", D22C), ("22d full (6, seeds 300-305)", D22D)):
    rs = streams(d, "full")
    v = np.array([r["evals"][0]["S1"].mean() for r in rs])
    rows.append(dict(set=lab, n_streams=len(rs), mean_ckpt0_S1=v.mean(), min=v.min(), max=v.max(), sd=v.std(ddof=1),
                     true_uniform_random_natural_1200=67.31916666666666))
write_csv(RUN / "item3_ckpt0_vs_uniform.csv", rows)
for r in rows: print(r)

# V21 baseline check: V21 checkpoint-0 evals are uniform because the all-zero score vector triggers the uniform branch
rs21 = [ld(p) for p in sorted((D21 / "streams").glob("full_s*.pkl"))] if (D21 / "streams").exists() else []
print("V21 stream pickles:", len(rs21))
if rs21:
    v = np.array([r["evals"][0]["S1"].mean() for r in rs21]); print("V21 ckpt0 per stream", v.mean(), v.min(), v.max(), "n_eval", len(rs21[0]["evals"][0]["S1"]))

# seeds
train_gen = {}
for name, seeds in (("22b", list(range(0, 12))), ("22c", list(range(100, 112))), ("22d_full", list(range(300, 306))), ("22d_abl", list(range(200, 204)))):
    for s in seeds:
        train_gen.setdefault(name, []).append((s * 7919 + 13, s * 104729 + 7))
ev = set(range(EVAL_SEED, EVAL_SEED + 1200)); probe = set(range(EVAL_SEED + 500000, EVAL_SEED + 500000 + 80))
coll = {k: sum(1 for a, b in v for x in (a, b) if x in ev or x in probe) for k, v in train_gen.items()}
mx = {k: max(max(a, b) for a, b in v) for k, v in train_gen.items()}
print("collisions", coll, "max seed value", mx)
# Expt-20 rules
rules = json.load(open(ROOT / "Expt_20_Winning_Combination_LTM" / "results" / "20260930_214303_baselines" / "rules.json", encoding="utf-8"))
write_csv(RUN / "item3_expt20_rules.csv", [dict(name=r.get("name"), group=r.get("group"), anchor=r.get("anchor"), piece=r.get("piece"), place=r.get("place"), note=r.get("note", "")) for r in rules])
print(len(rules), "rules; groups", {g for g in (r.get("group") for r in rules)})
json.dump(dict(training_generator_seed_collisions=coll, max_seed_values=mx, ev_range=[EVAL_SEED, EVAL_SEED + 1199], probe_range=[EVAL_SEED + 500000, EVAL_SEED + 500079]),
          open(RUN / "item4_seed_disjointness.json", "w"), indent=1)
