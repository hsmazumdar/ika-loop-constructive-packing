# Expt-17 — Arrangement census

Read-only acquisition. Do successful primitive packings contain small connected arrangements that recur across different inventories and can be recognised cheaply enough to justify a later reuse test?

1. Extract connected groups of 2 or 3 placed pieces from acceptable training packings. Keep relative geometry and piece counts. No rectangular outline. No large-piece ordering.
2. Remove absolute position by translation only. That normalisation is engineered, not discovered. Rotations and reflections are not applied.
3. Count distinct training inventories. Repeats inside one trajectory count once. Two seeds of one inventory count as one inventory. Extraction stops at 4,000 groups examined per box.
4. Freeze patterns that appear in at least two inventories. On fresh ordinary trajectories, record whether a frozen group fits in free space with the pieces still available. Bill the checks. Bin opportunities by occupied cells: early below 34, middle below 67, late otherwise.
5. Stop at coverage. A fit is not placed.

Problem sets are the hash-checked Expt-16 manifests. The primitive phase strings match Expt-16, so the trajectories are the same solves.

```text
python -m pytest -q
python run_expt17.py --smoke
python run_expt17.py --diagnostic
```
