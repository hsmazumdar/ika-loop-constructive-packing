# NIGHT_LOG.md — Expt_23 MultiProblem baselines
Overnight babysit entries (IST). Stay quiet unless a problem needs Himanshu.

## 2026-10-02 00:36 IST — hourly check (healthy)
- Parent `python src\run_streams.py` PID **23360** alive (started 2026-10-01 23:31:42); 12 worker children burning CPU (~55 min CPU each).
- Progress via `results\streams_log.txt` (last write 00:17:59): first wave is `std capped_nat` seeds 2300–2303 for N/DQN/PPO.
  - N @ ep 10000 (~0.77 S1/free, ~43 min); DQN @ ep 5000 (~0.72); PPO @ ep 2000 (~0.77). Next CKPTS 10000/20000 — gap since last log line is expected (between checkpoints).
- Finished stream JSONs: **0 / 102** (48×20k + 54×10k). No failures in log. stdout/stderr empty (normal; log goes to streams_log).
- CEM + refs already DONE per RESUME.md. Design rules untouched. No restart needed.


## 2026-10-02 01:32 IST - hourly check (healthy)
- Parent `python src\run_streams.py` PID **23360** alive (started 2026-10-01 23:31:42); 12 worker children.
- `results\streams_log.txt` last write 01:31:15; advancing. Finished stream JSONs: **4 / 126** (N std capped_nat s2300-2303 DONE). Second wave: N/DQN/PPO std capped_nat s2304-2305 mid-stream (N @ ep 5000 ~0.75; DQN @ ep 2000; PPO @ ep 1000). First-wave DQN at ep 10000 (~0.75).
- No failures. Design rules untouched. No restart needed.

## 2026-10-02 02:34 IST - hourly check (healthy)
- Parent python src/run_streams.py PID **23360** alive (started 2026-10-01 23:31:42); 12 worker children (13 python total).
- results/streams_log.txt last write 02:34; advancing. Finished stream JSONs: **5 / 126** (N std capped_nat s2300-2304 DONE; s2304 just finished 5762s). Second wave mid-stream: N s2305 @ ep 10000 (~0.76); DQN s2304 @ ep 5000 (~0.72); PPO first-wave at ep 10000 (~0.80) and s2304 @ ep 5000 (~0.77).
- No failures. Design rules untouched. No restart needed.

## 2026-10-02 03:39 IST - hourly check (healthy)
- Parent `python src\run_streams.py` PID **23360** alive (started 2026-10-01 23:31:42); 12 worker children (13 python total).
- `results\streams_log.txt` last write 03:33:58; advancing. Finished stream JSONs: **10 / 126** (N std capped_nat s2300-2305 DONE; DQN std capped_nat s2300-2303 DONE). Mid-stream: N s2306/s2307 @ ep 10000 (~0.77); DQN s2304 @ ep 10000 (~0.75), s2305/s2306 @ ep 5000 (~0.73); PPO s2304 @ ep 10000 (~0.78), s2305/s2306 @ ep 2000 (~0.76).
- No failures. Design rules untouched. No restart needed.

## 2026-10-02 04:38 IST - hourly check (healthy)
- Parent `python src\run_streams.py` PID **23360** alive (started 2026-10-01 23:31:42); 12 worker children (13 python total).
- `results\streams_log.txt` last write 04:37:13; advancing. Finished stream JSONs: **15 / 126** (N std capped_nat s2300-2307 DONE; DQN std capped_nat s2300-2304 DONE; PPO std capped_nat s2302 DONE; N hard capped_nat s2300 DONE). Mid-stream: DQN std s2305/s2306/s2307; PPO std s2304-s2307; hard wave started (DQN/PPO hard s2300).
- No failures. Design rules untouched. No restart needed.

## 2026-10-02 05:33 IST - hourly check (healthy)
- Parent `python src\run_streams.py` PID **23360** alive (started 2026-10-01 23:31:42); 12 worker children (13 python total).
- `results\streams_log.txt` last write 05:30:05; advancing. Finished stream JSONs: **17 / 126** (N std capped_nat s2300-2307 DONE; DQN std capped_nat s2300-2306 DONE; PPO std capped_nat s2302 DONE; N hard capped_nat s2300 DONE). Mid-stream: DQN std s2307 @ ep 10000 (~0.75); PPO std s2305/s2306 @ ep 10000 (~0.80), s2307 @ ep 5000 (~0.78); hard wave: N s2301 mid, DQN s2300 @ ep 10000 (~0.69) / s2301 early, PPO s2300 @ ep 10000 (~0.75).
- No failures. Design rules untouched. No restart needed.


## 2026-10-02 06:40 IST — final morning check (healthy; overnight babysit ending)
- Parent python src\run_streams.py PID **23360** alive (started 2026-10-01 23:31:42); 12 worker children (13 python total).
- 
esults\streams_log.txt last write 06:40:10; advancing. Finished stream JSONs: **22 / 126**.
  - Done: N std capped_nat x8; DQN std capped_nat x8; PPO std capped_nat s2302; N hard capped_nat s2300–s2302; DQN hard capped_nat s2300; PPO hard capped_nat s2300.
  - Mid-stream: remaining PPO std capped_nat mostly @ ep 10000 (~0.80); hard wave N/DQN/PPO advancing.
- Partial nalyze_baselines.py: std capped_nat N 0.879 (n=8) vs DQN 0.825 (n=8) vs hand ref 0.931; hard capped_nat N 0.857 (n=3) vs hand 0.888. No failures.
- Design rules untouched. No restart needed. Overnight babysit routine will pause after this report; streams keep running on Vivobook.

2026-10-02 20:47 IST (i9): D4 skipped here via results_i9\skip_units.txt; runs on the Vivobook (A7-update). i9 state: D1 8/8, D2 4/8 running, then D3 + D2L.
2026-10-03 06:31 IST (i9): A8 written in DESIGN.md, then launched: i9 seeds 2400-2405 (60 streams, 10 workers, BelowNormal) 06:28; i7 seeds 2406-2407 (20 streams, 7 workers) 06:29. i7 validated: 246/144/55 files, tests 34 passed via stand-in runner (pytest not installed, nothing installed).
2026-10-03 09:25 IST (i9): A8 i9 share 60/60 done 09:10. i7 offline since ~08:18 -> seeds 2406-2407 launched on i9 into results_ctrloff_i9b (16 workers, BelowNormal) 09:22; analyze_ctrloff.py updated (dedupe + replicate section, tested); DESIGN.md A8 implementation note added.
2026-10-03 10:12 IST (i9): i7 results (20/20, finished 08:35) copied to i9 and verified; analyze_ctrloff.py default order set to i9, i7, i9b (tested on scratch copies, deleted); i9b continues as replicate; real analysis NOT run; DESIGN.md A8 implementation note 2 added (incl. disclosure of the scratch-test printout).