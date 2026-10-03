# Expt-9 report

Can remembering a successful continuation replace primitive search on an exact remaining board-and-inventory match? This is memorization, not abstraction, and not a rescue of Expt-8C.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_09_Exact_Continuation_Reuse\results\20260929_234344_diagnostic`
- Preset: `diagnostic`
- Store boxes (12): ['inv_e6fa7cb5f30a', 'inv_b7f156f34d67', 'inv_bf234856d667', 'inv_b3afed463a2a', 'inv_d669540bf6ee', 'inv_48e1f4cbac8b', 'inv_7bd1067b1298', 'inv_046ff92d326b', 'inv_a3dda772bc1b', 'inv_f045499b8aa6', 'inv_24e6c1f06e23', 'inv_6219159aba3b'].
- Fresh boxes (12): ['inv_e87f1d136371', 'inv_3ae11652dd8a', 'inv_ab53dae89732', 'inv_23cf12192ee8', 'inv_46bf8cb4c812', 'inv_95af4783cc33', 'inv_5469d6a209dd', 'inv_f2b19b2bfedb', 'inv_a04ac752aab3', 'inv_914bbd709321', 'inv_00ce50783338', 'inv_8a1aa0d0dff8'].
- Continuation keys stored: 542; storage bytes 74457; table frozen before eval.
- A = primitive_evals + lookup + validation + learning. Lookup, validation, storage, and learning are counted separately.
- Exact reuse is memorization. It is not evidence of abstraction and not a confirmation of Expt-8C.

## Recurrence

- Recurring (same boxes as store) lookup hit rate: 1.
- Fresh lookup hit rate: 0. Fresh hits are accidental identical remaining states.

## Conditions

- store/primitive: n=36; mean A 900.8; mean Q 76.36; mean effort-saving 0; quality-loss 0; acceptable 1; hit rate NA (0/0 lookups); replays 0; validation fails 0; mean lookup 0; mean validation 0; mean learning 15.06; mean primitive_evals 885.8.
- recurring/exact: n=36; mean A 16.83; mean Q 76.75; mean effort-saving 868.9; quality-loss 0; acceptable 1; hit rate 1 (36/36 lookups); replays 36; validation fails 0; mean lookup 1; mean validation 15.83; mean learning 0; mean primitive_evals 0.
- fresh/primitive: n=36; mean A 1251; mean Q 75.97; mean effort-saving 0; quality-loss 0; acceptable 0.9444; hit rate NA (0/0 lookups); replays 0; validation fails 0; mean lookup 0; mean validation 0; mean learning 0; mean primitive_evals 1251.
- fresh/exact: n=36; mean A 1267; mean Q 75.97; mean effort-saving -16.36; quality-loss 0; acceptable 0.9444; hit rate 0 (0/589 lookups); replays 0; validation fails 0; mean lookup 16.36; mean validation 0; mean learning 0; mean primitive_evals 1251.

- Useful on recurring (positive mean effort-saving, quality-loss ≤ 0.2, nonzero hits): True.
- Whole-box on new inventories was not run. This experiment tests whether memory replaces search on exact matches.
- Exact reuse is memorization. Fresh hits, if any, are accidental identical remaining states, not learned equivalence.
