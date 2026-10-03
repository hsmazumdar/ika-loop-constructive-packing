# Expt-8B target audit

{
  "training_action": "first_legal_site (8 shuffled anchors), not oracle-best placement",
  "deployment_action": "first_legal_site (8 shuffled anchors)",
  "train_deploy_action_mismatch": false,
  "remaining_saving_sign": "A_skip - A_commit; positive means fewer remaining evaluations",
  "training_units": "raw remaining primitive evaluations",
  "training_remaining_cap": "pair_eval_cap=1600 (truncated vs full remaining budget)",
  "expt7b_remaining_cap": "eval_cap - prefix_primitive_A",
  "expt8b_remaining_cap": "eval_cap - prefix_primitive_A for fit, validation, and holdout",
  "cap_mismatch": true,
  "expt8b_cap_mismatch": false,
  "n_training_labels": 206,
  "training_saving_mean": -99.14077669902913,
  "training_saving_weighted_mean": -611.9314508340753,
  "n_training_negative": 86,
  "n_training_beneficial": 110,
  "severe_loss_weighting": "sample_weight adds max(0,-saving)/400 plus 8 on quality failure",
  "seeds": [],
  "note": "Uniformly negative deployment predictions can follow from fitting a linear model to severe-loss-weighted labels whose weighted mean is largely negative, even when the unweighted mean is near zero. That is not a sign error. It also does not by itself prove that placement features are uninformative.",
  "expt7_result": "E:\\PaperSubmissions2026\\MGA_Memory_Guided_Assembly\\Expt_07_Indexed_Retrieval\\results\\20260929_220030_diagnostic",
  "exists": true
}
