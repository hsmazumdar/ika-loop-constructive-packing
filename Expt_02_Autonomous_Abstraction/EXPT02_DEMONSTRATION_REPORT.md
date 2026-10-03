# Expt-2 demonstration report

Working title: Autonomous Discovery of Reusable Operations.

## Designer-supplied versus discovered

Supplied by the designer: the 10×10 world, the A–P catalogue, PLACE/UNDO/SUBMIT, an exact clone of the transition rules, the typed AST constructors (PLACE_REL, SEQ, CALL, CHOOSE, REPEAT, IF, LOOKAHEAD), bounded search, STM/LTM, the paired utility formula, and the bandit dispatcher.

Discovered only if the logs show it: which operations were proposed, which entered memory, and which were reused. Nothing in the source preloads a successful macro.

## Run status

- Run directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_02_Autonomous_Abstraction\results\20260929_092518_discovery_smoke`
- Preset: `discovery_smoke`
- Complete: `True`
- Stop reason: `finished`
- Episodes written: 416
- Planned episodes: 416
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Source hash: `b4b5019341f04251241d49584a77177b4ba0ceebe03529805f786ed5675b4ae8`
- Config hash: `7dabf51426f546ebfdac0b65151787fb69804c8441b111e5f5b7fec1f775b0fa`

## Performance by mode and seed

Differences are means with sample standard deviations. A gap of one occupied cell is not treated as a significance test.

| mode | seed | phase | n | final mean | final sd | best mean | physical mean | macros mean | evals mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flat_library | 11 | eval | 12 | 22.92 | 5.35 | 22.92 | 4.75 | 0.75 | 50000.0 |
| flat_library | 11 | train | 40 | 27.95 | 7.82 | 27.95 | 5.92 | 1.68 | 50000.0 |
| flat_library | 22 | eval | 12 | 23.92 | 5.63 | 23.92 | 5.00 | 0.92 | 50000.0 |
| flat_library | 22 | train | 40 | 26.05 | 8.17 | 26.05 | 5.33 | 0.85 | 50000.0 |
| hierarchical_library | 11 | eval | 12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 50000.0 |
| hierarchical_library | 11 | train | 40 | 5.88 | 8.97 | 5.88 | 1.23 | 0.10 | 50000.0 |
| hierarchical_library | 22 | eval | 12 | 17.67 | 16.44 | 17.67 | 3.67 | 0.00 | 50000.0 |
| hierarchical_library | 22 | train | 40 | 11.00 | 10.47 | 11.00 | 2.33 | 0.05 | 50000.0 |
| primitive | 11 | eval | 12 | 66.58 | 2.97 | 66.58 | 13.92 | 0.00 | 50000.0 |
| primitive | 11 | train | 40 | 65.42 | 3.70 | 65.42 | 13.93 | 0.00 | 50000.0 |
| primitive | 22 | eval | 12 | 66.92 | 2.23 | 66.92 | 13.83 | 0.00 | 50000.0 |
| primitive | 22 | train | 40 | 65.03 | 3.10 | 65.03 | 13.85 | 0.00 | 50000.0 |
| search_only | 11 | eval | 12 | 63.50 | 5.07 | 63.50 | 14.00 | 0.00 | 50000.0 |
| search_only | 11 | train | 40 | 63.65 | 4.45 | 63.65 | 14.00 | 0.00 | 50000.0 |
| search_only | 22 | eval | 12 | 64.58 | 4.29 | 64.58 | 14.00 | 0.00 | 50000.0 |
| search_only | 22 | train | 40 | 63.48 | 4.24 | 63.48 | 13.95 | 0.00 | 49931.7 |

## Evidence

Observed evidence level: **2**.

- 0: engine ran, no validated useful discovery.
- 1: a repeated action sequence was stored and reused.
- 2: a stored operation was used at another location or task.
- 3: a parent combines independently used children and itself has positive real utility.
- 4: not claimed. Causal lesion checks were not part of this bounded run.

Up to three operations with recorded real use or provisional paired support:

### `op_88cdca7387db0487`

- Library `flat_library|11`, status `confirmed`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `cross_task`.
- Real uses: 19. Tasks: `['inv_ad0404a64b5b', 'inv_e5a7016014b8', 'inv_521aa3f4db2c', 'inv_0b96b3917fa7', 'inv_ac2c19d4f316', 'inv_0a58649f313c', 'inv_bfd90425f5bd', 'inv_3853d99a7890']`. Origins: `[[2, 5, 0], [4, 2, 0], [3, 2, 0], [2, 4, 0], [6, 3, 0], [5, 2, 0], [3, 6, 0], [6, 4, 0], [4, 5, 0], [2, 2, 0], [3, 3, 0], [2, 6, 0], [3, 4, 0]]`.
- Utility sum (real only): 1.8240000000000005. Paired utility sum: 0.0958. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 0, "type": "G"}, {"dx": -2, "dy": -2, "kind": "PLACE_REL", "rotation": 2, "type": "G"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 0], [0, 1], [1, 1], [2, 0], [2, 1]], "dx": 0, "dy": 0, "rotation": 0, "type": "G"}, {"cells": [[-2, -2], [-2, -1], [-1, -2], [0, -2], [0, -1]], "dx": -2, "dy": -2, "rotation": 2, "type": "G"}]`

### `op_90b500c639b43245`

- Library `flat_library|11`, status `confirmed`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `cross_task`.
- Real uses: 15. Tasks: `['inv_b70847430efc', 'inv_a5b815783152', 'inv_1f2dbf0588dc', 'inv_846c32759cc2']`. Origins: `[[6, 1, 0], [6, 2, 0], [4, 3, 0], [2, 0, 0], [3, 1, 0], [3, 3, 0], [0, 1, 0], [2, 1, 0], [1, 0, 0], [4, 0, 0], [1, 3, 0], [0, 3, 0], [5, 3, 0]]`.
- Utility sum (real only): 1.29. Paired utility sum: 0.06580000000000003. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 1, "type": "M"}, {"dx": 0, "dy": 5, "kind": "PLACE_REL", "rotation": 3, "type": "C"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 0], [1, 0], [2, 0], [3, 0]], "dx": 0, "dy": 0, "rotation": 1, "type": "M"}, {"cells": [[0, 6], [1, 6], [2, 6], [3, 5], [3, 6]], "dx": 0, "dy": 5, "rotation": 3, "type": "C"}]`

### `op_dcf066feed1d27a9`

- Library `flat_library|11`, status `confirmed`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `cross_task`.
- Real uses: 14. Tasks: `['inv_b70847430efc', 'inv_0b96b3917fa7', 'inv_0a58649f313c', 'inv_dddce847bbe5']`. Origins: `[[4, 3, 0], [1, 1, 0], [1, 6, 0], [3, 1, 0], [5, 4, 0], [4, 1, 0], [5, 3, 0], [0, 5, 0], [5, 2, 0], [4, 5, 0]]`.
- Utility sum (real only): 1.204. Paired utility sum: 0.09580000000000005. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 1, "type": "I"}, {"dx": 3, "dy": -1, "kind": "PLACE_REL", "rotation": 1, "type": "O"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 1], [0, 2], [1, 0], [1, 1], [2, 0]], "dx": 0, "dy": 0, "rotation": 1, "type": "I"}, {"cells": [[3, 0], [4, -1], [4, 0], [4, 1]], "dx": 3, "dy": -1, "rotation": 1, "type": "O"}]`


## Flat versus hierarchical

- Flat macro invocations per logged box: mean 1.163.
- Hierarchical macro invocations per logged box: mean 0.058.
- No operation with effective depth above 1 had positive real utility in this run.

## Discovery cost

- Sum of charged model transitions over logged boxes: 3283.
- Both branches of each paired check are included in that total.
- No extrapolated savings are reported. Amortization is claimed only if the tables show later boxes costing less computation after a library exists; this bounded run does not fit a crossover curve.

## Dry-run estimate

- Probe boxes: 2. Elapsed seconds: 0.036469099999976606.
- Linear estimate for the planned episode count: 7.585572799995134 seconds.
- The probe is not included in the episode table.

## Limitations

- Utility weights are the published engineering defaults, not a tuned objective.
- Paired rollouts are short local comparisons.
- The primitive controller examines legal placements until the evaluation cap, so many boxes end on `compute_budget` rather than a full board.
- Lesion checks for evidence level 4 were not executed.
- A next debugging step, if proposal counts are nonzero but promotions are not, is to log how often paired utility is negative because both branches pay the full scan cost inside an 8-step horizon.

Package version 0.2.0. Python 3.13.1 on Windows-10-10.0.19045-SP0.

## Checks recorded with this delivery

- `python -m pytest -q`: 33 passed, 0 failed.
- Inventory generator: 24 train, 8 development, 12 test. `validate_tasks.py` returned status OK for 44 tasks.
- Tiny preset `results/20260929_092511_tiny`: 12/12 legacy boxes, complete. Evidence level on that run was 2, with flat-library reuse labelled `same_task` because every box used task id `legacy`.
- GUI test: a withdrawn Tk session refreshed, took one internal step with the real mask unchanged, then one physical step.
- `memory_sweep` was not launched.
