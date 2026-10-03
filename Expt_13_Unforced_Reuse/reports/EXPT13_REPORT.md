# Expt-13 report

Does frozen exact and learned-transform memory reduce total effort at preserved quality when the agent must reach reusable states through its own ordinary decisions, without constructed prefixes or scheduled matches? Absence of reuse means none was observed in these streams with this frozen table and exact state representation. It does not establish how rare recurrence is throughout the environment, and it does not mean demonstrated recall has disappeared.

- Directory: `results\20260930_064034_diagnostic`
- Preset: `diagnostic`
- Independent store: ['inv_d8b68bbe6798', 'inv_2c026de405cd', 'inv_fa5d7bb4b837', 'inv_71dd471978b7', 'inv_f97271a89ede', 'inv_dfea32dc34c7', 'inv_020ca7562c34', 'inv_ff4853a411a8'].
- Family store: ['inv_8f0ffed15b9f', 'inv_dc647e71af2e', 'inv_d2a00773eba7', 'inv_254bd10f46ed', 'inv_9412901a0b50', 'inv_4483192f48f2', 'inv_0bf3275a34ee', 'inv_acfcfa621f58'].
- Family specs (declared before evaluation, no table consult): [{'family_id': 'fam_be5a68440841', 'type_set': ['B', 'D', 'E', 'K', 'L', 'O'], 'rule': 'independent catalogue packings restricted to a frozen type-set; inventory counts may differ; the memory table is not consulted', 'consults_memory_table': False}, {'family_id': 'fam_9189233f2ede', 'type_set': ['A', 'C', 'J', 'M'], 'rule': 'independent catalogue packings restricted to a frozen type-set; inventory counts may differ; the memory table is not consulted', 'consults_memory_table': False}, {'family_id': 'fam_7811cbc0cb65', 'type_set': ['A', 'B', 'E', 'F', 'J', 'L', 'P'], 'rule': 'independent catalogue packings restricted to a frozen type-set; inventory counts may differ; the memory table is not consulted', 'consults_memory_table': False}, {'family_id': 'fam_597b55393d4e', 'type_set': ['A', 'B', 'F', 'K', 'L', 'N'], 'rule': 'independent catalogue packings restricted to a frozen type-set; inventory counts may differ; the memory table is not consulted', 'consults_memory_table': False}].
- Frozen keys: 683 (empty-board 16); overwrites 33; bytes 92336.
- Table frozen before evaluation: True. Selection frozen before evaluation: True.
- Coverage pass (selection only, not evaluation): {'n_constructed_train_cases': 22, 'n_constructed_total': 33, 'used_for_evaluation': False, 'rule': 'T-first coverage pass; same Expt-11 selection rule; not an evaluation workload'}.
- Selected: ['rot90', 'rot180', 'rot270'].
- Coverage (attempts / compatible / valid_replays / successes / fails): {'rot90': {'attempts': 22, 'compatible': 11, 'valid_replays': 11, 'successes': 11, 'fails': 0, 'insufficient_coverage': False}, 'rot180': {'attempts': 22, 'compatible': 7, 'valid_replays': 7, 'successes': 7, 'fails': 0, 'insufficient_coverage': False}, 'rot270': {'attempts': 22, 'compatible': 4, 'valid_replays': 4, 'successes': 4, 'fails': 0, 'insufficient_coverage': False}, 'refl_x': {'attempts': 22, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_y': {'attempts': 22, 'compatible': 1, 'valid_replays': 0, 'successes': 0, 'fails': 1, 'insufficient_coverage': False}, 'refl_d': {'attempts': 22, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_ad': {'attempts': 22, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}}.
- Selection rule is the frozen Expt-11 rule. The T-first coverage pass is the same additional training used in Expt-12; it is not an evaluation workload. A transform with a recorded failure is excluded on evidence; one with zero compatible keys is excluded for insufficient coverage.
- A = primitive_evals + lookup + matching + transformation + validation + learning.
- Evaluation has no constructed prefixes, no scheduled matches, and no task-category input to the agent. Family inventories were not filtered against stored inventories.
- Seeds are paired comparisons on identical starts, not independent learned memories.

## Independent fresh inventories

- Independent streams: 3.
- Learned: across-stream mean effort-saving -65.17 (min -65.83, max -64.5).
- Across-stream mean fraction of boxes with valid reuse: 0.
- Across-stream mean quality-loss: 0.
- Initial-state hits: 0. Intermediate hits after autonomous placements: 0.
- Net-save and quality ok: False. Autonomous-intermediate success: False.
- Verdict: no valid reuse observed in these streams with this frozen table and exact state representation; this does not establish how rare recurrence is throughout the environment.

- stream 0 / learned: n=24 (8 tasks × 3 paired seeds); mean A 1590; mean Q 75.25; mean effort-saving -65.17; mean quality delta 0; quality-loss 0 (n=0); valid-reuse 0/24; initial hits 0; intermediate hits 0; mean primitive-evals before first hit NA; mean lookup 16.29; matching 48.88; constructed-prefix rows 0.
- stream 1 / learned: n=24 (8 tasks × 3 paired seeds); mean A 1283; mean Q 75.96; mean effort-saving -65.83; mean quality delta 0; quality-loss 0 (n=0); valid-reuse 0/24; initial hits 0; intermediate hits 0; mean primitive-evals before first hit NA; mean lookup 16.46; matching 49.38; constructed-prefix rows 0.
- stream 2 / learned: n=24 (8 tasks × 3 paired seeds); mean A 1420; mean Q 76.12; mean effort-saving -64.5; mean quality delta 0; quality-loss 0 (n=0); valid-reuse 0/24; initial hits 0; intermediate hits 0; mean primitive-evals before first hit NA; mean lookup 16.12; matching 48.38; constructed-prefix rows 0.

## Recurring task families with varying inventories

- Independent streams: 3.
- Learned: across-stream mean effort-saving 96.24 (min 57.47, max 153.5).
- Across-stream mean fraction of boxes with valid reuse: 0.1111.
- Across-stream mean quality-loss: 0.
- Initial-state hits: 12. Intermediate hits after autonomous placements: 0.
- Net-save and quality ok: True. Autonomous-intermediate success: False.
- Verdict: all hits were initial-state whole-problem recurrences (the inventory itself repeated); no reusable intermediate state was reached through autonomous placements in these streams; net saving came from exact whole-problem recall.

- stream 0 / learned: n=36 (12 tasks × 3 paired seeds); mean A 1976; mean Q 75.31; mean effort-saving 77.78; mean quality delta 0.2222; quality-loss 0 (n=0); valid-reuse 3/36; initial hits 3; intermediate hits 0; mean primitive-evals before first hit 0; mean lookup 15.58; matching 46.5; constructed-prefix rows 0.
- stream 1 / learned: n=36 (12 tasks × 3 paired seeds); mean A 1091; mean Q 75.61; mean effort-saving 153.5; mean quality delta 0.25; quality-loss 0 (n=0); valid-reuse 6/36; initial hits 6; intermediate hits 0; mean primitive-evals before first hit 0; mean lookup 13.19; matching 39.08; constructed-prefix rows 0.
- stream 2 / learned: n=36 (12 tasks × 3 paired seeds); mean A 1586; mean Q 75.31; mean effort-saving 57.47; mean quality delta 0.1111; quality-loss 0 (n=0); valid-reuse 3/36; initial hits 3; intermediate hits 0; mean primitive-evals before first hit 0; mean lookup 15.22; matching 45.42; constructed-prefix rows 0.

## Decomposition by whether the inventory itself repeated a stored inventory

An initial-state hit requires the whole inventory to repeat. It is exact whole-problem recall, not a reusable state reached through autonomous placements.

- independent_fresh / exact / inventory new: n=72 (24 task-ids); mean effort-saving -16.29; mean quality delta 0; quality-loss 0/72; valid-reuse 0/72; initial hits 0; intermediate hits 0.
- independent_fresh / learned / inventory new: n=72 (24 task-ids); mean effort-saving -65.17; mean quality delta 0; quality-loss 0/72; valid-reuse 0/72; initial hits 0; intermediate hits 0.
- recurring_family / exact / inventory repeats store: n=12 (2 task-ids); mean effort-saving 1313; mean quality delta 1.75; quality-loss 0/12; valid-reuse 12/12; initial hits 12; intermediate hits 0.
- recurring_family / exact / inventory new: n=96 (30 task-ids); mean effort-saving -16.39; mean quality delta 0; quality-loss 0/96; valid-reuse 0/96; initial hits 0; intermediate hits 0.
- recurring_family / learned / inventory repeats store: n=12 (2 task-ids); mean effort-saving 1313; mean quality delta 1.75; quality-loss 0/12; valid-reuse 12/12; initial hits 12; intermediate hits 0.
- recurring_family / learned / inventory new: n=96 (30 task-ids); mean effort-saving -55.83; mean quality delta 0; quality-loss 0/96; valid-reuse 0/96; initial hits 0; intermediate hits 0.

## All agents by stream

- independent_fresh_s0/primitive: n=24; mean A 1525; mean Q 75.25; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 0; matching 0.
- independent_fresh_s1/primitive: n=24; mean A 1217; mean Q 75.96; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 0; matching 0.
- independent_fresh_s2/primitive: n=24; mean A 1356; mean Q 76.12; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 0; matching 0.
- independent_fresh_s0/exact: n=24; mean A 1541; mean Q 75.25; mean effort-saving -16.29; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 16.29; matching 0.
- independent_fresh_s1/exact: n=24; mean A 1234; mean Q 75.96; mean effort-saving -16.46; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 16.46; matching 0.
- independent_fresh_s2/exact: n=24; mean A 1372; mean Q 76.12; mean effort-saving -16.12; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 16.12; matching 0.
- independent_fresh_s0/learned: n=24; mean A 1590; mean Q 75.25; mean effort-saving -65.17; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 16.29; matching 48.88.
- independent_fresh_s1/learned: n=24; mean A 1283; mean Q 75.96; mean effort-saving -65.83; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 16.46; matching 49.38.
- independent_fresh_s2/learned: n=24; mean A 1420; mean Q 76.12; mean effort-saving -64.5; quality-loss 0 (n=0); valid-reuse 0/24; initial 0 intermediate 0; mean lookup 16.12; matching 48.38.
- recurring_family_s0/primitive: n=36; mean A 2054; mean Q 75.08; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/36; initial 0 intermediate 0; mean lookup 0; matching 0.
- recurring_family_s1/primitive: n=36; mean A 1244; mean Q 75.36; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/36; initial 0 intermediate 0; mean lookup 0; matching 0.
- recurring_family_s2/primitive: n=36; mean A 1644; mean Q 75.19; mean effort-saving 0; quality-loss 0 (n=0); valid-reuse 0/36; initial 0 intermediate 0; mean lookup 0; matching 0.
- recurring_family_s0/exact: n=36; mean A 1956; mean Q 75.31; mean effort-saving 98.47; quality-loss 0 (n=0); valid-reuse 3/36; initial 3 intermediate 0; mean lookup 15.61; matching 0.
- recurring_family_s1/exact: n=36; mean A 1052; mean Q 75.61; mean effort-saving 192.6; quality-loss 0 (n=0); valid-reuse 6/36; initial 6 intermediate 0; mean lookup 13.19; matching 0.
- recurring_family_s2/exact: n=36; mean A 1541; mean Q 75.31; mean effort-saving 102.9; quality-loss 0 (n=0); valid-reuse 3/36; initial 3 intermediate 0; mean lookup 15.22; matching 0.
- recurring_family_s0/learned: n=36; mean A 1976; mean Q 75.31; mean effort-saving 77.78; quality-loss 0 (n=0); valid-reuse 3/36; initial 3 intermediate 0; mean lookup 15.58; matching 46.5.
- recurring_family_s1/learned: n=36; mean A 1091; mean Q 75.61; mean effort-saving 153.5; quality-loss 0 (n=0); valid-reuse 6/36; initial 6 intermediate 0; mean lookup 13.19; matching 39.08.
- recurring_family_s2/learned: n=36; mean A 1586; mean Q 75.31; mean effort-saving 57.47; quality-loss 0 (n=0); valid-reuse 3/36; initial 3 intermediate 0; mean lookup 15.22; matching 45.42.

- Evaluation has no constructed prefixes and no scheduled matching states. Family inventories are generated from a predeclared type-set rule that does not consult the memory table. Seeds are paired comparisons on identical starts, not independent learned memories. Results are summarised across independent streams. The table and selected transforms are frozen before evaluation; there is no online memory growth. Initial-state hits are reported separately from intermediate hits after autonomous placements.
