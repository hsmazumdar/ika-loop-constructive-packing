# MGA Expt-2 — Autonomous Discovery of Reusable Operations

Observable test of whether an agent can propose operations, keep useful ones, and reuse them. A run that discovers nothing useful is a valid negative result. This folder does not edit Expt-1.

Create a fresh virtual environment here. Do not reuse `Expt_01_10x10_Packing/.venv`.

```powershell
cd Expt_02_Autonomous_Abstraction
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python tools\generate_tasks.py --config configs\default.json
.\.venv\Scripts\python tools\validate_tasks.py --manifest data\runtime\manifest.json
.\.venv\Scripts\python run_experiment.py --preset tiny
.\.venv\Scripts\python run_experiment.py --preset discovery_smoke --wall-cap-minutes 30
.\.venv\Scripts\python run_experiment.py --resume results\<run_id>
.\.venv\Scripts\python run_gui.py
```

`discovery_smoke` uses seeds 11 and 22, modes `primitive`, `search_only`, `flat_library`, and `hierarchical_library`, 40 training boxes per mode and seed, and 12 frozen evaluation boxes per mode and seed (416 boxes) after the inventory split exists. The 30 minute cap stops between boxes, writes `checkpoint.pkl`, and leaves `complete: false` when the schedule is unfinished. Resume continues that same directory. Partial tables are not a finished comparison.

`memory_sweep` is described in `configs/memory_sweep.json` and is refused by the launcher in this delivery.

`expt2a` loads `configs/expt2a.json`. It does not train. It freezes the baseline flat library and compares four held-out policies. The stopping rule and the hierarchy test are not in that run.

`run_gui.py` opens a manual session. Its memory is not the scientific checkpoint. The panel labelled SIMULATION is the mental board.

See `DESIGN_DECISIONS.md` for the supplied mechanisms and `EXPT02_DEMONSTRATION_REPORT.md` after a run for measured evidence.
