# Expt-16 report

Were the bounded regions observed during ordinary packing fillable with the pieces available at that moment, but left unfinished by the primitive policy? Acquisition searches each recorded region offline, under a predeclared budget, without changing the store trajectory. Successful exact fillings are frozen as local entries and first tested read-only on fresh ordinary trajectories. Downstream consequences at compatible matches are measured by paired counterfactuals from the same saved state; these are diagnostic work, not information available to an agent. Partial fillings are not considered.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_16_Search_Acquired_Local_Memory\results\20260930_071502_smoke`
- Preset: `smoke`; problem sets from frozen manifests (hash-checked).
- Region size range 8–20 cells; entry key (translation-normalised geometry, consumed multiset); alternative placements for the same key recorded, not merged away.
- No transformations, hierarchy, learned gate, or partial fillings.

## Acquisition (offline search at recorded region snapshots; store trajectories unchanged)

- Store trajectories 2 (excluded as not acceptable: 0); bounded region snapshots 8.
- Search budget per region: 5000 candidate placements examined (predeclared).
- Outcomes: exact filling found 1; proven impossible 7; budget exhausted, feasibility unknown 0. Fill rate 0.125.
- Fillings validated on the rebuilt board: 1. Fillings using only pieces the store trajectory left unused at the end: 1.
- By region size: {'8': {'impossible': 2}, '9': {'found': 1}, '11': {'impossible': 1}, '13': {'impossible': 1}, '14': {'impossible': 1}, '15': {'impossible': 2}}.
- By placements remaining when the region appeared: {'0': {'impossible': 1}, '1': {'impossible': 1}, '3': {'impossible': 1}, '4': {'found': 1, 'impossible': 1}, '5': {'impossible': 2}, '9': {'impossible': 1}}.
- Search evals when found: {'mean': 325.0, 'median': 325, 'max': 325}; when proven impossible: {'mean': 128.42857142857142, 'median': 103}.
- Acquisition costs (separate): detection 913, search 1224, validation 2, insertion 2.
- Table: 1 entries in 1 geometries; insertion outcomes {'written': 1}; entries with alternative placements 0; geometries with more than one multiset 0.

## Applicability (read-only matching on fresh ordinary trajectories)

The detector is the unchanged Expt-15 flood fill, billed per free cell visited. Its overhead is reported explicitly and has not been optimised.

- Independent fresh inventories: 3 boxes (0 repeat a store inventory); regions per box 3.667; detector 538.3 per box, lookup 3.667, availability 0 (total detector/lookup 1626; primitive A per box 4835); geometry matches 0 in 0 boxes; inventory-compatible matches 0 in 0 boxes (0 on new whole inventories).
- Recurring task families: 3 boxes (0 repeat a store inventory); regions per box 3.333; detector 534.7 per box, lookup 3.333, availability 0 (total detector/lookup 1614; primitive A per box 816); geometry matches 0 in 0 boxes; inventory-compatible matches 0 in 0 boxes (0 on new whole inventories).
- no compatible matches; stopped before counterfactuals.

## Downstream consequences at compatible matches (diagnostic counterfactuals)

- Not run.

## Decision

- Row: **no_recurrence**. Representation or coverage remains the problem.
- Few-fillings flag (fill rate < 0.1 or no entries): False. Fresh boxes with a compatible match: 0 (recurrence threshold 3).
- not run: a deployed policy is tested only after the decision row saves_and_preserves.
