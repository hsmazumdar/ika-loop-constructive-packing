# RESUME_vivo_diag

D4 on the Vivobook (started 2026-10-02 20:46 IST) - see DESIGN.md A7-update
- Command: `powershell -File scripts\run_diag_vivo.ps1` (= `python src\diag_i9.py run --suites D4 --nw 14 --seed0 2300 --n-seeds 8 --out results_vivo_diag`), std + hard x seeds 2300-2307 = 16 units, 20,000 episodes each. Log: `results_vivo_diag\diag_log.txt`, `run_log.txt`; results `results_vivo_diag\D4\*.json|csv`; per-unit status: `python src\diag_i9.py status --out results_vivo_diag`.
- Restart after an interruption: run the same command again (finished units are skipped, unfinished units restart from scratch).
- D4 is NOT run on the i9 (`results_i9\skip_units.txt` contains `D4`; honoured by diag_i9.py).
- Merge for analysis: `python src\diag_i9_analyze.py --root results_i9 results_vivo_diag` (accepts several roots; outputs written next to the first), or copy `results_vivo_diag\D4` to `results_i9\D4` (no name clashes).
- Do not start D1/D2/D3/D2L here; those run on the i9.