# Expt-8C report

Expt-8B holdout was reused development, not unseen confirmation. Freeze those models and decision rules, then evaluate once on genuinely new boxes. Do not retune thresholds.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_08C_Unseen_Confirmation\results\20260929_233348_smoke`
- Preset: `smoke`
- Frozen libraries from Expt-7. Models frozen from Expt-8B development fit labels. Thresholds not retuned on this set.
- Unseen boxes (4): ['inv_1d502c7cfaab', 'inv_2476cc8828e5', 'inv_7988f7c150bf', 'inv_cc5b3a4fa7b9'].
- Label budget: eval_cap - prefix_primitive_A. Cache key: (state_fingerprint, action_key, remaining_cap).
- labels_fit sha256: 6a18c0cdff39172422046adaead86119970819dd29952808dbb66866237cd487.
- model payload sha256: f2b78e90a808a038b6ab6599360f52ff5b1be216977f88c90c76579788dec087.
- frozen file sha256: e14c795908ac987f14267cdaf8659ecccd65754407f67fc2b71fd8b2f15348cf.

## Provenance: Expt-8B eight-box set is not unseen

- Status: development/reused evaluation, not unseen confirmation.
- Boxes with at least one prior data-file use: 8 / 8.
- inv_22521942205c: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']
- inv_791d780fc6e4: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']
- inv_115b41c2392a: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']
- inv_5fc1ecabd17f: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']
- inv_8b533a843808: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']
- inv_bce49701ff81: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']
- inv_ffe570c70457: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']
- inv_1696d00e5191: ['Expt_08_Action_Level_Value/data/development.json', 'Expt_08C_Unseen_Confirmation/data/development.json', 'Expt_08B_Consistent_Labels/data/development.json', 'Expt_07_Indexed_Retrieval/data/development.json', 'Expt_07B_Decision_Audit/data/development.json', 'Expt_06_Frozen_Library_Opportunity/data/development.json', 'Expt_05_Consult_and_Commit_Gates/data/development.json', 'Expt_04D_Where_Reuse_Loses_Advantage/data/development.json', 'Expt_04D2_Costly_Choices/data/development.json', 'Expt_04C_Confirm_Reusable_Knowledge/data/development.json', 'Expt_03_Mined_Operation_Library/data/runtime/development.json', 'Expt_02_Autonomous_Abstraction/data/runtime/development.json']

## Corrected-label identity

- Fit y changed vs Expt-8: 0 of 1086 common rows.
- Val y changed vs Expt-8: 0 of 287 common rows.
- Fit file sha256 Expt-8 d2a6a5c2308d668ff35dbf7b95c43716e5343bb16f76e5c7ba8841ca0b363926; Expt-8B 6a18c0cdff39172422046adaead86119970819dd29952808dbb66866237cd487.
- 1600-replay differs from the actual 8B/8 fit label on 167 fit rows.
- Expt-8 and Expt-8B per-seed, frozen Expt-7, and weighted-model validation summaries match because Expt-8 remaining_pair already used eval_cap − prefix_A for both fit and val. pair_eval_cap was recorded but not used as the solve budget. File hashes differ because 8B added censoring and 1600-replay columns. Weighted models were rebuilt from those same y values. Unweighted models are new. Frozen Expt-7 is a historical comparator trained under pair_eval_cap=1600.
- Frozen Expt-7 rankers are historical comparators (trained under pair_eval_cap=1600). Newly fitted unweighted models are rebuilt from Expt-8B labels_fit.csv and serialized with that budget in their identity.

## Unseen first-legal error

- per_seed_mean: n=10; MAE 1247; pooled Pearson NA; pred mean -350.1 vs y mean -1062; pred range [-350.1, -350.1].
- frozen [historical]: n=10; MAE 1214; pooled Pearson 0.461; pred mean -242 vs y mean -1062; pred range [-290.9, -200].
- context_unweighted: n=10; MAE 1267; pooled Pearson -0.0581; pred mean -381.2 vs y mean -1062; pred range [-426.6, -323.5].
- action_unweighted: n=10; MAE 1261; pooled Pearson 0.2091; pred mean -407.8 vs y mean -1062; pred range [-479, -357.3].
- context_weighted [historical]: n=10; MAE 1785; pooled Pearson -0.1318; pred mean -1759 vs y mean -1062; pred range [-1954, -1482].
- action_weighted [historical]: n=10; MAE 1812; pooled Pearson 0.2806; pred mean -1866 vs y mean -1062; pred range [-2111, -1545].
- Unweighted action MAE beats per-seed mean: False.

## Unseen selection (thresholds frozen)

- Admission bound pred_saving > 8. Not changed after inspecting this set.
- per_seed_mean: **zero coverage** (0/10 actions). Eligible: 3 unique boxes, 3 seed–box pairs, 10 states, 10 actions.
- frozen [historical comparator]: **zero coverage** (0/10 actions). Eligible: 3 unique boxes, 3 seed–box pairs, 10 states, 10 actions.
- context_unweighted: **zero coverage** (0/10 actions). Eligible: 3 unique boxes, 3 seed–box pairs, 10 states, 10 actions.
- action_unweighted: **zero coverage** (0/10 actions). Eligible: 3 unique boxes, 3 seed–box pairs, 10 states, 10 actions.
- context_weighted [historical comparator]: **zero coverage** (0/10 actions). Eligible: 3 unique boxes, 3 seed–box pairs, 10 states, 10 actions.
- action_weighted [historical comparator]: **zero coverage** (0/10 actions). Eligible: 3 unique boxes, 3 seed–box pairs, 10 states, 10 actions.

## Accepted-action costs (unweighted action model)

- Accepted 0 actions on 0 seeds.
- Sum remaining-saving NA.
- Mean net after site checks only NA. Site-check net is not total deployment savings.
- Sum action decision cost (examined + feature_checks) NA.
- Consult cost on all scored states (index + compat + ranking, including rejects) 32.
- Net after those decision costs NA.
- Largest accepted box: None.
- Remaining-saving without that box NA.
- By seed: {}.
- net_after_decision_costs subtracts accepted site checks and feature checks plus index/ranking on every consulted state, including rejected consultations. It is still not whole-box policy savings.

## Whole-box confirmation

- Skipped. unseen offline evidence was not convincing across seeds and boxes
- Convincing unseen offline evidence: False.
- No new retrieval or placement mechanism. Thresholds were not retuned on this set.

## Ledgers

- skip 10; commit 10; cache 0; feature checks 322.
