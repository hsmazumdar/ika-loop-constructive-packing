# Expt-14 report

Does accumulating exact continuations online, box by box, create useful future matches that the frozen table lacked? Each box is solved with only the memory available before it; eligible continuations are stored afterwards and insertion is billed. Retrieval is exact state identity. Transformation matching is excluded from the primary comparison.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_14_Online_Memory_Growth\results\20260930_064808_smoke`
- Preset: `smoke`
- Independent store: ['inv_96b4b562aa29', 'inv_3b578229e9fd'].
- Family store: ['inv_903326cfbdef'].
- Family specs (declared before evaluation): [['B', 'E', 'F', 'G', 'H', 'I', 'O']].
- Base table: 32 keys (empty-board 2); frozen condition uses it unchanged; each stream's growing copy starts from it.
- Streams: 1 independent streams × 4 boxes per workload; one seed per stream.
- Insertion billing: 1 per stack state probed + 1 per key written, charged to the box that inserts.
- A = primitive_evals + lookup + validation + insertion.
- Retrieval is exact state identity. Transformation matching is excluded from this comparison. First write wins.
- Streams are declared before evaluation; no task is chosen by checking memory. Repeated inventories are kept and reported separately.

## Independent fresh inventories

- Decision: no reuse of any kind in this workload.
- Also: memory grew substantially without useful intermediate hits: stop expanding the exact-state table and investigate a representation that can reuse smaller subproblems.
- Growing: intermediate hits on never-encountered inventories 0; reuse on never-encountered 0; reuse on repeated 0; repays on never-encountered False; key growth ×2.938 (substantial ≥ ×1.5: True).

- frozen_exact: streams 1; cumulative saving per stream mean -62 (min -62, max -62); per-box -15.5; early third -15 vs late third -16 (late > early in 0 streams); initial hits 0; intermediate hits 0; hits on grown keys 0; never-encountered rows 4 (mean saving -15.5, reuse 0, intermediate hits 0); repeated rows 0 (reuse 0, saving sum 0); quality-loss 0; validation fails 0; key growth factor 1; insertion per box 0.
- growing_exact: streams 1; cumulative saving per stream mean -186 (min -186, max -186); per-box -46.5; early third -45 vs late third -48 (late > early in 0 streams); initial hits 0; intermediate hits 0; hits on grown keys 0; never-encountered rows 4 (mean saving -46.5, reuse 0, intermediate hits 0); repeated rows 0 (reuse 0, saving sum 0); quality-loss 0; validation fails 0; key growth factor 2.938; insertion per box 31.

  - stream 0 / frozen_exact: n=4; cumulative -62; early -15 late -16; initial 0 intermediate 0 grown-key hits 0; reuse 0/4; never-encountered 4 (saving -62); quality-loss 0; validation fails 0; keys 32 → 32; lookup 15.5 insertion 0.
  - stream 0 / growing_exact: n=4; cumulative -186; early -45 late -48; initial 0 intermediate 0 grown-key hits 0; reuse 0/4; never-encountered 4 (saving -186); quality-loss 0; validation fails 0; keys 32 → 94; lookup 15.5 insertion 31.

## Recurring task families with varying inventories

- Decision: no reuse of any kind in this workload.
- Also: memory grew substantially without useful intermediate hits: stop expanding the exact-state table and investigate a representation that can reuse smaller subproblems.
- Growing: intermediate hits on never-encountered inventories 0; reuse on never-encountered 0; reuse on repeated 0; repays on never-encountered False; key growth ×2.938 (substantial ≥ ×1.5: True).

- frozen_exact: streams 1; cumulative saving per stream mean -62 (min -62, max -62); per-box -15.5; early third -15 vs late third -16 (late > early in 0 streams); initial hits 0; intermediate hits 0; hits on grown keys 0; never-encountered rows 4 (mean saving -15.5, reuse 0, intermediate hits 0); repeated rows 0 (reuse 0, saving sum 0); quality-loss 0; validation fails 0; key growth factor 1; insertion per box 0.
- growing_exact: streams 1; cumulative saving per stream mean -186 (min -186, max -186); per-box -46.5; early third -45 vs late third -48 (late > early in 0 streams); initial hits 0; intermediate hits 0; hits on grown keys 0; never-encountered rows 4 (mean saving -46.5, reuse 0, intermediate hits 0); repeated rows 0 (reuse 0, saving sum 0); quality-loss 0; validation fails 0; key growth factor 2.938; insertion per box 31.

  - stream 0 / frozen_exact: n=4; cumulative -62; early -15 late -16; initial 0 intermediate 0 grown-key hits 0; reuse 0/4; never-encountered 4 (saving -62); quality-loss 0; validation fails 0; keys 32 → 32; lookup 15.5 insertion 0.
  - stream 0 / growing_exact: n=4; cumulative -186; early -45 late -48; initial 0 intermediate 0 grown-key hits 0; reuse 0/4; never-encountered 4 (saving -186); quality-loss 0; validation fails 0; keys 32 → 94; lookup 15.5 insertion 31.

- Each box is solved with only the memory available before it. Growing memory inserts the growing agent's completed solve afterwards (first write wins) and bills insertion to that box. Each stream has its own memory copy starting from the same frozen base table. Streams are declared before evaluation; no task is chosen by checking memory. Retrieval is exact state identity; transformation matching is excluded. Initial-state and intermediate hits are reported separately. Streams, not seeds, are the independent units.
