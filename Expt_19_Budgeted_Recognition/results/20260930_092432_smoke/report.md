# Expt-19 report

Can a frozen budgeted matcher expose quality-preserving placement actions from the 58 arrangements, within an absolute recognition budget, without using future outcomes to choose where to look?

The 58 arrangements stay frozen. The matcher may only propose a placement; commitment is disabled. Development manifests set one absolute recognition budget from their mean primitive effort. Validation fresh is the decision set. Counterfactual replays that label the reference are a separate diagnostic ledger. Recall is against that sample, not against every legal placement.

The advice note recommended this recognition step only after Expt-18, and it kept a commitment rule as a later experiment. It also suggested a learned embedding and a risk gate. Those are not part of this run. The anchor rule was not adjusted to the ten Expt-18 boxes or the five patterns those boxes used.

- Directory: `K:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_19_Budgeted_Recognition\results\20260930_092432_smoke`
- Preset: `smoke`
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Frozen patterns: 58. Reference sample indices: [0, 1, 2, 3].
- Stronger-support indices inside that sample: [0, 1, 2, 3].
- Development boxes: 4. Mean primitive effort 984. Absolute budget 98.
- Validation tasks excluded because their id was in the development manifests: 0.
- Anchors: If the board is empty, the only anchor is [0, 0]. Otherwise the first 4 free cells in row-major order that touch an occupied cell. The scan stops when that many anchors are found.
- Gate: mean recognition cost / mean primitive effort on validation fresh < 0.10. Recall floor 0.5. Retention floor 0.5. At least 3 fresh boxes with a reference opportunity.

## Validation fresh (decision set)

### validation_fresh

- Boxes 1. Mean primitive effort 816. Mean recognition 85. Mean ratio 0.1042.
- Boxes under the 0.10 gate: 0. Budget exhausted: 0.
- Audited states with a useful reference action: 0. State recall n/a. Action recall n/a of 0 useful actions.
- Boxes with a reference opportunity: 0. Mean oracle saving n/a. Mean retained n/a. Mean retention n/a.
- Miss reasons among useful actions: {}.
- Stronger support (at least 3 inventories): {'useful_actions': 0, 'exposed_actions': 0, 'action_recall': None, 'n_boxes': 0, 'mean_retention': None}.
- Support-two patterns: {'useful_actions': 0, 'exposed_actions': 0, 'action_recall': None, 'n_boxes': 0, 'mean_retention': None}.
- Unlabeled exposures (not in the sampled reference): 2.
- Diagnostic enumeration and replays, not recognition cost: 8 discovery checks, 0 counterfactual evaluations.

## Validation family (not the decision)

### validation_family

- Boxes 1. Mean primitive effort 768. Mean recognition 95. Mean ratio 0.1237.
- Boxes under the 0.10 gate: 0. Budget exhausted: 0.
- Audited states with a useful reference action: 0. State recall n/a. Action recall n/a of 0 useful actions.
- Boxes with a reference opportunity: 0. Mean oracle saving n/a. Mean retained n/a. Mean retention n/a.
- Miss reasons among useful actions: {}.
- Stronger support (at least 3 inventories): {'useful_actions': 0, 'exposed_actions': 0, 'action_recall': None, 'n_boxes': 0, 'mean_retention': None}.
- Support-two patterns: {'useful_actions': 0, 'exposed_actions': 0, 'action_recall': None, 'n_boxes': 0, 'mean_retention': None}.
- Unlabeled exposures (not in the sampled reference): 2.
- Diagnostic enumeration and replays, not recognition cost: 19 discovery checks, 9201 counterfactual evaluations.

## Decision

- Row: **recognition_expensive**.
- Recognition remains expensive relative to primitive effort on the held-out fresh boxes. Stop this access design.
- Fresh recognition / primitive: 0.1042. Cheap: False.
- State recall n/a. Mean retention n/a.
- Commitment: disabled.
- applied to validation fresh; not used to choose the absolute budget.
- A successful recogniser would still not establish cheaper autonomous solving. That needs a frozen commitment policy that preserves whole-box quality and repays recognition, including rejected consultations.
