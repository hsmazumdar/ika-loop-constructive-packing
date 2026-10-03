# Expt-2A — Cost-aware use of discovered operations

Held-out inventories only. The library is the flat library saved by the baseline discovery smoke. It is frozen: this run does not discover a new operation into long-term memory and does not change that file.

- Library run: `results/20260929_092518_discovery_smoke`
- Seeds: [11, 22]
- Eval boxes per policy per seed: 12
- Candidate-eval cap: 50000
- Cheap-scan reserve: 0
- Fixed THINK allowance: 3636 evaluations, one catalogue pass, chosen before this comparison.

The four policies share that cap. `primitive_only` ignores the library. `library_lookup` may execute stored operations and does not THINK. `fixed_think` may THINK until the allowance is spent, then acts. `adaptive_think` is the current flat interval of one THINK batch every 5 decisions, with no extra stop.

Training cost that created the library is not charged again here. The question is whether the stored operations are worth using inside a held-out box.

## One box

- Policy `adaptive_think`, seed 11, task `inv_37a9c4ede811`.
- Occupied cells 24. Evaluations 50000. Physical actions 5. Macros 1. THINK batches 1. Termination `compute_budget`.
- Plot: `BOX_TRACE.png`. Per-decision counts: `BOX_TRACE.json`.

Evaluations in that box, as a partition of candidate evaluations:

- candidate: 0
- paired: 38132
- library_scan: 960
- lookahead: 0
- placement: 10908
- think: 0
- other: 0
- think_span: 38132

`think_span` includes paired tests that ran inside THINK. `candidate` is proposal generation; it does not examine placements. `paired` includes the guard scans inside paired tests. `library_scan` is an origin check for a stored operation on the real board.

## Held-out means

| policy | seed | n | final mean | evals mean | physical mean | macros mean | think batches |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primitive_only | 11 | 12 | 66.58 | 50000.0 | 13.92 | 0.000 | 0.00 |
| primitive_only | 22 | 12 | 66.92 | 50000.0 | 13.83 | 0.000 | 0.00 |
| library_lookup | 11 | 12 | 66.17 | 47661.0 | 14.00 | 0.917 | 0.00 |
| library_lookup | 22 | 12 | 67.25 | 48309.7 | 14.33 | 1.000 | 0.00 |
| fixed_think | 11 | 12 | 63.42 | 48570.0 | 13.42 | 0.917 | 1.00 |
| fixed_think | 22 | 12 | 65.83 | 49153.0 | 13.92 | 1.083 | 1.00 |
| adaptive_think | 11 | 12 | 22.92 | 50000.0 | 4.75 | 0.750 | 1.00 |
| adaptive_think | 22 | 12 | 23.92 | 50000.0 | 5.00 | 0.917 | 1.00 |

## Success criterion

A frozen library policy meets the criterion only when, on every seed, its mean occupied cells are higher than `primitive_only` at this same cap, or its mean occupied cells are at least as high and its mean evaluations are lower.

- `library_lookup`: does not meet the criterion on every seed.
  - seed 11: score 66.17 vs primitive 66.58; evals 47661.0 vs 50000.0.
  - seed 22: score 67.25 vs primitive 66.92; evals 48309.7 vs 50000.0.
- `fixed_think`: does not meet the criterion on every seed.
  - seed 11: score 63.42 vs primitive 66.58; evals 48570.0 vs 50000.0.
  - seed 22: score 65.83 vs primitive 66.92; evals 49153.0 vs 50000.0.
- `adaptive_think`: does not meet the criterion on every seed.
  - seed 11: score 22.92 vs primitive 66.58; evals 50000.0 vs 50000.0.
  - seed 22: score 23.92 vs primitive 66.92; evals 50000.0 vs 50000.0.

No frozen library policy meets the criterion on every seed. The one-box breakdown is the evidence for what to change. A learned stopping rule and a hierarchy comparison were not run.

Postponed: teaching the dispatcher to stop THINK from an expected-gain estimate, testing a parent against its flattened children, and any memory or harder-task sweep.
