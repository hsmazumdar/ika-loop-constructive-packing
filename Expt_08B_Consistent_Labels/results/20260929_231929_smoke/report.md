# Expt-8B report

Give the predictor a consistent remaining-budget target and test whether its decisions improve on a per-seed mean baseline. Libraries stay frozen. Remaining-solves are diagnosis only.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_08B_Consistent_Labels\results\20260929_231929_smoke`
- Preset: `smoke`
- Frozen libraries from Expt-7. No library retraining. Same features and admit bar as Expt-8.
- Development fit boxes (3): ['inv_01dcb410da3d', 'inv_28f717865766', 'inv_4b9eb8f15eaf'].
- Development validation boxes (1): ['inv_ca731e3c4c13'].
- Frozen-protocol holdout boxes (2): ['inv_22521942205c', 'inv_791d780fc6e4'].
- Label remaining budget is eval_cap − prefix_primitive_A for fit, validation, and holdout.
- remaining_saving = A_skip − A_commit and does not include site-check cost. Net after check subtracts actual examined, not the admission bound of 8.
- Primary saving fit is unweighted. Severe-loss-weighted models are a labeled comparison, not expected savings.

## Cap mismatch: same actions, both budgets

- Paired replays: 40; 1600-cap hits skip 0, commit 5, either 5.
- Mean saving full -192.6; mean saving 1600 -40.85; mean (full − 1600) -151.8.
- Full greater 0; full smaller 5; equal 35.
- A positive delta means the full remaining budget records a larger saving than the 1600 cap on that same state–action. Both directions occur.

## Development validation error (first-legal)

- per_seed_mean: n=3; MAE 286.5; RMSE 294.2; pooled Pearson NA; within-seed Pearson {11: None}; AUC(beneficial) 0.5; pred mean -239.4 vs y mean -174.7; pred range [-239.4, -239.4].
- frozen: n=3; MAE 296; RMSE 304.7; pooled Pearson -0.2021; within-seed Pearson {11: -0.2020761807246337}; AUC(beneficial) 0; pred mean -268 vs y mean -174.7; pred range [-284.5, -251.3].
- context_unweighted: n=3; MAE 278.5; RMSE 291.8; pooled Pearson -0.2514; within-seed Pearson {11: -0.2513753835347626}; AUC(beneficial) 0; pred mean -214.6 vs y mean -174.7; pred range [-224.4, -205.2].
- action_unweighted: n=3; MAE 314; RMSE 321.5; pooled Pearson -0.992; within-seed Pearson {11: -0.9919990232652504}; AUC(beneficial) 0; pred mean -311.2 vs y mean -174.7; pred range [-315.5, -305.9].
- context_weighted: n=3; MAE 739.1; RMSE 797.2; pooled Pearson -0.2442; within-seed Pearson {11: -0.2442154784438069}; AUC(beneficial) 0; pred mean -913.7 vs y mean -174.7; pred range [-962.2, -867.5].
- action_weighted: n=3; MAE 985.5; RMSE 1036; pooled Pearson -0.7744; within-seed Pearson {11: -0.7743863152007149}; AUC(beneficial) 0; pred mean -1160 vs y mean -174.7; pred range [-1217, -1124].
- Unweighted action-level MAE beats per-seed mean: False.
- Per-seed mean is constant within a seed, so within-seed Pearson is undefined. Pooled Pearson can still be nonzero because seed means differ.

## Development validation selection

- Admission bound pred_saving > 8. Quality gate unchanged.
- per_seed_mean first-legal: **zero coverage** (0/3 actions). Eligible: 1 unique boxes, 1 seed–box pairs, 3 states, 3 actions. Reject-all is not successful selection.
- frozen first-legal: **zero coverage** (0/3 actions). Eligible: 1 unique boxes, 1 seed–box pairs, 3 states, 3 actions. Reject-all is not successful selection.
- context_unweighted first-legal: **zero coverage** (0/3 actions). Eligible: 1 unique boxes, 1 seed–box pairs, 3 states, 3 actions. Reject-all is not successful selection.
- action_unweighted first-legal: **zero coverage** (0/3 actions). Eligible: 1 unique boxes, 1 seed–box pairs, 3 states, 3 actions. Reject-all is not successful selection.
- context_weighted first-legal: **zero coverage** (0/3 actions). Eligible: 1 unique boxes, 1 seed–box pairs, 3 states, 3 actions. Reject-all is not successful selection.
- action_weighted first-legal: **zero coverage** (0/3 actions). Eligible: 1 unique boxes, 1 seed–box pairs, 3 states, 3 actions. Reject-all is not successful selection.

## Holdout (models frozen after development fit)

- per_seed_mean: n=8; MAE 1092; RMSE 1815; pooled Pearson NA; within-seed Pearson {11: None}; AUC(beneficial) 0.5; pred mean -239.4 vs y mean -1044; pred range [-239.4, -239.4].
- per_seed_mean first-legal: **zero coverage** (0/8 actions). Eligible: 2 unique boxes, 2 seed–box pairs, 7 states, 8 actions. Reject-all is not successful selection.
- context_unweighted: n=8; MAE 1098; RMSE 1822; pooled Pearson -0.1889; within-seed Pearson {11: -0.18894748678430803}; AUC(beneficial) 0.2667; pred mean -225.1 vs y mean -1044; pred range [-238.4, -210.6].
- context_unweighted first-legal: **zero coverage** (0/8 actions). Eligible: 2 unique boxes, 2 seed–box pairs, 7 states, 8 actions. Reject-all is not successful selection.
- action_unweighted: n=8; MAE 1070; RMSE 1819; pooled Pearson -0.1602; within-seed Pearson {11: -0.1602301896060243}; AUC(beneficial) 0.7333; pred mean -251.5 vs y mean -1044; pred range [-310.6, -170.5].
- action_unweighted first-legal: **zero coverage** (0/8 actions). Eligible: 2 unique boxes, 2 seed–box pairs, 7 states, 8 actions. Reject-all is not successful selection.
- Holdout useful subset: False.

## Whole-box confirmation

- Skipped. holdout did not support a useful accepted subset
- No new retrieval or placement mechanism was added.

## Ledgers

- skip 116; commit 116; cache 0; feature checks 1655.

The 8-evaluation figure is the admission bound (pred_saving > anchors). Billed site-check cost is examined, often 1–3, which is why net can drop by about two rather than eight.
