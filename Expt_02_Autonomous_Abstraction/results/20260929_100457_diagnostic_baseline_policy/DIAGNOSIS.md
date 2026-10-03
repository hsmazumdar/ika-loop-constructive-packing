# Diagnostic: where the evaluation budget goes

This run repeats the discovery-smoke schedule (seeds 11 and 22, 40 training boxes, 12 frozen eval boxes, modes primitive / search_only / flat_library / hierarchical_library) with `budgets.cheap_scan_reserve` set to 0. That setting keeps the previous policy: when `can_eval` fails, the box submits with `compute_budget` even if the physical budget remains. Instrumentation does not draw from the decision, discovery, or evaluation streams.

The hierarchical rows match the baseline smoke `20260929_092518_discovery_smoke`: seed 11 train final mean 5.88 and eval 0.00; seed 22 train 11.00 and eval 17.67. Flat macros per box 1.163. Hierarchical macros per box 0.058. Cheap actions: 0. All 104 hierarchical boxes end on `compute_budget`.

`part_*` is an innermost partition of `candidate_evals`. `span_think` and `span_paired` are inclusive and overlap that partition.

## Evaluations per batch

Hierarchical library, 104 boxes, every box charges 50,000 evaluations:

| quantity | mean per box |
| --- | --- |
| part_paired | 43,864 |
| part_guard | 88 |
| part_selection | 6,048 |
| part_think | 0 |
| span_think | 43,932 |
| span_paired | 43,932 |

`part_think` is 0 because a library THINK batch's proposal step does not examine placements. The open THINK tally contains paired validation, and the innermost tally during that validation is `paired` or `guard`. The THINK cost is `span_think`, which here equals `span_paired`.

Guard scans are the small term. `legal_origins` stops after 64 trials, and the hierarchical mean guard count is 88 per box, about 0.2% of the THINK span. The paired rollout is the cost: both branches examine catalogue placements out to the horizon, and one such batch commonly takes the rest of the 50,000 cap (library think-batch maximum 50,000; 121 hierarchical batches).

Search-only is different. Its lookahead sits under `selection` inside `think`, so `part_think` is also 0, while `span_think` averages 11,259 of about 49,974 evaluations. Most of a search box is still ordinary primitive selection.

## Why the dispatcher keeps choosing THINK

Library THINK does not itself place a piece. Delayed credit (`_settle_think`) is applied only when a later decision sees at least `think_horizon` (8) further physical actions. The episode loop does not ask the agent to decide once the box is already terminal, so that credit is usually never written.

It was written once, on seed 11 training: `think_outcome` reward 0.374 from 39 cells of later fill. The stored selector at the end of seed 11 is:

- think: n=1, sum=0.374, mean 0.374
- ltm: n=2, sum=0.192, mean 0.096
- stm: n=2, sum=0.192, mean 0.096
- primitive: unseen, mean 0

UCB with unseen count 1 and exploration 0.5 ranks think strictly above the other arms. After that update the seed-11 choices are think 69, primitive 32, stm 7, ltm 3 (111 arm events). The first decision is think on 38 of 52 boxes. Frozen eval keeps that selector, so all 12 eval boxes open with THINK, spend the whole cap inside paired validation (`part_selection` 0), and place nothing. Eval final score is 0.00. Thirty-one of the 52 seed-11 boxes place nothing.

Seed 22 never records a think outcome. Its selector has only ltm n=2, sum=0.172. Think stays at the unseen mean. First decisions split across primitive 18, stm 17, think 11, ltm 6. Eval still places (physical mean 3.67, final mean 17.67) and still ends on `compute_budget`.

This run does not retune UCB or the delayed credit. Those stay as they were, so the next run isolates the cap correction.

## Why macros are invoked 0.058 times per box

Hierarchical macro invocations are 6 in 104 boxes (4 on seed 11, 2 on seed 22). Arm selections that ask for a library operation are much more common: stm 66 and ltm 20, 86 in total. An invocation is counted only after `legal_origins` returns a site and the interpreter runs. The other 80 selections do not execute a macro. On seed 11 that is mostly because think's one optimistic credit stops the dispatcher from returning to ltm/stm. On seed 22 the dispatcher does return to those arms, and the stored operations still usually have no legal origin in the current inventory within the 64-trial guard. The guard is not the budget sink; the paired THINK batch is.

Flat mode does not learn a THINK arm. It thinks on a fixed interval and still spends most of the cap inside paired checks (span_think mean 38,866), but it executes macros 121 times (1.163 per box) because it does not have to win a bandit against that credit.

## What this does not show

The matching scores show that the zero reserve reproduced the baseline policy. They do not show improved packing, a useful hierarchy, or amortized discovery cost. A memory sweep is not justified until a box can still take a legal primitive after deliberation hits the cap.
