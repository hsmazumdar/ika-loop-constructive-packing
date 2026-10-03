# Expt-22d PARTIAL SUMMARY - STOPPED EARLY ~07:09 IST (manual stop, SSD removal). NOT FINAL.

Run `20261001_060654_main` (started 06:07 IST). All workers + parent (PID 20564) were stopped by exact PID at 07:08:58 IST. Held-out = frozen memory, 1,200 fresh boxes (same as 22b/22c). Targets: full 60,000 boxes (6 streams), ablations 32,000 boxes (4 streams each). Reference: Expt-22c full at 32k = 88.28 (87.49-88.95, n=12); V21 final 83.70; hand rule 89.61 (ref only).

DONE = stream reached its target and has a final pickle in `streams/`; CUT = stopped before its target; the last saved held-out checkpoint is shown (checkpoints at 0,500,1k,2k,3k,5k,7.5k,10k,15k,20k,24k,28k,32k,...).

| condition | seed | last held-out checkpoint (boxes) | S1 | status |
|---|---|---|---|---|
| full | 300 | 28000 | 87.56 | CUT (target 60000) |
| full | 301 | 36000 | 91.58 | CUT (target 60000) |
| full | 302 | 32000 | 87.24 | CUT (target 60000) |
| full | 303 | 20000 | 85.81 | CUT (target 60000) |
| full | 304 | 28000 | 85.96 | CUT (target 60000) |
| full | 305 | 20000 | 84.67 | CUT (target 60000) |
| no_meta | 200 | 32000 | 86.61 | DONE (32000) |
| no_meta | 201 | 32000 | 88.19 | DONE (32000) |
| no_meta | 202 | 32000 | 88.94 | DONE (32000) |
| no_meta | 203 | 32000 | 86.97 | CUT (target 32000) |
| no_meta_matched_floor | 200 | 32000 | 87.34 | CUT (target 32000) |
| no_meta_matched_floor | 201 | 32000 | 86.96 | DONE (32000) |
| no_meta_matched_floor | 202 | 32000 | 87.90 | DONE (32000) |
| no_meta_matched_floor | 203 | 32000 | 86.84 | DONE (32000) |
| no_dream | 200 | 28000 | 84.57 | CUT (target 32000) |
| no_dream | 201 | 28000 | 86.84 | CUT (target 32000) |
| no_dream | 202 | 32000 | 89.09 | DONE (32000) |
| no_dream | 203 | 32000 | 87.14 | DONE (32000) |
| no_concepts | 200 | 15000 | 83.70 | CUT (target 32000) |
| no_concepts | 201 | 28000 | 85.58 | CUT (target 32000) |
| no_concepts | 202 | 28000 | 89.12 | CUT (target 32000) |
| no_concepts | 203 | 32000 | 87.48 | DONE (32000) |
| no_sleep | 200 | 32000 | 87.14 | DONE (32000) |
| no_sleep | 201 | 32000 | 85.73 | DONE (32000) |
| no_sleep | 202 | 32000 | 86.21 | DONE (32000) |
| no_sleep | 203 | 32000 | 86.81 | DONE (32000) |

## Per-condition summary at 32,000 boxes (only DONE/reached streams; the 22c reference full is 88.28, n=12)

| condition | streams with 32k checkpoint | mean S1 | min-max |
|---|---|---|---|
| full | 2/6 | 88.42 | 87.24-89.61 |
| no_meta | 4/4 | 87.68 | 86.61-88.94 |
| no_meta_matched_floor | 4/4 | 87.26 | 86.84-87.90 |
| no_dream | 2/4 | 88.12 | 87.14-89.09 |
| no_concepts | 1/4 | 87.48 | 87.48-87.48 |
| no_sleep | 4/4 | 86.48 | 85.73-87.14 |

(n is 2-4 per condition, so no confidence intervals/significance claims are made here; the earlier-reported 22b result stands: no_meta, no_dream, no_concepts not distinguishable at 10k boxes.)

## Full (60k) streams: held-out S1 by checkpoint

| seed | 10000 | 20000 | 24000 | 28000 | 32000 | 36000 |
|---|---|---|---|---|---|---|
| 300 | 85.54 | 85.63 | 86.10 | 87.56 | - | - |
| 301 | 84.36 | 85.43 | 87.04 | 88.43 | 89.61 | 91.58 |
| 302 | 84.68 | 85.82 | 86.33 | 86.43 | 87.24 | - |
| 303 | 84.85 | 85.81 | - | - | - | - |
| 304 | 84.86 | 84.96 | 85.57 | 85.96 | - | - |
| 305 | 84.89 | 84.67 | - | - | - | - |

## Resume / continuing on another PC
- Streams are NOT resumable: the snapshots in `streams_partial/` (and finished `streams/*.pkl`) store the S1 history, held-out evaluations, hyperparameter logs and self-modification events, but NOT the agent state (network weights, replay memory, concept library, RNG). A cut stream would have to be rerun from box 0 (a 32k stream takes ~75 min on 12 free workers; 60k about 2.5-3 h).
- All DONE streams and all partial checkpoints are valid, usable results. To regenerate the full report from whatever exists: `cd Expt_22d_Long_Ablations_Saturation; python run_expt22d.py --report-only results\20261001_060654_main` (needs numpy, matplotlib; reads the Expt_22c reference streams in ../Expt_22c_Long_Streams/results/20261001_044425_run/streams).
- To rerun missing streams on another PC, copy the `Expt_22d_Long_Ablations_Saturation` folder and run `python run_expt22d.py --workers N --long-reps 6 --long-boxes 60000 --abl-reps 4 --abl-boxes 32000 --tag rerun` (full rerun; seeds are fixed in the script, 300+ for full, 200+ for ablations, so reruns reproduce the same streams statistically, not bit-for-bit across machines).
