# Expt-18 report

Do the recurring arrangements from Expt-17 have enough quality-preserving whole-box benefit, on a predeclared sample of legal placements, to justify building a cheaper matcher?

Expt-17 separated recurrence from applicability, and showed that exhaustive translation matching exceeds its 0.10 bar by about 456 times on fresh inventories and about 818 times on recurring families. This run does not revisit that gate and does not treat a legal fit as a reason to commit. It asks only whether the recorded arrangements have enough quality-preserving benefit, on a small predeclared sample, to justify building a cheaper matcher later.

- Directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_18_Arrangement_Utility\results\20260930_091301_diagnostic`
- Preset: `diagnostic`
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Frozen dictionary: Expt-17 `20260930_090000_diagnostic`, 58 patterns, sha256 `b02cd72c92b7a9f00b8660b7a54633a1cb93844c62d20ff98ae0812ea62c904c`.
- Sampled pattern indices: [0, 1, 2, 3, 4, 6, 22, 19, 24, 44, 7, 18, 9].
- Of those, support at least 3 inventories: [0, 1, 2, 3, 4].
- Fresh box indices (stride 5): [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55].
- Family box indices (stride 10): [0, 10, 20, 30, 40, 50].
- Stages: ['early', 'middle']. One earliest legal translation per box, pattern, and stage.
- Benefit floor: remaining-effort saving at least 48 after commitment checks, quality within 1.0, acceptability kept.
- Broad bar: at least 3 independent fresh boxes, at least 3 patterns, and both early and middle.

## What was measured

Each sampled placement is replayed twice from the saved board, inventory, RNG state, and tabu. One branch continues with the primitive policy. The other places the pattern, after one check per piece and per cell, then continues with the primitive policy. Both branches keep the same primitive search room, `eval_cap` minus the effort already spent. Commitment checks are part of the commit branch's effort. The box-level opportunity is the single best quality-preserving candidate in that box. It is not the sum of the candidates. Within a stage the placement is the earliest fitting prefix, so an early sample is the empty board whenever the initial inventory already contains the pattern's pieces. Later prefixes in that same bin are not additional samples.

## Candidate-level detail

A candidate average can be dominated by many similar early placements. It is not the decision statistic.

### independent_fresh

- Placements replayed 91; invalid commits 0; primitive replay failures 0.
- Candidate-level, valid replays: n=91, mean saving 709.9, median 324, mean quality delta -0.4945, quality losses 25.
- Candidate-level, quality-preserving and effort-positive: n=53, mean saving 1077, median 340.
- These averages are not added across prefixes of the same box.

### recurring_family

- Placements replayed 34; invalid commits 0; primitive replay failures 0.
- Candidate-level, valid replays: n=34, mean saving -53.79, median 132, mean quality delta -0.4412, quality losses 7.
- Candidate-level, quality-preserving and effort-positive: n=19, mean saving 238.1, median 132.
- These averages are not added across prefixes of the same box.

## Box-level opportunities

Ideal selection keeps only candidates that preserve quality and acceptability and reduce remaining effort. The reported saving is the best such candidate, or zero when none exists.

- independent_fresh index 0 `inv_1dec36052a8a`: candidates 11, quality-preserving 6, ideal saving 4595 (pattern 4, early, occupied 0, quality delta 0), counts as benefit: True. Largest valid saving 4643 lost quality: True.
- independent_fresh index 5 `inv_6bba36258da4`: candidates 9, quality-preserving 6, ideal saving 324 (pattern 6, early, occupied 0, quality delta 0), counts as benefit: True. Largest valid saving 324 lost quality: False.
- independent_fresh index 10 `inv_2aba0a9c4949`: candidates 16, quality-preserving 10, ideal saving 84 (pattern 0, middle, occupied 35, quality delta 0), counts as benefit: True. Largest valid saving 84 lost quality: False.
- independent_fresh index 15 `inv_9ff62dba8d36`: candidates 12, quality-preserving 7, ideal saving 2020 (pattern 24, middle, occupied 36, quality delta -1), counts as benefit: True. Largest valid saving 2068 lost quality: True.
- independent_fresh index 20 `inv_253c2c604fa9`: candidates 0, quality-preserving 0, ideal saving 0, counts as benefit: False.
- independent_fresh index 25 `inv_8a1fe1944805`: candidates 4, quality-preserving 2, ideal saving 84 (pattern 2, middle, occupied 34, quality delta 0), counts as benefit: True. Largest valid saving 84 lost quality: False.
- independent_fresh index 30 `inv_ae592383dd89`: candidates 0, quality-preserving 0, ideal saving 0, counts as benefit: False.
- independent_fresh index 35 `inv_43023fd0b715`: candidates 13, quality-preserving 7, ideal saving 1060 (pattern 2, middle, occupied 35, quality delta 0), counts as benefit: True. Largest valid saving 1108 lost quality: True.
- independent_fresh index 40 `inv_884523aa77c6`: candidates 14, quality-preserving 4, ideal saving 276 (pattern 0, middle, occupied 35, quality delta -1), counts as benefit: True. Largest valid saving 324 lost quality: True.
- independent_fresh index 45 `inv_c283ecd10aec`: candidates 5, quality-preserving 5, ideal saving 752 (pattern 6, early, occupied 0, quality delta 0), counts as benefit: True. Largest valid saving 752 lost quality: False.
- independent_fresh index 50 `inv_a362b3146a7c`: candidates 4, quality-preserving 4, ideal saving 3764 (pattern 2, early, occupied 0, quality delta 5), counts as benefit: True. Largest valid saving 3764 lost quality: False.
- independent_fresh index 55 `inv_5980af6e0651`: candidates 3, quality-preserving 2, ideal saving 1790 (pattern 4, early, occupied 0, quality delta 10), counts as benefit: True. Largest valid saving 1790 lost quality: False.
- recurring_family index 0 `inv_a8956340ad37`: candidates 4, quality-preserving 0, ideal saving 0, counts as benefit: False. Largest valid saving 132 lost quality: True.
- recurring_family index 10 `inv_41ec58701360`: candidates 14, quality-preserving 6, ideal saving 636 (pattern 22, early, occupied 0, quality delta -1), counts as benefit: True. Largest valid saving 636 lost quality: True.
- recurring_family index 20 `inv_4dbbbf516584`: candidates 1, quality-preserving 1, ideal saving 132 (pattern 24, early, occupied 0, quality delta 0), counts as benefit: True. Largest valid saving 132 lost quality: False.
- recurring_family index 30 `inv_a21f4dc3bf54`: candidates 1, quality-preserving 1, ideal saving 36 (pattern 3, early, occupied 0, quality delta 2), counts as benefit: False. Largest valid saving 36 lost quality: False.
- recurring_family index 40 `inv_5ba647788a08`: candidates 12, quality-preserving 9, ideal saving 132 (pattern 0, middle, occupied 35, quality delta 0), counts as benefit: True. Largest valid saving 132 lost quality: False.
- recurring_family index 50 `inv_6cf68140c244`: candidates 2, quality-preserving 2, ideal saving 84 (pattern 2, early, occupied 0, quality delta 0), counts as benefit: True. Largest valid saving 84 lost quality: False.

## Where the fresh box-level benefit sits

- Fresh boxes whose best quality-preserving candidate is an empty-board early placement: 5.
- Fresh boxes whose best quality-preserving candidate is a middle placement: 5.
- On 4 benefiting fresh boxes the largest effort cut lost more than the quality margin, and ideal selection did not take it.
- A one-cell drop is inside the margin of 1.0. It is not counted as a quality loss.

## Diagnostic cost

- Discovery checks to locate the sampled placements: 5764.
- Counterfactual effort, both branches: 342742.
- Wall time: 2.894 seconds.
- diagnostic only; not a deployable matcher and not a relaxation of the Expt-17 cost gate.

## Decision

- Row: **build_budgeted_matcher**.
- Quality-preserving benefit on the sample covers independent fresh boxes, more than one stage, and more than two patterns. A later experiment may build a budgeted matcher. This run did not build one, and it does not show that recognition is cheap.
- Independent fresh boxes at or above the saving floor: 10. Patterns [0, 2, 4, 6, 24]. Stages ['early', 'middle'].
- Family boxes at or above the saving floor: 4. Family benefit alone cannot justify a general matcher.
- Commitment: diagnostic counterfactuals only; no pattern was admitted to a policy.
- Expt-17 cost gate: not relaxed.
