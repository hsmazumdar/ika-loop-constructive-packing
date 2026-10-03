# RESUME_i9.md - diagnostics on the i9Win10 (DESIGN.md A7: post-hoc, descriptive)
Machine: i9Win10 (machineId 4cb97ccc-d910-4d0c-8eae-51a8b9978f2e), Intel Core i9-10900K 3.7 GHz, 10 cores / 20 threads, 31.9 GB RAM, Python 3.12.4, numpy 2.0.0, scipy 1.13.1, torch 2.9.0+cpu (not used).
Project folder on this machine: F:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem (external SSD, drive letter F: on 2 Oct 2026).
Launched 2026-10-02 19:07 IST: powershell scripts\run_diag_i9.ps1 (pid 9380) -> python src\diag_i9.py run --suites D1 D2 --nw 8, then --suites D3 D4 D2L --nw 8. Python parent pid (D1/D2 stage) 7692. 8 workers = 10 cores - 2.
Units: D1 8, D2 8 (stage 1: 16 units); D3 8, D4 8, D2L 8 (stage 2: 24 units).
Smoke/timing before the start: tests\test_diag_i9.py 5 passed (18 s); 230 training episodes 0.103 s/episode; one standard evaluation pass 35 s.
Restart rule: run scripts\run_diag_i9.ps1 again (finished units are skipped; a cut unit restarts from episode 0). See START_ON_i9Win10.md sections 6-8.
Log of checks:
- 2026-10-02 19:09 first checkpoints written, all 8 D1 workers running, no errors.
## D4 moved to the Vivobook (2026-10-02 20:46 IST) - see DESIGN.md A7-update
- D4 is NOT run on this machine: `results_i9\skip_units.txt` contains `D4` (installed 20:43 IST; `src\diag_i9.py` now has `skipped()`; tested: `run --suites D4` -> "0 of 8 units to run"; a running unit is never touched). The stage-2 command of `scripts\run_diag_i9.ps1` (`--suites D3 D4 D2L`) therefore runs only D3 and D2L. To run D4 here after all, delete the line from skip_units.txt.
- D4 runs on the Vivobook (16 units, std+hard x seeds 2300-2307) into `results_vivo_diag\` there. Merge when done: copy `results_vivo_diag\D4` into `results_i9\D4` (no name clashes) or `python src\diag_i9_analyze.py --root results_i9 results_vivo_diag` (several roots accepted).
- Python/numpy differ: this machine 3.12.4 / 2.0.0, Vivobook 3.13.1 / 2.5.2 (same as the main run).