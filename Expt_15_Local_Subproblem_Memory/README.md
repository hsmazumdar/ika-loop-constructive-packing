# Expt-15 — Local subproblem memory

A local entry records how to fill a bounded free region (translation-normalised geometry) with a specified piece multiset, the relative placements, and measured acquisition cost. It matches when the region geometry is identical and the multiset is available; the rest of the board and unused inventory may differ. No transformations, hierarchy, or learned gate.

- Test 1: constructed independent regions with assigned piece budgets. The region is supplied as an experimental aid, not learned decomposition. Conditions: primitive whole, exact whole-state, primitive decomposed, local decomposed.
- Test 2: ordinary packing with naturally occurring regions and shared inventory. Regions are found by an engineered flood fill next to each placement, billed per free cell visited. Conditions: primitive, exact whole-state, local.

```text
python -m pytest -q
python run_expt15.py --smoke
python run_expt15.py --diagnostic
```
