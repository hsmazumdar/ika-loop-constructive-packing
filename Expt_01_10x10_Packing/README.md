# Memory-Guided Assembly — Expt-1: 10×10 Packing

Interactive desktop experiment: one agent sequentially packs a 10×10 box from a 16-piece catalogue (A–P). Short-term memory (STM) is per box; long-term memory (LTM) persists across boxes. Score = occupied cells = 100 − blanks. Every PLACE, UNDO or SUBMIT (including invalid attempts) costs one of 100 actions.

This folder is the working directory for **Expt_01_10x10_Packing**. STM/LTM are a first, deliberately simple memory mechanism. Equal entry counts are not equal byte budgets. A passing test suite proves implementation behaviour, not intelligence.

## Folders

| Path | Contents |
| --- | --- |
| `code/mga/` | Simulation, agent, memory, validator, experiment runner, GUI |
| `configs/` | Published heuristic weights and experiment presets |
| `data/` | Catalogue export and GUI snapshots |
| `results/` | Tests, witnesses, smoke-run CSVs, plots, checkpoints |
| `docs/` | Reviewer Word pack (briefing, methods, result analysis) |

## Windows commands (local venv)

```powershell
cd <REPO_ROOT>\Expt_01_10x10_Packing
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest -q --junitxml=results/tests.xml
.\.venv\Scripts\python validate_catalogue.py --output results/catalogue_validation.json
.\.venv\Scripts\python run_experiment.py --config configs/default.json --preset tiny
.\.venv\Scripts\python run_experiment.py --config configs/default.json --preset smoke
.\.venv\Scripts\python run_gui.py
```

`tiny` is a crash check (4 modes × 1 seed × 5 boxes). `smoke` is the planned 1,560-box run (4 modes × 3 seeds × 100 train + 30 eval).

## GUI

`run_gui.py` opens the instructive desktop app.

- **Manual:** click a catalogue piece, choose 0°/90°/180°/270°, click a board anchor. Green preview is legal; red is rejected atomically. Manual play does not write LTM or experiment metrics.
- **Training:** Start / Pause / Single Step animates the shared heuristic policy. Pause always stops before the next action.
- **New Box** clears the board, stack, STM and action counters; **LTM is kept**.
- **Reset Run** discards learned LTM for the *current* ablation mode only.
- Switching `none` / `stm` / `ltm` / `both` starts an isolated table for that mode.
- Keyboard: Space step, S start, P pause, N new box, R rotate, U undo.
- **Demo launcher:** double-click `Launch_MGA_Expt01_Demo.bat`, or `.\.venv\Scripts\python run_gui.py --demo`

## Ablations

All four modes share observations, legal placements, heuristic, ε=0.15 and the 100-action budget. The board stack is external state, not agent memory.

Dead-end rule (all modes): if no unique legal placement remains (after STM exclusions when enabled), UNDO while the stack is nonempty, otherwise SUBMIT.

## What not to claim

Do not claim that memory improves packing unless the measured smoke summary supports it. Repeated empty 10×10 boxes test practice on the same task; they are not transfer to unseen tasks. Perfect-tiling witnesses validate the catalogue only and are never shown to the agent.
