# Constructive packing with memory: reviewer repository

Standalone reviewer repository for the packing line of experiments (Expt-1 to Expt-23). It contains the experiment code, unit tests, the saved runs, and the supplementary tables and figures.

The manuscript (V2: docx, markdown, figures) is in [`_Manuscript/`](_Manuscript/).

Three studies (plus the manuscript folder) share this repository:

| Part | Experiments | Question |
| --- | --- | --- |
| A | `Expt_01` to `Expt_19` | When does memory reduce deliberation? (effort saving from stored arrangements, exact recall, gates, recognizers) |
| B | `Expt_20` to `Expt_22e` | Continuous learning and memory consolidation for constructive packing (one box at a time, sleep consolidation, learned value function, under a 14-piece handicap) |
| C | `Expt_23_MultiProblem` | Multi-problem packing case study of the information -> knowledge -> application loop. Controller-on main run: negative. Post-hoc diagnostics D1-D4. Controller-off confirmation A8 (seeds 2400-2407, 80 streams, standard and hard): confirmed; guided vs random data and consolidation vs plain / compute-matched. Baselines DQN, PPO, hand rule |
| M | `_Manuscript` | Manuscript V2 for Part C (docx, md, figures) |

## Read this first

1. [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md): what was measured, what was not, and which run is authoritative, for all parts.
2. Part A: [supplementary/SUPPLEMENTARY_TABLES.md](supplementary/SUPPLEMENTARY_TABLES.md) (Word: `supplementary/SUPPLEMENTARY_TABLES.docx`) and [supplementary/SUPPLEMENTARY_FIGURES.pdf](supplementary/SUPPLEMENTARY_FIGURES.pdf).
3. Part B: [Expt_22e_Closure_Analyses/results/20261001_122457_run/report.md](Expt_22e_Closure_Analyses/results/20261001_122457_run/report.md) (paired statistics, multiplicity control, piece-P usage, baseline audit, evaluation-set description, provenance), and the `summary.md` of each authoritative run listed in the guide.
4. Part C: [Expt_23_MultiProblem/analysis_ctrloff/ctrloff_summary.md](Expt_23_MultiProblem/analysis_ctrloff/ctrloff_summary.md) (A8 controller-off confirmation, 80 streams, standard and hard variants, verdict: confirmed), [Expt_23_MultiProblem/DESIGN.md](Expt_23_MultiProblem/DESIGN.md), and the Part C section of the guide (what Expt-23 is, order of evidence, how to run the tests and re-analyse or rerun A8, where the results are, primary versus replicate data).
5. Manuscript: [_Manuscript/Continuous_Learning_Memory_Consolidation_V2.docx](_Manuscript/Continuous_Learning_Memory_Consolidation_V2.docx) (same text in `.md`; figures in `_Manuscript/figures_v2/`; number provenance in `_Manuscript/V2_SOURCES_AND_CHANGES.md`).

Double-click **`run_reviewer.bat`** for a menu. It opens the guide and the supplementary documents, runs unit tests, and can open the Expt-1 packing window. It does not start a new diagnostic or a new learning stream.

## Launchers

| File | What it does |
| --- | --- |
| `run_reviewer.bat` | Menu |
| `open_tables.bat` | Opens `supplementary/SUPPLEMENTARY_TABLES.docx` |
| `open_figures.bat` | Opens `supplementary/SUPPLEMENTARY_FIGURES.pdf` |
| `run_unit_tests.bat` | Pytest for Expt-1 through Expt-22d and Expt-23 (34 tests), then a read-only re-analysis of the saved A8 streams that must reproduce `analysis_ctrloff/` byte for byte. No new scientific run. Part B and Part C suites take several minutes |
| `run_expt01_demo.bat` | Opens the Expt-1 packing window |

Smoke, diagnostic and stream commands write a new results folder. They are not on the menu. A new smoke or a rerun is not a replacement for the runs named in `REVIEWER_GUIDE.md`.

## Environment

Windows. From this folder:

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

The experiments need `numpy`, `pandas`, `matplotlib`, `scipy` and `pytest`. The launchers use `.venv\Scripts\python.exe` in this folder. Part B runs were produced with Python 3.13.1; Part C (Expt-23) streams were produced on Python 3.12.x (i9: 3.12.4 / numpy 2.0.0 for seeds 2400-2405; i7: 3.12.10 / numpy 2.4.6 for seeds 2406-2407; the i7 streams are primary for those seeds, `results_ctrloff_i9b` is a replicate only). Library versions per run are in each run's `manifest.json` where present. Set `OMP_NUM_THREADS=1` (and `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`) before starting a multi-worker Part B or Part C run; the run scripts pin BLAS threads themselves.

All code locates sibling experiments by relative path (Part B imports the Expt-1 `mga` package from `Expt_01_10x10_Packing/code`), so the repository can sit on any drive. A few historical launch records (`Expt_22a.../results/_launch_main.bat`, `Expt_22d.../launch_main.bat`, `launch_resume.bat`, `Expt_22e.../code/launch_one.bat`) contain the drive letter of the machine that ran them; edit the `cd /d` line before reusing them.

## What a passing test means

A passing unit test means the checked function behaved as coded. It does not mean memory reduced deliberation or that the learner improved, and it does not replace the saved runs.
