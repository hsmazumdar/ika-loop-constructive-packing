# Expt-11 report

Can a remaining-state isometry, either supplied as a rule or selected from experience, transform a stored continuation and replace remaining search? Exact matching is the miss control. This tests which declared transforms are useful, not inventing transforms, and not a general claim of abstraction.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_11_Remaining_State_Equivalence\results\20260930_060924_smoke`
- Preset: `smoke`
- Store boxes (2): ['inv_585b0b5234c9', 'inv_39eeee54dcb4'].
- Fresh boxes (2): ['inv_8a878e7dd4f6', 'inv_7c14b189767a'].
- Train families: ['inv_39eeee54dcb4']. Test families: ['inv_585b0b5234c9'].
- Constructed equivalence tasks: train 2, test 2.
- Continuation keys: 31 (2 empty-board); overwrites 0; bytes 4415.
- Declared candidates: ['rot90', 'rot180', 'rot270', 'refl_x', 'refl_y', 'refl_d', 'refl_ad'].
- Train transform successes: {'rot90': 2, 'rot180': 0, 'rot270': 0, 'refl_x': 0, 'refl_y': 0, 'refl_d': 0, 'refl_ad': 0}. Failures: {'rot90': 0, 'rot180': 0, 'rot270': 0, 'refl_x': 0, 'refl_y': 0, 'refl_d': 0, 'refl_ad': 0}.
- Selected from experience: ['rot90']. Rule: select T if train successes >= 1 and train validation/transform failures == 0.
- A = primitive_evals + lookup + matching + transformation + validation + learning.
- Engineered (supplied) and learned selection are reported separately. Learning does not invent transforms.
- Symmetric remaining states are excluded. Family transforms stay in the donor partition.
- Foils must reject reuse. Natural opportunity on fresh traces is not pooled with constructed equivalence.

## Cases

- eqv_e6aceedbb4c1 donor inv_585b0b5234c9 test T=rot90 cut 1 kind constructed_equiv.
- eqv_1d24596c28ed donor inv_585b0b5234c9 test T=rot90 cut 3 kind constructed_equiv.
- eqv_7dec40bc99c4 donor inv_39eeee54dcb4 train T=rot90 cut 1 kind constructed_equiv.
- eqv_4d4bee618749 donor inv_39eeee54dcb4 train T=rot90 cut 3 kind constructed_equiv.

## Conditions

- store/primitive: n=2; mean A 1486; mean Q 75.5; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 1470; natural-opportunity rate 0.
- recurring/exact: n=2; mean A 16.5; mean Q 75.5; mean effort-saving 1454; mean remaining-search-avoided 1470; quality-loss 0 (n=0); acceptable 1; hits 2 (exact 0, equiv 0) / 2 lookups; replays 2; validation fails 0; initial-state hits 2; mean lookup 1; matching 0; transformation 0; validation 15.5; mean primitive 0; natural-opportunity rate 0.
- equiv_train/primitive: n=2; mean A 3288; mean Q 73.5; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.5; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 3288; natural-opportunity rate 0.
- equiv_train/exact: n=2; mean A 3306; mean Q 73.5; mean effort-saving -18; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.5; hits 0 (exact 0, equiv 0) / 36 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 18; matching 0; transformation 0; validation 0; mean primitive 3288; natural-opportunity rate 0.
- equiv_train/supplied: n=2; mean A 126; mean Q 76; mean effort-saving 3162; mean remaining-search-avoided 3192; quality-loss 0 (n=0); acceptable 1; hits 2 (exact 0, equiv 2) / 2 lookups; replays 2; validation fails 0; initial-state hits 0; mean lookup 1; matching 1; transformation 14; validation 14; mean primitive 96; natural-opportunity rate 0.
- equiv_train/learned: n=2; mean A 126; mean Q 76; mean effort-saving 3162; mean remaining-search-avoided 3192; quality-loss 0 (n=0); acceptable 1; hits 2 (exact 0, equiv 2) / 2 lookups; replays 2; validation fails 0; initial-state hits 0; mean lookup 1; matching 1; transformation 14; validation 14; mean primitive 96; natural-opportunity rate 0.
- equiv_test/primitive: n=2; mean A 1982; mean Q 78; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 1982; natural-opportunity rate 0.
- equiv_test/exact: n=2; mean A 1996; mean Q 78; mean effort-saving -14; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 28 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 14; matching 0; transformation 0; validation 0; mean primitive 1982; natural-opportunity rate 0.
- equiv_test/supplied: n=2; mean A 124; mean Q 75; mean effort-saving 1858; mean remaining-search-avoided 1886; quality-loss 1 (n=2); acceptable 1; hits 2 (exact 0, equiv 2) / 2 lookups; replays 2; validation fails 0; initial-state hits 0; mean lookup 1; matching 1; transformation 13; validation 13; mean primitive 96; natural-opportunity rate 0.
- equiv_test/learned: n=2; mean A 124; mean Q 75; mean effort-saving 1858; mean remaining-search-avoided 1886; quality-loss 1 (n=2); acceptable 1; hits 2 (exact 0, equiv 2) / 2 lookups; replays 2; validation fails 0; initial-state hits 0; mean lookup 1; matching 1; transformation 13; validation 13; mean primitive 96; natural-opportunity rate 0.
- foil/primitive: n=6; mean A 2097; mean Q 75.33; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8333; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 2097; natural-opportunity rate 0.
- foil/exact: n=6; mean A 2113; mean Q 75.33; mean effort-saving -15.33; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8333; hits 0 (exact 0, equiv 0) / 92 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 15.33; matching 0; transformation 0; validation 0; mean primitive 2097; natural-opportunity rate 0.
- foil/supplied: n=6; mean A 2220; mean Q 75.33; mean effort-saving -122.7; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8333; hits 0 (exact 0, equiv 0) / 92 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 15.33; matching 107.3; transformation 0; validation 0; mean primitive 2097; natural-opportunity rate 0.
- foil/learned: n=6; mean A 2128; mean Q 75.33; mean effort-saving -30.67; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 0.8333; hits 0 (exact 0, equiv 0) / 92 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 15.33; matching 15.33; transformation 0; validation 0; mean primitive 2097; natural-opportunity rate 0.
- fresh/primitive: n=2; mean A 840; mean Q 77; mean effort-saving 0; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 0 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 0; matching 0; transformation 0; validation 0; mean primitive 840; natural-opportunity rate 0.
- fresh/exact: n=2; mean A 856; mean Q 77; mean effort-saving -16; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 32 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 16; matching 0; transformation 0; validation 0; mean primitive 840; natural-opportunity rate 0.
- fresh/supplied: n=2; mean A 968; mean Q 77; mean effort-saving -128; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 32 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 16; matching 112; transformation 0; validation 0; mean primitive 840; natural-opportunity rate 0.
- fresh/learned: n=2; mean A 872; mean Q 77; mean effort-saving -32; mean remaining-search-avoided 0; quality-loss 0 (n=0); acceptable 1; hits 0 (exact 0, equiv 0) / 32 lookups; replays 0; validation fails 0; initial-state hits 0; mean lookup 16; matching 16; transformation 0; validation 0; mean primitive 840; natural-opportunity rate 0.

- Exact matching evades transformed test remaining states: True.
- Supplied rules save effort on unseen families: True.
- Learned selection useful on unseen families (saving > 0, quality-loss ≤ 0.2, equiv hits, no empty-board hits): False.
- Foil supplied equivalence hits: 0.
- Natural opportunity rate on fresh primitive traces: 0.
- Engineered (supplied) and learned selection are reported separately. Learning chooses among declared D4 candidates; it does not invent transforms. Constructed equivalence is labeled. Natural opportunity on fresh traces is separate. Paired quality-loss versus the same-start primitive is reported, including first-write cases.
