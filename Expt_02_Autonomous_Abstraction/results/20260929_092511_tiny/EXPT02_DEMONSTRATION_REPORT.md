# Expt-2 demonstration report

Working title: Autonomous Discovery of Reusable Operations.

## Designer-supplied versus discovered

Supplied by the designer: the 10×10 world, the A–P catalogue, PLACE/UNDO/SUBMIT, an exact clone of the transition rules, the typed AST constructors (PLACE_REL, SEQ, CALL, CHOOSE, REPEAT, IF, LOOKAHEAD), bounded search, STM/LTM, the paired utility formula, and the bandit dispatcher.

Discovered only if the logs show it: which operations were proposed, which entered memory, and which were reused. Nothing in the source preloads a successful macro.

## Run status

- Run directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_02_Autonomous_Abstraction\results\20260929_092511_tiny`
- Preset: `tiny`
- Complete: `True`
- Stop reason: `finished`
- Episodes written: 12
- Planned episodes: 12
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Source hash: `b4b5019341f04251241d49584a77177b4ba0ceebe03529805f786ed5675b4ae8`
- Config hash: `4bea1da991df5794d923e514294fc61911edae381a276c75ea9df564c082d074`

## Performance by mode and seed

Differences are means with sample standard deviations. A gap of one occupied cell is not treated as a significance test.

| mode | seed | phase | n | final mean | final sd | best mean | physical mean | macros mean | evals mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flat_library | 1 | train | 3 | 27.00 | 11.27 | 27.00 | 5.33 | 1.33 | 50000.0 |
| hierarchical_library | 1 | train | 3 | 25.67 | 32.47 | 25.67 | 5.33 | 0.67 | 50000.0 |
| primitive | 1 | train | 3 | 65.33 | 2.08 | 65.33 | 14.00 | 0.00 | 50000.0 |
| search_only | 1 | train | 3 | 68.00 | 1.00 | 68.00 | 14.00 | 0.00 | 50000.0 |

## Evidence

Observed evidence level: **2**.

- 0: engine ran, no validated useful discovery.
- 1: a repeated action sequence was stored and reused.
- 2: a stored operation was used at another location or task.
- 3: a parent combines independently used children and itself has positive real utility.
- 4: not claimed. Causal lesion checks were not part of this bounded run.

Up to three operations with recorded real use or provisional paired support:

### `op_8dfc757e972b0260`

- Library `flat_library|1`, status `same_task_reuse`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `same_task`.
- Real uses: 4. Tasks: `['legacy']`. Origins: `[[2, 1, 0], [7, 2, 0], [5, 4, 0], [0, 1, 0]]`.
- Utility sum (real only): 0.384. Paired utility sum: 0.0958. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 3, "type": "G"}, {"dx": 1, "dy": 3, "kind": "PLACE_REL", "rotation": 3, "type": "G"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 0], [0, 2], [1, 0], [1, 1], [1, 2]], "dx": 0, "dy": 0, "rotation": 3, "type": "G"}, {"cells": [[1, 3], [1, 5], [2, 3], [2, 4], [2, 5]], "dx": 1, "dy": 3, "rotation": 3, "type": "G"}]`

### `op_84ebca72d7c61408`

- Library `hierarchical_library|1`, status `provisional`, source `mine`, provenance `real`.
- Parents: `[]`. Effective depth: 1.
- Confirmation scope: `not confirmed`.
- Real uses: 2. Tasks: `['legacy']`. Origins: `[[1, 2, 0], [0, 0, 0]]`.
- Utility sum (real only): 0.192. Paired utility sum: 0.09579999999999994. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 1, "type": "B"}, {"dx": 6, "dy": 3, "kind": "PLACE_REL", "rotation": 2, "type": "E"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]], "dx": 0, "dy": 0, "rotation": 1, "type": "B"}, {"cells": [[6, 4], [6, 5], [7, 3], [7, 4], [7, 5]], "dx": 6, "dy": 3, "rotation": 2, "type": "E"}]`

### `op_b533df6b7ecac4b1`

- Library `hierarchical_library|1`, status `provisional`, source `mutate`, provenance `simulated`.
- Parents: `['op_84ebca72d7c61408']`. Effective depth: 1.
- Confirmation scope: `not confirmed`.
- Real uses: 0. Tasks: `[]`. Origins: `[]`.
- Utility sum (real only): 0.0. Paired utility sum: 0.04789999999999994. Failures: 0.
- AST: `{"children": [{"dx": 0, "dy": 0, "kind": "PLACE_REL", "rotation": 0, "type": "B"}, {"dx": 6, "dy": 3, "kind": "PLACE_REL", "rotation": 2, "type": "E"}], "kind": "SEQ"}`
- Primitive expansion: `[{"cells": [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]], "dx": 0, "dy": 0, "rotation": 0, "type": "B"}, {"cells": [[6, 4], [6, 5], [7, 3], [7, 4], [7, 5]], "dx": 6, "dy": 3, "rotation": 2, "type": "E"}]`


## Flat versus hierarchical

- Flat macro invocations per logged box: mean 1.333.
- Hierarchical macro invocations per logged box: mean 0.667.
- No operation with effective depth above 1 had positive real utility in this run.

## Discovery cost

- Sum of charged model transitions over logged boxes: 89.
- Both branches of each paired check are included in that total.
- No extrapolated savings are reported. Amortization is claimed only if the tables show later boxes costing less computation after a library exists; this bounded run does not fit a crossover curve.

## Limitations

- Utility weights are the published engineering defaults, not a tuned objective.
- Paired rollouts are short local comparisons.
- The primitive controller examines legal placements until the evaluation cap, so many boxes end on `compute_budget` rather than a full board.
- Lesion checks for evidence level 4 were not executed.
- A next debugging step, if proposal counts are nonzero but promotions are not, is to log how often paired utility is negative because both branches pay the full scan cost inside an 8-step horizon.

Package version 0.2.0. Python 3.13.1 on Windows-10-10.0.19045-SP0.
