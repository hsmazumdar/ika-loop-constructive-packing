# Expt-15 report

Can experience preserve a useful solution fragment while discarding details of the surrounding problem that are irrelevant to its reuse? A local entry records how to fill a bounded free region with a specified piece multiset; it matches when the region geometry is identical and the pieces are available, while the rest of the board and the unused inventory may differ. Test 1 supplies independent regions and budgets as an experimental aid. Test 2 uses ordinary packing with an engineered, billed region detector; it is not learned decomposition.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_15_Local_Subproblem_Memory\results\20260930_065912_diagnostic`
- Preset: `diagnostic`
- Region size range: 8–20 cells. Match rule: identical translation-normalised geometry and multiset available; first stored available entry.
- A = primitive_evals (incl. region search) + detection + lookup + availability + validation + insertion.
- No transformations, no hierarchy, no learned gate. Memories frozen before evaluation.
- Allocation failure: a box where local memory committed at least one filling and final quality fell more than 1.0 below the same-start reference, or acceptability was lost.

## Test 1: constructed independent regions with assigned budgets (experimental aid)

The region and its piece budget are supplied. Decomposed agents fill the region first (local memory hit, else deterministic region search billed per candidate placement), then complete the box with the primitive policy. Local savings are paired against the primitive decomposed agent; whole-box references are reported alongside.

- Library regions: 12; control regions (geometry and budget not in the library): 12; evaluation boxes: 36.
- Local entries 12 in 12 geometries (1800 bytes). Exact whole-state keys 436.
- Acquisition (region search evals per library region): [132, 215, 282, 316, 1002, 369, 410, 7, 1385, 114, 370, 522].

- matched / primitive_whole (vs none): n=72 (24 boxes × seeds); mean A 1222; mean Q 75.68; mean saving 0; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 0.9306; region filled NA; lookup 0; validation 0; seconds 0.02079.
- matched / exact_whole (vs primitive_whole): n=72 (24 boxes × seeds); mean A 1239; mean Q 75.68; mean saving -16.54; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 0.9306; region filled NA; lookup 16.54; validation 0; seconds 0.02093.
- matched / primitive_decomposed (vs primitive_whole): n=72 (24 boxes × seeds); mean A 1741; mean Q 75.65; mean saving -518.8; saving vs primitive whole NA; region search 538.5 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 8; allocation failures 0; acceptable 0.9444; region filled 1; lookup 0; validation 0; seconds 0.01873.
- matched / local_decomposed (vs primitive_decomposed): n=72 (24 boxes × seeds); mean A 1207; mean Q 75.65; mean saving 534; saving vs primitive whole 15.21; region search 0 (avoided 538.5); local hits 72; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 0.9444; region filled 1; lookup 1; validation 2.417; seconds 0.01817.
- control / primitive_whole (vs none): n=36 (12 boxes × seeds); mean A 1162; mean Q 75.72; mean saving 0; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 0.9444; region filled NA; lookup 0; validation 0; seconds 0.0191.
- control / exact_whole (vs primitive_whole): n=36 (12 boxes × seeds); mean A 1179; mean Q 75.72; mean saving -16.22; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 0.9444; region filled NA; lookup 16.22; validation 0; seconds 0.01948.
- control / primitive_decomposed (vs primitive_whole): n=36 (12 boxes × seeds); mean A 1390; mean Q 75.92; mean saving -227.6; saving vs primitive whole NA; region search 559.4 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 3; allocation failures 0; acceptable 1; region filled 1; lookup 0; validation 0; seconds 0.01446.
- control / local_decomposed (vs primitive_decomposed): n=36 (12 boxes × seeds); mean A 1391; mean Q 75.92; mean saving -1; saving vs primitive whole -228.6; region search 559.4 (avoided 0); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled 1; lookup 1; validation 0; seconds 0.01497.

## Test 2: ordinary packing, naturally occurring regions, shared inventory

Region detection is an engineered flood fill of free cells next to each new placement, bounded to the configured size range and billed per free cell visited. It is not learned decomposition. A local hit commits the first stored filling whose geometry is identical and whose multiset is available, with no gate; downstream consequences are measured against the same-start primitive.

- Store boxes: 16 × store seeds. Exact whole-state keys 591.
- Local entries 0 in 0 geometries; duplicates not stored 0; bytes 0.
- Local memory growth over store solves: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0].
- Store acquisition: extraction 46770, insertion 0, entries found 0; amortised over 120 evaluation boxes = 389.8 per box (not included in per-box A).

### Independent fresh inventories

- exact_whole: n=60 over 4 streams; cumulative saving per stream mean -259.2 (min -271, max -234); per-box -17.28; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/60 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 0; detection 0; lookup 17.28; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -17.28; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.02823.
- local: n=60 over 4 streams; cumulative saving per stream mean -7186 (min -7808, max -6500); per-box -479.1; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/60 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 3.017; detection 509.1; lookup 3.017; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -479.1; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.02935.
- primitive reference: mean A 2106; mean Q 74.97; seconds 0.02827.

### Recurring task families with varying inventories

- exact_whole: n=60 over 4 streams; cumulative saving per stream mean -238.5 (min -244, max -234); per-box -15.9; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/60 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 0; detection 0; lookup 15.9; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -15.9; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.02051.
- local: n=60 over 4 streams; cumulative saving per stream mean -7575 (min -7840, max -7424); per-box -505; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/60 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 3.15; detection 501.9; lookup 3.15; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -505; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.02286.
- primitive reference: mean A 1118; mean Q 75.98; seconds 0.02055.

- Test 1 supplies independent regions and budgets as an experimental aid; it is not learned decomposition. Test 2 uses an engineered flood-fill detector next to each placement, billed per free cell visited; it is not autonomous abstraction. Local entries match on identical translation-normalised geometry with the multiset available; no transformations, hierarchy, or learned gate. Memories are frozen before evaluation; store-phase acquisition is reported separately. Constructed opportunities (Test 1) are never pooled with naturally encountered ones (Test 2).
