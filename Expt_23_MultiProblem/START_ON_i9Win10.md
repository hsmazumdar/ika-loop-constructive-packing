# START_ON_i9Win10.md - run the post-hoc diagnostics (DESIGN.md A7) on the i9Win10
Written 2026-10-02 evening IST. Master copy of the project: Vivobook `D:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem`. This note exists in `Expt_23_MultiProblem\` and one level up (`Assembly_Skill_Learning\`).
Status when written: the diagnostics were started on the i9Win10 at 19:07 IST from the external-SSD copy (mounted as F:), with 8 workers. If you are reading this in a fresh session, FIRST check whether they are still running (step 6) before starting anything.

## What the diagnostics are (post-hoc, NOT pre-registered; see DESIGN.md A7)
Why: in the main E-streams the full learner F (0.841 on std) did not beat the plain N (0.879) or the compute-matched NM (0.869), and F's meta-controller left tau near 1.0. D1-D4 look for the reason. Report them only as "post-hoc diagnostics".
| id | what | units | est. time per unit (i9, 1 core) |
|---|---|---|---|
| D1 | F retrained (saved models do not exist), evaluates FAST net and SLOW net, tau 0.05-1.0, with/without concept column; saves models | 8 (std,hard x seeds 2300-2303) | std about 80 min, hard about 50 min |
| D2 | F with width 64 (22d-like), std | 8 (seeds 2300-2307) | about 70 min |
| D3 | sleep interval pinned 200 vs 1000, std | 8 (2 arms x 4 seeds) | about 60 min |
| D4 | F_nometa (meta off, annealed tau/eps), std,hard | 8 | about 50 min |
| D2L | port check on the legacy 10x10 A-P problem (22d task), F and F_w64 | 8 (2 arms x 4 seeds) | about 40 min |
Timing basis (measured on the i9, idle): 0.103 s per training episode early in training, standard evaluation pass (600 rollouts) 35 s. 8 workers in parallel: D1+D2 about 2.5-3 h, then D3+D4+D2L about 2.5 h.

## 1. Find the project (the drive letter changes)
```
Get-PSDrive -PSProvider FileSystem
Get-ChildItem -Path F:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem   # try every drive letter shown; it was F: on 2 Oct (E: on the Vivobook)
```
Pick the letter where `...\Assembly_Skill_Learning\Expt_23_MultiProblem\src\diag_i9.py` exists and set it below (`$P`). Work directly on the SSD (results_i9 is then ready to carry back), or copy the folder to a local disk with
`robocopy "<drive>:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem" "C:\Work\Expt_23_MultiProblem" /E` and copy `results_i9` back at the end.
The folder must contain: `src\` (45+ files incl. diag_i9.py, run_e_streams.py, learner_full.py), `tests\`, `results\` (refs\ 36 CSVs are REQUIRED; e_streams\ 62 of 64 main-run JSONs - NM hard s2306, s2307 are missing in the copy and not needed), `scripts\run_diag_i9.ps1`. The 22d code is next door in `..\Expt_22d_Long_Ablations_Saturation\` (reference only). NOTE: no model files exist in `results\` (the main run did not save models), hence D1 retrains.

## 2. Check Python / numpy / scipy (torch is NOT needed for the diagnostics)
```
python --version ; python -c "import numpy, scipy; print(numpy.__version__, scipy.__version__)"
python -c "import torch; print(torch.__version__)"
```
Vivobook (main run): Python 3.13.1, numpy 2.5.2, scipy 1.18.1, torch 2.14.1+cpu. i9 on 2 Oct: Python 3.12.4, numpy 2.0.0, scipy 1.13.1, torch 2.9.0+cpu. Torch is only used by DQN/PPO (`nn_agents.py`), not by D1-D4. If you really need it: `pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu` (check that this exact version exists for the i9 Python; otherwise keep the installed one and write the version into results_i9\RESUME_i9.md). Different numpy versions can change random streams, which is why D1 contains a reproduction check against the main run.

## 3. Set workers = physical cores - 2
```
$P = "F:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem"
Set-Location $P
$NW = (Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum - 2     # i9-10900K: 10 cores -> 8
```
Every worker is single-threaded (OMP/MKL threads are forced to 1 in the scripts). One unit = one process = one stream.

## 4. Tests (about 20 s, one core) - run before a fresh start
```
python -m pytest tests\test_diag_i9.py -q -p no:cacheprovider
```
(5 tests: unit lists, extra-evaluation profile, tiny D1 unit incl. model save + exact re-evaluation of a saved model, width 64 + pinned sleep interval, legacy problem.)

## 5. Start (exact commands)
Everything in two stages (D1+D2 first, then D3, D4, D2L), in the background, logs in results_i9\:
```
New-Item -ItemType Directory -Force "$P\results_i9" | Out-Null
Start-Process powershell -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","$P\scripts\run_diag_i9.ps1" -WorkingDirectory $P -WindowStyle Hidden -RedirectStandardOutput "$P\results_i9\stdout.txt" -RedirectStandardError "$P\results_i9\stderr.txt"
```
Or a single suite by hand: `python src\diag_i9.py run --suites D1 D2 --nw $NW` (add `--n-seeds 2` for fewer seeds, `--n-ep 5000` for a shorter budget; both change the units, so use a different `--out` folder for such experiments).
Output: `results_i9\<suite>\<suite>_<arm>_<variant>_capped_nat_s<seed>.json` (full raw arrays: standard evaluation, all extra evaluations, hyper-parameters at each checkpoint, repro check) and `.csv` (one row per checkpoint x net x tau x concepts x split: mean S1, S1/free, S1/ref), `results_i9\models\*.npz` (fast and slow weights + concept library; D1 at every checkpoint, others at the end), `results_i9\diag_log.txt` (progress), `results_i9\run_log.txt` (launch lines), `stdout.txt`, `stderr.txt`.

## 6. Monitor
```
python src\diag_i9.py status                       # done/total per suite
Get-Content results_i9\diag_log.txt -Tail 15
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select ProcessId,CreationDate,CommandLine
python src\diag_i9_analyze.py                      # descriptive summary -> results_i9\diag_summary.md and diag_all.csv (works on partial results)
```
Re-evaluate a saved model (e.g. fast vs slow net at other tau): `python src\diag_i9.py reeval --model results_i9\models\D1_F_std_capped_nat_s2300_ck20000.npz --variant std --seed 2300 --taus 0.1 0.25 0.5 --noconc --save results_i9\reeval_s2300.json`

## 7. RESUME RESTART RULE
- Everything is restartable by running the same command again: a unit whose JSON exists is skipped; a unit that was cut restarts from episode 0 (no mid-stream resume; at most about 80 min are lost per cut unit). A leftover `*.json.tmp` is harmless (delete it).
- NEVER delete or edit anything in `results\` (Vivobook main-run results), never edit `src\` files other than adding new ones, never run two launchers at once (check step 6 first; kill only by exact PID).
- Keep `results_i9\RESUME_i9.md` current: what was launched (command, NW, start time, machine specs), what is done (`status`), problems. Append a line after each check.
- If a unit fails ("FAILED" in diag_log.txt with a traceback): do not change the design; record it in RESUME_i9.md and continue with the remaining units (a failed unit has no JSON and is retried by the next start).
- Interpret results only as POST-HOC DIAGNOSTICS (DESIGN.md A7): descriptive, no p-values, no "supported" labels.

## 8. Merge results_i9 back into the Vivobook master (no name collisions: new folder, unit-named files)
On the Vivobook (or from the i9 via a share), with the SSD mounted as X: (check the letter):
```
robocopy "X:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem\results_i9" "D:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem\results_i9" /E /XO
robocopy "X:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem" "D:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem" DESIGN.md RESUME.md NIGHT_LOG.md START_ON_i9Win10.md /XO
robocopy "X:\...\Expt_23_MultiProblem\src" "D:\...\Expt_23_MultiProblem\src" diag_i9.py diag_i9_analyze.py /XO
cd D:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem
python src\diag_i9_analyze.py            # rebuilds diag_all.csv / diag_summary.md from the merged units
```
`/XO` never overwrites a newer file. Each unit's JSON/CSV is self-contained (arm, variant, seed, checkpoint, net, tau, split), so merged tables can simply be concatenated.

## 9. Known open items
- A6 result (A6-result in DESIGN.md): PPO with 8 episodes per update beat the default on dev (+0.029); the tuned arm PPOt (std,hard x 4 seeds) is NOT yet run. DQN default stays.
- NM hard seeds 2306, 2307 exist only on the Vivobook.
## D4 moved to the Vivobook (2026-10-02 20:46 IST) - see DESIGN.md A7-update
- D4 is NOT run on this machine: `results_i9\skip_units.txt` contains `D4` (installed 20:43 IST; `src\diag_i9.py` now has `skipped()`; tested: `run --suites D4` -> "0 of 8 units to run"; a running unit is never touched). The stage-2 command of `scripts\run_diag_i9.ps1` (`--suites D3 D4 D2L`) therefore runs only D3 and D2L. To run D4 here after all, delete the line from skip_units.txt.
- D4 runs on the Vivobook (16 units, std+hard x seeds 2300-2307) into `results_vivo_diag\` there. Merge when done: copy `results_vivo_diag\D4` into `results_i9\D4` (no name clashes) or `python src\diag_i9_analyze.py --root results_i9 results_vivo_diag` (several roots accepted).
- Python/numpy differ: this machine 3.12.4 / 2.0.0, Vivobook 3.13.1 / 2.5.2 (same as the main run).