# Expt-3 report

Mining reusable operations from teacher packings of the Expt-2 training inventories.
Rectangularity is a designer-supplied filter. A negative result is a valid result.

## Run

- Directory: `D:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_03_Mined_Operation_Library\results\20260929_130446_discovery_smoke`
- Preset: `discovery_smoke`
- Complete: `True`
- Stop reason: `finished`
- Episodes written: 736 of 736
- Device: `NVIDIA GeForce RTX 5060 Ti`
- CUDA bytes allocated at the end: 36522496
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Dataset hash: `668304e744f0d0ef22b164fb0e6a63a2fb065f835e170e9073a8fe3be7af53ce`
- Source hash: `72752f027242340c1d24a3fbe329a7fb52b70d3c54057ab9b487b91b8dba4de3`
- Corpus solutions: 48
- Teacher cost: `{"exact_nodes": 1291729, "exact_seconds": 28.891385100054322, "gpu_seconds": 5.028851000068244, "gpu_ops": 505, "tasks": 24, "exact_solutions": 24, "gpu_solutions": 24, "rejected_replay": 0, "solutions": 48, "quality_min": 90, "quality_max": 100}`
- Mining seconds (library construction, separate from agent evaluation): 11.174
- Wall seconds for this process: 92.974
- Snapshot plan notes: `[{"requested": 40, "status": "unavailable", "available_tasks": 24}, {"requested": null, "status": "added_actual_corpus_size", "available_tasks": 24}]`

## What was supplied and what was measured

Supplied by the designer: the A–P catalogue, the Expt-2 inventory split, the rectangle filter, the shared placement score, the retrieval rule, and the teacher exact-cover solver.
Measured: which training groups met the support and within-training validation rule, which of those were rectangles, and what the frozen libraries did on held-out inventories.
The teacher solutions are labeled teacher experience. The agent did not discover them.
Expt-1 action traces are unlimited-piece boxes. They are not in this comparison.

## Corpus

- Solutions: 48. Q min 90, max 100, mean 97.27.
- By solver: `{'teacher_exact_cover': 24, 'teacher_gpu_beam': 24}`.
- Distinct training tasks represented: 24.

## Development lock

- Development episodes: 16. Mean final Q 79.31. Boxes with P=0: 0.
- The budget in `configs/default.json` was predeclared from the Expt-2 cap failure. Development did not choose an arm and did not change the cap.

## Held-out tables

Means are descriptive. The held-out set has 12 inventories at full size. A mean gap is not a claim of statistical superiority.

| snapshot | arm | seed | n | Q mean | Q sd | P mean | attainment | conditional E | censored | evals mean | macros mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | matched_control | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 0 | matched_control | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 0 | matched_control | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 0 | neutral_mined | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 0 | neutral_mined | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 0 | neutral_mined | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 0 | primitive | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 0 | primitive | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 0 | primitive | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 0 | rect_mined | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 0 | rect_mined | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 0 | rect_mined | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 0 | rect_mined_no_retrieval | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 0 | rect_mined_no_retrieval | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 0 | rect_mined_no_retrieval | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 10 | matched_control | 11 | 12 | 72.83 | 5.57 | 21.17 | 2/12 | 3.518 | 10 | 7807.4 | 0.83 |
| 10 | matched_control | 22 | 12 | 77.33 | 4.50 | 22.00 | 5/12 | 3.584 | 7 | 7650.9 | 0.75 |
| 10 | matched_control | 33 | 12 | 76.25 | 3.63 | 22.50 | 4/12 | 3.681 | 7 | 7642.8 | 0.67 |
| 10 | neutral_mined | 11 | 12 | 74.25 | 2.71 | 21.42 | 1/12 | 3.636 | 9 | 7772.6 | 1.00 |
| 10 | neutral_mined | 22 | 12 | 77.83 | 4.30 | 22.08 | 6/12 | 3.542 | 5 | 7304.4 | 1.00 |
| 10 | neutral_mined | 33 | 12 | 76.50 | 5.65 | 22.58 | 6/12 | 3.520 | 6 | 7706.0 | 1.00 |
| 10 | primitive | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 10 | primitive | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 10 | primitive | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 10 | rect_mined | 11 | 12 | 74.67 | 3.66 | 21.83 | 2/12 | 3.636 | 8 | 7871.1 | 0.58 |
| 10 | rect_mined | 22 | 12 | 78.00 | 6.31 | 22.17 | 7/12 | 3.485 | 4 | 7233.4 | 0.92 |
| 10 | rect_mined | 33 | 12 | 77.00 | 4.56 | 22.17 | 6/12 | 3.528 | 5 | 7474.3 | 0.83 |
| 10 | rect_mined_no_retrieval | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 10 | rect_mined_no_retrieval | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 10 | rect_mined_no_retrieval | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 20 | matched_control | 11 | 12 | 76.67 | 3.45 | 22.67 | 3/12 | 3.298 | 4 | 7599.3 | 1.00 |
| 20 | matched_control | 22 | 12 | 78.92 | 5.39 | 22.33 | 5/12 | 3.501 | 5 | 7903.6 | 1.00 |
| 20 | matched_control | 33 | 12 | 75.17 | 4.62 | 22.33 | 3/12 | 3.422 | 5 | 7813.9 | 0.83 |
| 20 | neutral_mined | 11 | 12 | 77.58 | 4.39 | 22.58 | 7/12 | 3.488 | 5 | 7588.5 | 1.17 |
| 20 | neutral_mined | 22 | 12 | 77.08 | 6.21 | 22.00 | 5/12 | 3.548 | 6 | 7776.9 | 1.17 |
| 20 | neutral_mined | 33 | 12 | 74.50 | 3.55 | 21.83 | 2/12 | 3.833 | 8 | 7684.9 | 1.25 |
| 20 | primitive | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 20 | primitive | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 20 | primitive | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 20 | rect_mined | 11 | 12 | 75.08 | 3.93 | 21.83 | 3/12 | 3.450 | 6 | 7883.0 | 0.83 |
| 20 | rect_mined | 22 | 12 | 77.25 | 5.54 | 21.67 | 7/12 | 3.554 | 4 | 7532.4 | 1.17 |
| 20 | rect_mined | 33 | 12 | 75.50 | 4.37 | 22.08 | 5/12 | 3.480 | 5 | 7783.2 | 1.00 |
| 20 | rect_mined_no_retrieval | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 20 | rect_mined_no_retrieval | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 20 | rect_mined_no_retrieval | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 24 | matched_control | 11 | 12 | 72.92 | 6.36 | 21.83 | 2/12 | 3.518 | 8 | 7815.8 | 1.00 |
| 24 | matched_control | 22 | 12 | 78.42 | 6.69 | 22.17 | 7/12 | 3.543 | 4 | 7713.1 | 1.00 |
| 24 | matched_control | 33 | 12 | 73.67 | 4.01 | 21.92 | 2/12 | 3.810 | 8 | 7850.8 | 1.17 |
| 24 | neutral_mined | 11 | 12 | 78.92 | 4.05 | 22.58 | 6/12 | 3.532 | 3 | 7588.8 | 1.67 |
| 24 | neutral_mined | 22 | 12 | 76.92 | 4.31 | 21.67 | 7/12 | 3.594 | 5 | 7601.3 | 1.42 |
| 24 | neutral_mined | 33 | 12 | 77.50 | 4.33 | 22.50 | 6/12 | 3.362 | 6 | 7628.2 | 1.75 |
| 24 | primitive | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 24 | primitive | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 24 | primitive | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |
| 24 | rect_mined | 11 | 12 | 74.58 | 4.15 | 21.83 | 3/12 | 3.450 | 7 | 7883.0 | 0.92 |
| 24 | rect_mined | 22 | 12 | 78.17 | 4.18 | 21.92 | 7/12 | 3.554 | 3 | 7532.4 | 1.08 |
| 24 | rect_mined | 33 | 12 | 74.58 | 6.05 | 22.08 | 5/12 | 3.480 | 5 | 7783.2 | 1.00 |
| 24 | rect_mined_no_retrieval | 11 | 12 | 75.83 | 4.37 | 22.50 | 4/12 | 3.392 | 7 | 7775.0 | 0.00 |
| 24 | rect_mined_no_retrieval | 22 | 12 | 78.92 | 5.82 | 22.58 | 7/12 | 3.473 | 3 | 7443.6 | 0.00 |
| 24 | rect_mined_no_retrieval | 33 | 12 | 77.42 | 3.40 | 22.50 | 5/12 | 3.591 | 5 | 7706.2 | 0.00 |

## Paired differences at the largest snapshot

Largest held-out snapshot in this file: 24. Target Q>=80.
- rect_minus_neutral_Q: n=36, mean -2.00, sd 6.23.
- rect_minus_primitive_Q: n=36, mean -1.61, sd 5.61.
- neutral_minus_primitive_Q: n=36, mean 0.39, sd 5.33.
- rect_minus_matched_Q: n=36, mean 0.78, sd 5.56.
- matched_control: no_legal 9/36, mean undos 6.39, mean placements 21.97.
- neutral_mined: no_legal 10/36, mean undos 6.17, mean placements 22.25.
- primitive: no_legal 12/36, mean undos 6.58, mean placements 22.53.
- rect_mined: no_legal 6/36, mean undos 6.19, mean placements 21.94.
- rect_mined_no_retrieval: no_legal 12/36, mean undos 6.58, mean placements 22.53.

## Libraries

- Snapshot 0: pool 0, admitted 0, rectangle candidates 0, rectangles inside the neutral library 0, bytes {'rect_mined': 0, 'neutral_mined': 0, 'matched_control': 0}, mismatches 1.
- Snapshot 10: pool 4908, admitted 6, rectangle candidates 2, rectangles inside the neutral library 2, bytes {'rect_mined': 546, 'neutral_mined': 1591, 'matched_control': 529}, mismatches 0.
- Snapshot 20: pool 9158, admitted 89, rectangle candidates 4, rectangles inside the neutral library 4, bytes {'rect_mined': 1167, 'neutral_mined': 24902, 'matched_control': 1082}, mismatches 0.
- Snapshot 24: pool 11035, admitted 114, rectangle candidates 4, rectangles inside the neutral library 4, bytes {'rect_mined': 1224, 'neutral_mined': 32464, 'matched_control': 1158}, mismatches 0.

## Conditional efficiency and sensitivity

- Held-out rows with Q>=80: 300 of 720.
- Held-out rows with Q>=70: 690 of 720.
- Held-out rows with Q>=90: 14 of 720.
Efficiency is reported in the table only for rows that met the preregistered target of 80. Thresholds 70 and 90 are descriptive counts. They were not used to pick a winner.

## Amortization

- Offline teacher search plus GPU beam: 33.920s. Mining: 11.174s. These costs are not inside the per-box evaluation cap.
- No amortization crossover is fitted. End-to-end savings would require the measured evaluation work, plus teacher and mining work, to fall below the primitive arm inside this run. See the evals column. Teacher effort is included in any such claim, and this report does not make that claim unless the table shows it.
- At snapshot 24, mean candidate evaluations were 7641.6 (primitive) and 7732.9 (rect_mined). Offline teacher and mining seconds are additional.

## Plain answers

- At snapshot 24, mean final Q is higher for shape-neutral extraction (77.78) than for rectangular extraction (75.78). Rectangular extraction did not beat shape-neutral extraction on this schedule.
- Primitive mean final Q at that snapshot: 77.39.
- Neutral library rectangles: 4 of the admitted neutral operations. Those rectangles were selected by frequency, not by the rectangle filter.
- Learned behaviour, if any, is which stored operations the retrieval rule fired. The rectangle test itself was supplied.

A favourable ratio, or a single transferred macro, is not general intelligence.

## Expt-1 exploratory pilot

Four unlimited-piece boards from `D:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_01_10x10_Packing\results\20260928_180809_smoke\action_trace.jsonl` finished at Q>=80. They produced 203 connected groups. 105 of those groups (0.52) have a piece multiset that at least one Expt-2 training inventory can supply. That is not transfer to inventory-constrained packing, and those groups were not loaded into the libraries above.
