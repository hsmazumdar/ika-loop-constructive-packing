# Expt-8B report

Give the predictor a consistent remaining-budget target and test whether its decisions improve on a per-seed mean baseline. Libraries stay frozen. Remaining-solves are diagnosis only.

- Directory: `e:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_08B_Consistent_Labels\results\20260929_231956_diagnostic`
- Preset: `diagnostic`
- Frozen libraries from Expt-7. No library retraining. Same features and admit bar as Expt-8.
- Development fit boxes (18): ['inv_01dcb410da3d', 'inv_28f717865766', 'inv_4b9eb8f15eaf', 'inv_ca731e3c4c13', 'inv_6b8058ed8650', 'inv_a50ff1cb12a5', 'inv_b8ca10ec1d55', 'inv_7334cb152bb1', 'inv_7f78315a08cd', 'inv_3a6415ba14bb', 'inv_a25252ed98bb', 'inv_2bcf2bd11f08', 'inv_e2258e487b41', 'inv_cd1593616a9d', 'inv_f37c190fae44', 'inv_f38e4acaef91', 'inv_99ae609def69', 'inv_18db09080c0d'].
- Development validation boxes (6): ['inv_ede60bd9d08e', 'inv_8b9cdaf23e25', 'inv_436a74b58bb1', 'inv_c0cfc0835886', 'inv_965fc9524c0a', 'inv_465ab2834adf'].
- Frozen-protocol holdout boxes (8): ['inv_22521942205c', 'inv_791d780fc6e4', 'inv_115b41c2392a', 'inv_5fc1ecabd17f', 'inv_8b533a843808', 'inv_bce49701ff81', 'inv_ffe570c70457', 'inv_1696d00e5191'].
- Label remaining budget is eval_cap − prefix_primitive_A for fit, validation, and holdout.
- remaining_saving = A_skip − A_commit and does not include site-check cost. Net after check subtracts actual examined, not the admission bound of 8.
- Primary saving fit is unweighted. Severe-loss-weighted models are a labeled comparison, not expected savings.

## Coverage counts (development validation, first-legal eligible)

- Split lists 6 validation box IDs. Eligible first-legal labels exist on 5 unique boxes, 11 seed–box pairs, 40 states, 56 actions.
- Expt-8's "5/11 boxes" was 5 unique boxes and 11 seed–box pairs with eligible actions, not 11 unique boxes. One of the six listed validation IDs produced no eligible first-legal action.
- Holdout lists 8 box IDs. Eligible first-legal labels: 7 unique boxes, 14 seed–box pairs, 59 states, 72 actions.

## Cap mismatch: same actions, both budgets

- Paired replays: 1373; 1600-cap hits skip 248, commit 203, either 384.
- Mean saving full 288.7; mean saving 1600 61.65; mean (full − 1600) 227.1.
- Full greater 195; full smaller 105; equal 1073.
- Distortion goes both ways. A 1600 cap does not automatically inflate validation savings. The signed mean here is the measured effect on these paired labels, not a general inflation theorem.

## Development validation error (first-legal)

- per_seed_mean: n=56; MAE 2567; RMSE 3753; pooled Pearson -0.2142; within-seed Pearson {'11': None, '22': None, '33': None}; AUC(beneficial) 0.4172; pred mean -122.9 vs y mean 1875; pred range [-350.1, 31.04].
- frozen: n=56; MAE 2886; RMSE 3935; pooled Pearson 0.3535; within-seed Pearson {'11': -0.3083899218050123, '22': -0.26521566920307676, '33': 0.7790658915248916}; AUC(beneficial) 0.5953; pred mean -576.9 vs y mean 1875; pred range [-746, -190.7].
- context_unweighted: n=56; MAE 2561; RMSE 3762; pooled Pearson -0.3037; within-seed Pearson {'11': 0.1740374024895242, '22': 0.2532006966678221, '33': -0.3341877811093087}; AUC(beneficial) 0.3984; pred mean -118.8 vs y mean 1875; pred range [-417.3, 95.45].
- action_unweighted: n=56; MAE 2650; RMSE 3798; pooled Pearson -0.05983; within-seed Pearson {'11': 0.059178503004828006, '22': 0.06801629105590024, '33': 0.11794527644599721}; AUC(beneficial) 0.3766; pred mean -240 vs y mean 1875; pred range [-605.4, 152.9].
- context_weighted: n=56; MAE 4487; RMSE 5250; pooled Pearson 0.3131; within-seed Pearson {'11': 0.2639555719195702, '22': -0.6600835136380244, '33': -0.10904793176945488}; AUC(beneficial) 0.4891; pred mean -2432 vs y mean 1875; pred range [-3461, -1359].
- action_weighted: n=56; MAE 4766; RMSE 5463; pooled Pearson 0.309; within-seed Pearson {'11': 0.4264606520386135, '22': -0.051528315497965396, '33': -0.009344105539754325}; AUC(beneficial) 0.475; pred mean -2697 vs y mean 1875; pred range [-4611, -1388].
- Unweighted action-level MAE beats per-seed mean: False.
- The baseline is a per-seed mean, constant within a seed. Within-seed Pearson is undefined. Pooled Pearson can still be nonzero because seed means differ (fit means were negative on seeds 11 and 22 and slightly positive on seed 33).
- Weighted models estimate a different target. Their large negative predictions are not ordinary expected savings.

## Development validation selection

- Admission bound pred_saving > 8. Quality gate unchanged. Billed cost is examined, not the bound of 8.
- per_seed_mean first-legal: accepted 22/56 actions on 5 unique boxes / 5 seed–box pairs / 20 states (eligible: 5 boxes, 11 pairs, 40 states); mean remaining-saving 1805; mean billed examined 2.364; mean net = remaining-saving − examined 1803; admission bound 8 is not subtracted from the label; quality-loss rate 0.2273; severe losses 3 (0.1364).
- frozen first-legal: **zero coverage** (0/56 actions). Eligible: 5 unique boxes, 11 seed–box pairs, 40 states, 56 actions. Reject-all is not successful selection.
- context_unweighted first-legal: **zero coverage** (0/56 actions). Eligible: 5 unique boxes, 11 seed–box pairs, 40 states, 56 actions. Reject-all is not successful selection.
- action_unweighted first-legal: **zero coverage** (0/56 actions). Eligible: 5 unique boxes, 11 seed–box pairs, 40 states, 56 actions. Reject-all is not successful selection.
- context_weighted first-legal: **zero coverage** (0/56 actions). Eligible: 5 unique boxes, 11 seed–box pairs, 40 states, 56 actions. Reject-all is not successful selection.
- action_weighted first-legal: **zero coverage** (0/56 actions). Eligible: 5 unique boxes, 11 seed–box pairs, 40 states, 56 actions. Reject-all is not successful selection.
- Per-seed mean still accepts only where the seed's fit mean exceeds 8 (seed 33). Quality-loss 0.2273 exceeds the 0.2 gate. Positive mean net on that slice is not a useful subset.
- Unweighted action-level coverage on development validation: 0 accepted. Frozen choice after development is abstain: no learned predictor has a useful accepted subset.

## Holdout (protocol frozen; models fit on development only)

- per_seed_mean: n=72; MAE 1053; RMSE 2125; pooled Pearson 0.2893; within-seed Pearson {'11': None, '22': None, '33': None}; AUC(beneficial) 0.5961; pred mean -141.5 vs y mean 141.5; pred range [-350.1, 31.04].
- per_seed_mean first-legal: accepted 36/72 actions on 7 unique boxes / 7 seed–box pairs / 32 states (eligible: 7 boxes, 14 pairs, 59 states); mean remaining-saving 814.6; mean billed examined 2.306; mean net = remaining-saving − examined 812.2; admission bound 8 is not subtracted from the label; quality-loss rate 0.02778; severe losses 10 (0.2778).
- context_unweighted: n=72; MAE 1059; RMSE 2131; pooled Pearson 0.2265; within-seed Pearson {'11': 0.13084417287881092, '22': 0.7556523037996558, '33': -0.09552068355866532}; AUC(beneficial) 0.6258; pred mean -130.5 vs y mean 141.5; pred range [-430.5, 155.5].
- context_unweighted first-legal: accepted 3/72 actions on 2 unique boxes / 2 seed–box pairs / 3 states (eligible: 7 boxes, 14 pairs, 59 states); mean remaining-saving 1030; mean billed examined 3; mean net = remaining-saving − examined 1027; admission bound 8 is not subtracted from the label; quality-loss rate 0; severe losses 0 (0).
- action_unweighted: n=72; MAE 1054; RMSE 2128; pooled Pearson 0.3048; within-seed Pearson {'11': 0.06117252977515784, '22': 0.7359959290783582, '33': -0.007256480983435678}; AUC(beneficial) 0.657; pred mean -192.4 vs y mean 141.5; pred range [-503.6, 158.2].
- action_unweighted first-legal: accepted 4/72 actions on 3 unique boxes / 3 seed–box pairs / 4 states (eligible: 7 boxes, 14 pairs, 59 states); mean remaining-saving 546.5; mean billed examined 3.25; mean net = remaining-saving − examined 543.2; admission bound 8 is not subtracted from the label; quality-loss rate 0; severe losses 0 (0).
- Mechanical holdout useful_subset flag: True.
- Action-unweighted accepted 4 first-legal actions on 3 unique boxes, all on seed 33. Mean net 543.2 with quality-loss 0. That slice includes a zero-saving placement whose billed checks are a net loss; the mean is carried by one large positive remainder.
- Per-seed mean also accepts on seed 33 only (36 actions, quality-loss 0.02778, severe-loss rate 0.2778). A larger mean net with 27.8% severe losses is not a better policy.
- Holdout does not show that action-level decisions improve on the per-seed mean across seeds. Development already froze the learned models at zero coverage. The four-action holdout slice is not a selected, deployable subset.

## Whole-box confirmation

- Skipped. n_fresh=0
- No new retrieval or placement mechanism was added. Budget 0 remains required if a later subset is ever deployed.

## Ledgers

- skip 3552; commit 3552; cache 0; feature checks 49203.

The 8-evaluation figure is the admission bound (pred_saving > anchors). Billed site-check cost is examined (often 1–3, mean about 2.2 on development first-legal). That is why net can drop by about two rather than eight.

## Provenance addendum (Expt-8C audit)

The eight-box set listed above as “frozen-protocol holdout” is **development / reused evaluation**, not unseen confirmation. All eight IDs appear in `development.json` from Expt-2 through Expt-8B, including Expt-4D2 diagnostic cases (`inv_115b41c2392a`, `inv_bce49701ff81`, `inv_ffe570c70457`, `inv_22521942205c`, and the other four). Disjointness from the 18/6 fit–val split does not make them fresh.

Fit and validation remaining-saving values are identical to Expt-8 on all 1,086 + 287 paired rows. Expt-8 `remaining_pair` already used `eval_cap − prefix_A`; `pair_eval_cap=1600` was recorded but not used as the solve budget. Matching per-seed, frozen Expt-7, and weighted-model validation summaries are therefore expected. File hashes differ because 8B added cap-hit and 1600-replay columns. Frozen Expt-7 remains a historical 1600-cap comparator. Unweighted models are the new 8B fits.

Net after check subtracts site checks only. It is not total deployment savings.

## History correction (Expt-8C)

Expt-8 already used eval_cap − prefix_A for action-level fit and validation labels. Expt-8B added cap-hit and 1600-replay columns but changed none of those remaining-saving values (0/1086 fit, 0/287 val). The 1600-cap mismatch is a property of the historical Expt-7 predictor, not of Expt-8/8B action-level labels.

