# Expt-15 report

Can experience preserve a useful solution fragment while discarding details of the surrounding problem that are irrelevant to its reuse? A local entry records how to fill a bounded free region with a specified piece multiset; it matches when the region geometry is identical and the pieces are available, while the rest of the board and the unused inventory may differ. Test 1 supplies independent regions and budgets as an experimental aid. Test 2 uses ordinary packing with an engineered, billed region detector; it is not learned decomposition.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_15_Local_Subproblem_Memory\results\20260930_065830_smoke`
- Preset: `smoke`
- Region size range: 8–20 cells. Match rule: identical translation-normalised geometry and multiset available; first stored available entry.
- A = primitive_evals (incl. region search) + detection + lookup + availability + validation + insertion.
- No transformations, no hierarchy, no learned gate. Memories frozen before evaluation.
- Allocation failure: a box where local memory committed at least one filling and final quality fell more than 1.0 below the same-start reference, or acceptability was lost.

## Test 1: constructed independent regions with assigned budgets (experimental aid)

The region and its piece budget are supplied. Decomposed agents fill the region first (local memory hit, else deterministic region search billed per candidate placement), then complete the box with the primitive policy. Local savings are paired against the primitive decomposed agent; whole-box references are reported alongside.

- Library regions: 2; control regions (geometry and budget not in the library): 1; evaluation boxes: 3.
- Local entries 2 in 2 geometries (400 bytes). Exact whole-state keys 32.
- Acquisition (region search evals per library region): [380, 505].

- matched / primitive_whole (vs none): n=2 (2 boxes × seeds); mean A 1248; mean Q 76; mean saving 0; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled NA; lookup 0; validation 0; seconds 0.02703.
- matched / exact_whole (vs primitive_whole): n=2 (2 boxes × seeds); mean A 1264; mean Q 76; mean saving -16; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled NA; lookup 16; validation 0; seconds 0.02697.
- matched / primitive_decomposed (vs primitive_whole): n=2 (2 boxes × seeds); mean A 1272; mean Q 75.5; mean saving -23.5; saving vs primitive whole NA; region search 575.5 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled 1; lookup 0; validation 0; seconds 0.01997.
- matched / local_decomposed (vs primitive_decomposed): n=2 (2 boxes × seeds); mean A 701.5; mean Q 75.5; mean saving 570; saving vs primitive whole 546.5; region search 0 (avoided 575.5); local hits 2; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled 1; lookup 1; validation 3.5; seconds 0.01705.
- control / primitive_whole (vs none): n=1 (1 boxes × seeds); mean A 912; mean Q 76; mean saving 0; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled NA; lookup 0; validation 0; seconds 0.02259.
- control / exact_whole (vs primitive_whole): n=1 (1 boxes × seeds); mean A 929; mean Q 76; mean saving -17; saving vs primitive whole NA; region search 0 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled NA; lookup 17; validation 0; seconds 0.02654.
- control / primitive_decomposed (vs primitive_whole): n=1 (1 boxes × seeds); mean A 844; mean Q 76; mean saving 68; saving vs primitive whole NA; region search 124 (avoided NA); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled 1; lookup 0; validation 0; seconds 0.01743.
- control / local_decomposed (vs primitive_decomposed): n=1 (1 boxes × seeds); mean A 845; mean Q 76; mean saving -1; saving vs primitive whole 67; region search 124 (avoided 0); local hits 0; exact hits 0; validation fails 0; quality-loss 0; allocation failures 0; acceptable 1; region filled 1; lookup 1; validation 0; seconds 0.01911.

## Test 2: ordinary packing, naturally occurring regions, shared inventory

Region detection is an engineered flood fill of free cells next to each new placement, bounded to the configured size range and billed per free cell visited. It is not learned decomposition. A local hit commits the first stored filling whose geometry is identical and whose multiset is available, with no gate; downstream consequences are measured against the same-start primitive.

- Store boxes: 3 × store seeds. Exact whole-state keys 47.
- Local entries 0 in 0 geometries; duplicates not stored 0; bytes 0.
- Local memory growth over store solves: [0, 0, 0].
- Store acquisition: extraction 3353, insertion 0, entries found 0; amortised over 6 evaluation boxes = 558.8 per box (not included in per-box A).

### Independent fresh inventories

- exact_whole: n=3 over 1 streams; cumulative saving per stream mean -50 (min -50, max -50); per-box -16.67; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/3 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 0; detection 0; lookup 16.67; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -16.67; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.02461.
- local: n=3 over 1 streams; cumulative saving per stream mean -1339 (min -1339, max -1339); per-box -446.3; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/3 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 2.667; detection 443.7; lookup 2.667; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -446.3; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.02576.
- primitive reference: mean A 1315; mean Q 75.33; seconds 0.02206.

### Recurring task families with varying inventories

- exact_whole: n=3 over 1 streams; cumulative saving per stream mean -45 (min -45, max -45); per-box -15; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/3 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 0; detection 0; lookup 15; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -15; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.01768.
- local: n=3 over 1 streams; cumulative saving per stream mean -1778 (min -1778, max -1778); per-box -592.7; local hits 0 in 0 boxes (0); on unseen whole inventories 0 hits in 0/3 boxes; exact hits 0 (initial 0, intermediate 0); regions detected per box 1.667; detection 591; lookup 1.667; availability 0; validation 0; primitive before first hit NA; mean hit size NA; saving on hit boxes NA vs no-hit boxes -592.7; quality delta on hit boxes NA; quality-loss 0; acceptability lost 0; allocation failures 0; validation fails 0; seconds 0.01578.
- primitive reference: mean A 736; mean Q 75; seconds 0.01565.

- Test 1 supplies independent regions and budgets as an experimental aid; it is not learned decomposition. Test 2 uses an engineered flood-fill detector next to each placement, billed per free cell visited; it is not autonomous abstraction. Local entries match on identical translation-normalised geometry with the multiset available; no transformations, hierarchy, or learned gate. Memories are frozen before evaluation; store-phase acquisition is reported separately. Constructed opportunities (Test 1) are never pooled with naturally encountered ones (Test 2).
