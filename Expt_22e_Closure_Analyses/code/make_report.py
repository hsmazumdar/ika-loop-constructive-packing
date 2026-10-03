"""Builds results/20261001_122457_run/report.md from the saved CSV/JSON files ONLY (no simulation). Every number in a table is read
from a file; narrative numbers were checked against the same files. Usage: python code/make_report.py"""
import csv, json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1] / "results" / "20261001_122457_run"
R = lambda n: list(csv.DictReader(open(RUN / n, encoding="utf-8")))
J = lambda n: json.load(open(RUN / n, encoding="utf-8"))
f2 = lambda x: f"{float(x):.2f}"
f3 = lambda x: f"{float(x):.3f}"
f4 = lambda x: f"{float(x):.4f}"
sg = lambda x: f"{float(x):+.2f}"
def p(x):
    x = float(x)
    return "<0.0001" if x < 1e-4 else f"{x:.4f}"
def tab(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"

o = []
A = o.append
A("""# Expt 22e - Closure analyses for "Continuous Learning and Memory Consolidation for Constructive Packing"

Run folder: `Expt_22e_Closure_Analyses/results/20261001_122457_run/`. All numbers below are read from the saved CSV/JSON files in this folder
(`code/make_report.py` generates the tables). Everything derives from saved Expt 21 / 22a-d data, plus modest new simulation that is fully logged:
(i) 1,200-episode evaluations of uniform natural placing, the hand rule, five extra simple packers and three piece-choice references (items 2/3);
(ii) re-evaluation of the two stored memories (22b s0, 22c s100); (iii) six reruns of the Expt 22d `full` streams (seeds 300-305, 60k boxes, unmodified
Expt_22d `src`) done only to obtain final agent memories, because Expt 22d did not store them (`memory_reruns/`, `progress.log`).
Times are IST (UTC+5:30). "S1" = 100 - empty cells after the episode (held-out mean over the 1,200 evaluation episodes, tau_eval 0.25, unless stated).

Status of the machines: items 1, 3, 4, 5 and the simulations were produced on HsmPc1 (python 3.13.1, numpy 2.2.0); this report was assembled on i9Win10 from the files only.

""")

# ---------------- item 1 ----------------
pa = R("item1a_paired_saturation.csv")
A("## Item 1 - Paired statistics\n\n### 1a. 22d saturation run: paired stream-level differences (n = 6 `full` streams, seeds 300-305, same replicate streams at every checkpoint)\n\n")
A("Difference = S1(to) - S1(from) within each stream, then averaged over the 6 streams. Bootstrap = percentile 95% CI of the mean paired difference "
  "(resampling streams, 20,000 draws, rng seed 20261001). t-CI = paired t interval (df 5). Sign-flip = exact two-sided sign-flip permutation p (2^6 flips; the smallest attainable p is 0.03125). "
  "`indep CI` = the independent-samples bootstrap CI (the way summary.md compared checkpoints), shown for contrast.\n\n")
rows = []
for r in pa:
    rows.append([f"{int(r['from_boxes'])//1000}k -> {int(r['to_boxes'])//1000}k", sg(r["mean_diff"]), f"{sg(r['boot_lo'])}, {sg(r['boot_hi'])}", f"{sg(r['t_lo'])}, {sg(r['t_hi'])}",
                 p(r["p_t_paired"]), f"{float(r['p_signflip_exact']):.4f}", f"{r['n_streams_up']}/6", f"{sg(r['indep_boot_lo'])}, {sg(r['indep_boot_hi'])}", r["per_stream_diffs"].replace(";", " ")])
A(tab(["from -> to (boxes)", "mean diff", "paired bootstrap 95% CI", "paired-t 95% CI", "p (paired t)", "p (sign-flip, exact)", "streams up", "indep. bootstrap CI", "per-stream diffs (s300..s305)"], rows))
A("\nNo multiplicity correction is applied across these 14 contrasts; the p-values are descriptive. Figure: `fig_item1a_paired_differences.png` (left: per-stream trajectories; right: paired 4k-step differences with CIs).\n\n")
last = [r for r in pa if r["from_boxes"] == "56000"][0]
A(f"**56k -> 60k, redone as paired:** mean {sg(last['mean_diff'])} S1, paired bootstrap 95% CI [{sg(last['boot_lo'])}, {sg(last['boot_hi'])}], paired-t CI [{sg(last['t_lo'])}, {sg(last['t_hi'])}], "
  f"{last['n_streams_up']} of 6 streams up, exact sign-flip p = {float(last['p_signflip_exact']):.3f}. The independent-sample CI was [{sg(last['indep_boot_lo'])}, {sg(last['indep_boot_hi'])}]; the paired CI (width {float(last['boot_hi'])-float(last['boot_lo']):.2f}) is about {(float(last['indep_boot_hi'])-float(last['indep_boot_lo']))/(float(last['boot_hi'])-float(last['boot_lo'])):.0f}x narrower than the independent one (width {float(last['indep_boot_hi'])-float(last['indep_boot_lo']):.2f}) because the stream-to-stream level differences are removed. "
  "So the last 4k boxes change S1 by at most about +0.13 (upper bound) and the data are consistent with zero change. "
  "Earlier steps are not zero: 48k -> 52k is +0.22 (paired bootstrap CI +0.09, +0.36; 6/6 streams up) and 32k -> 36k is +1.63 (+1.28, +1.99). "
  "20k -> 60k is +6.38 (+5.73, +7.33), 6/6 up. The honest description is a **near-plateau** (paired gains of +0.5 to +1.6 per 4k boxes between 20k and 40k, +0.22 at 48k -> 52k, +0.07 and +0.04 over the last two 4k steps), not a proven ceiling: 6 streams, one setting, and the 52k -> 60k contrast is +0.11 (-0.04, +0.29).\n\n")

A("### 1b. Five 22d ablations vs the 22c `full` reference at 32k boxes (multiplicity control)\n\n")
A("Family of m = 5 comparisons (no_concepts, no_meta, no_dream, no_meta_matched_floor, no_sleep). Reference = 22c `full` streams at 32k (n = 12, seeds 100-111); each ablation has n = 4 (seeds 200-203, 22d). "
  "Difference = reference minus variant (positive = ablation worse). Four tests: `Welch normal` is the test used in the 22d summary.md (Welch standard error, normal reference); `Welch t` uses Satterthwaite df; "
  "`exact permutation` enumerates every assignment of the pooled values; `Mann-Whitney U`. Holm, Bonferroni and BH are applied within each test across the 5 variants. "
  "`survives` = adjusted p < 0.05 (Holm / Bonferroni / BH).\n\n")
mult = R("item1b_ablation_multiplicity.csv")
for ref, title in (("22c_full_n12", "Reference = 22c full, n = 12 (primary)"), ("pooled_22c+22d_full_n18", "Reference = pooled 22c full (n = 12) + 22d full at 32k (n = 6) = n 18 (pooled version)")):
    A(f"**{title}**\n\n")
    rows = []
    for r in mult:
        if r["reference"] == ref:
            rows.append([r["test"].split(" (")[0], r["variant"], f"{f2(r['ref_mean'])} / {f2(r['var_mean'])}", sg(r["ref_minus_var"]), f"{sg(r['boot_lo'])}, {sg(r['boot_hi'])}", p(r["p_raw"]), p(r["p_holm"]), p(r["p_bonferroni"]), p(r["p_BH"]),
                         "/".join("Y" if r[k] == "True" else "n" for k in ("survives_holm_05", "survives_bonf_05", "survives_BH_05"))])
    A(tab(["test", "variant", "ref / variant mean", "ref - variant", "bootstrap 95% CI of diff", "raw p", "Holm", "Bonferroni", "BH", "survives Holm/Bonf/BH"], rows))
    A("\n")
A("""**Reading.**
- `no_sleep` (-1.81 S1 vs the 22c reference): survives Holm, Bonferroni and BH under both Welch versions (Welch normal Holm 0.0013; Welch t Holm 0.0174), also with the pooled reference (Holm 0.0002 / 0.0102). Under the exact permutation test (Holm 0.1016) and Mann-Whitney (Holm 0.0659) it does **not** reach 0.05 after correction; the raw permutation p is 0.0203 and raw Mann-Whitney 0.0132. So the conclusion "no_sleep is lower" is robust to Welch-type tests and to the direction of every test, but with only 4 ablation streams the rank/permutation tests lack the power to survive correction.
- `no_meta_matched_floor` (-1.02): raw Welch-normal p = 0.0231, but Holm 0.0924, Bonferroni 0.1155, BH 0.0577 -> **does not survive** against the 22c reference -> label **exploratory**. With the pooled reference it survives under Welch-normal (Holm 0.0382) but not under Welch t (Holm 0.0817), permutation (0.6103) or Mann-Whitney (0.2122), so it is not robust either.
- `no_concepts`, `no_meta`, `no_dream`: raw p between 0.30 and 0.74 in every test; no evidence of a difference (this is absence of evidence at n = 4, not evidence of equivalence; the bootstrap CIs of the difference all span zero and are about 3 S1 points wide, e.g. no_concepts -1.21 to +1.77).
- Caveat on the design: the reference (22c, Vivobook run 04:44) and the ablations (22d) are different runs (both compared at 32k boxes) with slightly different code (22d adds the matched_floor variant, extra checkpoints and an `on_eval` hook; policy mechanics unchanged - see item 3). The pooled version adds the six 22d `full` streams at 32k, which ran concurrently with the ablations (pooled reference mean 88.29 vs 88.28 for 22c alone).

""")

# ---------------- item 2 ----------------
A("## Item 2 - Piece-P usage\n\nP is the 7-cell piece (area 7; most pieces have area 5, M/N/O area 4). Same 14-piece natural-placing task, same 1,200 evaluation seeds (7,700,000 + j), for all policies. "
  "The learner rows are the **frozen final memories** (the agent's value net, concept library etc. evaluated with `learner_ref`/stream evaluation code at tau_eval 0.25; each re-evaluation reproduces the saved held-out S1 exactly "
  "(8 of 8 memories, 0 differing episodes; the 22c s100 memory reproduces exactly only with single-threaded BLAS - with default threads one of 1,200 episodes differed by float noise, 87.8267 vs 87.8258). "
  "The 22d `full` memories come from the six 22e reruns (identical to the saved 22d streams, item 5), because 22d itself did not store memories; 22b s0 (at 20k) and 22c s100 (at 32k) were stored by those experiments.\n\n")
rows = []
pu = R("item2_piece_P_usage.csv")
for r in pu:
    rows.append([r["policy"], f3(r["S1"]), f3(r["mean_pieces"]), f3(r["mean_piece_area"]), f3(r["frac_boxes_with_P"]), f3(r["mean_P_per_box"]), r["max_P"], f3(r["frac_boxes_2plusP"]), f3(r["frac_cells_in_P"]), f3(r["frac_S1_ge_90"]),
                 r.get("reproduces_saved_heldout_exactly") or "-"])
A(tab(["policy", "S1", "mean pieces/episode", "mean piece area", "fraction of episodes using P", "mean P pieces/episode", "max P", "frac >= 2 P", "frac cells covered by P", "frac S1 >= 90", "re-eval = saved?"], rows))
d6 = [r for r in pu if r["policy"].startswith("22d")]
mean = lambda k: sum(float(r[k]) for r in d6) / len(d6)
A(f"\nMean of the six 22d memories at 60k: S1 {mean('S1'):.3f}, P pieces/episode {mean('mean_P_per_box'):.3f}, piece area {mean('mean_piece_area'):.3f}, fraction of cells covered by P {mean('frac_cells_in_P'):.3f}; range of S1 {min(float(r['S1']) for r in d6):.3f}-{max(float(r['S1']) for r in d6):.3f}.\n\n")
A("**S1 split by P used / not used.** (`S1_P_used`, `n_P_used`, `S1_P_not_used`, `n_P_not_used` in `item2_piece_P_usage.csv`.)\n\n")
rows = []
for r in pu:
    nu = r["S1_P_not_used"]
    rows.append([r["policy"], r["n_P_used"], f3(r["S1_P_used"]), r["n_P_not_used"], "n/a (no such episodes)" if nu in ("nan", "") or int(float(r["n_P_not_used"])) == 0 else f3(nu)])
A(tab(["policy", "n episodes using P", "S1 (P used)", "n not using P", "S1 (P not used)"], rows))
A("""
For every learner memory and for the hand rule the fraction of episodes using P is 1.000, so the P-used / not-used split is degenerate (nothing to compare). It is informative only for uniform natural placing (68.883 with P, n = 566; 65.923 without, n = 634).
Association between P count and S1 (descriptive, not causal), `n episodes (mean S1)` by number of P pieces:

""")
rows = []
for r in pu:
    cells = []
    for k in range(14):
        n = r.get(f"n_boxes_P={k}")
        if n is not None and int(float(n)) > 0:
            cells.append(f"{k}P: {int(float(n))} ({f2(r[f'S1_P={k}'])})")
    rows.append([r["policy"], "; ".join(cells)])
A(tab(["policy", "episodes by number of P pieces (mean S1)"], rows))
A("\n**Piece-choice references** (new here; always choose a placement of piece P when one exists, same task and seeds; not used by any learner):\n\n")
rows = []
for r in R("item2b_P_only_baselines.csv"):
    rows.append([r["policy"], f3(r["S1"]), f3(r["mean_pieces"]), f3(r["mean_piece_area"]), f3(r["mean_P_per_box"]), f3(r["frac_cells_in_P"]), f3(r["frac_S1_ge_90"])])
A(tab(["reference", "S1", "mean pieces", "mean piece area", "mean P/episode", "frac cells in P", "frac S1 >= 90"], rows))
A("""
**Reading.** (1) Learners and the hand rule use P in every episode (uniform: 47.2% of episodes, 0.631 P pieces/episode, mean piece area 4.809). The learned policies (6.31 -> 6.39 -> 6.53-6.71 mean piece area) and the hand rule (6.424) use almost only large pieces.
(2) A large part of the improvement over uniform natural placing is therefore **piece choice** (choose P), not only placement quality: restricting uniform natural placing to P placements alone gives S1 82.335, and P-only with contact-greedy placement gives 88.918 - already about equal to the hand rule (89.617) and above the 22b learner at 20k (83.887) and the 22c learner at 32k (87.826). The six 60k learners (90.985-93.988; mean 91.761) are above that P-only contact-greedy reference (88.918), so their placement is better than contact-greedy; the 22b/22c learners are below it.
(3) Under the 14-piece cap the area term of the hand rule is the active ingredient (item 3 table: without an area term 70.24; hole terms removed: 88.925).
(4) Why 13.3-14 pieces rather than 14: some episodes end before the cap when no natural placement remains (mean pieces/episode in the table).

""")

# ---------------- item 3 ----------------
A("## Item 3 - Baseline audit\n\n")
A("""**Verdict.** Learner (22b/c/d), uniform natural placing, V21 and the 89.61 hand rule share: the same engine file (byte-identical), the same legality and 14-piece cap, the same natural restriction (contact > 0), the same unlimited-inventory piece availability (all 16 types always offered; there is no per-box inventory in Expt 21/22), the same stopping rule, and the same evaluation seeds. They do **not** share: tau_eval and episode count between V21 and 22 (0.3 vs 0.25; 2,000 vs 1,200), the random-number stream consumption (policies draw differently), and the definition of the "uniform ~67" and "89.61" numbers in the reports (below). Details:

""")
rows = [
    ["engine.py", "sha-prefix 8295979bb1e6 in Expt_21, 22a, 22b, 22c, 22d (byte-identical)", "item3_4_facts.json"],
    ["learner_ref.py", "sha-prefix 8fe669b8f1f3 in 22b, 22c, 22d (uniform_ref and hand_ref); agent.py, feat.py, net.py, meta.py identical in 22b/c/d", "item3_4_facts.json"],
    ["stream.py, config.py (22d vs 22b/c)", "differ: 22d adds checkpoints 24k-56k, the matched_floor variant, an on_eval hook and schedule bounds; policy mechanics unchanged", "diff of src files"],
    ["Legality + 14-piece cap", "Expt_22d/src/engine.py:117-121 Box.legal() returns no move once n >= budget; budget 14: Expt_22d/src/config.py:12, Expt_21/src/config.py:7", "item3_code_refs.csv"],
    ["Piece availability", "engine.py:110 `self.allowed = np.ones(N_TYPES)`: all 16 types always allowed; no inventory, no blocked cells in the 21/22 task (blocked/obstacle machinery exists but is unused)", "item3_code_refs.csv"],
    ["Natural restriction (uniform, hand, V21)", "engine.natural_candidates, engine.py:172-183: legal placements with contact > 0 (touch wall or placed piece). V21 uses it at Expt_21/src/learner.py:289; uniform and hand use it in Expt_22d/src/learner_ref.py", "item3_code_refs.csv"],
    ["Natural restriction (22 learner)", "its own filter, feat.step_features, Expt_22d/src/feat.py:33 `nat = (occ_c + wall) > 0`; equivalence to engine.natural_candidates checked on every decision state visited: 0 mismatches in 4,500 (uniform trajectories), 4,483 (hand), 4,350 (mixed policy), 4,424 (learner trajectories)", "item3_natural_filter_equivalence.json"],
    ["Stopping rule", "every policy ends when no natural candidate remains or the 14-piece cap is hit (agent.py:98-125, learner_ref.py, learner.py:289)", "item3_code_refs.csv"],
    ["Evaluation seeds", "episode j uses np.random.default_rng(eval_seed + j), eval_seed = 7,700,000 in V21 (stream.py:26) and 22 (stream.py:22, config.py:43); uniform_ref and hand_ref use the same seeds (learner_ref.py)", "item3_code_refs.csv"],
]
A(tab(["item", "finding", "file"], rows))
A("\n**Mismatches / caveats (precise):**\n\n")
a = R("item3_ckpt0_vs_uniform.csv")
mm = [
    "V21 evaluates with tau_eval = 0.3 and 2,000 episodes (`Expt_21/src/config.py:19,56`); 22b/c/d use tau_eval = 0.25 (`Expt_22d/src/config.py:19`) and 1,200 episodes (the `Cfg` default is 2,000 at config.py:42, overridden to 1,200 in the manifests). Same seeds, first 1,200 of V21's 2,000.",
    "The reported \"89.61\" hand rule is the mean over the **first 1,000** evaluation episodes (`Expt_21/src/report.py:81-82`; `Expt_22b/src/report.py:82`). Recomputed here: 89.606 (first 1,000), 89.617 (the 1,200 evaluation episodes), 89.6475 (2,000). V21 and 22 reference code give identical numbers on the same seeds (`item3_v21refs_stdout.txt`, `item3_v22refs_stdout.txt`).",
    "The \"uniform ~ 67\" quoted in the 22b/c/d reports (`Expt_22b/src/report.py:83`) is **not** true uniform natural placing: it is the mean checkpoint-0 held-out S1 of each stream's randomly initialised value net at tau 0.25: " + "; ".join(f"{r['set']}: {f3(r['mean_ckpt0_S1'])} (range {f2(r['min'])}-{f2(r['max'])})" for r in a) + f". True uniform natural placing is {f3(a[0]['true_uniform_random_natural_1200'])} on the 1,200 episodes (67.328 first 1,000; 67.297 on V21's 2,000, which is the V21 value, produced through the all-zero-score uniform branch of `choose()`).",
    "Stochasticity differs by policy: learner = softmax at tau 0.25 over natural placements (agent.py:117-125); hand rule = argmax of score + U(0, 0.5) noise (learner_ref.py:32); uniform = uniform draw (learner_ref.py:17). They consume the RNG differently, so the same seed id does not give identical random numbers, only the same seed. (Paired per-episode comparisons across policies are therefore comparisons of independent draws.)",
    "22b/c/d training used a single continuing generator per stream (not the evaluation seeds); see item 4.",
    "The Expt-20 baselines (below) were evaluated on a **different task** (empty 10x10 box, unlimited pieces, 100-action budget; `Expt_20.../20260930_214303_baselines/summary.md`): its `uniform_random_control` scores 79.800 there versus 67.319 for uniform natural placing under the 14-piece cap, so numbers across the two tasks are not comparable.",
]
for m in mm:
    A(f"- {m}\n")
A("""
### Hand rule (paper-ready definition; `Expt_22d/src/learner_ref.py:22-33`, `Expt_21/src/learner.py:296-303`)

> *Hand-written contact/hole/area reference.* At each step the rule considers all natural placements (legal placements of any of the 16 piece types in any orientation that touch the wall or a previously placed piece), scores each placement by
> `score = contact - 3 * h1 - n3 + 2 * area + u`, where `contact` is the number of cell edges of the piece touching the wall or already occupied cells, `h1` is the number of empty neighbouring cells that the placement leaves fully enclosed (one-cell holes), `n3` is the number of empty neighbouring cells left with three blocked sides (dead-end notches), `area` is the piece area (5 for most pieces, 4 for M, N, O, 7 for P) and `u ~ U(0, 0.5)` is a tie-breaking noise term, and places the arg-max. The episode ends when no natural placement remains or after 14 pieces. The rule has no learning and no memory and is used only as a reference; the weights (-3, -1, +2) are fixed constants in the code. Their origin (hand-set or tuned, and on which episodes) was not looked up in the earlier experiments' records for this report - state this in the manuscript only after checking.

Mean S1 on the 1,200 evaluation episodes: 89.617 (89.606 on the first 1,000, the "89.61" quoted in the manuscript; 89.6475 on 2,000).

### Other simple packers and whether any is evaluated under the 14-piece handicap

**Expt 20 baselines** (`Expt_20.../results/20260930_214303_baselines`; 14 rules in `rules.json`, listed in `item3_expt20_rules.csv`): first-fit and greedy rules on the unrestricted empty box (unlimited pieces, 100 actions); best: G_contact_any_first_tie 98.000, FF_contact_first_tie 97.000, Expt20_D_anchor_contact_eps0 96.253; weakest plain rules FF_largest_first_legal 84.000, G_area_any_rowmajor_tie 84.000, G_area_any_random_tie 83.436; uniform_random_control 79.800. **None is evaluated under the 14-piece cap** inside Expt 20.

**New in Expt 22e** (same 14-piece natural task, same 1,200 evaluation episodes; these are *not* the Expt-20 rules, which use anchors and other action spaces, but simple contact/area variants of the hand rule):

""")
rows = []
for r in R("item3_extra_packers_under_14cap.csv"):
    rows.append([r["policy"], f3(r["S1"]), f3(r["mean_pieces"]), f3(r["mean_piece_area"]), f3(r["frac_boxes_with_P"]), f3(r["mean_P_per_box"]), f3(r["frac_S1_ge_90"])])
A(tab(["rule", "S1", "mean pieces", "mean piece area", "frac episodes with P", "mean P/episode", "frac S1 >= 90"], rows))
A("\nThe area term is essential (without it 70.24 or 77.52); the hole/notch terms add 89.617 - 88.925 = 0.69 S1 (the hand-rule noise is the same in both).\n\n")

# ---------------- item 4 ----------------
fa = J("item3_4_facts.json"); sd = J("item4_seed_disjointness.json")
A("## Item 4 - Evaluation set description\n\n")
A(f"""**Facts (from code and saved data).**
- Seeds: evaluation episode j (j = 0..1199) uses `np.random.default_rng({sd['ev_range'][0]} + j)`, i.e. seeds {sd['ev_range'][0]:,}..{sd['ev_range'][1]:,} (`config.py:43`, `stream.py:22`). V21 evaluated seeds 7,700,000..7,701,999 (2,000 episodes), which contain the 1,200.
- Identical across the 1,200: the start board (empty 10 x 10; `start_board_empty` = {fa['start_board_empty']}), the piece catalogue (all 16 types always allowed, no inventory), the 14-piece allowance and the natural-placing rule. There is **no per-episode piece draw or ordering**: the episodes differ **only** through the random number stream that drives stochastic action selection (softmax sampling for the learner, noise for the hand rule, uniform draws for uniform placing). They are 1,200 evaluation episodes of **one fixed problem**, not 1,200 distinct problems. The training "boxes" are likewise episodes of the same fixed problem.
- Distinctness of the outcomes (22c s100 memory): {fa['distinctness']['learner_22c_s100_memory']['distinct_sequences']} distinct placement sequences, {fa['distinctness']['learner_22c_s100_memory']['distinct_final_placement_sets']} distinct final placement sets, {fa['distinctness']['learner_22c_s100_memory']['distinct_first_placements']} distinct first placements out of 1,200 episodes. Hand rule: {fa['distinctness']['hand_rule']['distinct_sequences']} / {fa['distinctness']['hand_rule']['distinct_final_placement_sets']} / {fa['distinctness']['hand_rule']['distinct_first_placements']}. Uniform natural: {fa['distinctness']['uniform_natural']['distinct_sequences']} / {fa['distinctness']['uniform_natural']['distinct_final_placement_sets']} / {fa['distinctness']['uniform_natural']['distinct_first_placements']}.
- Noise: episode-level SD of S1 for the 22c s100 memory = {f3(fa['learner_22c_s100_episode_sd'])}, so the standard error of a 1,200-episode mean = {f3(fa['learner_22c_s100_se_of_mean_1200'])}.
- Disjointness from training: training of stream seed s uses `default_rng(s*7919+13)` (box generator, one continuing stream) and an agent generator `s*104729+7`; the evaluation episodes use `default_rng(7,700,000+j)` and the meta-controller's probe episodes use seeds 8,200,000+j (j < 80; `stream.py:45,74`: eval_seed + 500,000). Largest training seed values: 22b {sd['max_seed_values']['22b']:,}; 22c {sd['max_seed_values']['22c']:,}; 22d full {sd['max_seed_values']['22d_full']:,}; 22d ablations {sd['max_seed_values']['22d_abl']:,}; numeric collisions with the evaluation or probe seed ranges: 22b {sd['training_generator_seed_collisions']['22b']}, 22c {sd['training_generator_seed_collisions']['22c']}, 22d full {sd['training_generator_seed_collisions']['22d_full']}, 22d ablations {sd['training_generator_seed_collisions']['22d_abl']}. (Caveat: seed integers that differ are not a proof of independence of the generated streams, but PCG64 streams from distinct integer seeds are independent for practical purposes; training never uses the evaluation episodes' outcomes for updates.) Note that the meta-controller (a learned component) uses 80 probe episodes **separate** from the 1,200 evaluation episodes, so no meta decision uses held-out evaluation data.

**Where lambda = 1 was chosen on these episodes (prior use).**
- V22a pilot (NIGHT_LOG 03:03 IST, `Expt_22a.../results/pilot_*.log`, 12k boxes, **300 evaluation episodes = seeds 7,700,000..7,700,299**, i.e. the first 300 of the 1,200): `mc_only` (lambda = 1, Monte-Carlo returns) logged held-out 84.3 at 12k (82.17 at 1k, 83.76 at 4k, 84.38 at 10k) vs about 80.4-81.8 at 12k for the bootstrapped lambda = 0.9 `full` pilots (peaks 82.6/81.8/81.6 at 4-6k). Decision logged: default lambda = 1.0 (TD(0.9) kept as ablation `td090`).
- The V22a main-run manifests used eval_boxes 400 (pilot manifest), 600, 800 and 1,200 in different launches (`Expt_22a.../results/*/manifest.json`; all eval_seed 7,700,000, lam 0.95 default in those manifests), and a V22b pilot sweep (7 jobs, 10k boxes, eval = 300, NIGHT_LOG 03:0x) confirmed lambda = 1. The logs of that sweep (`results/p2_*.log`) and `q2.py` are **not on disk** (not found in `Expt_22b/...` or `Expt_22a/...`; NIGHT_LOG says the q2 sweeps were killed), so the sweep's exact evaluation seeds/size are known only from the NIGHT_LOG text - **not recoverable from files**.
- V21 used the same 2,000-episode set (seeds 7.7M..) for its final reporting and the hand-rule reference (first 1,000).
- Therefore the 1,200 episodes are "held out" in the sense that **no gradient update, sleep replay, concept extraction or meta decision used them**, but at least their first 300 members were used in pilot comparisons that selected lambda = 1 (and other early design choices), so they are **not a pristine test set**. A check that the first 300 episodes are not unusual (final `full` streams, first 300 vs the other 900 episodes):

""")
rows = [[r["set"], f3(r["mean_first300_eps"]), f3(r["mean_rest900_eps"]), f"{float(r['diff_first300_minus_rest']):+.3f}", f3(r["sd_of_diff_over_streams"]), f"{r['streams_first300_higher']}/{r['n_streams']}"] for r in R("item4_pilot_overlap_check.csv")]
A(tab(["streams", "first 300", "other 900", "diff", "SD of diff over streams", "streams with first300 higher"], rows))
A("""
**Paper-ready paragraph (suggested).**

> *Evaluation protocol.* All reported performance numbers are means over 1,200 evaluation episodes of the same packing problem: an empty 10 x 10 box, the fixed 16-piece-type catalogue, a limit of 14 pieces, and placements restricted to positions touching the wall or a previously placed piece. The episodes are indexed by the seed of the random number generator (7,700,000 + j, j = 0..1,199) and differ only in the random draws behind stochastic action selection (softmax sampling for the learner, a small noise term for the hand-written reference, uniform draws for uniform natural placing); they are therefore 1,200 evaluation episodes of one fixed problem, not 1,200 distinct problems, and the variability across them (SD of S1 about 2.4 for a trained policy, standard error of the mean about 0.07) measures action-selection randomness, not variation across problem instances. These seeds are disjoint from the generators used for training and from the 80 probe episodes used by the meta-controller, and no learning update used them. They are, however, not an untouched test set: the first 300 of them were used in pilot runs when the return definition (lambda = 1) and other design choices were selected, and the same seeds (the first 2,000) were used for the earlier Expt 21 evaluation. Generalisation to other problem instances (other boxes, piece sets or allowances) is therefore not established by these numbers; between-stream variability is the unit of replication (12 streams at 20k and 32k boxes, 6 at 60k).

""")

# ---------------- item 5 ----------------
A("## Item 5 - Provenance\n\n")
A("""Source files: `manifest.json` / `manifest_rerun.json` of each run folder, `progress.log`, `progress_run1_stopped_0709.log`, `streams_partial_run1_stopped_0709/`, the stream pickles, NIGHT_LOG.md. Start time is **derived** (log DONE-line time minus the pickle's recorded runtime), finish time is the DONE-line time (IST). The stream seed is the training seed (generators `s*7919+13`, `s*104729+7`).

**Runs.**

| run folder | machine | created | code hash | workers | python | notes |
|---|---|---|---|---|---|---|
| `Expt_22b/results/20261001_034445_run` | Vivobook (1c7a0169) | 03:44:45 | d95b3495dd5324ec | 10 | 3.13.1 (MSC v.1942) | 44 streams; wall 7,096 s; an earlier dead launch `20261001_033100_run` is left on disk |
| `Expt_22c/results/20261001_044425_run` | Vivobook | 04:44:25 | c50aba87f089b5bd | 12 | 3.13.1 | 12 streams; wall 4,510 s |
| `Expt_22d/results/20261001_060654_main` | Vivobook | 06:06:54 | 05907550c5739d90 | 26 | 3.13.1 | 26 streams; **stopped by exact PID at 07:08:58** (13 streams finished, 13 cut) |
| same folder, `manifest_rerun.json` | **HsmPc1** (a418bb52) | 09:00:27 | 97ef4b81f9a19dd3 | 13 | 3.13.1; numpy 2.2.0 (scipy-openblas 0.3.28); matplotlib 3.10.0 | `run_expt22d.py --resume-dir ...`: reruns exactly the streams with no final pickle, **from box 0, same seed**; the hash differs from 05907550... only because `run_expt22d.py` gained the `--resume-dir` option (backup `run_expt22d.py.bak_before_resume`); `src/` files unchanged |

Software versions: python 3.13.1 in every manifest. numpy/matplotlib on the Vivobook are **not recorded in any manifest or log** (NIGHT_LOG only says "same python 3.13.1 + numpy/matplotlib/pytest"), so the numpy version used for the original runs is **not recoverable** from files. Restart policy: streams are not resumable (agent state not saved); a cut stream is restarted from box 0 with the same seed, no partial state is reused. Config: all 22b/c/d runs `OMP/BLAS = 1` threads, eval 1,200 episodes (seeds 7,700,000+), tau_eval 0.25, budget 14, hidden 64 growing in 64/128/256 steps, 22b full 12 x 20k, ablations 4 x 10k (seeds 0-11 / 0-3); 22c full 12 x 32k (seeds 100-111); 22d full 6 x 60k (300-305), ablations 4 x 32k (200-203); the full configuration is in each `manifest.json` (`cfg`, `variants`).

**Every stream** (82 streams: 22b 44, 22c 12, 22d 26; `item5_stream_provenance.csv`). `rerun` = rerun from box 0 on HsmPc1 after the 07:09 stop (13 streams).

""")
rows = []
for r in R("item5_stream_provenance.csv"):
    rows.append([r["run_folder"].split("/")[0], r["variant"], r["seed"], r["n_boxes"], r["machine"].split(" (")[0] + (" (rerun)" if r["rerun_after_0709_stop"] == "True" else ""), r["start_IST"], r["finish_IST"], r["code_hash"][:8], r["rerun_after_0709_stop"], f2(r["final_heldout_S1"])])
A(tab(["exp", "variant", "seed", "boxes", "machine", "start IST", "finish IST", "code hash", "rerun", "final S1"], rows))
A("""
Note: the 44 22b streams include control variants (`frozen`, `badinit_fixed`, `badinit_meta`, `td095`); their final S1 (about 66-70 for frozen/badinit) are not part of the main claims.

### Reproducibility: the 13 rerun streams vs the partial run-1 values (same seed, new machine)

Run-1 checkpoints exist for each cut stream up to the stop; rerun checkpoints are from the HsmPc1 rerun (`item5_rerun_vs_run1_checkpoints.csv`, 154 pairs).
""")
div = R("item5_rerun_divergence.csv"); prov = {(r["variant"], r["seed"]): r for r in R("item5_stream_provenance.csv")}
cp = R("item5_rerun_vs_run1_checkpoints.csv")
rows = []
for r in div:
    pr = prov[(r["variant"], r["seed"])]
    mine = [c for c in cp if c["variant"] == r["variant"] and c["seed"] == r["seed"]]
    nid = sum(c["identical_per_box"] == "True" for c in mine)
    mx = max(abs(float(c["diff_rerun_minus_run1"])) for c in mine)
    rows.append([r["variant"], r["seed"], r["run1_boxes_reached"], f"{nid}/{len(mine)}", f"{mx:.4f}", r["first_training_S1_divergence_box"] or "none", r["train_S1_identical_over_run1_boxes"], f3(r["frac_train_S1_equal"]), pr["finish_IST"], f2(pr["final_heldout_S1"])])
A(tab(["variant", "seed", "run-1 boxes reached", "checkpoints identical (per-episode)", "max |held-out diff|", "first training-S1 divergence (box)", "train S1 identical over run-1 boxes", "frac train S1 equal", "rerun finish IST", "rerun final S1"], rows))
rs = J("item5_reproducibility_summary.json")
A(f"""
Summary: {rs['identical_checkpoints']} of {rs['n_checkpoints']} checkpoint pairs are identical per episode. The only difference is `full` s303: training S1 diverges at box 18,906 (fraction of run-1 training boxes equal 0.951), and its 20k held-out is 85.809 (run 1) vs 85.755 (rerun), difference -0.054 (the largest in the set). Over the 89 pairs with checkpoint >= 5,000 boxes: mean abs diff {rs['mean_abs_diff']:.4f}, SD {rs['sd_diff']:.4f}, max abs {rs['max_abs_diff']:.4f}; over the 37 pairs >= 20,000: mean abs {rs['mean_abs_diff_ge20000']:.4f}, SD {rs['sd_diff_ge20000']:.4f}. So the rerun reproduced run 1 essentially bit-exactly in 12 of 13 streams over everything run 1 reached; the cause of the single divergence (a floating-point difference between machines/BLAS builds is the likely, but not verified, reason) was not investigated. Run 1 only reached the earlier checkpoints, so we cannot say whether the 60k endpoints would also have been identical.

**Third replication of the six 60k `full` streams (Expt 22e memory reruns).** The 22e reruns (same HsmPc1 machine, same code, single-threaded) of `full` s300-s305 reproduce the saved 22d final streams at all 120 shared checkpoints per episode ({J('item5_third_run_summary.json')['identical_checkpoints']}/{J('item5_third_run_summary.json')['n_checkpoint_pairs']} identical, max abs diff {J('item5_third_run_summary.json')['max_abs_diff']}), with training S1 identical over all 60k boxes in {J('item5_third_run_summary.json')['n_streams_identical_training_S1']}/6 streams and the same final mean ({J('item5_third_run_summary.json')['mean_final_22e']:.4f}). Since the saved 22d `full` streams were themselves produced by the HsmPc1 rerun, this shows determinism on one machine, **not** independent cross-machine reproducibility.
""")
tt = R("item5_third_run_divergence.csv")
A("\n" + tab(["seed", "identical training S1", "boxes differing", "final held-out 22d", "final held-out 22e rerun"], [[r["seed"], r["identical_training_S1"], r["n_boxes_differ"], f3(r["final_heldout_22d"]), f3(r["final_heldout_22e"])] for r in tt]))

# ---------------- claims ----------------
A("""
## What this changes in the manuscript's claims

1. **Plateau (22d):** replace the independent-bootstrap statement for 56k -> 60k (CI about -1.1 to +1.1) by the paired one: +0.04 S1, 95% CI [-0.04, +0.13], 4 of 6 streams up. The data support a near-plateau (last 8k boxes +0.07 and +0.04), not a hard ceiling (48k -> 52k +0.22, CI +0.09..+0.36; 6/6 up). n = 6 streams, one configuration.
2. **Ablations:** only `no_sleep` (-1.81) is supported after multiplicity correction (Holm 0.0013 Welch-normal, 0.0174 Welch-t; does **not** survive the exact permutation test or Mann-Whitney with n = 4: Holm 0.102 / 0.066). `no_meta_matched_floor` (-1.02) does not survive Holm/Bonferroni/BH -> label **exploratory**. `no_meta`, `no_dream`, `no_concepts`: no detectable effect (n = 4 each; not evidence of no effect).
3. **Piece P:** the learned policies use P in 100% of episodes (9.2 -> 10.0 -> about 10.9 P pieces/episode at 20k/32k/60k); uniform natural placing uses P in 47.2% of episodes (0.63 per episode). A large share of the gain over uniform is piece choice: always choosing P with uniform placement already gives 82.3; P-only with contact-greedy placement 88.9 (about the hand rule 89.6). The 60k learners (mean 91.76) exceed that reference. Do not describe the learner as discovering placement skill alone.
4. **Baselines:** the "uniform ~ 67" in the 22b/c/d reports is the untrained network at checkpoint 0 (67.23-67.81), not uniform natural placing (67.32); V21's 67.30 is true uniform (2,000 episodes). "89.61" is the hand rule on the first 1,000 seeds (89.617 on the 1,200 episodes; 89.648 on 2,000). V21 used tau_eval 0.3 and 2,000 episodes; 22b-d used 0.25 and 1,200. The Expt-20 baselines (best 98.0) are on a different task (unlimited pieces, 100 actions) and none was evaluated under the 14-piece cap there; under the cap the new simple packers give 70.2-89.6.
5. **Evaluation set terminology:** "1,200 fresh/held-out boxes" -> "1,200 evaluation episodes of one fixed problem (seeds 7,700,000 + j) that differ only in the random draws of action selection". They are disjoint from training, but their first 300 were used in pilots to choose lambda = 1 (and V21 used the same seeds), so they are not a pristine test set; claims about generalisation to other box instances are not supported by this evaluation.
6. **Reproducibility wording (student write-up / manuscript):** replace "reproducible statistically, not bit for bit" by: the 13 streams rerun after the interruption matched the first run per episode at 153 of 154 shared checkpoints (one stream diverged from box 18,906 with a -0.054 difference at 20k). Held-out values of reruns agree to within 0.054 (mean absolute difference 0.0006 for checkpoints >= 5,000 boxes).
7. **Provenance statement:** 13 of the 26 22d streams (6 `full`, 3 no_concepts, 2 no_dream, 1 no_meta, 1 no_meta_matched_floor) were produced on HsmPc1 after a manual stop; the other 13 ran on the Vivobook. The numpy version used on the Vivobook is not recorded.

## Caveats and things not recoverable

- Expt 22d did not store final agent memories; item 2 used reruns (identical to the saved streams, verified at all 120 checkpoints). 22b/22c stored only seed-0 / seed-100 memories (one of 12 each).
- The Vivobook numpy / BLAS versions are not recorded. The cause of the single run-1 vs rerun divergence (full s303) was not investigated.
- The V22b pilot sweep logs (`p2_*.log`) and `q2.py` are not on disk: evaluation size/seeds of that sweep are known only from NIGHT_LOG text. The V22a main-run manifests record eval_boxes 400/600/800/1,200 across launches; lambda default in those manifests is 0.95 (the lambda = 1 default was set later in code - see NIGHT_LOG 03:03-03:04).
- The origin of the hand-rule weights (-3, -1, +2, noise 0.5) was not traced (they are constants in `learner_ref.py` / `learner.py`); whether they were tuned on the evaluation seeds is unknown to this report.
- n is small: 6 streams for saturation, 4 per ablation; permutation-based tests cannot reach strong significance with n = 4 vs 12 after correction. No power analysis was done.
- Exact-number CSVs are in the same folder; none of the existing experiment folders or the student write-up was modified.

## Table of exact numbers (headline)

""")
pm = {r["policy"]: r for r in pu}
hl = [
    ["Item 1a", "56k -> 60k paired mean diff (95% paired bootstrap CI)", f"{sg(last['mean_diff'])} ({sg(last['boot_lo'])}, {sg(last['boot_hi'])}); n = 6"],
    ["Item 1a", "20k -> 60k", next(f"{sg(r['mean_diff'])} ({sg(r['boot_lo'])}, {sg(r['boot_hi'])})" for r in pa if r["from_boxes"] == "20000" and r["to_boxes"] == "60000")],
    ["Item 1a", "48k -> 52k", next(f"{sg(r['mean_diff'])} ({sg(r['boot_lo'])}, {sg(r['boot_hi'])})" for r in pa if r["from_boxes"] == "48000" and r["to_boxes"] == "52000")],
]
for v in ("no_sleep", "no_meta_matched_floor"):
    for t in ("welch_normal(as in summary.md)", "welch_t(df Satterthwaite)", "permutation_exact", "mannwhitney_U"):
        r = next(x for x in mult if x["reference"] == "22c_full_n12" and x["test"] == t and x["variant"] == v)
        hl.append(["Item 1b", f"{v}, {t.split(' (')[0]} (22c ref)", f"diff {sg(r['ref_minus_var'])}; raw p {p(r['p_raw'])}, Holm {p(r['p_holm'])}, Bonf {p(r['p_bonferroni'])}, BH {p(r['p_BH'])}"])
for k, lab in (("uniform natural (1200)", "uniform natural"), ("hand contact/hole/area rule (1200)", "hand rule"), ("22b full s0 @20k boxes", "22b s0 @20k"), ("22c full s100 @32k boxes", "22c s100 @32k")):
    r = pm[k]
    hl.append(["Item 2", lab, f"S1 {f3(r['S1'])}; P in {f3(r['frac_boxes_with_P'])} of episodes; {f3(r['mean_P_per_box'])} P/episode; area {f3(r['mean_piece_area'])}"])
hl.append(["Item 2", "22d full @60k, mean of 6 memories", f"S1 {mean('S1'):.3f}; P in 1.000; {mean('mean_P_per_box'):.3f} P/episode; area {mean('mean_piece_area'):.3f}"])
for r in R("item2b_P_only_baselines.csv"):
    hl.append(["Item 2", r["policy"], f"S1 {f3(r['S1'])}; {f3(r['mean_P_per_box'])} P/episode"])
hl += [["Item 3", "hand rule on 1,000 / 1,200 / 2,000 episodes", "89.606 / 89.617 / 89.6475"],
       ["Item 3", "uniform natural on 1,000 / 1,200 / 2,000 episodes", "67.328 / 67.319 / 67.297"],
       ["Item 3", "checkpoint-0 mean S1 (untrained net) 22b / 22c / 22d", " / ".join(f3(r["mean_ckpt0_S1"]) for r in a)],
       ["Item 4", "evaluation seeds; SE of mean (22c s100)", f"7,700,000 + j, j < 1,200; SD {f3(fa['learner_22c_s100_episode_sd'])}, SE {f3(fa['learner_22c_s100_se_of_mean_1200'])}"],
       ["Item 5", "identical checkpoints rerun vs run 1", f"{rs['identical_checkpoints']}/{rs['n_checkpoints']}; max abs diff {rs['max_abs_diff']:.4f} (full s303 @20k)"],
       ["Item 5", "abs diff, checkpoints >= 5k (n = 89)", f"mean {rs['mean_abs_diff']:.4f}, SD {rs['sd_diff']:.4f}"]]
A(tab(["item", "quantity", "value"], hl))
A("""
## Files

`item1a_paired_saturation.csv`, `item1a_per_stream_heldout.csv`, `item1b_ablation_multiplicity.csv`, `item1_inputs.json`, `fig_item1a_paired_differences.png`; `item2_piece_P_usage.csv`, `item2b_P_only_baselines.csv`, `item2_per_box.npz`, `item2_meta.json` (the `*_before_22d_memories.*` copies are the earlier 4-policy outputs); `item3_code_refs.csv`, `item3_expt20_rules.csv`, `item3_extra_packers_under_14cap.csv`, `item3_ckpt0_vs_uniform.csv`, `item3_natural_filter_equivalence.json`, `item3_4_facts.json`, `item3_refs_v21.npz`, `item3_refs_v22.npz`; `item4_pilot_overlap_check.csv`, `item4_seed_disjointness.json`; `item5_stream_provenance.csv`, `item5_rerun_vs_run1_checkpoints.csv`, `item5_rerun_divergence.csv`, `item5_reproducibility_summary.json`, `item5_third_run_*.csv/json`; `memory_reruns/` (six final memories and streams, `progress.log`).
""")
(RUN / "report.md").write_text("".join(o), encoding="utf-8")
print("report.md written", sum(len(x) for x in o))