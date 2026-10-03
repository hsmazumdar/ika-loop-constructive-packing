# RESUME.md - Expt_23 (restart note), rewritten 2026-10-02 11:10 IST
Machine: Vivobook (machineId 1c7a0169-...). Folder: D:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem. Shell starts at C:\. Plan = DESIGN.md (amendments A1-A6 at the bottom are binding).

## What is running right now (check with Get-CimInstance Win32_Process -Filter "Name='python.exe'")
1. Baseline streams: parent python pid 23360 (`set NW=12` then `python src\run_streams.py`; started 23:38 on 1 Oct), 12 workers, one process per job (maxtasksperchild=1). Job count is 102 (not 126 as earlier notes said), of which 11 PPO jobs are dropped by A4 via `results/skip_jobs.txt` (read by `run_streams.job()` when a worker starts a job) -> 91 planned.
   Restart after a crash: `set NW=12` and `python src\run_streams.py` (finished streams are skipped, a cut stream restarts from episode 0; skip list is honoured). NEVER kill by name; only by exact PID.
2. DQN/PPO dev tuning (A6): `python src\tune_dev.py DQN` (pid 8940) and `... PPO` (pid 20316), BelowNormal priority, output `results/tune/tune_DQN.jsonl` / `tune_PPO.jsonl`. dev split only. Safe to kill by PID if it slows the main run; it appends one JSON line per finished config.
3. Watcher pid 21148: `python src\launch_e_when_ready.py`. When no process with 'run_streams' in its command line is left it checks that 91 baseline stream JSONs exist and then starts `run_e_streams.py` (NW=12). Log: `results/launcher_log.txt`. If it died: start the E-streams by hand with the command below.

## E1-E4 streams (not started; start automatically when baselines end)
Manual command: `set NW=12` then `python src\run_e_streams.py` (64 jobs = arms F, R, RN, NM x std,hard capped_nat x 8 seeds 2300-2307 x 20,000 episodes; output `results/e_streams/*.json`, log `results/e_streams_log.txt`; finished streams are skipped on re-run). Afterwards: `python src\analyze_e.py` (writes results/e_summary.md/.csv).
Optional arms (not in the default list): NMs (Adam-step-matched plain), F_nometa, F_nodream, F_noconcepts, data-swap test, few-shot; add by calling `run_e_streams.job_list(arms=(...))`.
Design-file changes since the last note: A4 (job count correction, PPO cut), A5 (compute-matched arm NM, `src/learner_matched.py`, `tests/test_matched.py` 5 passed), A6 (dev tuning). Do not edit `src/learner.py`, `encode.py`, `net.py`, `nn_agents.py`, `variants.py`, `env.py` while baseline workers are starting (workers re-import them at each job start).

## Analysis commands
`python src\analyze_baselines.py` -> results/baseline_summary.md (partial results are fine); `python src\status_counts.py` -> results/status_counts.md (this table).

## Stream counts at 2026-10-02 11:07 IST
Baseline: 59 done / 91 planned after A4 (102 listed, 11 dropped).
### Baseline streams (N, DQN, PPO)

| arm | variant | condition | done | running | not started | dropped (A4) | total |
|---|---|---|---|---|---|---|---|
| N | std | capped_nat | 8 | 0 | 0 | 0 | 8 |
| DQN | std | capped_nat | 8 | 0 | 0 | 0 | 8 |
| PPO | std | capped_nat | 8 | 0 | 0 | 0 | 8 |
| N | hard | capped_nat | 8 | 0 | 0 | 0 | 8 |
| DQN | hard | capped_nat | 8 | 0 | 0 | 0 | 8 |
| PPO | hard | capped_nat | 8 | 0 | 0 | 0 | 8 |
| N | std | capped_any | 6 | 0 | 0 | 0 | 6 |
| DQN | std | capped_any | 4 | 2 | 0 | 0 | 6 |
| PPO | std | capped_any | 1 | 5 | 0 | 0 | 6 |
| N | std | unc_nat | 0 | 2 | 4 | 0 | 6 |
| DQN | std | unc_nat | 0 | 2 | 4 | 0 | 6 |
| PPO | std | unc_nat | 0 | 1 | 0 | 5 | 6 |
| N | std | unc_any | 0 | 0 | 6 | 0 | 6 |
| DQN | std | unc_any | 0 | 0 | 6 | 0 | 6 |
| PPO | std | unc_any | 0 | 0 | 0 | 6 | 6 |
| **all** | | | **59** | 12 | 20 | 11 | **102** |

### E-streams (F, R, RN, NM)

| arm | variant | condition | done | running | not started | dropped (A4) | total |
|---|---|---|---|---|---|---|---|
| F | std | capped_nat | 0 | 0 | 8 | 0 | 8 |
| R | std | capped_nat | 0 | 0 | 8 | 0 | 8 |
| RN | std | capped_nat | 0 | 0 | 8 | 0 | 8 |
| NM | std | capped_nat | 0 | 0 | 8 | 0 | 8 |
| F | hard | capped_nat | 0 | 0 | 8 | 0 | 8 |
| R | hard | capped_nat | 0 | 0 | 8 | 0 | 8 |
| RN | hard | capped_nat | 0 | 0 | 8 | 0 | 8 |
| NM | hard | capped_nat | 0 | 0 | 8 | 0 | 8 |
| **all** | | | **0** | 0 | 64 | 0 | **64** |

## Open items
- Verify that the skip list is honoured by the running parent: look for `'skipped'` lines in `results/streams_stdout.txt` when the unc_nat / unc_any PPO jobs are dequeued. If a PPO unc_nat 2301-2305 or unc_any job has instead STARTED (its `ep 0` line appears in streams_log.txt) kill that single worker by exact PID (find it via CommandLine / start time); it has no progress to lose.
- CS2 / CS3 loop stores and arms are not written yet (environments + tests exist, see tests/test_cs23_envs.py).
## D4 moved to the Vivobook (2026-10-02 20:46 IST) - see DESIGN.md A7-update
- D4 is NOT run on this machine: `results_i9\skip_units.txt` contains `D4` (installed 20:43 IST; `src\diag_i9.py` now has `skipped()`; tested: `run --suites D4` -> "0 of 8 units to run"; a running unit is never touched). The stage-2 command of `scripts\run_diag_i9.ps1` (`--suites D3 D4 D2L`) therefore runs only D3 and D2L. To run D4 here after all, delete the line from skip_units.txt.
- D4 runs on the Vivobook (16 units, std+hard x seeds 2300-2307) into `results_vivo_diag\` there. Merge when done: copy `results_vivo_diag\D4` into `results_i9\D4` (no name clashes) or `python src\diag_i9_analyze.py --root results_i9 results_vivo_diag` (several roots accepted).
- Python/numpy differ: this machine 3.12.4 / 2.0.0, Vivobook 3.13.1 / 2.5.2 (same as the main run).
## A8 controller-off confirmation run (launched 2026-10-03 06:28 IST on i9, 06:29 on i7) - see DESIGN.md A8
- 80 streams = 5 arms (F, R, RN, NM, N; controller OFF) x 2 variants (std, hard; capped_nat) x 8 seeds (2400-2407), 20,000 episodes. Split by whole seed-sets:
  i9Win10 seeds 2400-2405 = 60 streams -> `results_ctrloff_i9\streams`, 10 workers, BelowNormal priority, launcher `scripts\run_ctrloff_i9.ps1`;
  i7Win11B seeds 2406-2407 = 20 streams -> `results_ctrloff_i7\streams`, 7 workers, launcher `scripts\run_ctrloff_i7.ps1`.
- Start / restart (idempotent: finished streams are skipped; unfinished ones restart from scratch): `powershell -File scripts\run_ctrloff_i9.ps1` (i9) or `scripts\run_ctrloff_i7.ps1` (i7).
- Status: `python src\run_ctrloff.py status --out results_ctrloff_i9 results_ctrloff_i7` (counts of the folders present on this PC), `results_ctrloff_*\status.txt`, `log.txt` (per-checkpoint heldout and DONE lines), `manifest.json` (machine and library versions).
- Analysis (merges both folders; sync the other machine's `results_ctrloff_*\streams` first, ~20-60 small json files): `python src\analyze_ctrloff.py --folders results_ctrloff_i9 results_ctrloff_i7` -> `analysis_ctrloff\ctrloff_summary.md/csv`. Tested on relabelled earlier data (reproduces the earlier numbers).
- Do NOT change arms, seeds, checkpoints or tests after launch (A8). BLAS threads are pinned to 1 in run_ctrloff.py (before numpy import).
## A8 update 2026-10-03 09:22 IST - i9 share finished; seeds 2406-2407 re-run on the i9 (see DESIGN.md A8 implementation note)
- `results_ctrloff_i9` (seeds 2400-2405): 60/60 streams DONE at 09:10, no failures (not touched since).
- i7Win11B went offline at ~08:18; its seeds 2406-2407 (`results_ctrloff_i7`) are unavailable. The same protocol for seeds 2406-2407 (20 streams) is running on the i9 -> `results_ctrloff_i9b`, 16 workers, BelowNormal, launched 09:22: `powershell -File scripts\run_ctrloff_i9b.ps1` (restart = same command, idempotent).
- Status: `python src\run_ctrloff.py status --out results_ctrloff_i9 results_ctrloff_i9b --seeds 2400-2407` (expect 80/80 when done).
- Analysis: `python src\analyze_ctrloff.py` (default folders i9, i9b, i7 in this order; a stream present in several folders counts once, later copies are only machine-nuisance replicates, listed in a "Replicate streams" section). Do NOT start the analysis for decisions before 80/80 are present.
- If i7 comes back with finished seeds 2406-2407 streams: copy `results_ctrloff_i7\streams` here (small json files) as replicates only.
## A8 update 2026-10-03 10:1x IST - i7 results arrived; analysis order i9, i7, i9b
- i7Win11B finished its 20 streams (seeds 2406-2407) at 08:35; `results_ctrloff_i7` copied byte-identically here (26 files, 7,898,916 bytes) and verified (see DESIGN.md A8 implementation note 2). The i9b re-run continues (replicate only).
- `analyze_ctrloff.py` default folders now: results_ctrloff_i9 results_ctrloff_i7 results_ctrloff_i9b (i7 is primary for seeds 2406-2407; i9b = machine-nuisance replicate). Run the real analysis ONCE, after i9b is 20/20: `python src\analyze_ctrloff.py`.