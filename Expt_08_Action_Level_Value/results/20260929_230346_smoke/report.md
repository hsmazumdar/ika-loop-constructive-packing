# Expt-8 report

Can inexpensive information available before a specific placement distinguish beneficial reuse from costly reuse? Libraries stay frozen. Remaining-solves are diagnosis only.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_08_Action_Level_Value\results\20260929_230346_smoke`
- Preset: `smoke`
- Frozen libraries: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_07_Indexed_Retrieval\results\20260929_220030_diagnostic` (no library retraining).
- Fit boxes: ['inv_01dcb410da3d', 'inv_28f717865766', 'inv_4b9eb8f15eaf']; validation boxes: ['inv_ca731e3c4c13'].
- Remaining-solves are diagnosis only. consultation_cost includes index probes and ranking.
- Accept if predicted remaining-saving > remaining-check cost (anchors) AND P(quality_ok) ≥ threshold. The saving bar is not lowered.

## 1. Prediction-target audit

- Training action: first_legal_site (8 shuffled anchors), not oracle-best placement.
- Deployment action: first_legal_site (8 shuffled anchors).
- Train/deploy action mismatch: False (both are first_legal_site, not the oracle-best placement).
- Sign: A_skip - A_commit; positive means fewer remaining evaluations. Units: raw remaining primitive evaluations. No inverse scaling. No prediction clipping.
- Training remaining-solve cap: pair_eval_cap=1600 (truncated vs full remaining budget). Expt-7B used eval_cap - prefix_primitive_A. Cap mismatch: True.
- Training labels n=206; unweighted mean remaining-saving -99.14; severe-loss-weighted mean -611.9.
- Benefit model has no operation identifier; quality model has per-op bias. Context features have no orientation/anchor/local geometry.
- Uniformly negative deployment predictions can follow from fitting a linear model to severe-loss-weighted labels whose weighted mean is largely negative, even when the unweighted mean is near zero. That is not a sign error. It also does not by itself prove that placement features are uninformative.

## 2. Held-out prediction error (first-legal actions)

- constant: n=3; MAE 286.5; RMSE 294.2; Pearson NA; AUC(beneficial) 0.5; pred mean -239.4 vs y mean -174.7; pred range [-239.4, -239.4].
- frozen: n=3; MAE 296; RMSE 304.7; Pearson -0.2021; AUC(beneficial) 0; pred mean -268 vs y mean -174.7; pred range [-284.5, -251.3].
- context: n=3; MAE 739.1; RMSE 797.2; Pearson -0.2442; AUC(beneficial) 0; pred mean -913.7 vs y mean -174.7; pred range [-962.2, -867.5].
- action: n=3; MAE 985.5; RMSE 1036; Pearson -0.7744; AUC(beneficial) 0; pred mean -1160 vs y mean -174.7; pred range [-1217, -1124].
- Action-level MAE beats constant mean: False.

## 3. Selection quality on validation (do not read reject-all as success)

- Remaining-check cost = 8.
- constant first-legal: **zero coverage** (0/3 accepted). Rejecting everything is not successful selection.
- constant all labeled placements: **zero coverage** (0/8 accepted). Rejecting everything is not successful selection.
- frozen first-legal: **zero coverage** (0/3 accepted). Rejecting everything is not successful selection.
- frozen all labeled placements: **zero coverage** (0/8 accepted). Rejecting everything is not successful selection.
- context first-legal: **zero coverage** (0/3 accepted). Rejecting everything is not successful selection.
- context all labeled placements: **zero coverage** (0/8 accepted). Rejecting everything is not successful selection.
- action first-legal: **zero coverage** (0/3 accepted). Rejecting everything is not successful selection.
- action all labeled placements: **zero coverage** (0/8 accepted). Rejecting everything is not successful selection.

## 4. Bounded placement selection

- Skipped. Validation did not support a useful accepted subset, so extra legal placements were not promoted to a deployable search.

## 5. Whole-box confirmation

- Skipped. validation did not support a useful accepted subset, or n_fresh=0. Budget 0 remains the required comparator if a later subset is ever deployed.

## Ledgers

- Diagnostic skip rollouts 40; commit rollouts 40; cache hits 0; feature checks 1166.

## What this does and does not show

- Do not lower the acceptance threshold just because predictions are negative. A negative mean outcome means indiscriminate acceptance can restore quality or effort damage.
- Uniformly negative predictions do not alone prove miscalibration. Distinguish implementation error, calibration to a weighted mean, and missing placement information using the audit and the three-predictor comparison.
- Offline remaining-solve benefit is not whole-box policy savings. Commitments change later states.
- Include consultation budget 0 in any later deployment comparison.

Libraries were not retrained. The question is whether inexpensive pre-commitment information about a specific placement can distinguish beneficial reuse from costly reuse.
