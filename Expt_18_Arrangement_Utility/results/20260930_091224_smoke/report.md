# Expt-18 report

Do the recurring arrangements from Expt-17 have enough quality-preserving whole-box benefit, on a predeclared sample of legal placements, to justify building a cheaper matcher?

Expt-17 separated recurrence from applicability, and showed that exhaustive translation matching exceeds its 0.10 bar by about 456 times on fresh inventories and about 818 times on recurring families. This run does not revisit that gate and does not treat a legal fit as a reason to commit. It asks only whether the recorded arrangements have enough quality-preserving benefit, on a small predeclared sample, to justify building a cheaper matcher later.

- Directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_18_Arrangement_Utility\results\20260930_091224_smoke`
- Preset: `smoke`
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Frozen dictionary: Expt-17 `20260930_090000_diagnostic`, 58 patterns, sha256 `b02cd72c92b7a9f00b8660b7a54633a1cb93844c62d20ff98ae0812ea62c904c`.
- Sampled pattern indices: [0, 1, 2, 3, 4].
- Of those, support at least 3 inventories: [0, 1, 2, 3, 4].
- Fresh box indices (stride 5): [0].
- Family box indices (stride 10): [0].
- Stages: ['early']. One earliest legal translation per box, pattern, and stage.
- Benefit floor: remaining-effort saving at least 48 after commitment checks, quality within 1.0, acceptability kept.
- Broad bar: at least 3 independent fresh boxes, at least 3 patterns, and both early and middle.

## What was measured

Each sampled placement is replayed twice from the saved board, inventory, RNG state, and tabu. One branch continues with the primitive policy. The other places the pattern, after one check per piece and per cell, then continues with the primitive policy. Both branches keep the same primitive search room, `eval_cap` minus the effort already spent. Commitment checks are part of the commit branch's effort. The box-level opportunity is the single best quality-preserving candidate in that box. It is not the sum of the candidates.

## Candidate-level detail

A candidate average can be dominated by many similar early placements. It is not the decision statistic.

### independent_fresh

- Placements replayed 3; invalid commits 0; primitive replay failures 0.
- Candidate-level, valid replays: n=3, mean saving 3694, median 3779, mean quality delta 0.3333, quality losses 0.
- Candidate-level, quality-preserving and effort-positive: n=3, mean saving 3694, median 3779.
- These averages are not added across prefixes of the same box.

### recurring_family

- Placements replayed 1; invalid commits 0; primitive replay failures 0.
- Candidate-level, valid replays: n=1, mean saving -2683, median -2683, mean quality delta -2, quality losses 1.
- Candidate-level, quality-preserving and effort-positive: n=0, mean saving n/a, median n/a.
- These averages are not added across prefixes of the same box.

## Box-level opportunities

Ideal selection keeps only candidates that preserve quality and acceptability and reduce remaining effort. The reported saving is the best such candidate, or zero when none exists.

- independent_fresh index 0 `inv_1dec36052a8a`: candidates 3, quality-preserving 3, ideal saving 4595 (pattern 4, early, quality delta 0), counts as benefit: True. Largest valid saving 4595 lost quality: False.
- recurring_family index 0 `inv_a8956340ad37`: candidates 1, quality-preserving 0, ideal saving 0, counts as benefit: False. Largest valid saving -2683 lost quality: True.

## Diagnostic cost

- Discovery checks to locate the sampled placements: 86.
- Counterfactual effort, both branches: 25100.
- Wall time: 0.1855 seconds.
- diagnostic only; not a deployable matcher and not a relaxation of the Expt-17 cost gate.

## Decision

- Row: **narrow_retrieval**.
- Quality-preserving benefit appears, but only for a few patterns or contexts. The next question would be a narrowly targeted retrieval rule, not a general matcher. The Expt-17 cost gate on exhaustive translation search still stands.
- Independent fresh boxes at or above the saving floor: 1. Patterns [4]. Stages ['early'].
- Family boxes at or above the saving floor: 0. Family benefit alone cannot justify a general matcher.
- Commitment: diagnostic counterfactuals only; no pattern was admitted to a policy.
- Expt-17 cost gate: not relaxed.
