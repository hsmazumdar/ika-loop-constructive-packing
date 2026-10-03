# Expt_22e_Closure_Analyses

**Purpose.** Five closure analyses for the manuscript "Continuous Learning and Memory Consolidation for Constructive Packing", using only saved Expt 21 / 22a-d data plus modest, logged new simulation:
1. paired statistics (22d saturation; Holm/Bonferroni/BH over the five ablations), 2. piece-P usage (learner final memories, hand rule, uniform natural placing), 3. baseline audit (code-level), 4. description of the 1,200 evaluation episodes, 5. provenance of every 22b/c/d stream and run-to-run reproducibility.

**Status: COMPLETE** (2026-10-01). Main deliverable: `results/20261001_122457_run/report.md` (one section per item, claim changes, caveats, exact-number table).

## File map (all in `results/20261001_122457_run/`)
| item | files |
|---|---|
| report | `report.md`, `fig_item1a_paired_differences.png` |
| 1 | `item1a_paired_saturation.csv`, `item1a_per_stream_heldout.csv`, `item1b_ablation_multiplicity.csv`, `item1_inputs.json` |
| 2 | `item2_piece_P_usage.csv` (10 policies), `item2b_P_only_baselines.csv`, `item2_per_box.npz`, `item2_meta.json`, `item2_*_before_22d_memories.*` (earlier 4-policy outputs), `memory_reruns/` (six 22d `full` final memories `full_s30x_final_memory.pkl` + streams + `progress.log`) |
| 3 | `item3_code_refs.csv` (file:line refs), `item3_natural_filter_equivalence.json`, `item3_ckpt0_vs_uniform.csv`, `item3_expt20_rules.csv`, `item3_extra_packers_under_14cap.csv`, `item3_refs_v21.npz`, `item3_refs_v22.npz`, `item3_4_facts.json` |
| 4 | `item4_pilot_overlap_check.csv`, `item4_seed_disjointness.json`, `item3_4_facts.json` |
| 5 | `item5_stream_provenance.csv` (82 streams), `item5_rerun_vs_run1_checkpoints.csv`, `item5_rerun_divergence.csv`, `item5_reproducibility_summary.json`, `item5_third_run_*.csv/json` |

`code/` : `common.py` (paths/loaders), `item1_paired_stats.py`, `item2_piece_P.py`, `item2b_P_only.py`, `item3_4_audit.py`, `item3_natural_equiv.py`, `item3_v21_vs_22_refs.py`, `item34_addon.py`, `item5_provenance.py`, `item5_third_run.py`, `rerun_full_for_memory.py` + `launch_one.bat` (memory reruns), `check_threads.py`, `make_figure_item1a.py`, `make_report.py`. `RESUME_22e.md` = hand-over notes (now COMPLETE).

## Reproduce (relative paths; nothing needs the drive letter)
Requirements: python 3.13 (reports were produced with 3.13.1 / numpy 2.2.0; `make_report.py` and `make_figure_item1a.py` also run with python 3.12 / numpy 2.0 and only need the standard library and matplotlib), numpy, scipy (item 1), matplotlib (figure).
```
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
cd Expt_22e_Closure_Analyses
python code\item1_paired_stats.py          # seconds (uses a fixed bootstrap seed 20261001)
python code\item2_piece_P.py               # ~10-20 min, single process; needs memory_reruns\*_final_memory.pkl
python code\item2b_P_only.py ; python code\item3_4_audit.py ; python code\item34_addon.py ; python code\item5_provenance.py
python code\item3_v21_vs_22_refs.py v21 ; python code\item3_v21_vs_22_refs.py v22   # separate processes
python code\item5_third_run.py ; python code\make_figure_item1a.py ; python code\make_report.py
```
The report and figure are rebuilt from the saved CSV/JSON files only (`make_report.py`, `make_figure_item1a.py`: seconds, no simulation). `common.py` locates the Expt_21/22a-d result folders relative to this folder (`Assembly_Skill_Learning/`); the run folder name `20261001_122457_run` is hard-coded. Rerunning the memory reruns takes about 75-80 min per stream (`code\launch_one.bat <seed>`; edit the drive letter in its `cd /d` line). Existing experiment folders and the student write-up are read-only for this experiment.

## Key caveats
n = 6 streams (saturation) and 4 per ablation; Vivobook numpy version unrecorded; V22b pilot sweep logs not on disk; the 1,200 evaluation episodes are episodes of one fixed problem and partly used in pilots (details in `report.md`).