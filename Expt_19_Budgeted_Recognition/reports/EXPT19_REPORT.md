# Expt-19 report

Can a frozen budgeted matcher expose quality-preserving placement actions from the 58 arrangements, within an absolute recognition budget, without using future outcomes to choose where to look?

The 58 arrangements stay frozen. The matcher may only propose a placement; commitment is disabled. Development manifests set one absolute recognition budget from their mean primitive effort. Validation fresh is the decision set. Counterfactual replays that label the reference are a separate diagnostic ledger. Recall is against that sample, not against every legal placement.

The advice note recommended this recognition step only after Expt-18, and it kept a commitment rule as a later experiment. It also suggested a learned embedding and a risk gate. Those are not part of this run. The anchor rule was not adjusted to the ten Expt-18 boxes or the five patterns those boxes used.

- Directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_19_Budgeted_Recognition\results\20260930_092450_diagnostic`
- Preset: `diagnostic`
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Frozen patterns: 58. Reference sample indices: [0, 1, 2, 3, 4, 6, 22, 19, 24, 44, 7, 18, 9].
- Stronger-support indices inside that sample: [0, 1, 2, 3, 4].
- Development boxes: 120. Mean primitive effort 1411. Absolute budget 141.
- Validation tasks excluded because their id was in the development manifests: 8.
- Anchors: If the board is empty, the only anchor is [0, 0]. Otherwise the first 4 free cells in row-major order that touch an occupied cell. The scan stops when that many anchors are found.
- Gate: mean recognition cost / mean primitive effort on validation fresh < 0.10. Recall floor 0.5. Retention floor 0.5. At least 3 fresh boxes with a reference opportunity.

## Validation fresh (decision set)

### validation_fresh

- Boxes 60. Mean primitive effort 1125. Mean recognition 127.7. Mean ratio 0.1381.
- Boxes under the 0.10 gate: 15. Budget exhausted: 18.
- Audited states with a useful reference action: 53. State recall 0.6226. Action recall 0.4859 of 142 useful actions.
- Boxes with a reference opportunity: 39. Mean oracle saving 425.4. Mean retained 316.5. Mean retention 0.7916.
- Miss reasons among useful actions: {'budget_before_state': 49, 'exposed': 69, 'budget_during_consult': 24}.
- Stronger support (at least 3 inventories): {'useful_actions': 60, 'exposed_actions': 39, 'action_recall': 0.65, 'n_boxes': 24, 'mean_retention': 0.9123439000960615}.
- Support-two patterns: {'useful_actions': 82, 'exposed_actions': 30, 'action_recall': 0.36585365853658536, 'n_boxes': 15, 'mean_retention': 0.5983758475944463}.
- Unlabeled exposures (not in the sampled reference): 198.
- Diagnostic enumeration and replays, not recognition cost: 10590 discovery checks, 611742 counterfactual evaluations.

## Validation family (not the decision)

### validation_family

- Boxes 52. Mean primitive effort 1183. Mean recognition 138.8. Mean ratio 0.1531.
- Boxes under the 0.10 gate: 8. Budget exhausted: 39.
- Audited states with a useful reference action: 69. State recall 0.5217. Action recall 0.5048 of 208 useful actions.
- Boxes with a reference opportunity: 45. Mean oracle saving 548.2. Mean retained 526.1. Mean retention 0.7956.
- Miss reasons among useful actions: {'exposed': 105, 'budget_during_consult': 29, 'budget_before_state': 74}.
- Stronger support (at least 3 inventories): {'useful_actions': 84, 'exposed_actions': 52, 'action_recall': 0.6190476190476191, 'n_boxes': 34, 'mean_retention': 0.8203640200474809}.
- Support-two patterns: {'useful_actions': 124, 'exposed_actions': 53, 'action_recall': 0.4274193548387097, 'n_boxes': 11, 'mean_retention': 0.7190704032809296}.
- Unlabeled exposures (not in the sampled reference): 157.
- Diagnostic enumeration and replays, not recognition cost: 15753 discovery checks, 816828 counterfactual evaluations.

## Decision

- Row: **recognition_expensive**.
- Recognition remains expensive relative to primitive effort on the held-out fresh boxes. Stop this access design.
- The ratio of means is 0.1135. The mean of per-box ratios is 0.138. Fifteen of 60 fresh boxes are individually under 0.10. The absolute budget was 141, one tenth of the development mean 1,411; these fresh boxes cost 1,125 on average, so that fixed budget is more than a tenth of their effort.
- Useful reference actions missed for budget, not for anchors: 69 exposed, 49 already out of budget before the state, 24 out of budget during that consultation, 0 outside the anchor set.
- State recall 0.6226 and mean retention 0.7916 would have met the recall floors. They do not open a commitment experiment, because the cost gate failed.
- Stronger-support action recall is 0.65; support-two action recall is 0.37. The dictionary order spends the budget on the front of the list. That split was not used to reorder the list.
- Commitment: disabled. Commitment quality and end-to-end savings remain untested for this dictionary.
- applied to validation fresh; not used to choose the absolute budget.
- Recorded conclusion: this sequential recognizer failed. Useful recall does not override the cost gate. No anchor misses occurred among the sampled reference actions; that does not show the anchor set covers every useful placement. The gap from about 128 to the gate of 112.5 is about 12% at mean primitive effort 1,125, and cutting the budget could cut recall, so it is not evidence that a small change will pass. A learned embedding was not tested and is not justified over simpler indexing. Do not lower this budget on these same boxes until the gate passes.
