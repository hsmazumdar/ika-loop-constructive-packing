# Expt-16 — Search-acquired local memory

Bounded acquisition diagnosis. Were bounded regions seen during ordinary packing exactly fillable with the pieces available at that moment, but left unfinished by the primitive policy?

1. Frozen problem sets: `manifests/` (hash-checked; created once by `tools/freeze_manifests.py`, which refuses to overwrite). The acquisition store is the Expt-15 store set that produced the 128-region census.
2. Offline search at each region snapshot, store trajectory unchanged. Outcomes: found, proven impossible, budget exhausted (unknown).
3. Detection, search, validation, and insertion billed separately.
4. Entries keyed by (geometry, multiset); alternative placements recorded.
5. Frozen table; read-only matching on fresh ordinary trajectories.
6. Paired counterfactuals (commit then primitive vs primitive only) from the same saved state, diagnostic only.

No transformations, hierarchy, learned gate, or partial fillings. A deployed policy is tested only if the decision row is `saves_and_preserves`.

```text
python -m pytest -q
python run_expt16.py --smoke
python run_expt16.py --diagnostic
```
