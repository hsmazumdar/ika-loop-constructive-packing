# Expt-10 report

Can an exact remaining-state continuation replace the rest of search after a genuine non-empty primitive prefix inside an otherwise new problem? This is memorization, not abstraction. Whole-solution recall from the empty board is retained only as a positive control.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_10_Exact_Subproblem_Reuse\results\20260930_055508_smoke`
- Preset: `smoke`
- Store boxes (2): ['inv_03fd2ad4b58d', 'inv_3254a8f18876'].
- Fresh boxes (2): ['inv_6416ed2616d2', 'inv_03be0c5a020a'].
- Constructed boxes (1): ['cstr_8b461c7489a8'].
- Continuation keys stored: 32 (2 empty-board, 30 intermediate); storage bytes 4680; overwrites counted not stored 0; table frozen before eval.
- Memory: shared across seeds; first write wins; not per-agent; not best-of.
- A = primitive_evals + lookup + validation + learning.
- Exact reuse is memorization. It is not evidence of abstraction and not a confirmation of Expt-8C.
- Constructed recurrence is labeled. Each constructed inventory is an alternative covering of a stored prefix region, so the remaining (mask, inventory) matches after a nonempty prefix. Empty-board matches are excluded.
- Natural intermediate recurrence is counted on fresh primitive traces (occupied > 0) without taking the hit. It is not pooled with constructed hits.

## Recurrence

- Recurring complete problems lookup hit rate: 1.
- Constructed intermediate lookup hit rate: 1.
- Fresh lookup hit rate: 0. Fresh completed solves on new inventories; hits would be accidental identical remaining states.
- Natural intermediate opportunity rate on fresh primitive traces: 0.

## Constructed donors

- cstr_8b461c7489a8 from donor inv_03fd2ad4b58d (first successful seed 11); cut 2; prefix occupied 10; alt prefix length 2; stored suffix length 14.

## Conditions

- store/primitive: n=2; mean A 856; mean Q 77; mean effort-saving 0; mean remaining-search-avoided 0; mean prefix primitive 840; mean prefix placements 16; mean first-hit occupied NA; quality-loss 0; acceptable 1; hit rate NA (0/0 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 0; mean validation 0; mean learning 16; mean primitive_evals 840; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- recurring/exact: n=2; mean A 17; mean Q 77; mean effort-saving 823; mean remaining-search-avoided 840; mean prefix primitive 0; mean prefix placements 0; mean first-hit occupied 0; quality-loss 0; acceptable 1; hit rate 1 (2/2 lookups); replays 2; validation fails 0; initial-state hits 2; nonzero-prefix hits 0; mean lookup 1; mean validation 16; mean learning 0; mean primitive_evals 0; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- constructed/memory_off: n=1; mean A 816; mean Q 76; mean effort-saving 0; mean remaining-search-avoided 0; mean prefix primitive 96; mean prefix placements 2; mean first-hit occupied NA; quality-loss 0; acceptable 1; hit rate NA (0/0 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 0; mean validation 0; mean learning 0; mean primitive_evals 816; mean remaining primitive 720; natural-opportunity traces 0 (rate 0).
- constructed/memory_on: n=1; mean A 111; mean Q 76; mean effort-saving 705; mean remaining-search-avoided 720; mean prefix primitive 96; mean prefix placements 2; mean first-hit occupied 10; quality-loss 0; acceptable 1; hit rate 1 (1/1 lookups); replays 1; validation fails 0; initial-state hits 0; nonzero-prefix hits 1; mean lookup 1; mean validation 14; mean learning 0; mean primitive_evals 96; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- fresh/primitive: n=2; mean A 768; mean Q 75.5; mean effort-saving 0; mean remaining-search-avoided 0; mean prefix primitive 768; mean prefix placements 15.5; mean first-hit occupied NA; quality-loss 0; acceptable 1; hit rate NA (0/0 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 0; mean validation 0; mean learning 0; mean primitive_evals 768; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- fresh/exact: n=2; mean A 783.5; mean Q 75.5; mean effort-saving -15.5; mean remaining-search-avoided 0; mean prefix primitive 768; mean prefix placements 15.5; mean first-hit occupied NA; quality-loss 0; acceptable 1; hit rate 0 (0/31 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 15.5; mean validation 0; mean learning 0; mean primitive_evals 768; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).

- Useful on recurring complete repeats: True.
- Useful on constructed intermediate reuse (positive remaining-search avoided, quality-loss ≤ 0.2, nonzero-prefix hits, zero initial-state hits): True.
- Exact reuse is memorization. Constructed tasks are labeled: an alternative covering reaches a stored (mask, inventory) after a nonempty prefix. Natural intermediate recurrence on fresh primitive traces is reported separately. Fresh completed solves measure lookup overhead when no stored remaining state matches.
