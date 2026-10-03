# Expt-17 report

Do successful packing trajectories contain small arrangements that recur across different problems and can be recognized cheaply enough to justify testing their reuse?

Arrangements are connected groups of a few pieces taken from acceptable primitive packings. Absolute position is removed by translation only. That normalisation is an engineered representation choice, not a discovered equivalence. Groups are not filtered for a rectangular outline and are not ordered by piece size. The dictionary is frozen before fresh trajectories are examined. A legal fit is recorded and not placed.

- Directory: `results\20260930_090000_diagnostic`
- Preset: `diagnostic`
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Pattern size: 2 to 3 pieces. Extraction cap per box: 4000 groups.
- Recurrence: at least 2 distinct training inventories. Repeats inside one trajectory count as one box.
- Stage bins: early occupied < 34, middle until 67, then late.
- Cheap bar: matching checks below 0.1 of the same workload's mean primitive effort, and at least 3 independent fresh boxes with an early or middle fit.

## Acquisition

- Trajectories 48; acceptable 40; excluded 8.
- Extraction checks 24482 (612 per acceptable box). Connected groups examined 3139. Boxes stopped by the extraction cap: 0.
- Distinct patterns 3043. Frozen because they recur across inventories: 58.
- Frozen by piece count: {'2': 55, '3': 3}.
- Support by distinct inventories: {'1': 2985, '2': 53, '3': 4, '4': 1}.
- Support by independent boxes: {'1': 2967, '2': 64, '3': 10, '4': 2}.
- Store primitive effort per trajectory: 1736. Extraction is a separate count of groups examined, not candidate-placement evaluations.

## Fresh trajectories (read-only)

### independent_fresh

- Boxes 60; inventories also in the store: 0.
- Primitive effort per box 1598. Matching checks per box 7.287e+04 (45.6 times primitive effort).
- Boxes with any legal fit: 59. Boxes with an early or middle fit: 59.
- Fit events early 4999, middle 2089, late 19 (a prefix and a pattern with at least one translation).

### recurring_family

- Boxes 60; inventories also in the store: 0.
- Primitive effort per box 1138. Matching checks per box 9.31e+04 (81.8 times primitive effort).
- Boxes with any legal fit: 60. Boxes with an early or middle fit: 60.
- Fit events early 6888, middle 2206, late 36 (a prefix and a pattern with at least one translation).

## Decision

- Row: **fits_but_not_cheap**.
- Legal fits exist, but matching cost is not under the predeclared fraction of primitive effort.
- Commitment: not run. A fit is not admission into a policy.
- If this census is negative, the next change is the environment or the representation, not another memory mechanism on the same late-cavity idea.
