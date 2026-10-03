# Expt-11 report

Can a remaining-state isometry, either supplied as a rule or selected from experience, transform a stored continuation and replace remaining search? Exact matching is the miss control. This tests which declared transforms are useful, not inventing transforms, and not a general claim of abstraction.

- Directory: `e:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_11_Remaining_State_Equivalence\results\20260930_060957_diagnostic`
- Preset: `diagnostic`
- Store boxes (12): ['inv_6416ed2616d2', 'inv_03be0c5a020a', 'inv_c2d0911fe9c4', 'inv_308784ecedb8', 'inv_0060794c55b2', 'inv_6613f5a60f23', 'inv_b3b326fd6092', 'inv_afa20f7d02a9', 'inv_c08bed243755', 'inv_a00d6da51508', 'inv_a9afc95a59e9', 'inv_a61456dc8c05'].
- Fresh boxes (12): ['inv_585b0b5234c9', 'inv_39eeee54dcb4', 'inv_c058788dcb60', 'inv_5a1ec7fd3aa3', 'inv_1f3f9b7fb9d5', 'inv_4405d48464ce', 'inv_19c38d529b4f', 'inv_38efe2f69aac', 'inv_1674f7d51756', 'inv_74ef40691c4f', 'inv_daa98cb0685f', 'inv_8ebdf4063e68'].
- Train families: ['inv_0060794c55b2', 'inv_03be0c5a020a', 'inv_308784ecedb8', 'inv_6416ed2616d2', 'inv_6613f5a60f23', 'inv_a00d6da51508', 'inv_a61456dc8c05', 'inv_a9afc95a59e9']. Test families: ['inv_afa20f7d02a9', 'inv_b3b326fd6092', 'inv_c08bed243755', 'inv_c2d0911fe9c4'].
- Constructed equivalence tasks: train 13, test 11.
- Continuation keys: 509 (12 empty-board); overwrites 22; bytes 69345.
- Declared candidates: ['rot90', 'rot180', 'rot270', 'refl_x', 'refl_y', 'refl_d', 'refl_ad'].
- Train transform successes: {'rot90': 12, 'rot180': 1, 'rot270': 0, 'refl_x': 0, 'refl_y': 0, 'refl_d': 0, 'refl_ad': 0}. Failures: {'rot90': 0, 'rot180': 0, 'rot270': 0, 'refl_x': 0, 'refl_y': 0, 'refl_d': 0, 'refl_ad': 0}.
- Selected from experience: ['rot90', 'rot180']. Rule: select T if train successes >= 1 and train validation/transform failures == 0.
- A = primitive_evals + lookup + matching + transformation + validation + learning.
- Engineered (supplied) and learned selection are reported separately. Learning does not invent transforms.
- Symmetric remaining states are excluded. Family transforms stay in the donor partition.
- Foils must reject reuse. Natural opportunity on fresh traces is not pooled with constructed equivalence.

## Cases

- eqv_80067d201969 donor inv_6416ed2616d2 train T=rot90 cut 2 kind constructed_equiv.
- eqv_ae3ac0baab96 donor inv_03be0c5a020a train T=rot90 cut 2 kind constructed_equiv.
- eqv_827a905daf36 donor inv_03be0c5a020a train T=rot90 cut 3 kind constructed_equiv.
- eqv_1cf4dbfe4025 donor inv_03be0c5a020a train T=rot180 cut 4 kind constructed_equiv.
- eqv_b1fe8b80b97c donor inv_c2d0911fe9c4 test T=rot90 cut 2 kind constructed_equiv.
- eqv_11b6be327acf donor inv_c2d0911fe9c4 test T=rot90 cut 3 kind constructed_equiv.
- eqv_6a492a3fa8ca donor inv_c2d0911fe9c4 test T=rot180 cut 4 kind constructed_equiv.
- eqv_bda374d0f863 donor inv_308784ecedb8 train T=rot90 cut 2 kind constructed_equiv.
- eqv_bfa72353b84a donor inv_0060794c55b2 train T=rot90 cut 2 kind constructed_equiv.
- eqv_023fd3a0c6fb donor inv_0060794c55b2 train T=rot90 cut 3 kind constructed_equiv.
- eqv_924e8f09dd2c donor inv_6613f5a60f23 train T=rot90 cut 2 kind constructed_equiv.
- eqv_837dfbe27392 donor inv_6613f5a60f23 train T=rot90 cut 3 kind constructed_equiv.
- eqv_aba4dfc27b86 donor inv_b3b326fd6092 test T=rot90 cut 2 kind constructed_equiv.
- eqv_e17970f90624 donor inv_b3b326fd6092 test T=rot90 cut 4 kind constructed_equiv.
- eqv_50f7e175cb64 donor inv_b3b326fd6092 test T=rot180 cut 4 kind constructed_equiv.
- eqv_066281c6a8f2 donor inv_afa20f7d02a9 test T=rot90 cut 2 kind constructed_equiv.
- eqv_294e5ae09b62 donor inv_afa20f7d02a9 test T=rot90 cut 4 kind constructed_equiv.
- eqv_090a0ecaf335 donor inv_afa20f7d02a9 test T=rot180 cut 4 kind constructed_equiv.
- eqv_32269bd763cc donor inv_c08bed243755 test T=rot90 cut 2 kind constructed_equiv.
- eqv_949c62af2345 donor inv_c08bed243755 test T=rot90 cut 4 kind constructed_equiv.
- eqv_be0d5df99773 donor inv_a00d6da51508 train T=rot90 cut 2 kind constructed_equiv.
- eqv_4ef66d029efe donor inv_a00d6da51508 train T=rot90 cut 3 kind constructed_equiv.
- eqv_c2d71c4b99f4 donor inv_a9afc95a59e9 train T=rot90 cut 2 kind constructed_equiv.
- eqv_1f5f9d7b0d63 donor inv_a61456dc8c05 train T=rot90 cut 2 kind constructed_equiv.

## Conditions

- store/primitive: n=36; mean A 1350; mean Q 76.03; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.9444; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 1335; natural-opportunity rate 0.
- recurring/exact: n=36; mean A 16.58; mean Q 76.25; mean effort-saving 1319; mean remaining-search-avoided 1335; quality-loss 0.05556 (n=2); acceptable 1; hits 36 (exact 0, equiv 0) / 36 lookups; replays 36; validation fails 0; initial-state hits 36; mean lookup 1; matching 0; transformation 0; validation 15.58; mean primitive 0; natural-opportunity rate 0.
- equiv_train/primitive: n=39; mean A 1616; mean Q 75.49; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8718; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 1616; natural-opportunity rate 0.
- equiv_train/exact: n=39; mean A 1630; mean Q 75.49; mean effort-saving -14.05; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8718; hits 0 (exact 0, equiv 0) / 548 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 14.05; matching 0; transformation 0; validation 0; mean primitive 1616; natural-opportunity rate 0.
- equiv_train/supplied: n=39; mean A 149.8; mean Q 76.54; mean effort-saving 1466; mean remaining-search-avoided 1494; quality-loss 0.1026 (n=4); acceptable 1; hits 39 (exact 0, equiv 39) / 39 lookups; replays 39; validation fails 0; initial-state hits 0; mean lookup 1; matching 1.077; transformation 12.92; validation 12.92; mean primitive 121.8; natural-opportunity rate 0.
- equiv_train/learned: n=39; mean A 149.8; mean Q 76.54; mean effort-saving 1466; mean remaining-search-avoided 1494; quality-loss 0.1026 (n=4); acceptable 1; hits 39 (exact 0, equiv 39) / 39 lookups; replays 39; validation fails 0; initial-state hits 0; mean lookup 1; matching 1.077; transformation 12.92; validation 12.92; mean primitive 121.8; natural-opportunity rate 0.
- equiv_test/primitive: n=33; mean A 990.8; mean Q 75.52; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 990.8; natural-opportunity rate 0.
- equiv_test/exact: n=33; mean A 1003; mean Q 75.52; mean effort-saving -12.3; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 406 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 12.3; matching 0; transformation 0; validation 0; mean primitive 990.8; natural-opportunity rate 0.
- equiv_test/supplied: n=33; mean A 184.3; mean Q 76; mean effort-saving 806.5; mean remaining-search-avoided 833.7; quality-loss 0 (n=0); acceptable 1; hits 33 (exact 0, equiv 33) / 33 lookups; replays 33; validation fails 0; initial-state hits 0; mean lookup 1; matching 1.273; transformation 12.45; validation 12.45; mean primitive 157.1; natural-opportunity rate 0.
- equiv_test/learned: n=33; mean A 184.3; mean Q 76; mean effort-saving 806.5; mean remaining-search-avoided 833.7; quality-loss 0 (n=0); acceptable 1; hits 33 (exact 0, equiv 33) / 33 lookups; replays 33; validation fails 0; initial-state hits 0; mean lookup 1; matching 1.273; transformation 12.45; validation 12.45; mean primitive 157.1; natural-opportunity rate 0.
- foil/primitive: n=24; mean A 1416; mean Q 74.88; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.9167; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 1416; natural-opportunity rate 0.
- foil/exact: n=24; mean A 1429; mean Q 74.88; mean effort-saving -13.75; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.9167; hits 0 (exact 0, equiv 0) / 330 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 13.75; matching 0; transformation 0; validation 0; mean primitive 1416; natural-opportunity rate 0.
- foil/supplied: n=24; mean A 1239; mean Q 75.04; mean effort-saving 176.2; mean remaining-search-avoided 265.7; quality-loss 0 (n=0); acceptable 0.9167; hits 6 (exact 0, equiv 6) / 251 lookups; replays 6; validation fails 0; initial-state hits 0; mean lookup 10.46; matching 71.71; transformation 3.625; validation 3.625; mean primitive 1150; natural-opportunity rate 0.
- foil/learned: n=24; mean A 1188; mean Q 75.04; mean effort-saving 227.3; mean remaining-search-avoided 265.7; quality-loss 0 (n=0); acceptable 0.9167; hits 6 (exact 0, equiv 6) / 251 lookups; replays 6; validation fails 0; initial-state hits 0; mean lookup 10.46; matching 20.67; transformation 3.625; validation 3.625; mean primitive 1150; natural-opportunity rate 0.
- fresh/primitive: n=36; mean A 1835; mean Q 75.5; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8611; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 1835; natural-opportunity rate 0.
- fresh/exact: n=36; mean A 1852; mean Q 75.5; mean effort-saving -16.89; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8611; hits 0 (exact 0, equiv 0) / 608 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 16.89; matching 0; transformation 0; validation 0; mean primitive 1835; natural-opportunity rate 0.
- fresh/supplied: n=36; mean A 1970; mean Q 75.5; mean effort-saving -135.1; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8611; hits 0 (exact 0, equiv 0) / 608 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 16.89; matching 118.2; transformation 0; validation 0; mean primitive 1835; natural-opportunity rate 0.
- fresh/learned: n=36; mean A 1886; mean Q 75.5; mean effort-saving -50.67; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8611; hits 0 (exact 0, equiv 0) / 608 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 16.89; matching 33.78; transformation 0; validation 0; mean primitive 1835; natural-opportunity rate 0.

- Exact matching evades transformed test remaining states: True.
- Supplied rules save effort on unseen families: True.
- Learned selection useful on unseen families (saving > 0, quality-loss ≤ 0.2, equiv hits, no empty-board hits): True.
- Foil supplied equivalence hits: 6. Inventory foils rejected reuse. Geometry near-miss foils can still match a different stored intermediate (declared; not pooled with constructed-equivalence success).
- Natural opportunity rate on fresh primitive traces: 0.
- Engineered (supplied) and learned selection are reported separately. Learning chooses among declared D4 candidates; it does not invent transforms. Constructed equivalence is labeled. Natural opportunity on fresh traces is separate. Paired quality-loss versus the same-start primitive is reported, including first-write cases.

## Distinctions

- Test families are unseen for the transformation-selection rule. Their donor continuations are stored; retrieval is from memory. What transfers is the selected isometry set, not a new solution.
- The 33 test rows are 11 constructed tasks drawn from four families, each evaluated at three seeds (11 × 3). They are not 11 × 4 × 3 tasks, and they are not 33 independent tests of learning a transformation rule.
- Zero training successes is not evidence a transform is useless unless it had enough eligible (compatible-key) trials. rot270 preserves geometry when orientations allow it; its absence from the selected set may be training coverage, not a geometric failure.
