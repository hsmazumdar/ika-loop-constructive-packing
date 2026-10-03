# Expt-9 report

Can remembering a successful continuation replace primitive search on an exact remaining board-and-inventory match? This is memorization, not abstraction, and not a rescue of Expt-8C.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_09_Exact_Continuation_Reuse\results\20260929_234314_smoke`
- Preset: `smoke`
- Store boxes (2): ['inv_e87f1d136371', 'inv_3ae11652dd8a'].
- Fresh boxes (2): ['inv_24870bb4615d', 'inv_40f63ca5c47b'].
- Continuation keys stored: 32; storage bytes 4680; table frozen before eval.
- A = primitive_evals + lookup + validation + learning. Lookup, validation, storage, and learning are counted separately.
- Exact reuse is memorization. It is not evidence of abstraction and not a confirmation of Expt-8C.

## Recurrence

- Recurring (same boxes as store) lookup hit rate: 1.
- Fresh lookup hit rate: 0. Fresh hits are accidental identical remaining states.

## Conditions

- store/primitive: n=2; mean A 1120; mean Q 76; mean effort-saving 0; quality-loss 0; acceptable 1; hit rate NA (0/0 lookups); replays 0; validation fails 0; mean lookup 0; mean validation 0; mean learning 16; mean primitive_evals 1104.
- recurring/exact: n=2; mean A 17; mean Q 76; mean effort-saving 1087; quality-loss 0; acceptable 1; hit rate 1 (2/2 lookups); replays 2; validation fails 0; mean lookup 1; mean validation 16; mean learning 0; mean primitive_evals 0.
- fresh/primitive: n=2; mean A 1398; mean Q 76; mean effort-saving 0; quality-loss 0; acceptable 1; hit rate NA (0/0 lookups); replays 0; validation fails 0; mean lookup 0; mean validation 0; mean learning 0; mean primitive_evals 1398.
- fresh/exact: n=2; mean A 1414; mean Q 76; mean effort-saving -16; quality-loss 0; acceptable 1; hit rate 0 (0/32 lookups); replays 0; validation fails 0; mean lookup 16; mean validation 0; mean learning 0; mean primitive_evals 1398.

- Useful on recurring (positive mean effort-saving, quality-loss ≤ 0.2, nonzero hits): False.
- Whole-box on new inventories was not run. This experiment tests whether memory replaces search on exact matches.
- Exact reuse is memorization. Fresh hits, if any, are accidental identical remaining states, not learned equivalence.
