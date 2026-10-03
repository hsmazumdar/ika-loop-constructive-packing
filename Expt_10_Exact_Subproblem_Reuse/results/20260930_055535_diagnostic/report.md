# Expt-10 report

Can an exact remaining-state continuation replace the rest of search after a genuine non-empty primitive prefix inside an otherwise new problem? This is memorization, not abstraction. Whole-solution recall from the empty board is retained only as a positive control.

- Directory: `e:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_10_Exact_Subproblem_Reuse\results\20260930_055535_diagnostic`
- Preset: `diagnostic`
- Store boxes (12): ['inv_8f90151d2f41', 'inv_b7d902c2bbb3', 'inv_00a2b7802a3f', 'inv_a72eda8dd42d', 'inv_a26caf0a6da7', 'inv_1073a448a3e1', 'inv_92902c7772c4', 'inv_d0925af31fab', 'inv_32dcbb1b27ba', 'inv_1421d1c30977', 'inv_e02533291370', 'inv_730133179504'].
- Fresh boxes (12): ['inv_03fd2ad4b58d', 'inv_3254a8f18876', 'inv_fcb41de75195', 'inv_d8ae3f7f43d0', 'inv_bb451445fb30', 'inv_ce29862259f1', 'inv_102e32e795af', 'inv_d3c1d55a9b76', 'inv_ae861d7ff4cc', 'inv_e35813c55159', 'inv_d777c44459fc', 'inv_3ec8cc643dd3'].
- Constructed boxes (10): ['cstr_e92370e70657', 'cstr_b08758931fdb', 'cstr_0f12ce99f2fa', 'cstr_1eab26dd0a40', 'cstr_c0dabe15aecc', 'cstr_0add6dab9aab', 'cstr_10c5cb7edef5', 'cstr_9cae0debd697', 'cstr_bba529439d4c', 'cstr_a4c67a0d6492'].
- Continuation keys stored: 506 (12 empty-board, 494 intermediate); storage bytes 68744; overwrites counted not stored 22; table frozen before eval.
- Memory: shared across seeds; first write wins; not per-agent; not best-of.
- A = primitive_evals + lookup + validation + learning.
- Exact reuse is memorization. It is not evidence of abstraction and not a confirmation of Expt-8C.
- Constructed recurrence is labeled. Each constructed inventory is an alternative covering of a stored prefix region, so the remaining (mask, inventory) matches after a nonempty prefix. Empty-board matches are excluded.
- Natural intermediate recurrence is counted on fresh primitive traces (occupied > 0) without taking the hit. It is not pooled with constructed hits.

## Protocol

- One shared continuation table across seeds. First write wins. Evaluation agents share the frozen snapshot; they do not get private memories. A later seed's better packing is not retained.
- Constructed prefix: each step bills one primitive scan (same RNG stream for memory-on and memory-off), then commits the labeled alternative covering, not necessarily the scan's argmax. Lookups start only after that nonempty prefix. Empty-board matches are excluded.
- Remaining search avoided = primitive evaluations after the prefix on memory-off minus those after the prefix on memory-on.
- Recurring complete repeats allow an empty-board hit (Expt-9 positive control). That is whole-solution recall, not intermediate reuse.
- Fresh completed solves are new inventories. Hits there would be accidental exact remaining-state matches, not abstraction.

## Recurrence

- Recurring complete problems lookup hit rate: 1.
- Constructed intermediate lookup hit rate: 1.
- Fresh lookup hit rate: 0. Fresh completed solves on new inventories; hits would be accidental identical remaining states.
- Natural intermediate opportunity rate on fresh primitive traces: 0.

## Constructed donors

- cstr_e92370e70657 from donor inv_8f90151d2f41 (first successful seed 11); cut 3; prefix occupied 15; alt prefix length 3; stored suffix length 12.
- cstr_b08758931fdb from donor inv_00a2b7802a3f (first successful seed 11); cut 4; prefix occupied 20; alt prefix length 4; stored suffix length 12.
- cstr_0f12ce99f2fa from donor inv_a72eda8dd42d (first successful seed 11); cut 3; prefix occupied 15; alt prefix length 3; stored suffix length 13.
- cstr_1eab26dd0a40 from donor inv_a26caf0a6da7 (first successful seed 11); cut 3; prefix occupied 15; alt prefix length 3; stored suffix length 12.
- cstr_c0dabe15aecc from donor inv_1073a448a3e1 (first successful seed 11); cut 4; prefix occupied 20; alt prefix length 4; stored suffix length 12.
- cstr_0add6dab9aab from donor inv_d0925af31fab (first successful seed 11); cut 4; prefix occupied 20; alt prefix length 4; stored suffix length 12.
- cstr_10c5cb7edef5 from donor inv_32dcbb1b27ba (first successful seed 11); cut 2; prefix occupied 10; alt prefix length 2; stored suffix length 14.
- cstr_9cae0debd697 from donor inv_1421d1c30977 (first successful seed 11); cut 4; prefix occupied 20; alt prefix length 4; stored suffix length 13.
- cstr_bba529439d4c from donor inv_e02533291370 (first successful seed 11); cut 3; prefix occupied 21; alt prefix length 4; stored suffix length 10.
- cstr_a4c67a0d6492 from donor inv_730133179504 (first successful seed 11); cut 3; prefix occupied 17; alt prefix length 4; stored suffix length 13.

## Conditions

- store/primitive: n=36; mean A 1252; mean Q 75.61; mean effort-saving 0; mean remaining-search-avoided 0; mean prefix primitive 1238; mean prefix placements 15.72; mean first-hit occupied NA; quality-loss 0; acceptable 0.9444; hit rate NA (0/0 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 0; mean validation 0; mean learning 14.06; mean primitive_evals 1238; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- recurring/exact: n=36; mean A 16.5; mean Q 75.92; mean effort-saving 1222; mean remaining-search-avoided 1238; mean prefix primitive 0; mean prefix placements 0; mean first-hit occupied 0; quality-loss 0.05556; acceptable 1; hit rate 1 (36/36 lookups); replays 36; validation fails 0; initial-state hits 36; nonzero-prefix hits 0; mean lookup 1; mean validation 15.5; mean learning 0; mean primitive_evals 0; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- constructed/memory_off: n=30; mean A 1611; mean Q 75.3; mean effort-saving 0; mean remaining-search-avoided 0; mean prefix primitive 168; mean prefix placements 3.5; mean first-hit occupied NA; quality-loss 0; acceptable 0.9; hit rate NA (0/0 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 0; mean validation 0; mean learning 0; mean primitive_evals 1611; mean remaining primitive 1443; natural-opportunity traces 0 (rate 0).
- constructed/memory_on: n=30; mean A 181.3; mean Q 76; mean effort-saving 1430; mean remaining-search-avoided 1443; mean prefix primitive 168; mean prefix placements 3.5; mean first-hit occupied 17.3; quality-loss 0; acceptable 1; hit rate 1 (30/30 lookups); replays 30; validation fails 0; initial-state hits 0; nonzero-prefix hits 30; mean lookup 1; mean validation 12.3; mean learning 0; mean primitive_evals 168; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- fresh/primitive: n=36; mean A 1663; mean Q 75.56; mean effort-saving 0; mean remaining-search-avoided 0; mean prefix primitive 1663; mean prefix placements 16.17; mean first-hit occupied NA; quality-loss 0; acceptable 0.8611; hit rate NA (0/0 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 0; mean validation 0; mean learning 0; mean primitive_evals 1663; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).
- fresh/exact: n=36; mean A 1680; mean Q 75.56; mean effort-saving -16.92; mean remaining-search-avoided 0; mean prefix primitive 1663; mean prefix placements 16.17; mean first-hit occupied NA; quality-loss 0; acceptable 0.8611; hit rate 0 (0/609 lookups); replays 0; validation fails 0; initial-state hits 0; nonzero-prefix hits 0; mean lookup 16.92; mean validation 0; mean learning 0; mean primitive_evals 1663; mean remaining primitive 0; natural-opportunity traces 0 (rate 0).

- Useful on recurring complete repeats: True.
- Useful on constructed intermediate reuse (positive remaining-search avoided, quality-loss ≤ 0.2, nonzero-prefix hits, zero initial-state hits): True.
- Exact reuse is memorization. Constructed tasks are labeled: an alternative covering reaches a stored (mask, inventory) after a nonempty prefix. Natural intermediate recurrence on fresh primitive traces is reported separately. Fresh completed solves measure lookup overhead when no stored remaining state matches.
