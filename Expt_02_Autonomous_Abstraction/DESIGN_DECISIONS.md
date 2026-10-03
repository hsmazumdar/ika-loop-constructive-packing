# Design decisions — Expt-2

These are designer-supplied mechanisms. They are not claimed as discoveries.

## World

The A–P catalogue is copied from Expt-1. Its SHA-256 is computed from the same canonical JSON payload. Rotations are 0/90/180/270 clockwise. Reflections are not generated.

`legacy_unlimited` keeps unlimited copies, so an all-B packing remains legal. `inventory_tasks` expose only the remaining multiset. Witnesses live in `validation_only/` and are not imported by `src/mga2`.

## Primitive baseline

`primitive` draws uniformly among the legal placements it was able to examine. It has no undo tabu, no hole filter, and no library. If the examination budget is exhausted, the episode ends with `compute_budget`. If placements remain legal but none were found before the cap, the same reason is used. If the scan finishes and nothing legal remains, the agent submits.

## Engineered reference

`engineered_reference` is the Expt-1 contact/fill heuristic with the small-component hard filter and a one-step undo tabu. Autonomous modes do not call those functions.

## Language

Programs are JSON ASTs. The interpreter never calls `eval`. `PLACE_REL` anchors are min-corners of the normalized orientation. A caller rotation moves that anchor by rotating the offset and then shifting by the min corner of the rotated local cells, so the occupied cells match a rigid rotation. `LOOKAHEAD` cannot run inside another `LOOKAHEAD`.

Limits, from configuration: 24 nodes, 12 expanded physical actions, call depth 4, `REPEAT` 1..4, lookahead depth 1..3 and width 1..4. Flat and hierarchical modes share `max_expanded` and the paired horizon.

## Utility

`U = delta_filled / 100 - 0.002 * physical_actions - 0.0001 * model_transitions` on each branch. The paired estimate is the candidate branch minus the primitive branch. Both branches are charged to the ledger. Real-use utility, which is what confirmation sums, counts only real executions. Simulation utility stays in `paired_utility_sum`.

## Memory bytes

Logical size is the UTF-8 length of canonical JSON, including ids, guards, stats, child operations stored in the library, and selector counts. This is not process RAM. Process allocation is not used as the cap. Scratch candidates during a THINK batch are charged to the planning-workspace peak.

STM samples its size on each decision. `finish_box` records peak and average, and only then clears STM.

Promotion to provisional LTM requires a legal paired check with positive `U`. Confirmation requires at least 3 real uses, at least 2 training task ids, and positive real utility sum. One task id is labelled `same_task` and is not cross-task confirmation. Provisional records age out after 20 training boxes without beneficial real reuse. At capacity, provisional low value-per-byte records are removed first, with id as the tie break. Evicting an operation also evicts parents that reference it.

Frozen evaluation sets `ltm.frozen`. New entries, stat updates, promotions, selector writes, and evictions return without changing the library. STM may still hold transient candidates for that box.

## Dispatcher

Hierarchical selection is UCB over `primitive`, `stm`, `ltm`, and `think`, with unseen mean 0 and unseen count 1. Equal scores are broken by the decision RNG. Flat mode uses a fixed THINK interval rather than a learned THINK arm. Search-only may run lookahead with a configured probability and discards learned operations after the decision. Consecutive THINK batches are capped, and a library THINK does not place a piece by itself.

## Cap progress

Deliberation stops `cheap_scan_reserve` evaluations before the candidate-eval cap. When that key is absent the reserve is one full catalogue pass, 3636 evaluations. THINK, paired checks, lookahead, and ordinary selection use `can_eval` and therefore leave that remainder. If eligibility evaluations are still left, the agent takes one cheap legal primitive and counts those scans. If the true cap is exhausted, it submits with `compute_budget`. If a scan finishes and nothing legal remains, it submits. Setting `budgets.cheap_scan_reserve` to 0 restores the earlier policy, which submits as soon as `can_eval` fails. The reserve does not change UCB or the delayed THINK credit.

## Expt-2A

Expt-2A does not train. It loads the flat library from the baseline discovery smoke and evaluates four frozen policies on the held-out inventories: primitive only, library lookup with THINK disabled, THINK capped at 3636 evaluations, and the current flat THINK interval. The 3636 allowance is one catalogue pass. It was fixed before the comparison, as a limit on deliberation, not as a packing rule. A learned stop, a parent-versus-flattened comparison, and memory or harder-task sweeps are not part of this run.

## RNG

Each stream is `SHA-256(master | task | phase | repetition | purpose)`. Mode is not part of the seed, and streams are rebuilt per episode, so running another mode first does not change this episode's draws.

## What is not supplied as an answer

No rectangular composite, rectangle detector, large-first policy, or preloaded macro. CHOOSE weights start at zero, so area can later be weighted either way by mutation. Connectedness is a filter only when composing two footprints.
