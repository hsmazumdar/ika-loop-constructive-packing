# Expt-3 report

Mining reusable operations from teacher packings of the Expt-2 training inventories.
Rectangularity is a designer-supplied filter. A negative result is a valid result.

## Run

- Directory: `D:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_03_Mined_Operation_Library\results\20260929_120357_tiny`
- Preset: `tiny`
- Complete: `True`
- Stop reason: `finished`
- Episodes written: 12 of 12
- Device: `NVIDIA GeForce RTX 5060 Ti`
- CUDA bytes allocated at the end: 36522496
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Dataset hash: `668304e744f0d0ef22b164fb0e6a63a2fb065f835e170e9073a8fe3be7af53ce`
- Source hash: `6b5a80b3573c9dcee0e27512672881df2fef5b154fc15bd46bd340a91d7f0ba7`
- Corpus solutions: 2
- Teacher cost: `{"exact_nodes": 93177, "exact_seconds": 2.0946430999902077, "gpu_seconds": 0.0, "gpu_ops": 0, "tasks": 2, "exact_solutions": 2, "gpu_solutions": 0, "rejected_replay": 0, "solutions": 2, "quality_min": 100, "quality_max": 100}`
- Mining seconds (library construction, separate from agent evaluation): 0.048
- Wall seconds for this process: 0.865
- Snapshot plan notes: `[]`

## What was supplied and what was measured

Supplied by the designer: the A–P catalogue, the Expt-2 inventory split, the rectangle filter, the shared placement score, the retrieval rule, and the teacher exact-cover solver.
Measured: which training groups met the support and within-training validation rule, which of those were rectangles, and what the frozen libraries did on held-out inventories.
The teacher solutions are labeled teacher experience. The agent did not discover them.
Expt-1 action traces are unlimited-piece boxes. They are not in this comparison.

## Corpus

- Solutions: 2. Q min 100, max 100, mean 100.00.
- By solver: `{'teacher_exact_cover': 2}`.
- Distinct training tasks represented: 2.

## Development lock

- Development episodes: 2. Mean final Q 72.00. Boxes with P=0: 0.
- The budget in `configs/default.json` was predeclared from the Expt-2 cap failure. Development did not choose an arm and did not change the cap.

## Held-out tables

Means are descriptive. The held-out set has 12 inventories at full size. A mean gap is not a claim of statistical superiority.

| snapshot | arm | seed | n | Q mean | Q sd | P mean | attainment | conditional E | censored | evals mean | macros mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | matched_control | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 0 | neutral_mined | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 0 | primitive | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 0 | rect_mined | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 0 | rect_mined_no_retrieval | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 2 | matched_control | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 2 | neutral_mined | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 2 | primitive | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 2 | rect_mined | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |
| 2 | rect_mined_no_retrieval | 11 | 1 | 65.00 | 0.00 | 13.00 | 0/1 | NA | 1 | 680.0 | 0.00 |

## Paired differences at the largest snapshot

Largest held-out snapshot in this file: 2. Target Q>=80.
- rect_minus_neutral_Q: n=1, mean 0.00, sd 0.00.
- rect_minus_primitive_Q: n=1, mean 0.00, sd 0.00.
- neutral_minus_primitive_Q: n=1, mean 0.00, sd 0.00.
- rect_minus_matched_Q: n=1, mean 0.00, sd 0.00.

## Libraries

- Snapshot 0: pool 0, admitted 0, rectangle candidates 0, rectangles inside the neutral library 0, bytes {'rect_mined': 0, 'neutral_mined': 0, 'matched_control': 0}, mismatches 1.
- Snapshot 2: pool 259, admitted 0, rectangle candidates 0, rectangles inside the neutral library 0, bytes {'rect_mined': 0, 'neutral_mined': 0, 'matched_control': 0}, mismatches 1.

## Conditional efficiency and sensitivity

- Held-out rows with Q>=80: 0 of 10.
- Held-out rows with Q>=70: 0 of 10.
- Held-out rows with Q>=90: 0 of 10.
Efficiency is reported in the table only for rows that met the preregistered target of 80. Thresholds 70 and 90 are descriptive counts. They were not used to pick a winner.

## Amortization

- Offline teacher search plus GPU beam: 2.095s. Mining: 0.048s. These costs are not inside the per-box evaluation cap.
- No amortization crossover is fitted. End-to-end savings would require the measured evaluation work, plus teacher and mining work, to fall below the primitive arm inside this run. See the evals column. Teacher effort is included in any such claim, and this report does not make that claim unless the table shows it.
- At snapshot 2, mean candidate evaluations were 680.0 (primitive) and 680.0 (rect_mined). Offline teacher and mining seconds are additional.

## Plain answers

- At snapshot 2, rectangular extraction and shape-neutral extraction have the same mean final Q (65.00).
- Primitive mean final Q at that snapshot: 65.00.
- Neutral library rectangles: 0 of the admitted neutral operations. Those rectangles were selected by frequency, not by the rectangle filter.
- Learned behaviour, if any, is which stored operations the retrieval rule fired. The rectangle test itself was supplied.

A favourable ratio, or a single transferred macro, is not general intelligence.
