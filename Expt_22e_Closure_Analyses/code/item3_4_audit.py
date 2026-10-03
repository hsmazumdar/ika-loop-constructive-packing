"""Items 3 and 4: (3) code-reference table + extra simple packers under the SAME 14-piece natural task on the same 1,200
episodes; (4) facts about the 1,200 held-out episodes (what differs between them, overlap with pilots, distinctness)."""
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import D22B, D22C, D22D, EVAL_SEED, ROOT, RUN, ld, streams, write_csv
sys.path.insert(0, str(HERE))
import item2_piece_P as P2  # noqa: E402  (re-uses box runners; its __main__ block does not run)
import engine as E  # noqa: E402 (Expt_22d src via item2's sys.path)

N, BUD = 1200, 14

# ------------------------------------------------------------------ item 3a: code references (line numbers read from the files)
REFS = [
    ("Expt_22d/src/engine.py", r"def legal\(self\)|if self.n >= self.budget|return idx\[self.allowed", "legality + 14-piece cap (cap = no legal move once n>=budget)"),
    ("Expt_22d/src/engine.py", r"def natural_candidates|nat = f\[\"contact\"\] > 0", "natural restriction used by uniform, hand rule, V21"),
    ("Expt_22d/src/engine.py", r"self.allowed = np.ones", "all 16 piece types always allowed (no inventory/blocked cells in any experiment)"),
    ("Expt_22d/src/feat.py", r"def step_features|nat = \(occ_c \+ wall\) > 0|return None", "learner's own natural filter (same definition: contact>0)"),
    ("Expt_22d/src/agent.py", r"box = E.Box\(budget=budget\)|r = F.step_features|j = int\(np.searchsorted|if n == 1|elif tau <= 0.05", "learner episode loop and softmax sampling"),
    ("Expt_22d/src/stream.py", r"def evaluate|np.random.default_rng\(sd \+ j\)|probe_ids = |seed0=probe_ids", "held-out evaluation seeds (eval_seed + j); meta probe seeds eval_seed+500000+j"),
    ("Expt_22d/src/config.py", r"tau_eval|eval_boxes|eval_seed|budget: int", "evaluation parameters (tau_eval 0.25, 22d eval_boxes overridden to 1200)"),
    ("Expt_22d/src/learner_ref.py", r"def uniform_ref|rng.integers\(c.size\)|def hand_ref|sc = f\[\"contact\"\]", "uniform natural and hand rule (22b/c/d)"),
    ("Expt_21/src/learner.py", r"def play_box|E.natural_candidates\(box, lvl\)|def hand_box|sc = f\[\"contact\"\]|def choose", "V21 policy loop, choose(), hand rule"),
    ("Expt_21/src/stream.py", r"def evaluate|np.random.default_rng\(cfg.eval_seed \+ j\)|cfg.tau_eval", "V21 held-out evaluation"),
    ("Expt_21/src/config.py", r"BUDGET = 14|tau_eval|eval_boxes|eval_seed", "V21: budget 14, tau_eval 0.3, 2000 eval boxes"),
    ("Expt_21/src/report.py", r"hand = np.array|for j in range\(min\(cfg.eval_boxes, 1000\)\)", "V21 hand-rule reference computed on the first 1000 eval seeds"),
    ("Expt_22b/src/report.py", r"hand14 = |hand_ref\(|unif14 = ", "22b/c report: hand rule on min(eval_boxes,1000); 'uniform' = mean of untrained-net checkpoint-0 evals"),
]
rows = []
for rel, pat, why in REFS:
    exp, _, tail = rel.partition("/")
    base = {"Expt_22d": ROOT / "Expt_22d_Long_Ablations_Saturation", "Expt_21": ROOT / "Expt_21_Continuous_Learning_Memory",
            "Expt_22b": ROOT / "Expt_22b_Organic_Value_Learner"}[exp]
    p = base / tail
    for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if re.search(pat, ln):
            rows.append(dict(file=rel, line=i, code=ln.strip(), why=why))
write_csv(RUN / "item3_code_refs.csv", rows)

# ------------------------------------------------------------------ item 3b: engine identical across experiments
import hashlib
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:12]
eng = {n: h(ROOT / n / "src" / "engine.py") for n in ["Expt_21_Continuous_Learning_Memory", "Expt_22a_Organic_Value_Learner", "Expt_22b_Organic_Value_Learner",
                                                          "Expt_22c_Long_Streams", "Expt_22d_Long_Ablations_Saturation"]}
learner_ref = {n: h(ROOT / n / "src" / "learner_ref.py") for n in ["Expt_22b_Organic_Value_Learner", "Expt_22c_Long_Streams", "Expt_22d_Long_Ablations_Saturation"]}

# ------------------------------------------------------------------ item 3c: simple packers under the same 14-piece natural task
def run_rule(score_fn, n=N, noise=0.5, tie="random"):
    out = []
    for j in range(n):
        rng = np.random.default_rng(EVAL_SEED + j)
        b = E.Box(budget=BUD)
        while True:
            c, f = E.natural_candidates(b, 0)
            if c.size == 0:
                break
            sc = score_fn(c, f)
            if noise:
                sc = sc + rng.random(c.size) * noise
            b.place(int(c[int(np.argmax(sc))]))
        out.append(b)
    return out

RULES = {
    "hand_rule (contact -3*holes -notches +2*area, noise .5)": lambda c, f: f["contact"] - 3.0 * f["p1"] - f["n3"] + 2.0 * E.AREA[c],
    "contact_only_greedy (random tie)": lambda c, f: f["contact"].astype(float),
    "contact_minus_holes (no area term)": lambda c, f: f["contact"] - 3.0 * f["p1"] - f["n3"].astype(float),
    "area_only_greedy (largest piece, random tie)": lambda c, f: 1.0 * E.AREA[c],
    "contact_plus_area (no hole terms)": lambda c, f: f["contact"] + 2.0 * E.AREA[c],
}
srows = []
for name, fn in RULES.items():
    bx = run_rule(fn)
    r, s1, nP = P2.stats_of(bx, name)
    srows.append(r)
    print(name, round(r["S1"], 2), "P-frac", round(r["frac_boxes_with_P"], 3), flush=True)
write_csv(RUN / "item3_extra_packers_under_14cap.csv", srows)

# ------------------------------------------------------------------ item 4: the 1,200 evaluation episodes
res = dict(engine_hashes=eng, learner_ref_hashes=learner_ref)
# (a) what differs: nothing about the problem - verify all 1,200 start from an identical empty board with all 16 types
b0 = E.Box(budget=BUD)
res["start_board_empty"] = int(b0.occ) == 0 and bool(b0.allowed.all()) and b0.budget == 14
# (b) distinctness of outcomes for the stored 22c memory and for hand/uniform
ag, cfg = P2.load_agent(D22C / "ltm_full_seed0.pkl")
lb = P2.learner_boxes(ag, cfg, N)
ub = P2.uniform_boxes(N); hb = P2.hand_boxes(N)
def distinct(bx):
    seqs = {tuple(b.placed) for b in bx}
    boards = {tuple(sorted(b.placed)) for b in bx}
    firsts = {b.placed[0] for b in bx}
    return dict(distinct_sequences=len(seqs), distinct_final_placement_sets=len(boards), distinct_first_placements=len(firsts), n=len(bx))
res["distinctness"] = {"learner_22c_s100_memory": distinct(lb), "uniform_natural": distinct(ub), "hand_rule": distinct(hb)}
# (c) pilot overlap: the pilots used eval seeds 7,700,000+j for j < 300 (V22a/V22b pilots: eval=300; V22a pilot manifest eval_boxes=400; V22a cut-main 1200)
pil = []
for d, lab in ((D22B, "22b full@20k (12)"), (D22C, "22c full@32k (12)"), (D22D, "22d full@60k (6)")):
    rs = streams(d, "full"); k = max(rs[0]["evals"])
    a = np.array([r["evals"][k]["S1"] for r in rs], float)       # streams x 1200
    first300, rest = a[:, :300].mean(1), a[:, 300:].mean(1)
    pil.append(dict(set=lab, ckpt=k, mean_first300_eps=first300.mean(), mean_rest900_eps=rest.mean(), diff_first300_minus_rest=(first300 - rest).mean(),
                    sd_of_diff_over_streams=(first300 - rest).std(ddof=1), streams_first300_higher=int(((first300 - rest) > 0).sum()), n_streams=len(rs)))
write_csv(RUN / "item4_pilot_overlap_check.csv", pil)
# (d) variability of an episode-level mean due to the sampling of the 1,200 seeds for ONE frozen memory (episode SD)
sd = float(np.std([b.s1 for b in lb], ddof=1)); res["learner_22c_s100_episode_sd"] = sd; res["learner_22c_s100_se_of_mean_1200"] = sd / np.sqrt(N)
res["learner_22c_s100_S1_1200"] = float(np.mean([b.s1 for b in lb]))
json.dump(res, open(RUN / "item3_4_facts.json", "w"), indent=1)
print(json.dumps(res, indent=1))
print(open(RUN / "item4_pilot_overlap_check.csv").read())
