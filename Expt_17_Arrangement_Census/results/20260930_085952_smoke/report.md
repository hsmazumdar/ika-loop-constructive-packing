# Expt-17 report

Do successful packing trajectories contain small arrangements that recur across different problems and can be recognized cheaply enough to justify testing their reuse?

Arrangements are connected groups of a few pieces taken from acceptable primitive packings. Absolute position is removed by translation only. That normalisation is an engineered representation choice, not a discovered equivalence. Groups are not filtered for a rectangular outline and are not ordered by piece size. The dictionary is frozen before fresh trajectories are examined. A legal fit is recorded and not placed.

- Directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_17_Arrangement_Census\results\20260930_085952_smoke`
- Preset: `smoke`
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Pattern size: 2 to 3 pieces. Extraction cap per box: 4000 groups.
- Recurrence: at least 2 distinct training inventories. Repeats inside one trajectory count as one box.
- Stage bins: early occupied < 34, middle until 67, then late.
- Cheap bar: matching checks below 0.1 of the same workload's mean primitive effort, and at least 3 independent fresh boxes with an early or middle fit.

## Acquisition

- Trajectories 2; acceptable 2; excluded 0.
- Extraction checks 1120 (560 per acceptable box). Connected groups examined 151. Boxes stopped by the extraction cap: 0.
- Distinct patterns 151. Frozen because they recur across inventories: 0.
- Frozen by piece count: {}.
- Support by distinct inventories: {'1': 151}.
- Support by independent boxes: {'1': 151}.
- Store primitive effort per trajectory: 1920. Extraction is a separate count of groups examined, not candidate-placement evaluations.

## Fresh trajectories (read-only)

### independent_fresh

- Boxes 2; inventories also in the store: 0.
- Primitive effort per box 3120. Matching checks per box 0 (0 of primitive effort).
- Boxes with any legal fit: 0. Boxes with an early or middle fit: 0.
- Fit events early 0, middle 0, late 0 (a prefix and a pattern with at least one translation).

### recurring_family

- Boxes 2; inventories also in the store: 0.
- Primitive effort per box 792. Matching checks per box 0 (0 of primitive effort).
- Boxes with any legal fit: 0. Boxes with an early or middle fit: 0.
- Fit events early 0, middle 0, late 0 (a prefix and a pattern with at least one translation).

## Decision

- Row: **no_cross_inventory_recurrence**.
- No small arrangement recurred across the predeclared number of distinct training inventories.
- Commitment: not run. A fit is not admission into a policy.
- If this census is negative, the next change is the environment or the representation, not another memory mechanism on the same late-cavity idea.
