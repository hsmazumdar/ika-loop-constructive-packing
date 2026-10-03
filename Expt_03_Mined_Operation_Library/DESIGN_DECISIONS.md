# Design decisions — Expt-3

These mechanisms are designer-supplied. They are not discoveries.

## Paths

The brief named `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly`. This machine mounts the same tree at `D:\PaperSubmissions2026\MGA_Memory_Guided_Assembly`. Code resolves directories from `__file__`. Upstream projects are read only.

`pieces.py` is a byte-for-byte copy of Expt-2 `mga2/pieces.py`. Inventory counts are copied from Expt-2 `data/runtime`. Witness files under Expt-2 `validation_only/` are not copied and are not read.

## Scores

`Q` is the final occupied cell count. Best-ever occupied cells are stored and are not substituted for `Q`.

`P` counts every real PLACE attempt, including invalid attempts and every piece expanded from a macro. A macro is not one physical action.

`E = Q / P` when `P > 0`. Otherwise `E` is missing, not zero and not infinity. Tables of efficiency use `E` only when `Q >= 80`. Counts at 70 and 90 are descriptive.

Attempts to reach 80 are the PLACE count at the first time the board has at least 80 cells. If that never happens, the attempt is censored at the PLACE count when the box stopped.

## Teacher corpus

Expt-2 agent traces did not reach `Q >= 80`. The corpus is produced by a labeled teacher:

- `teacher_exact_cover`: depth-first search with a most-constrained cell, node cap 40,000, seeds 11, 22, 33, 44, 55. At most two distinct occupancy masks per training inventory.
- `teacher_gpu_beam`: a CUDA beam of greedy trajectories, kept only when replay reaches `Q >= 80` and the mask is new.

Teacher node counts, seconds, and GPU operations are a separate ledger. Held-out and development inventories are not passed to the teacher.

## Mining

Groups are connected sets of 2–4 placements inside an order window of length 10 on a teacher solution. The window bound is the enumeration limit. The same pool is built once per snapshot. The first smoke used a window of 6; length 10 is the shared replacement, still bounded.

Canonical form tries the four rotations, translates to the minimum corner, and keeps the lexicographically smallest JSON. Reflections are not candidates.

A rectangle is a group whose bounding box is completely filled, with both sides at least 2, and at least two pieces. That test is a filter on the rectangle arm only.

Admission requires at least two distinct training task ids. When the prefix has at least four tasks, the last quarter of task ids is a within-training validation split: frequency is not counted there. A candidate is kept when it has a legal site on the empty validation board or on a prefix of that task's teacher trace (the midpoint, and the trace with the group's own length removed from the end). A candidate with no such site is rejected. Tie-break is higher support, then more validation hits, then fewer bytes, then operation id. Each library stops at 256 KiB.

The matched arm draws, without replacement, from non-rectangles still in the admitted pool. Distance is piece count, footprint area, and inventory demand. Ties use `match_seed` 20260929. If the rectangle library is empty, the mismatch is recorded and the matched library stays empty.

No nested CALL representation is used. Hierarchy is not a success criterion here.

Support counts distinct task ids. Positions on one board do not count as extra boxes.

## Controller and the Expt-2 cap

Expt-2 spent the 50,000-evaluation cap inside paired THINK, and hierarchical evaluation could place nothing. The predeclared Expt-3 budget, locked before held-out scoring, is in `configs/default.json`:

- 8,000 candidate evaluations per box
- 400 of those reserved for one cheap legal scan
- 48 placement rows examined per decision, on the GPU workspace
- at most 6 library operations and 8 anchors each
- at most 4 consecutive macro decisions
- `think_allowance` 0
- `undo_budget` 8, shared by every arm, including the primitive arm
- a continuation of 2 primitive placements, each examining 8 rows, before a macro is accepted

If the spend limit is reached, the reserve may still pay for a cheap legal PLACE. If that scan cannot be paid, the box submits with `compute_budget`. If a full cheap scan finds nothing legal, the controller undoes the last placement, remembers that placement for one decision, and tries again. After 8 undos, or with an empty stack, the reason is `no_legal`. The undo is a physical action. It is not Expt-1's hole filter and it is not applied to only one arm.

Every arm uses the same primitive score: piece area, plus 0.2 times contact with occupied cells, plus 0.05 times boundary contacts. It is not the Expt-1 heuristic. A retrieved macro is placed only when a charged simulation of that macro plus the continuation gains more occupied cells than the same continuation after the primitive, and the simulated board has no empty region smaller than every piece still in inventory. The 0.05 training-success term cannot overturn a one-cell gap. Lookup, anchor checks, and simulated expansions are charged to the same cap. The lesion `rect_mined_no_retrieval` loads the rectangle library and does not look it up.

Evaluation does not add, revise, or evict library entries.

RNG streams are `SHA-256(master | task | phase | repetition | purpose)`. The arm name is not part of the seed.

## Learning curve

Snapshots follow the frozen training-manifest order. Requested sizes are 0, 10, 20, and 40. A size past the number of successful training tasks is marked unavailable, and the actual task count is evaluated instead. Snapshot 0 has an empty library.

## What would not be a result

A high `E` from large pieces, a single transferred macro, or a mean on 12 tasks is not evidence of general intelligence. Teacher effort is part of any end-to-end cost claim. This run does not fit an amortization curve.
