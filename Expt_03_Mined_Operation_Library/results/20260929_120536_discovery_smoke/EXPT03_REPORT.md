# Expt-3 report

Mining reusable operations from teacher packings of the Expt-2 training inventories.
Rectangularity is a designer-supplied filter. A negative result is a valid result.

## Run

- Directory: `D:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_03_Mined_Operation_Library\results\20260929_120536_discovery_smoke`
- Preset: `discovery_smoke`
- Complete: `True`
- Stop reason: `finished`
- Episodes written: 736 of 736
- Device: `NVIDIA GeForce RTX 5060 Ti`
- CUDA bytes allocated at the end: 2968064
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Dataset hash: `668304e744f0d0ef22b164fb0e6a63a2fb065f835e170e9073a8fe3be7af53ce`
- Source hash: `7f0923aec6673c77e0cfd841cdcf47ffecd75fce665e543a08489d1ed3f25070`
- Corpus solutions: 48
- Teacher cost: `{"exact_nodes": 1291729, "exact_seconds": 28.891385100054322, "gpu_seconds": 5.028851000068244, "gpu_ops": 505, "tasks": 24, "exact_solutions": 24, "gpu_solutions": 24, "rejected_replay": 0, "solutions": 48, "quality_min": 90, "quality_max": 100}`
- Mining seconds (library construction, separate from agent evaluation): 0.000
- Wall seconds for this process: 0.002
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
| 0 | matched_control | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 0 | matched_control | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 0 | matched_control | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 0 | neutral_mined | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 0 | neutral_mined | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 0 | neutral_mined | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 0 | primitive | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 0 | primitive | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 0 | primitive | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 0 | rect_mined | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 0 | rect_mined | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 0 | rect_mined | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 0 | rect_mined_no_retrieval | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 0 | rect_mined_no_retrieval | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 0 | rect_mined_no_retrieval | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 10 | matched_control | 11 | 12 | 73.08 | 4.31 | 15.17 | 1/12 | 4.706 | 11 | 1721.1 | 1.00 |
| 10 | matched_control | 22 | 12 | 77.42 | 6.30 | 16.08 | 6/12 | 4.829 | 6 | 1950.2 | 1.00 |
| 10 | matched_control | 33 | 12 | 75.50 | 3.73 | 15.67 | 3/12 | 4.824 | 9 | 1664.2 | 1.00 |
| 10 | neutral_mined | 11 | 12 | 75.50 | 2.66 | 15.67 | 2/12 | 4.853 | 10 | 1855.0 | 1.00 |
| 10 | neutral_mined | 22 | 12 | 78.67 | 5.07 | 16.33 | 6/12 | 4.897 | 6 | 2124.9 | 1.00 |
| 10 | neutral_mined | 33 | 12 | 75.75 | 3.81 | 15.75 | 4/12 | 4.794 | 8 | 1729.7 | 1.00 |
| 10 | primitive | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 10 | primitive | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 10 | primitive | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 10 | rect_mined | 11 | 12 | 76.33 | 3.12 | 15.83 | 3/12 | 4.824 | 9 | 1843.0 | 1.00 |
| 10 | rect_mined | 22 | 12 | 77.17 | 5.60 | 16.00 | 5/12 | 4.931 | 7 | 1900.4 | 1.00 |
| 10 | rect_mined | 33 | 12 | 76.42 | 3.55 | 15.92 | 4/12 | 4.794 | 8 | 1908.3 | 1.00 |
| 10 | rect_mined_no_retrieval | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 10 | rect_mined_no_retrieval | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 10 | rect_mined_no_retrieval | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 20 | matched_control | 11 | 12 | 75.67 | 5.09 | 15.75 | 4/12 | 4.811 | 8 | 2039.0 | 1.50 |
| 20 | matched_control | 22 | 12 | 77.92 | 5.11 | 16.25 | 4/12 | 4.811 | 8 | 1953.5 | 1.50 |
| 20 | matched_control | 33 | 12 | 78.17 | 5.08 | 16.25 | 6/12 | 4.778 | 6 | 1775.2 | 1.50 |
| 20 | neutral_mined | 11 | 12 | 75.33 | 4.80 | 15.75 | 4/12 | 4.868 | 8 | 1723.0 | 1.42 |
| 20 | neutral_mined | 22 | 12 | 78.25 | 5.58 | 16.33 | 6/12 | 4.922 | 6 | 1960.8 | 1.33 |
| 20 | neutral_mined | 33 | 12 | 76.17 | 4.65 | 16.00 | 6/12 | 4.749 | 6 | 2121.4 | 1.42 |
| 20 | primitive | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 20 | primitive | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 20 | primitive | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 20 | rect_mined | 11 | 12 | 77.17 | 3.58 | 16.08 | 5/12 | 4.709 | 7 | 2054.1 | 1.25 |
| 20 | rect_mined | 22 | 12 | 77.58 | 6.58 | 16.17 | 5/12 | 4.824 | 7 | 1953.8 | 1.42 |
| 20 | rect_mined | 33 | 12 | 76.50 | 3.57 | 16.00 | 5/12 | 4.666 | 7 | 1935.5 | 1.33 |
| 20 | rect_mined_no_retrieval | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 20 | rect_mined_no_retrieval | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 20 | rect_mined_no_retrieval | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 24 | matched_control | 11 | 12 | 74.92 | 4.27 | 15.50 | 2/12 | 5.000 | 10 | 1804.8 | 0.75 |
| 24 | matched_control | 22 | 12 | 79.50 | 4.63 | 16.50 | 8/12 | 4.811 | 4 | 1973.2 | 0.75 |
| 24 | matched_control | 33 | 12 | 77.50 | 4.72 | 16.08 | 5/12 | 4.839 | 7 | 1935.9 | 0.75 |
| 24 | neutral_mined | 11 | 12 | 77.75 | 5.39 | 16.08 | 6/12 | 4.744 | 6 | 1911.7 | 2.25 |
| 24 | neutral_mined | 22 | 12 | 79.42 | 3.15 | 16.42 | 7/12 | 4.853 | 5 | 1782.9 | 2.33 |
| 24 | neutral_mined | 33 | 12 | 77.92 | 5.02 | 16.17 | 7/12 | 4.716 | 5 | 1580.4 | 2.25 |
| 24 | primitive | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 24 | primitive | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 24 | primitive | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |
| 24 | rect_mined | 11 | 12 | 77.17 | 3.58 | 16.08 | 5/12 | 4.709 | 7 | 2018.6 | 1.25 |
| 24 | rect_mined | 22 | 12 | 78.00 | 6.23 | 16.25 | 5/12 | 4.824 | 7 | 1889.0 | 1.42 |
| 24 | rect_mined | 33 | 12 | 76.50 | 3.57 | 16.00 | 5/12 | 4.666 | 7 | 1834.7 | 1.33 |
| 24 | rect_mined_no_retrieval | 11 | 12 | 76.33 | 3.52 | 15.75 | 4/12 | 4.882 | 8 | 1773.2 | 0.00 |
| 24 | rect_mined_no_retrieval | 22 | 12 | 80.33 | 5.15 | 16.58 | 8/12 | 4.858 | 4 | 2089.2 | 0.00 |
| 24 | rect_mined_no_retrieval | 33 | 12 | 77.75 | 4.09 | 16.08 | 7/12 | 4.832 | 5 | 1870.2 | 0.00 |

## Paired differences at the largest snapshot

Largest held-out snapshot in this file: 24. Target Q>=80.
- rect_minus_neutral_Q: n=36, mean -1.14, sd 5.42.
- rect_minus_primitive_Q: n=36, mean -0.92, sd 5.01.
- neutral_minus_primitive_Q: n=36, mean 0.22, sd 5.75.
- rect_minus_matched_Q: n=36, mean -0.08, sd 4.62.

## Libraries


## Conditional efficiency and sensitivity

- Held-out rows with Q>=80: 338 of 720.
- Held-out rows with Q>=70: 713 of 720.
- Held-out rows with Q>=90: 15 of 720.
Efficiency is reported in the table only for rows that met the preregistered target of 80. Thresholds 70 and 90 are descriptive counts. They were not used to pick a winner.

## Amortization

- Offline teacher search plus GPU beam: 33.920s. Mining: 0.000s. These costs are not inside the per-box evaluation cap.
- No amortization crossover is fitted. End-to-end savings would require the measured evaluation work, plus teacher and mining work, to fall below the primitive arm inside this run. See the evals column. Teacher effort is included in any such claim, and this report does not make that claim unless the table shows it.
- At snapshot 24, mean candidate evaluations were 1910.9 (primitive) and 1914.1 (rect_mined). Offline teacher and mining seconds are additional.

## Plain answers

- At snapshot 24, mean final Q is higher for shape-neutral extraction (78.36) than for rectangular extraction (77.22). Rectangular extraction did not beat shape-neutral extraction on this schedule.
- Primitive mean final Q at that snapshot: 78.14.
- Learned behaviour, if any, is which stored operations the retrieval rule fired. The rectangle test itself was supplied.

A favourable ratio, or a single transferred macro, is not general intelligence.

## Expt-1 exploratory pilot

Four unlimited-piece boards from `Expt_01_10x10_Packing/results/20260928_180809_smoke/action_trace.jsonl` finished at Q>=80. They produced 203 connected groups. 105 of those groups (0.52) have a piece multiset that at least one Expt-2 training inventory can supply. That is not transfer to inventory-constrained packing, and those groups were not loaded into the libraries above.
