# Expt-2 demonstration report

Working title: Autonomous Discovery of Reusable Operations.

## Designer-supplied versus discovered

Supplied by the designer: the 10×10 world, the A–P catalogue, PLACE/UNDO/SUBMIT, an exact clone of the transition rules, the typed AST constructors (PLACE_REL, SEQ, CALL, CHOOSE, REPEAT, IF, LOOKAHEAD), bounded search, STM/LTM, the paired utility formula, and the bandit dispatcher.

Discovered only if the logs show it: which operations were proposed, which entered memory, and which were reused. Nothing in the source preloads a successful macro.

## Run status

- Run directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_02_Autonomous_Abstraction\results\20260929_100704_cap_progress`
- Preset: `discovery_smoke`
- Complete: `True`
- Stop reason: `finished`
- Episodes written: 416
- Planned episodes: 416
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Source hash: `a5985ed8529abb3d3577e40cc8699bfd739da49a314d7122ed1fb563f5ef1ac3`
- Config hash: `4377c6999413d51e4696b71ca389395bbbb74d3e4e1ec8877e1de2febf98821f`

## Performance by mode and seed

Differences are means with sample standard deviations. A gap of one occupied cell is not treated as a significance test.

| mode | seed | phase | n | final mean | final sd | best mean | physical mean | macros mean | evals mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flat_library | 11 | eval | 12 | 28.00 | 3.98 | 28.00 | 5.75 | 0.75 | 50000.0 |
| flat_library | 11 | train | 40 | 31.07 | 7.92 | 31.07 | 6.53 | 1.18 | 50000.0 |
| flat_library | 22 | eval | 12 | 27.42 | 3.80 | 27.42 | 5.58 | 0.50 | 50000.0 |
| flat_library | 22 | train | 40 | 31.32 | 7.92 | 31.32 | 6.42 | 0.85 | 50000.0 |
| hierarchical_library | 11 | eval | 12 | 13.83 | 8.63 | 13.83 | 2.83 | 0.00 | 50000.0 |
| hierarchical_library | 11 | train | 40 | 14.07 | 14.54 | 14.07 | 2.95 | 0.05 | 50000.0 |
| hierarchical_library | 22 | eval | 12 | 22.17 | 14.89 | 22.17 | 4.58 | 0.00 | 50000.0 |
| hierarchical_library | 22 | train | 40 | 16.15 | 10.30 | 16.15 | 3.40 | 0.05 | 50000.0 |
| primitive | 11 | eval | 12 | 66.83 | 2.72 | 66.83 | 13.92 | 0.00 | 50000.0 |
| primitive | 11 | train | 40 | 65.53 | 3.54 | 65.53 | 13.95 | 0.00 | 50000.0 |
| primitive | 22 | eval | 12 | 66.75 | 2.22 | 66.75 | 13.83 | 0.00 | 50000.0 |
| primitive | 22 | train | 40 | 65.12 | 3.16 | 65.12 | 13.88 | 0.00 | 50000.0 |
| search_only | 11 | eval | 12 | 64.17 | 5.20 | 64.17 | 14.00 | 0.00 | 50000.0 |
| search_only | 11 | train | 40 | 64.12 | 4.61 | 64.12 | 14.00 | 0.00 | 50000.0 |
| search_only | 22 | eval | 12 | 65.83 | 3.61 | 65.83 | 13.92 | 0.00 | 50000.0 |
| search_only | 22 | train | 40 | 64.15 | 3.48 | 64.15 | 13.95 | 0.00 | 50000.0 |

## Evidence

Observed evidence level: **2**.

- 0: engine ran, no validated useful discovery.
- 1: a repeated action sequence was stored and reused.
- 2: a stored operation was used at another location or task.
- 3: a parent combines independently used children and itself has positive real utility.
- 4: not claimed. Causal lesion checks were not part of this bounded run.

Up to three operations with recorded real use or provisional paired support:

### `op_a4f8bd8ae1b9395c`

- Library `flat_library|11`, status `confirmed`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `cross_task`.
- Real uses: 14. Tasks: `['inv_05bc74f7cd7c', 'inv_ad0404a64b5b', 'inv_521aa3f4db2c']`. Origins: `[[2, 1, 0], [0, 1, 0], [5, 0, 0], [2, 0, 0], [7, 1, 0], [3, 0, 0], [6, 1, 0], [1, 0, 0], [8, 1, 0], [1, 1, 0]]`.
- Utility sum (real only): 1.204. Paired utility sum: 0.14370000000000002. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 0, "type": "N"}, {"dx": 0, "dy": 6, "kind": "PLACE_REL", "rotation": 3, "type": "G"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 0], [0, 1], [0, 2], [1, 2]], "dx": 0, "dy": 0, "rotation": 0, "type": "N"}, {"cells": [[0, 6], [0, 8], [1, 6], [1, 7], [1, 8]], "dx": 0, "dy": 6, "rotation": 3, "type": "G"}]`

### `op_dcf066feed1d27a9`

- Library `flat_library|11`, status `confirmed`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `cross_task`.
- Real uses: 14. Tasks: `['inv_b70847430efc', 'inv_0b96b3917fa7', 'inv_0a58649f313c', 'inv_dddce847bbe5']`. Origins: `[[2, 5, 0], [0, 1, 0], [5, 1, 0], [2, 6, 0], [0, 3, 0], [5, 5, 0], [4, 2, 0], [4, 3, 0], [4, 5, 0], [1, 1, 0], [4, 4, 0]]`.
- Utility sum (real only): 1.204. Paired utility sum: 0.14370000000000005. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 1, "type": "I"}, {"dx": 3, "dy": -1, "kind": "PLACE_REL", "rotation": 1, "type": "O"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 1], [0, 2], [1, 0], [1, 1], [2, 0]], "dx": 0, "dy": 0, "rotation": 1, "type": "I"}, {"cells": [[3, 0], [4, -1], [4, 0], [4, 1]], "dx": 3, "dy": -1, "rotation": 1, "type": "O"}]`

### `op_b20ab824933bfa86`

- Library `flat_library|22`, status `confirmed`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `cross_task`.
- Real uses: 13. Tasks: `['inv_846c32759cc2', 'inv_e5a7016014b8', 'inv_e705d8722fa9', 'inv_1f2dbf0588dc']`. Origins: `[[7, 2, 0], [8, 0, 0], [7, 5, 0], [7, 1, 0], [8, 4, 0], [7, 0, 0], [8, 2, 0], [8, 5, 0]]`.
- Utility sum (real only): 1.248. Paired utility sum: 0.1237. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 2, "type": "C"}, {"dx": -7, "dy": 2, "kind": "PLACE_REL", "rotation": 1, "type": "D"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 0], [1, 0], [1, 1], [1, 2], [1, 3]], "dx": 0, "dy": 0, "rotation": 2, "type": "C"}, {"cells": [[-7, 3], [-6, 3], [-5, 2], [-5, 3], [-4, 2]], "dx": -7, "dy": 2, "rotation": 1, "type": "D"}]`


## Flat versus hierarchical

- Flat macro invocations per logged box: mean 0.923.
- Hierarchical macro invocations per logged box: mean 0.038.
- No operation with effective depth above 1 had positive real utility in this run.

## Discovery cost

- Sum of charged model transitions over logged boxes: 2925.
- Both branches of each paired check are included in that total.
- No extrapolated savings are reported. Amortization is claimed only if the tables show later boxes costing less computation after a library exists; this bounded run does not fit a crossover curve.

## Dry-run estimate

- Probe boxes: 2. Elapsed seconds: 0.06888309999976627.
- Linear estimate for the planned episode count: 14.327684799951385 seconds.
- The probe is not included in the episode table.

## Evaluation accounting

- Cheap-scan reserve: 3636 candidate evaluations. Deliberation stops at this distance before the cap. A cheap legal primitive may then use the remainder.
- `part_think`, `part_paired`, `part_guard`, `part_selection`, and `part_other` are an innermost partition of `candidate_evals`. Each charged evaluation is counted once, under the tally that was open on top.
- `span_think` counts every evaluation taken while a THINK tally was open, including paired validation and the guard scans inside it.
- `span_paired` counts every evaluation taken while a paired tally was open, including guard scans inside that check.
- The spans overlap the partition. They are not additional evaluations.
- These figures locate where the budget went. They do not show improved packing, a useful hierarchy, or amortized discovery cost.

| mode | n | evals mean | part think | part paired | part guard | part selection | span think | span paired | cheap mean | macros mean | physical mean | final mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flat_library | 104 | 50000.00 | 0.00 | 34262.46 | 913.85 | 14823.69 | 34326.46 | 34326.46 | 1.00 | 0.92 | 6.29 | 30.39 |
| hierarchical_library | 104 | 50000.00 | 0.00 | 38199.62 | 112.00 | 11688.38 | 38262.38 | 38262.38 | 1.00 | 0.04 | 3.30 | 15.78 |
| primitive | 104 | 50000.00 | 0.00 | 0.00 | 0.00 | 50000.00 | 0.00 | 0.00 | 0.90 | 0.00 | 13.90 | 65.66 |
| search_only | 104 | 50000.00 | 0.00 | 0.00 | 0.00 | 50000.00 | 10227.31 | 0.00 | 0.98 | 0.00 | 13.97 | 64.34 |

- Boxes whose innermost parts do not sum to candidate evaluations: 0.

## Limitations

- Utility weights are the published engineering defaults, not a tuned objective.
- Paired rollouts are short local comparisons.
- The primitive controller examines legal placements until the evaluation cap, so many boxes end on `compute_budget` rather than a full board.
- Lesion checks for evidence level 4 were not executed.
- A next debugging step, if proposal counts are nonzero but promotions are not, is to log how often paired utility is negative because both branches pay the full scan cost inside an 8-step horizon.

Package version 0.2.0. Python 3.13.1 on Windows-10-10.0.19045-SP0.
