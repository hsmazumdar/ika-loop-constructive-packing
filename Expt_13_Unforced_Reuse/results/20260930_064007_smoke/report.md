# Expt-13 report

Does frozen exact and learned-transform memory reduce total effort at preserved quality when the agent must reach reusable states through its own ordinary decisions, without constructed prefixes or scheduled matches? Absence of reuse means this environment rarely supplies the recurrence the mechanism needs, not that demonstrated recall has disappeared.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_13_Unforced_Reuse\results\20260930_064007_smoke`
- Preset: `smoke`
- Independent store: ['inv_2f4940dd8206', 'inv_82c6d6f9ea01'].
- Family store: ['inv_523e0d487bd9'].
- Family specs (declared before evaluation, no table consult): [{'family_id': 'fam_56b8c7003102', 'type_set': ['A', 'H', 'I', 'K', 'L'], 'rule': 'independent catalogue packings restricted to a frozen type-set; inventory counts may differ; the memory table is not consulted', 'consults_memory_table': False}].
- Frozen keys: 45 (empty-board 3); overwrites 0; bytes 6191.
- Table frozen before evaluation: True. Selection frozen before evaluation: True.
- Coverage pass (selection only, not evaluation): {'n_constructed_train_cases': 3, 'n_constructed_total': 6, 'used_for_evaluation': False, 'rule': 'T-first coverage pass; same Expt-11 selection rule; not an evaluation workload'}.
- Selected: ['rot90', 'rot180'].
- Coverage (attempts / compatible / valid_replays / successes / fails): {'rot90': {'attempts': 3, 'compatible': 2, 'valid_replays': 2, 'successes': 2, 'fails': 0, 'insufficient_coverage': False}, 'rot180': {'attempts': 3, 'compatible': 1, 'valid_replays': 1, 'successes': 1, 'fails': 0, 'insufficient_coverage': False}, 'rot270': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_x': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_y': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_d': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_ad': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}}.
- Selection rule is the frozen Expt-11 rule. The T-first coverage pass is the same additional training used in Expt-12; it is not an evaluation workload.
- A = primitive_evals + lookup + matching + transformation + validation + learning.
- Evaluation has no constructed prefixes, no scheduled matches, and no task-category input to the agent.
- Seeds are paired comparisons on identical starts, not independent learned memories.

## Independent fresh inventories

- Independent streams: 1.
- Across-stream mean effort-saving: -58.5 (min -58.5, max -58.5).
- Across-stream mean valid-reuse fraction: 0.
- Across-stream mean quality-loss: 0.
- Initial-state hits: 0; intermediate hits after autonomous placements: 0.
- Reuse present: False. Net-save and quality ok: False.
- this environment rarely supplied the recurrence the mechanism needs

- stream 0 / learned: n=2 (2 tasks × 1 paired seeds); mean A 4313; mean Q 73; mean effort-saving -58.5; quality-loss 0 (n=0); valid-reuse 0/2 (0); initial hits 0; intermediate hits 0; mean primitive-evals before first hit NA; mean lookup 19.5; matching 39; constructed-prefix rows 0.

## Recurring task families with varying inventories

- Independent streams: 1.
- Across-stream mean effort-saving: -48 (min -48, max -48).
- Across-stream mean valid-reuse fraction: 0.
- Across-stream mean quality-loss: 0.
- Initial-state hits: 0; intermediate hits after autonomous placements: 0.
- Reuse present: False. Net-save and quality ok: False.
- this environment rarely supplied the recurrence the mechanism needs

- stream 0 / learned: n=2 (2 tasks × 1 paired seeds); mean A 1696; mean Q 75; mean effort-saving -48; quality-loss 0 (n=0); valid-reuse 0/2 (0); initial hits 0; intermediate hits 0; mean primitive-evals before first hit NA; mean lookup 16; matching 32; constructed-prefix rows 0.

## All agents by stream

- independent_fresh_s0/primitive: n=2; mean A 4254; mean Q 73; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/2; initial 0 intermediate 0; mean lookup 0; matching 0.
- independent_fresh_s0/exact: n=2; mean A 4274; mean Q 73; mean effort-saving -19.5; quality-loss 0 (n=0); valid-reuse 0/2; initial 0 intermediate 0; mean lookup 19.5; matching 0.
- independent_fresh_s0/learned: n=2; mean A 4313; mean Q 73; mean effort-saving -58.5; quality-loss 0 (n=0); valid-reuse 0/2; initial 0 intermediate 0; mean lookup 19.5; matching 39.
- recurring_family_s0/primitive: n=2; mean A 1648; mean Q 75; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/2; initial 0 intermediate 0; mean lookup 0; matching 0.
- recurring_family_s0/exact: n=2; mean A 1664; mean Q 75; mean effort-saving -16; quality-loss 0 (n=0); valid-reuse 0/2; initial 0 intermediate 0; mean lookup 16; matching 0.
- recurring_family_s0/learned: n=2; mean A 1696; mean Q 75; mean effort-saving -48; quality-loss 0 (n=0); valid-reuse 0/2; initial 0 intermediate 0; mean lookup 16; matching 32.

- Evaluation has no constructed prefixes and no scheduled matching states. Family inventories are generated from a predeclared type-set rule that does not consult the memory table. Seeds are paired comparisons on identical starts, not independent learned memories. Results are summarised across independent streams. The table and selected transforms are frozen before evaluation; there is no online memory growth. Initial-state hits are reported separately from intermediate hits after autonomous placements.
