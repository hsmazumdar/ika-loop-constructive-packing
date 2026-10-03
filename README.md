# Constructive packing with memory: reviewer repository

Standalone reviewer repository for the packing line of experiments (Expt-1 to Expt-22e). It contains the experiment code, unit tests, the saved runs, and the supplementary tables and figures.

The manuscript is not included.

Two studies share this repository:

| Part | Experiments | Question |
| --- | --- | --- |
| A | `Expt_01` to `Expt_19` | When does memory reduce deliberation? (effort saving from stored arrangements, exact recall, gates, recognizers) |
| B | `Expt_20` to `Expt_22e` | Continuous learning and memory consolidation for constructive packing (one box at a time, sleep consolidation, learned value function, under a 14-piece handicap) |

## Read this first

1. [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md): what was measured, what was not, and which run is authoritative, for both parts.
2. Part A: [supplementary/SUPPLEMENTARY_TABLES.md](supplementary/SUPPLEMENTARY_TABLES.md) (Word: `supplementary/SUPPLEMENTARY_TABLES.docx`) and [supplementary/SUPPLEMENTARY_FIGURES.pdf](supplementary/SUPPLEMENTARY_FIGURES.pdf).
3. Part B: [Expt_22e_Closure_Analyses/results/20261001_122457_run/report.md](Expt_22e_Closure_Analyses/results/20261001_122457_run/report.md) (paired statistics, multiplicity control, piece-P usage, baseline audit, evaluation-set description, provenance), and the `summary.md` of each authoritative run listed in the guide.

Double-click **`run_reviewer.bat`** for a menu. It opens the guide and the supplementary documents, runs unit tests, and can open the Expt-1 packing window. It does not start a new diagnostic or a new learning stream.

## Launchers

| File | What it does |
| --- | --- |
| `run_reviewer.bat` | Menu |
| `open_tables.bat` | Opens `supplementary/SUPPLEMENTARY_TABLES.docx` |
| `open_figures.bat` | Opens `supplementary/SUPPLEMENTARY_FIGURES.pdf` |
| `run_unit_tests.bat` | Pytest for Expt-1 through Expt-22d. No new scientific run. Part B suites take several minutes |
| `run_expt01_demo.bat` | Opens the Expt-1 packing window |

Smoke, diagnostic and stream commands write a new results folder. They are not on the menu. A new smoke or a rerun is not a replacement for the runs named in `REVIEWER_GUIDE.md`.

## Environment

Windows. From this folder:

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

The experiments need `numpy`, `pandas`, `matplotlib`, `scipy` and `pytest`. The launchers use `.venv\Scripts\python.exe` in this folder. Part B runs were produced with Python 3.13.1; library versions per run are in each run's `manifest.json`. Set `OMP_NUM_THREADS=1` (and `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`) before starting a multi-worker Part B run; the run scripts pin BLAS threads themselves.

All code locates sibling experiments by relative path (Part B imports the Expt-1 `mga` package from `Expt_01_10x10_Packing/code`), so the repository can sit on any drive. A few historical launch records (`Expt_22a.../results/_launch_main.bat`, `Expt_22d.../launch_main.bat`, `launch_resume.bat`, `Expt_22e.../code/launch_one.bat`) contain the drive letter of the machine that ran them; edit the `cd /d` line before reusing them.

## What a passing test means

A passing unit test means the checked function behaved as coded. It does not mean memory reduced deliberation or that the learner improved, and it does not replace the saved runs.
