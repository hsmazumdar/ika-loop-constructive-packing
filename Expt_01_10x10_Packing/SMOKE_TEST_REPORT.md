# SMOKE_TEST_REPORT — MGA Expt-1: 10×10 Packing

Two complete 1,560-box smokes were run overnight. They are **not** mixed below.

1. **Official snapshot** (original shared heuristic, the planned experiment): `results/20260928_171840_smoke`
2. **Improved shared heuristic** (hole-free preference, size-6 unfillable regions, one-step undo tabu — all modes): `results/20260928_180809_smoke`

`results/LATEST_RUN.txt` currently points at run 2. GUI/`configs/default.json` now use the improved shared policy.

## Commands (Windows, local venv)

```powershell
cd E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_01_10x10_Packing
.\.venv\Scripts\python -m pytest -q --junitxml=results/tests.xml
.\.venv\Scripts\python validate_catalogue.py --output results/catalogue_validation.json
.\.venv\Scripts\python run_experiment.py --config configs/default.json --preset tiny
.\.venv\Scripts\python run_experiment.py --config configs/default.json --preset smoke
.\.venv\Scripts\python run_gui.py
```

Interpreter: `.venv` Python 3.13.1 on Windows 11; numpy 2.5.3, pandas 3.0.6, matplotlib 3.11.2, pytest 9.1.1.

Launch GUI: `.\.venv\Scripts\python run_gui.py`

## Tests

**34 passed** in 11.30 s. Files: `results/test_results.txt`, `results/tests.xml`, `results/test_results.xml`.

A passing suite proves implementation behaviour, not intelligence.

## Catalogue validation

- `results/catalogue_validation.json` — status **SOLVED**, 4 distinct witnesses (2 requested), 0.045 s
- Replay through the environment API succeeded
- Catalogue hash `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Witnesses were never shown to the agent

## Tiny crash check

`results/20260928_171100_tiny` — 4 modes × 1 seed × 5 boxes, no crash.

---

## Official smoke (run 1) — complete 1,560 boxes

Folder: `results/20260928_171840_smoke`  
Wall ~47 min. Copies at `results/episodes.csv`, `results/summary.csv`, `results/learning_curves.png`, `results/evaluation_scores.png`, `results/populated_canvas.png`, `results/action_trace.jsonl`.

### Evaluation (90 boxes/mode, 3 seeds)

| mode | mean terminal score | seed std | perfect fraction | mean undos | LTM hit fraction | mean LTM bytes | perfect / 1000 actions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| none | **88.29** | 0.49 | 0.000 | 42.90 | 0 | 0 | 0 |
| ltm | 87.28 | 1.46 | 0.000 | 42.92 | 0.033 | 89,397 | 0 |
| stm | 87.17 | 0.88 | 0.000 | 42.93 | 0 | 0 | 0 |
| both | 86.51 | 0.95 | 0.000 | 43.01 | 0.032 | 256,529 | 0 |

Per-seed eval means: none 88.53 / 87.60 / 88.73; stm 86.30 / 88.37 / 86.83; ltm 86.17 / 89.33 / 86.33; both 87.57 / 86.70 / 85.27.

LTM **was** reused (~3.2% hit rate, nonempty tables) but did **not** beat `none`.

**Verdict (run 1): no detectable improvement from memory.** Highest mean is `none`. Gaps are 1–2 cells. Three seeds are a smoke check, not significance. Negative result retained.

---

## Improved shared-heuristic smoke (run 2) — complete 1,560 boxes

Folder: `results/20260928_180809_smoke`  
Wall 2276 s (~38 min). Plots: `results/improved_learning_curves.png`, `results/improved_evaluation_scores.png`, `results/improved_summary.csv`.

Shared changes (all four modes, not a one-mode tune):

- Prefer placements that do not create unfillable empty components (sizes 1, 2, 3, **and 6**)
- After a dead-end UNDO, do not immediately replay that same placement (one-step tabu, not STM)

### Evaluation (90 boxes/mode, 3 seeds)

| mode | mean terminal score | seed std | perfect fraction | mean undos | LTM hit fraction | mean LTM bytes | perfect / 1000 actions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ltm | **91.37** | 0.78 | 0.011 | 41.67 | 0.029 | 100,374 | 0.114 |
| both | 91.00 | 1.06 | 0.044 | 40.90 | 0.033 | 272,535 | 0.468 |
| none | 90.96 | 0.66 | 0.011 | 41.88 | 0 | 0 | 0.114 |
| stm | 90.39 | 0.07 | 0.033 | 40.92 | 0 | 0 | 0.364 |

All modes rose by about **3 occupied cells** versus run 1. Mode means now differ by **less than 1 cell**. Perfect boxes appeared (especially `both` eval 4.4%). LTM hit fraction remains ~3%.

**Verdict (run 2): still no detectable memory advantage.** `ltm` is 0.4 cells above `none`. The packing gain is from the **shared** heuristic, not from STM/LTM. Do not claim BOTH must win.

---

## GUI

- Tkinter available (1600×1000). `run_gui.py` launches the instructive desktop app.
- Controls: Start / Pause / Single Step / New Box (keeps LTM) / Reset Run (clears this mode’s LTM) / Undo / Submit / Save Snapshot / mode / seed / speed.
- Manual PLACE shows green/red preview. Manual episodes do not train LTM.
- Programmatic callback check: `tests/gui_control_check.py` → `data/snapshots/gui_control_check.png`.
- Overnight babysitting did **not** include a human clicking every widget.
- Keys: Space step, S start, P pause, N new box, R rotate, U undo.

## Fixes made while babysitting

1. Frozen-eval false positive (`config_hash` written after the freeze snapshot) — fixed; official smoke then completed 1,560/1,560.
2. Incremental `episodes.csv` every 10 boxes.
3. Shared hole-avoidance + undo tabu after run 1 (used only in run 2 and the GUI).
4. LTM dump byte cache; progress logs.

## Remaining defect

~41 undos per box remain: after the board blocks, the 100-action budget is spent on recovery. That is inefficient sequential behaviour even when occupancy is ~91. Future experiments (quotas, harder boards) should not treat this occupancy as “solved packing skill.”

## Limitations

- Same empty 10×10 and same catalogue: practice, not transfer.
- Heuristic is engineered, not learned intelligence.
- Three seeds ≠ statistical significance.
- Equal LTM entry caps are not equal byte budgets.
