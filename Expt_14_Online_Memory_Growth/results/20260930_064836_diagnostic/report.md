# Expt-14 report

Does accumulating exact continuations online, box by box, create useful future matches that the frozen table lacked? Each box is solved with only the memory available before it; eligible continuations are stored afterwards and insertion is billed. Retrieval is exact state identity. Transformation matching is excluded from the primary comparison.

- Directory: `results\20260930_064836_diagnostic`
- Preset: `diagnostic`
- Independent store: ['inv_14b23c96d389', 'inv_df7793fb8a55', 'inv_26b826d85ffc', 'inv_2b7e57c9079c', 'inv_e0c44f0609a8', 'inv_2c8bf8c8028b', 'inv_44e21af494f1', 'inv_6f53a9f3ab40'].
- Family store: ['inv_2480408401be', 'inv_d4717658e407', 'inv_f66006ee83e9', 'inv_4ea07191b295', 'inv_aa433f939392', 'inv_62cc9dbdec9a', 'inv_7eb81632bbec', 'inv_7e80938eb8d9'].
- Family specs (declared before evaluation): [['A', 'B', 'G', 'H', 'J', 'L', 'N'], ['A', 'B', 'D', 'H', 'K'], ['A', 'C', 'F', 'G', 'L', 'O', 'P'], ['G', 'H', 'M', 'N']].
- Base table: 684 keys (empty-board 16); frozen condition uses it unchanged; each stream's growing copy starts from it.
- Streams: 6 independent streams × 30 boxes per workload; one seed per stream.
- Insertion billing: 1 per stack state probed + 1 per key written, charged to the box that inserts.
- A = primitive_evals + lookup + validation + insertion.
- Retrieval is exact state identity. Transformation matching is excluded from this comparison. First write wins.
- Streams are declared before evaluation; no task is chosen by checking memory. Repeated inventories are kept and reported separately.

## Independent fresh inventories

- Decision: no reuse of any kind in this workload.
- Also: memory grew substantially without useful intermediate hits: stop expanding the exact-state table and investigate a representation that can reuse smaller subproblems. The decisive evidence is the absence of intermediate hits, not the growth threshold.
- Growing: intermediate hits on never-encountered inventories 0; reuse on never-encountered 0; reuse on repeated 0; repays on never-encountered False; key growth ×1.635 (substantial ≥ ×1.5: True).

- frozen_exact: streams 6; cumulative saving per stream mean -490.5 (min -504, max -481); per-box -16.35; early third -16.45 vs late third -16.52 (late > early in 2 streams); initial hits 0; intermediate hits 0; hits on grown keys 0; never-encountered rows 180 (mean saving -16.35, reuse 0, intermediate hits 0); repeated rows 0 (reuse 0, saving sum 0); quality-loss 0; validation fails 0; key growth factor 1; insertion per box 0.
- growing_exact: streams 6; cumulative saving per stream mean -1358 (min -1397, max -1312); per-box -45.28; early third -45.75 vs late third -44.32 (late > early in 4 streams); initial hits 0; intermediate hits 0; hits on grown keys 0; never-encountered rows 180 (mean saving -45.28, reuse 0, intermediate hits 0); repeated rows 0 (reuse 0, saving sum 0); quality-loss 0; validation fails 0; key growth factor 1.635; insertion per box 28.93.

  - stream 0 / frozen_exact: n=30; cumulative -489; early -15.7 late -17; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -489); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.3 insertion 0.
  - stream 1 / frozen_exact: n=30; cumulative -484; early -16.7 late -16.1; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -484); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.13 insertion 0.
  - stream 2 / frozen_exact: n=30; cumulative -502; early -17 late -17; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -502); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.73 insertion 0.
  - stream 3 / frozen_exact: n=30; cumulative -504; early -16.7 late -16.9; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -504); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.8 insertion 0.
  - stream 4 / frozen_exact: n=30; cumulative -483; early -16.4 late -15.9; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -483); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.1 insertion 0.
  - stream 5 / frozen_exact: n=30; cumulative -481; early -16.2 late -16.2; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -481); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.03 insertion 0.
  - stream 0 / growing_exact: n=30; cumulative -1367; early -46.7 late -46.2; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -1367); quality-loss 0; validation fails 0; keys 684 → 1123; lookup 16.3 insertion 29.27.
  - stream 1 / growing_exact: n=30; cumulative -1360; early -45.5 late -43.7; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -1360); quality-loss 0; validation fails 0; keys 684 → 1122; lookup 16.13 insertion 29.2.
  - stream 2 / growing_exact: n=30; cumulative -1312; early -45.6 late -42.2; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -1312); quality-loss 0; validation fails 0; keys 684 → 1089; lookup 16.73 insertion 27.
  - stream 3 / growing_exact: n=30; cumulative -1358; early -48.5 late -41.7; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -1358); quality-loss 0; validation fails 0; keys 684 → 1111; lookup 16.8 insertion 28.47.
  - stream 4 / growing_exact: n=30; cumulative -1397; early -44 late -47.7; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -1397); quality-loss 0; validation fails 0; keys 684 → 1141; lookup 16.1 insertion 30.47.
  - stream 5 / growing_exact: n=30; cumulative -1357; early -44.2 late -44.4; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 30 (saving -1357); quality-loss 0; validation fails 0; keys 684 → 1122; lookup 16.03 insertion 29.2.

## Recurring task families with varying inventories

- Decision: B: gains confined to repeated inventories; the demonstrated capability remains whole-problem recall.
- Also: memory grew substantially without useful intermediate hits: stop expanding the exact-state table and investigate a representation that can reuse smaller subproblems. The decisive evidence is the absence of intermediate hits, not the growth threshold.
- Compare growing against both references: positive versus primitive does not mean better than frozen. Insertion can outweigh the additional recall benefit without removing all recall benefit.
- Growing: intermediate hits on never-encountered inventories 0; reuse on never-encountered 0; reuse on repeated 15; repays on never-encountered False; key growth ×1.595 (substantial ≥ ×1.5: True).

- frozen_exact: streams 6; cumulative saving per stream mean 1129 (min -504, max 2242); per-box 37.64; early third 42.6 vs late third 25.2 (late > early in 2 streams); initial hits 11; intermediate hits 0; hits on grown keys 0; never-encountered rows 165 (mean saving -16.32, reuse 0, intermediate hits 0); repeated rows 15 (reuse 11, saving sum 9471); quality-loss 0; validation fails 0; key growth factor 1; insertion per box 0.
- growing_exact: streams 6; cumulative saving per stream mean 936.3 (min 66, max 1404); per-box 31.21; early third 29.67 vs late third 24.2 (late > early in 3 streams); initial hits 15; intermediate hits 0; hits on grown keys 4; never-encountered rows 165 (mean saving -45.93, reuse 0, intermediate hits 0); repeated rows 15 (reuse 15, saving sum 13193); quality-loss 0; validation fails 0; key growth factor 1.595; insertion per box 28.56.

  - stream 0 / frozen_exact: n=30; cumulative 1337; early 69.7 late -16.3; initial 2 intermediate 0 grown-key hits 0; reuse 2/30; never-encountered 27 (saving -433); quality-loss 0; validation fails 0; keys 684 → 684; lookup 15.07 insertion 0.
  - stream 1 / frozen_exact: n=30; cumulative 1198; early -16 late 151.6; initial 2 intermediate 0 grown-key hits 0; reuse 2/30; never-encountered 27 (saving -427); quality-loss 0; validation fails 0; keys 684 → 684; lookup 14.9 insertion 0.
  - stream 2 / frozen_exact: n=30; cumulative -504; early -16.5 late -17.4; initial 0 intermediate 0 grown-key hits 0; reuse 0/30; never-encountered 29 (saving -487); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.8 insertion 0.
  - stream 3 / frozen_exact: n=30; cumulative 2242; early 156 late -15.8; initial 3 intermediate 0 grown-key hits 0; reuse 3/30; never-encountered 27 (saving -439); quality-loss 0; validation fails 0; keys 684 → 684; lookup 14.73 insertion 0.
  - stream 4 / frozen_exact: n=30; cumulative 2053; early -16.2 late 65.1; initial 3 intermediate 0 grown-key hits 0; reuse 3/30; never-encountered 27 (saving -435); quality-loss 0; validation fails 0; keys 684 → 684; lookup 14.6 insertion 0.
  - stream 5 / frozen_exact: n=30; cumulative 450; early 78.6 late -16; initial 1 intermediate 0 grown-key hits 0; reuse 1/30; never-encountered 28 (saving -474); quality-loss 0; validation fails 0; keys 684 → 684; lookup 16.4 insertion 0.
  - stream 0 / growing_exact: n=30; cumulative 1332; early 42.9 late 39.1; initial 3 intermediate 0 grown-key hits 1; reuse 3/30; never-encountered 27 (saving -1249); quality-loss 0; validation fails 0; keys 684 → 1092; lookup 14.53 insertion 28.93.
  - stream 1 / growing_exact: n=30; cumulative 1206; early 44.9 late 122.7; initial 3 intermediate 0 grown-key hits 1; reuse 3/30; never-encountered 27 (saving -1277); quality-loss 0; validation fails 0; keys 684 → 1109; lookup 14.33 insertion 30.1.
  - stream 2 / growing_exact: n=30; cumulative 66; early -44.1 late -42.6; initial 1 intermediate 0 grown-key hits 1; reuse 1/30; never-encountered 29 (saving -1295); quality-loss 0; validation fails 0; keys 684 → 1088; lookup 16.27 insertion 27.43.
  - stream 3 / growing_exact: n=30; cumulative 1404; early 130.9 late -47.4; initial 3 intermediate 0 grown-key hits 0; reuse 3/30; never-encountered 27 (saving -1225); quality-loss 0; validation fails 0; keys 684 → 1077; lookup 14.73 insertion 27.93.
  - stream 4 / growing_exact: n=30; cumulative 1180; early -47.8 late 38.2; initial 3 intermediate 0 grown-key hits 0; reuse 3/30; never-encountered 27 (saving -1255); quality-loss 0; validation fails 0; keys 684 → 1094; lookup 14.6 insertion 29.1.
  - stream 5 / growing_exact: n=30; cumulative 430; early 51.2 late 35.2; initial 2 intermediate 0 grown-key hits 1; reuse 2/30; never-encountered 28 (saving -1274); quality-loss 0; validation fails 0; keys 684 → 1084; lookup 15.87 insertion 27.83.

## State revisits at insertion time (growing memory)

Each completed trajectory state is probed on insertion. A probe that finds an existing key means the agent's own trajectory passed through a stored state.

- Independent fresh inventories / never-encountered inventories: boxes 180; states probed 2604; new keys 2604; already stored 0; mean new keys per box 14.5.
- Recurring task families with varying inventories / never-encountered inventories: boxes 165; states probed 2440; new keys 2440; already stored 0; mean new keys per box 14.8.
- Recurring task families with varying inventories / repeated inventories: boxes 15; states probed 260; new keys 0; already stored 260; mean new keys per box 0.

- Each box is solved with only the memory available before it. Growing memory inserts the growing agent's completed solve afterwards (first write wins) and bills insertion to that box. Each stream has its own memory copy starting from the same frozen base table. Streams are declared before evaluation; no task is chosen by checking memory. Retrieval is exact state identity; transformation matching is excluded. Initial-state and intermediate hits are reported separately. Streams, not seeds, are the independent units.
