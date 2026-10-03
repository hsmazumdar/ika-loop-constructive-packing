# Reviewer guide

Part A covers Expt-1 to Expt-19 (when memory reduces deliberation). Part B covers Expt-20 to Expt-22e (continuous learning and memory consolidation on one fixed problem). Part C covers Expt-23 (multi-problem packing case study of the information -> knowledge loop, with the A8 controller-off confirmation). The parts use different tasks and metrics; numbers are not comparable across them.

# Part A: Expt-1 to Expt-19

Effort saving is baseline effort minus agent effort. Positive means less effort. Packing quality is occupied cells and is reported separately. A quality loss, where that definition was recorded, is agent quality more than one cell below the paired baseline.

Seeds that share one memory table are repeated evaluations, not independent learned memories. A fit, a stored key, or an oracle replay is not a deployed saving.

## Claim that the record supports

Useful arrangements and exact repeats can be found under particular conditions. Those conditions are not the same thing as a policy that spends less effort on ordinary problems without losing quality.

- Exact whole-state recall helps when the same inventory is repeated (Expt-9, Expt-10). On fresh inventories it does not. Expt-9’s recurring hits were empty-board recall. The file does not split initial and intermediate hits.
- A supplied nonempty prefix can be recalled (Expt-10). That prefix was given to the agent. It was not an autonomous decision to decompose the box.
- Supplied rotations and reflections can be selected from experience when the transformed remainder was constructed (Expt-11, Expt-12). The smallest positive mixture is one measured setting, not a general break-even.
- On ordinary streams, intermediate hits were not observed (Expt-13). Growing memory on family streams stayed positive against primitive and below a frozen table (Expt-14). It did not lose the whole recall benefit, and it did not pay for itself on fresh streams.
- Supplied local regions can be cheaper than the same decomposed search (Expt-15). Against whole-box primitive search the picture is different, and ordinary streams did not produce local hits. Expt-16 found 5 exact fillings in 128 late regions. The primitive missed those five. Most regions were unfillable. Two downstream matches are descriptive cases, not a rate.
- Expt-17: small arrangements recur, and legal fits are common. Matching them exhaustively was far above a tenth of primitive effort.
- Expt-18: a diagnostic oracle, which sees both continuations, finds quality-preserving savings on some sampled boxes. Overlapping suffixes are not added. This is not a policy.
- Expt-19: the sequential budgeted recognizer cost 0.113 of mean primitive effort and failed the predeclared 0.10 gate. State recall was 0.623. Among 39 boxes with a useful reference action, the mean of the per-box retention ratios was 0.792. The ratio of summed retained saving to summed oracle saving on those boxes was 0.744. Those two retention summaries are different, and neither overrides the gate. Commitment was not tested. The ratio of means (0.113) is not the mean of per-box cost ratios (0.138).

## What is not established

- Learned operation libraries and gates did not reduce held-out effort without a quality cost (Expt-4C, Expt-5, Expt-7). Expt-7 evaluates three seed-specific frozen libraries; their snapshot hashes differ. The indexed ranker made zero commitments.
- Expt-8C’s action-level nets are negative. The saved offline net (−1,621) bills accepted feature checks only. The report-derived net (−19,893) also bills rejected checks. Neither is a whole-box deployment saving.
- A failed cost gate is not proof that no other access method could help, and it is not proof that the stored arrangements are useless.
- No confidence intervals are reported. Stream and seed ranges are sample descriptions.

## Authoritative runs

Use these directories, relative to this repository. Smoke folders and earlier diagnostics are not the numbers cited in the supplementary tables.

| Experiment | Run |
| --- | --- |
| Expt-2 baseline | `Expt_02_Autonomous_Abstraction/results/20260929_092518_discovery_smoke` |
| Expt-4C | `Expt_04C_Confirm_Reusable_Knowledge/results/20260929_200422_confirm` |
| Expt-5 | `Expt_05_Consult_and_Commit_Gates/results/20260929_212658_diagnostic` |
| Expt-7 | `Expt_07_Indexed_Retrieval/results/20260929_220030_diagnostic` |
| Expt-8C | `Expt_08C_Unseen_Confirmation/results/20260929_233422_diagnostic` |
| Expt-9 | `Expt_09_Exact_Continuation_Reuse/results/20260929_234344_diagnostic` |
| Expt-10 | `Expt_10_Exact_Subproblem_Reuse/results/20260930_055535_diagnostic` |
| Expt-11 | `Expt_11_Remaining_State_Equivalence/results/20260930_060957_diagnostic` |
| Expt-12 | `Expt_12_Mixed_Stream_Recurrence/results/20260930_061916_diagnostic` |
| Expt-13 | `Expt_13_Unforced_Reuse/results/20260930_064034_diagnostic` |
| Expt-14 | `Expt_14_Online_Memory_Growth/results/20260930_064836_diagnostic` |
| Expt-15 | `Expt_15_Local_Subproblem_Memory/results/20260930_070329_diagnostic` |
| Expt-16 | `Expt_16_Search_Acquired_Local_Memory/results/20260930_071552_diagnostic` |
| Expt-17 | `Expt_17_Arrangement_Census/results/20260930_090000_diagnostic` |
| Expt-18 | `Expt_18_Arrangement_Utility/results/20260930_091301_diagnostic` |
| Expt-19 | `Expt_19_Budgeted_Recognition/results/20260930_092450_diagnostic` |

Known substitutions, already applied in the tables:

- Expt-7 `20260929_220009` has an empty frozen-gates cell. Use `220030`.
- Expt-15 `20260930_065912` differs on fresh-stream effort. Use `070329`.
- On some Expt-9 and Expt-10 primitive rows, recorded effort saving is 0 while total effort includes lookup overhead. Those rows remain in the supplementary tables. Percentage savings for the agent rows use a stated comparator: primitive effort on the same rows, or, for Expt-10 constructed prefixes, the memory-off continuation.

# Part B: Expt-20 to Expt-22e

## Task and metric

Same 10x10 box and 16-piece catalogue (A-P, all rotations, unlimited supply) as Expt-1, but **at most 14 pieces per box** and **natural placing** only (a legal placement that touches the wall or an already placed piece). S1 = 100 - empty cells. One agent learns one box at a time; there are no batch phases. Held-out S1 is measured with learning frozen.

Expt-20 is on the unhandicapped task (unlimited pieces): simple contact rules reach 96-98 there, which is why Expt-21 onward adds the 14-piece cap. Expt-20 numbers are not comparable with Expt-21/22.

## Evaluation set (read before quoting "held-out")

Expt-22b/c/d evaluate on 1,200 evaluation episodes of one fixed problem (seeds 7,700,000 + j, near-greedy tau 0.25). They differ only in the random draws of action selection. They are disjoint from training, but the first 300 were used in pilots to choose lambda = 1, and Expt-21 used the same seeds (2,000 episodes, tau 0.3). They are not a pristine test set, and they do not support claims about other box instances.

## Claims that the record supports

- The value learner improves with experience: held-out S1 rises from about 67 (untrained) to 85.58 at 20k boxes (Expt-22b, n = 12), 88.28 at 32k (Expt-22c, n = 12, new seeds) and 91.76 at 60k (Expt-22d `full`, n = 6).
- Near-plateau, not a ceiling, at 60k: paired 56k -> 60k difference +0.04 S1 (95% paired bootstrap CI -0.04 to +0.13, n = 6); 48k -> 52k was still +0.22 (CI +0.09 to +0.36).
- Sleep consolidation matters: `no_sleep` is -1.81 S1 against the Expt-22c `full` reference at 32k and survives Holm correction under Welch tests (0.0013 normal, 0.0174 t). It does not survive the exact permutation test (Holm 0.102) or Mann-Whitney (Holm 0.066) with n = 4.
- Monte-Carlo returns beat bootstrapped TD(0.95) at 10k boxes (Expt-22b: +1.36).
- Run-to-run reproducibility: 13 streams rerun after an interruption matched the first run at 153 of 154 shared checkpoints; one stream diverged from box 18,906 (-0.054 at 20k).

## What is not established

- The meta-controller, dreams, the concept library and capacity growth: no detectable benefit (`no_meta`, `no_dream`, `no_concepts` n = 4 each; not evidence of no effect). `no_meta_matched_floor` (-1.02) does not survive multiplicity correction and is exploratory.
- Placement skill alone: learned policies use the 7-cell piece P in 100% of episodes (about 9-11 P per episode) against 47% for uniform placing. Always choosing P with uniform placement already gives 82.3; P-only with contact-greedy placement gives 88.9. A large share of the gain is piece choice.
- Generalisation to other boards, catalogues or budgets: not tested (the budget-transfer runs in Expt-22b/c change only the piece cap).
- The hand rule (89.62 on the 1,200 episodes) is a reference line only; the learner never calls it. The origin of its weights was not traced.
- The "uniform ~ 67" in the Expt-22b/c/d summaries is the untrained network at checkpoint 0 (67.23-67.81), not uniform natural placing (67.32).

## Authoritative runs

| Experiment | Run | Notes |
| --- | --- | --- |
| Expt-20 phase 1 (LTM from random fills) | `Expt_20_Winning_Combination_LTM/results/20260930_131353_run_S2default` | S2 ranking default; `20260930_131107_run` is the earlier run |
| Expt-20 LTM-guided fill | `Expt_20_Winning_Combination_LTM/results/20260930_203509_phases` | |
| Expt-20 stronger arms | `Expt_20_Winning_Combination_LTM/results/20260930_210213_stronger` | |
| Expt-20 plain-rule baselines | `Expt_20_Winning_Combination_LTM/results/20260930_214303_baselines` | best rule picked after seeing results |
| Expt-21 | `Expt_21_Continuous_Learning_Memory/results/20260930_233539_run` | additive hash tables; 2,000 evaluation episodes, tau 0.3 |
| Expt-22a | `Expt_22a_Organic_Value_Learner/results/20261001_032026_run` | earlier partial attempt; its `no_sleep` row is invalid (evaluated the never-updated slow net) |
| Expt-22b | `Expt_22b_Organic_Value_Learner/results/20261001_034445_run` | 12 x 20k boxes + ablations at 10k |
| Expt-22c | `Expt_22c_Long_Streams/results/20261001_044425_run` | 12 x 32k boxes, seeds 100-111; `summary.md` heading says "Expt-22b" (code copied unchanged) |
| Expt-22d | `Expt_22d_Long_Ablations_Saturation/results/20261001_060654_main` | 6 x 60k `full` + 5 ablations x 4 x 32k; stopped and resumed, see below |
| Expt-22e | `Expt_22e_Closure_Analyses/results/20261001_122457_run` | `report.md`; analyses of saved data plus logged reruns |

Earlier pilot, smoke and partial folders next to these are kept for provenance and are not the cited numbers.

## Provenance notes

- Expt-22d was stopped manually after about 62 minutes and the 13 unfinished streams were rerun from box 0 on a second machine (`manifest_rerun.json`, `progress_run1_stopped_0709.log`, `streams_partial_run1_stopped_0709/`). The other 13 streams are from the first machine. `run_expt22d.py` gained a `--resume-dir` option for this rerun.
- Expt-22d did not store final agent memories. Expt-22e reran the six `full` streams with the unmodified Expt-22d code to obtain them (`memory_reruns/`); all re-evaluate to the saved held-out values exactly.
- Not recoverable: the numpy version on the first machine for Expt-22b, 22c and 22d run 1; the Expt-22b pilot sweep logs that selected lambda = 1. Expt-22b/22c stored one final memory each (seed 0, seed 100).
- n is small (6 streams for saturation, 4 per ablation). No power analysis was done.


# Part C: Expt-23 MultiProblem

## Task and metric

Variable board sizes, obstacle cells, and polyomino catalogues (283 pieces of size 3-7; the Expt-1 A-P set is the `legacy` subset). Primary condition = 14-piece cap + natural placing. Score is normalised filled non-obstacle cells (S1 / free cells). Arms: full learner with guided generation and consolidation (`F`), plain online learner (`N`), compute-matched no-meta (`NM`), random-data full (`R`), random-data no-consolidate (`RN`). Hand rule and CEM-hand are references only.

The A8 controller-off confirmation freezes the self-tuning controller (fixed exploration / sleep schedule) after diagnostics showed the controller held the full learner back on the earlier E-runs.

## Claims that the record supports (A8 controller-off, std / capped_nat, n = 8 per arm)

- Consolidation helps: `F` vs `N` +0.0234; `F` vs `NM` +0.0266 (primary family, Holm-supported under Welch / permutation / MWU).
- Guided data helps: `F` vs `R` +0.0498 (primary family, Holm-supported).
- Secondary: `F` beats `RN`, earlier DQN, and earlier PPO; `F` remains below hand / cemhand references (~0.93).
- Transfer (E3): `F` final split means stay near test_iid (gaps to size / piece / both are small); `F` minus `N` is positive on every split.
- Improvement across checkpoints (E4): `F` rises from ~0.76 to ~0.90 over 20k episodes; generated-data quality under `F` rises across rounds while `R`/`RN` stay flat.

## What is not established

- Other domains in DESIGN.md (puzzles, programs, equations) are not run in this repository copy.
- Hard-variant and uncapped / non-natural condition grids are secondary; quote the A8 std / capped_nat table unless the guide names another run.
- The earlier controller-ON E-run (`F` 0.841) is superseded for the consolidation claim by the A8 controller-off confirmation.

## Authoritative runs

| Experiment | Run | Notes |
| --- | --- | --- |
| Expt-23 A8 analysis | `Expt_23_MultiProblem/analysis_ctrloff/` | `ctrloff_summary.md`; 80 streams; primary numbers |
| Expt-23 A8 streams (i9) | `Expt_23_MultiProblem/results_ctrloff_i9/` | controller-off streams |
| Expt-23 A8 streams (i9b) | `Expt_23_MultiProblem/results_ctrloff_i9b/` | split batch on i9 |
| Expt-23 A8 streams (i7) | `Expt_23_MultiProblem/results_ctrloff_i7/` | split batch on i7 |
| Expt-23 diagnostics D1-D4 | `Expt_23_MultiProblem/results_i9/`, `results_vivo_diag/` | controller-ON finding; not the A8 headline |

Earlier `results/` reference tables and smoke outputs are kept for provenance. `DESIGN.md` is the frozen plan.

## What this repository contains

| Path | Role |
| --- | --- |
| `supplementary/` | Part A supplementary tables and figures |
| `Expt_01_10x10_Packing/` through `Expt_19_Budgeted_Recognition/` | Part A code, tests, and saved runs |
| `Expt_20_Winning_Combination_LTM/` through `Expt_22e_Closure_Analyses/` | Part B code, tests, saved runs, and closure analyses |
| `Expt_23_MultiProblem/` | Part C multi-problem packing study, A8 controller-off confirmation, diagnostics |

The manuscript is not in this repository. Regenerating a run is not required to read the saved results, and the launchers do not start a new diagnostic or learning stream.
