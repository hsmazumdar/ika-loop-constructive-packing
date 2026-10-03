# Expt-8C report

Expt-8B holdout was reused development, not unseen confirmation. Freeze those models and decision rules, then evaluate once on genuinely new boxes. Do not retune thresholds.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_08C_Unseen_Confirmation\results\20260929_233422_diagnostic`
- Preset: `diagnostic`
- Frozen libraries from Expt-7. Models frozen from Expt-8B development fit labels. Thresholds not retuned on this set.
- Unseen boxes (50): ['inv_dc3325f3c616', 'inv_084f2c25ca3c', 'inv_62d7afc8ca88', 'inv_4b2473c6219a', 'inv_456b94ae0f13', 'inv_674657a8852e', 'inv_dabf123a3b0f', 'inv_6a9bba280138', 'inv_644723d65d0a', 'inv_8fb1b9d9af82', 'inv_d504b5a3fa5e', 'inv_35d63b1e1e60', 'inv_6c73e7b59327', 'inv_8cddbe1fd185', 'inv_38d97369daf6', 'inv_41f5b4065991', 'inv_7893b535de81', 'inv_5ffe7e3c21ce', 'inv_1f630c402535', 'inv_129dc24ddcd4', 'inv_d1cc869bdf0c', 'inv_a655fb0ee04b', 'inv_663e5b962493', 'inv_cb60c01efbe2', 'inv_b21f70de1ba4', 'inv_521ca502014b', 'inv_53a6adb46f26', 'inv_598ae18f142c', 'inv_722bd6592329', 'inv_8fe395831830', 'inv_59dde4cb3a17', 'inv_b50dc054cb2b', 'inv_5ac79be2484f', 'inv_b55b2e3c28a7', 'inv_87f5247026d1', 'inv_3026d42b3fbd', 'inv_573519390d2f', 'inv_4e76918c54df', 'inv_3b961c784c0e', 'inv_385ab4ab3835', 'inv_81ac190e5253', 'inv_5ed6035c9f29', 'inv_b7b8d91c40ff', 'inv_4d85817b5faf', 'inv_ef8f50584fbe', 'inv_67c35147142d', 'inv_fea51a4ab201', 'inv_e5e97de9ed6f', 'inv_cdcb182e4d92', 'inv_402a4ff3fd9e'].
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

- per_seed_mean: n=541; MAE 1153; pooled Pearson 0.1139; pred mean -128.8 vs y mean -99.83; pred range [-350.1, 31.04].
- frozen [historical]: n=541; MAE 1357; pooled Pearson -0.06909; pred mean -556.2 vs y mean -99.83; pred range [-791.9, -164.3].
- context_unweighted: n=541; MAE 1151; pooled Pearson 0.1019; pred mean -125 vs y mean -99.83; pred range [-448.5, 218.9].
- action_unweighted: n=541; MAE 1189; pooled Pearson 0.09442; pred mean -234.1 vs y mean -99.83; pred range [-891.6, 229.8].
- context_weighted [historical]: n=541; MAE 2688; pooled Pearson 0.03101; pred mean -2352 vs y mean -99.83; pred range [-3683, -1270].
- action_weighted [historical]: n=541; MAE 2849; pooled Pearson 0.03618; pred mean -2551 vs y mean -99.83; pred range [-4968, -1114].
- Unweighted action MAE beats per-seed mean: False.

## Unseen selection (thresholds frozen)

- Admission bound pred_saving > 8. Not changed after inspecting this set.
- per_seed_mean: accepted 231/541 actions on 40 unique boxes / 40 seed–box pairs / 191 states; mean remaining-saving 203.8; mean billed examined 2.385; mean net after site checks 201.5; quality-loss 0.1082; severe losses 62 (0.2684).
- frozen [historical comparator]: **zero coverage** (0/541 actions). Eligible: 45 unique boxes, 98 seed–box pairs, 419 states, 541 actions.
- context_unweighted: accepted 4/541 actions on 3 unique boxes / 3 seed–box pairs / 4 states; mean remaining-saving -415; mean billed examined 3.25; mean net after site checks -418.2; quality-loss 0.25; severe losses 1 (0.25).
- action_unweighted: accepted 8/541 actions on 7 unique boxes / 7 seed–box pairs / 8 states; mean remaining-saving 24.5; mean billed examined 3.25; mean net after site checks 21.25; quality-loss 0; severe losses 1 (0.125).
- context_weighted [historical comparator]: **zero coverage** (0/541 actions). Eligible: 45 unique boxes, 98 seed–box pairs, 419 states, 541 actions.
- action_weighted [historical comparator]: **zero coverage** (0/541 actions). Eligible: 45 unique boxes, 98 seed–box pairs, 419 states, 541 actions.

## Accepted-action costs (unweighted action model)

- Accepted 8 actions on 1 seeds.
- Sum remaining-saving 196.
- Mean net after site checks only 21.25. Site-check net is not total deployment savings.
- Sum action decision cost (examined + feature_checks) 209.
- Consult cost on all scored states (index + compat + ranking, including rejects) 1608.
- Net after those decision costs -1621.
- Largest accepted box: {'task_id': 'inv_b21f70de1ba4', 'n_accepted': 1, 'seeds': [33], 'remaining_saving': 96.0, 'share_of_accepted_saving': 0.4897959183673469, 'examined': 2.0, 'feature_checks': 28.0}.
- Remaining-saving without that box 100.
- By seed: {'33': {'n_accepted': 8, 'n_boxes': 7, 'remaining_saving': 196.0}}.
- net_after_decision_costs subtracts accepted site checks and feature checks plus index/ranking on every consulted state, including rejected consultations. It is still not whole-box policy savings.

## Whole-box confirmation

- Skipped. unseen offline evidence was not convincing across seeds and boxes
- Convincing unseen offline evidence: False.
- No new retrieval or placement mechanism. Thresholds were not retuned on this set.

## Ledgers

- skip 541; commit 541; cache 0; feature checks 17167.

Feature checks are cell inspections inside `action_vector` / `local_free_space` for each first-legal candidate. Remaining-solves do not add feature checks. Of 17,167: **183** were on the 8 accepted actions and **16,984** on the 533 rejected actions. The published offline net (−1,621) billed accepted features only. Scoring every candidate to decide is deployment-relevant, so rejected features belong in the decision ledger. Including them and rejected site checks (1,288) with consult 1,608 gives 196 − 26 − 17,167 − 1,288 − 1,608 = **−19,893**. The sign does not change.

