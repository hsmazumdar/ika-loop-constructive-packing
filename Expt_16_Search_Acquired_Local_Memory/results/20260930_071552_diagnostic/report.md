# Expt-16 report

Were the bounded regions observed during ordinary packing fillable with the pieces available at that moment, but left unfinished by the primitive policy? Acquisition searches each recorded region offline, under a predeclared budget, without changing the store trajectory. Successful exact fillings are frozen as local entries and first tested read-only on fresh ordinary trajectories. Downstream consequences at compatible matches are measured by paired counterfactuals from the same saved state; these are diagnostic work, not information available to an agent. Partial fillings are not considered.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_16_Search_Acquired_Local_Memory\results\20260930_071552_diagnostic`
- Preset: `diagnostic`; problem sets from frozen manifests (hash-checked).
- Region size range 8–20 cells; entry key (translation-normalised geometry, consumed multiset); alternative placements for the same key recorded, not merged away.
- No transformations, hierarchy, learned gate, or partial fillings.

## Acquisition (offline search at recorded region snapshots; store trajectories unchanged)

- Store trajectories 48 (excluded as not acceptable: 8); bounded region snapshots 128.
- Search budget per region: 20000 candidate placements examined (predeclared).
- Outcomes: exact filling found 5; proven impossible 123; budget exhausted, feasibility unknown 0. Fill rate 0.03906.
- Of the proven-impossible regions, 52 were ruled out at the root by area alone (region size not a sum of available piece sizes, 4/5/7 cells); the rest by exhaustive shape search.
- Fillings validated on the rebuilt board: 5. Fillings using only pieces the store trajectory left unused at the end: 4.
- By region size: {'8': {'impossible': 17, 'found': 2}, '9': {'found': 1, 'impossible': 14}, '10': {'impossible': 13}, '11': {'impossible': 12}, '12': {'impossible': 10, 'found': 1}, '13': {'impossible': 9}, '14': {'impossible': 6}, '15': {'impossible': 10}, '16': {'impossible': 9}, '17': {'impossible': 9}, '18': {'impossible': 8}, '19': {'found': 1, 'impossible': 3}, '20': {'impossible': 3}}.
- By placements remaining when the region appeared: {'0': {'impossible': 9}, '1': {'impossible': 15}, '2': {'impossible': 20}, '3': {'impossible': 21, 'found': 2}, '4': {'found': 1, 'impossible': 24}, '5': {'impossible': 11}, '6': {'found': 2, 'impossible': 6}, '7': {'impossible': 7}, '8': {'impossible': 2}, '9': {'impossible': 3}, '10': {'impossible': 2}, '11': {'impossible': 3}}.
- Search evals when found: {'mean': 777.4, 'median': 325, 'max': 2934}; when proven impossible: {'mean': 443.3008130081301, 'median': 140}.
- Acquisition costs (separate): detection 20684, search 58413, validation 13, insertion 10.
- Table: 5 entries in 5 geometries; insertion outcomes {'written': 5}; entries with alternative placements 0; geometries with more than one multiset 0.

## Applicability (read-only matching on fresh ordinary trajectories)

The detector is the unchanged Expt-15 flood fill, billed per free cell visited. Its overhead is reported explicitly and has not been optimised.

- Independent fresh inventories: 60 boxes (0 repeat a store inventory); regions per box 2.867; detector 497.8 per box, lookup 2.867, availability 0.05 (total detector/lookup 30042; primitive A per box 1598); geometry matches 3 in 3 boxes; inventory-compatible matches 1 in 1 boxes (1 on new whole inventories).
- Recurring task families: 60 boxes (0 repeat a store inventory); regions per box 3.267; detector 497.1 per box, lookup 3.267, availability 0.03333 (total detector/lookup 30021; primitive A per box 1138); geometry matches 2 in 2 boxes; inventory-compatible matches 1 in 1 boxes (1 on new whole inventories).

## Downstream consequences at compatible matches (diagnostic counterfactuals)

Both branches start from the same saved state (board, inventory, RNG state, tabu) with remaining cap eval_cap − prefix A. Commit branch: validate and place the stored filling, then primitive. Primitive branch: primitive only. These are diagnostic work, not information available to an agent.

- Primitive branch reproduced the original trajectory at 2 of 2 matches.
- First compatible match per box, first stored entry (primary): n=2 in 2 boxes; valid 2; remaining-effort saving mean -242 median -242 (positive 1, negative 1); quality delta mean -0.5; quality-loss 0 (0), gain 0; acceptability lost 0; mean region size 8.
- All matches, first entry: n=2 in 2 boxes; valid 2; remaining-effort saving mean -242 median -242 (positive 1, negative 1); quality delta mean -0.5; quality-loss 0 (0), gain 0; acceptability lost 0; mean region size 8.
- All matches, all diagnosed entries: n=2 in 2 boxes; valid 2; remaining-effort saving mean -242 median -242 (positive 1, negative 1); quality delta mean -0.5; quality-loss 0 (0), gain 0; acceptability lost 0; mean region size 8.
- Primary, Independent fresh inventories: n=1 in 1 boxes; valid 1; remaining-effort saving mean 94 median 94 (positive 1, negative 0); quality delta mean 0; quality-loss 0 (0), gain 0; acceptability lost 0; mean region size 8.
- Primary, Recurring task families: n=1 in 1 boxes; valid 1; remaining-effort saving mean -578 median -578 (positive 0, negative 1); quality delta mean -1; quality-loss 0 (0), gain 0; acceptability lost 0; mean region size 8.

## Decision

- Primary row: **few_fillings**. These late regions may be poor acquisition targets.
- All rows whose predeclared condition holds: few_fillings (These late regions may be poor acquisition targets.); no_recurrence (Representation or coverage remains the problem.)
- Counterfactuals were computed because compatible matches existed, but they fall below the recurrence threshold and are descriptive only.
- Few-fillings flag (fill rate < 0.1 or no entries): True. Fresh boxes with a compatible match: 2 (recurrence threshold 3).
- not run: a deployed policy is tested only after the decision row saves_and_preserves.
