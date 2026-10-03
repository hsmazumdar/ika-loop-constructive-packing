# MGA Expt-3 — Mined operation library

Offline mining of reusable placements from teacher solutions of the Expt-2 training inventories, then a frozen comparison on the held-out inventories.

This folder does not modify `Expt_01_10x10_Packing` or `Expt_02_Autonomous_Abstraction`.

The repository on this machine is `D:\PaperSubmissions2026\MGA_Memory_Guided_Assembly`.

```powershell
cd D:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_03_Mined_Operation_Library
python -m venv --system-site-packages .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python tools\verify_inputs.py
.\.venv\Scripts\python tools\build_training_corpus.py --config configs\default.json
.\.venv\Scripts\python tools\mine_libraries.py --config configs\default.json
.\.venv\Scripts\python run_experiment.py --preset tiny
.\.venv\Scripts\python run_experiment.py --preset discovery_smoke --wall-cap-minutes 30
.\.venv\Scripts\python run_experiment.py --resume results\<run_id>
.\.venv\Scripts\python run_gui.py --replay results\<run_id>\replay_transfer.json --snapshot results\<run_id>\gui_replay.png
```

`tiny` solves two training inventories, mines them, and evaluates one held-out inventory at library sizes 0 and 2. `discovery_smoke` uses the 24 training inventories, seeds 11, 22 and 33, the 12 held-out inventories, and library sizes 0, 10, 20, and the actual corpus size when 40 is not available. The wall cap stops between episodes and leaves a checkpoint.

The virtual environment is created with access to the machine PyTorch so the RTX 5060 Ti is visible. `configs/default.json` sets `"device": "cuda"`.

See `DESIGN_DECISIONS.md` for supplied mechanisms and `EXPT03_REPORT.md` after a run for measured results.
