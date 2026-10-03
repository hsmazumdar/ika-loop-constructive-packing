# RESUME_22e.md - how to finish Expt_22e_Closure_Analyses on another PC

Written 2026-10-01 ~13:55 IST on HsmPc1. Replace `<DRIVE>` below with the drive letter the SSD gets on the new PC (it was `K:` on HsmPc1).
Project root: `<DRIVE>:\PaperSubmissions2026\Assembly_Skill_Learning`   Folder: `Expt_22e_Closure_Analyses`   RUN = `results\20261001_122457_run`

## Requirements
- Python 3.13 with numpy (HsmPc1: python 3.13.1, numpy 2.2.0), scipy and matplotlib 3.10 (scipy is used by item1 and item5; matplotlib is optional).
- No other input is needed. All inputs are saved files on the SSD: Expt_21, 22a-d result folders, and `RUN\memory_reruns\full_s300..305_final_memory.pkl` + `full_s300..305_stream.pkl`.
- Every script uses paths relative to its own location (`common.py`: ROOT = parents[2]). The path `Expt_22e...\code\..\..` must be `Assembly_Skill_Learning`; the drive letter does not matter. Do NOT rename the RUN folder (RUN is hard-coded in common.py as `results\20261001_122457_run`).
- Never modify Expt_21 / 22a-d folders (read-only).

## Status
DONE (outputs already in RUN, nothing needs to be re-run):
| item | what | files |
|---|---|---|
| 1 | paired saturation stats, Holm/Bonferroni/BH, Welch normal / Welch-t / exact permutation / Mann-Whitney, 22c-only and pooled reference | item1a_*.csv, item1b_ablation_multiplicity.csv, item1_inputs.json |
| 3 | code refs, natural-filter equivalence, V21 vs 22 reference paths, Expt-20 rule list, extra packers under 14 cap | item3_*.csv/json/npz |
| 4 | evaluation-set facts, seed disjointness, pilot overlap | item3_4_facts.json, item4_*.csv/json |
| 5 | 82-stream provenance table, rerun-vs-run1 reproducibility (154 checkpoint pairs) | item5_stream_provenance.csv, item5_rerun_*.csv, item5_reproducibility_summary.json |
| 2 (partial) | P usage for uniform natural, hand rule, stored 22b s0 and 22c s100 memories; P-only references | item2_piece_P_usage.csv (12:54 version = 4 policies), item2b_P_only_baselines.csv, item2_meta.json |

UPDATE 13:59 IST: all 6 memory reruns finished (6 final_memory.pkl + 6 stream.pkl present). item5_third_run.py DONE: 120/120 checkpoint pairs per-episode identical between the 22e rerun and the saved 22d streams (all 6 streams, training S1 identical over all 60k boxes, final mean 91.7606 both). item2_piece_P.py was started 13:58 (see status line at the end of this file).

REMAINING (re-runnable, ~20-30 min total, no running process needed):
1. item 2 final: P usage for the six 22d full s300-305 final memories (60k boxes), added to the CSV.
2. (done) item 5 third-run comparison.
3. write `RUN\report.md` (+ optional figure) and `Expt_22e_Closure_Analyses\README.md`.
4. final NIGHT_LOG.md entry (append only).

## Commands (cmd.exe or PowerShell; set single-thread BLAS first so results are reproducible)
```
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
cd /d <DRIVE>:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_22e_Closure_Analyses

REM 0. verify inputs exist (expect 6 memory + 6 stream files)
dir results\20261001_122457_run\memory_reruns\*.pkl

REM 1. item 2 final (single process, ~10-20 min: 1,200 episodes x (uniform + hand + 2 stored + 6 memories); use start /b or a separate window)
python -u code\item2_piece_P.py > results\20261001_122457_run\item2_stdout.txt 2>&1
REM    It asserts that the reimplemented uniform/hand rules reproduce Expt_22d/src/learner_ref.py exactly, then reports
REM    'reproduces_saved_heldout_exactly' per memory. Overwrites item2_piece_P_usage.csv, item2_meta.json, item2_per_box.npz.
REM    (A back-up copy of the 12:54 outputs is item2_piece_P_usage_before_22d_memories.csv.)

REM 2. third-run comparison (seconds)
python -u code\item5_third_run.py > results\20261001_122457_run\item5_third_run_stdout.txt 2>&1

REM 3. optional: item 2b P-only references already done; re-run only if missing:  python -u code\item2b_P_only.py
```
Workers/cores: all scripts are single-process and need 1 core each (items 2 and 2b can run in parallel in 2 windows). Memory < 1 GB. A fast PC is not required.
Do not run more than ~6 python processes at once on a 12-thread machine; always set OMP/OPENBLAS/MKL threads to 1.

## If the memory reruns need to be repeated
(Only if `full_s303_final_memory.pkl` or `full_s305_final_memory.pkl` is missing; 4 of 6 were saved before the stop, the other two were running at 56k/60k at 13:52 IST.)
```
code\launch_one.bat 303      REM ~75 min for 60k boxes, one core
code\launch_one.bat 305
```
(launch_one.bat has K: hard-coded in its `cd /d` line - edit it to <DRIVE>:. Each run restarts from box 0 with the original seed; the 60k result is deterministic up to float noise: held-out at 60k should match the saved 22d stream, see item5 findings.) Log: `RUN\memory_reruns\progress.log`.

## Report content to write (numbers are in the CSVs; the headline findings to include)
- Item 1a: paired 56k->60k = +0.04 (paired bootstrap 95% CI -0.04..+0.13; independent CI was -1.15..+1.13); 20k->60k +6.38 (5.73..7.33); 48k->52k +0.22 (0.09..0.36) still positive. n=6 streams.
- Item 1b: 22c reference n=12 (32k) vs ablations n=4. no_sleep +1.81 survives Holm (Welch-normal .0013, Welch-t .0174; exact permutation Holm .102 does not, Mann-Whitney .066 does not). matched_floor +1.02: raw .023 -> Holm .092 / Bonf .116 / BH .058 -> not significant -> EXPLORATORY. Pooled reference (n=18): matched_floor survives Holm under Welch-normal (.038) but not Welch-t (.082), permutation (.61), Mann-Whitney (.21). no_meta/no_dream/no_concepts: indistinguishable (p>=.33).
- Item 2: uniform natural S1 67.32, P in 47.2% boxes (0.63 P per box); hand rule 89.62, P in 100% (10.1 per box); stored learners (83.89 @20k, 87.83 @32k) use P in 100% (9.2, 10.0 per box). P-only contact-greedy reference 88.92. Hand-rule area term essential (no-area variants 70.2-77.5).
- Item 3: engine.py byte-identical across 21/22a-d; same legality, 14-cap, natural filter (0 mismatches over >17k decision states); "uniform ~67" in 22 reports is the untrained net at checkpoint 0 (67.2-67.8) not true uniform (67.32; V21's 67.30 is true uniform); tau_eval 0.3 (V21) vs 0.25 (22); 89.61 = first-1,000-episode mean (89.617 on 1,200; 89.648 on 2,000); Expt-20 baselines (unrestricted empty box, unlimited pieces) never under the 14 cap in Expt 20.
- Item 4: 1,200 evaluation episodes of ONE fixed problem (empty 10x10 board, 16-type catalogue, 14-piece cap), seeds 7,700,000+j, differ only through the stochastic action selection; training seeds disjoint (0 collisions); the first 300 (pilot, lambda=1 chosen) and V21's 2,000 overlap them -> "held-out" = not used for gradient updates, not pristine.
- Item 5: 13 streams rerun from box 0 on HsmPc1 after the 07:09 stop; 153 of 154 checkpoint pairs per-episode identical; one divergence (full s303, from box 18,906; 20k held-out 85.809 -> 85.755). Vivobook numpy version not recorded anywhere (unrecoverable).
- Claims affected: 56k->60k plateau claim (paired CI), ablation claims (matched_floor exploratory), "not bit-identical" reproducibility wording, "fresh boxes" terminology, "uniform ~67 baseline" wording, 89.61 definition, held-out vs pilot-selected note.

## STATUS 14:04 IST (final before eject)
- item2_piece_P.py DONE (10 policy rows: uniform, hand, 22b s0, 22c s100, 22d s300-305; all 8 memories re-evaluate to saved held-out EXACTLY). item5_third_run.py DONE.
- ONLY REMAINING: write RUN\\report.md (+ optional paired-difference figure) and Expt_22e_Closure_Analyses\\README.md from the CSVs, then append a final NIGHT_LOG line. No more simulation needed. Steps 1 and 2 under Commands do NOT need re-running.
- 22d memories, per-policy P usage: see item2_piece_P_usage.csv.


## STATUS: COMPLETE (2026-10-01, written on i9Win10)
report.md (results/20261001_122457_run), README.md and fig_item1a_paired_differences.png were produced from the saved CSV/JSON files by code/make_report.py and code/make_figure_item1a.py. Nothing remains; no simulation was rerun.
