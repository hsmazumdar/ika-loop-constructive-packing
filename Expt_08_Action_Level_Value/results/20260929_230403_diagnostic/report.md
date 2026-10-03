# Expt-8 report

Can inexpensive information available before a specific placement distinguish beneficial reuse from costly reuse? Libraries stay frozen. Remaining-solves are diagnosis only.

- Directory: `results\20260929_230403_diagnostic`
- Preset: `diagnostic`
- Frozen libraries: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_07_Indexed_Retrieval\results\20260929_220030_diagnostic` (no library retraining).
- Fit boxes: ['inv_01dcb410da3d', 'inv_28f717865766', 'inv_4b9eb8f15eaf', 'inv_ca731e3c4c13', 'inv_6b8058ed8650', 'inv_a50ff1cb12a5', 'inv_b8ca10ec1d55', 'inv_7334cb152bb1', 'inv_7f78315a08cd', 'inv_3a6415ba14bb', 'inv_a25252ed98bb', 'inv_2bcf2bd11f08', 'inv_e2258e487b41', 'inv_cd1593616a9d', 'inv_f37c190fae44', 'inv_f38e4acaef91', 'inv_99ae609def69', 'inv_18db09080c0d']; validation boxes: ['inv_ede60bd9d08e', 'inv_8b9cdaf23e25', 'inv_436a74b58bb1', 'inv_c0cfc0835886', 'inv_965fc9524c0a', 'inv_465ab2834adf'].
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

- constant: n=56; MAE 2567; RMSE 3753; Pearson -0.2142; AUC(beneficial) 0.4172; pred mean -122.9 vs y mean 1875; pred range [-350.1, 31.04].
- frozen: n=56; MAE 2886; RMSE 3935; Pearson 0.3535; AUC(beneficial) 0.5953; pred mean -576.9 vs y mean 1875; pred range [-746, -190.7].
- context: n=56; MAE 4487; RMSE 5250; Pearson 0.3131; AUC(beneficial) 0.4891; pred mean -2432 vs y mean 1875; pred range [-3461, -1359].
- action: n=56; MAE 4766; RMSE 5463; Pearson 0.309; AUC(beneficial) 0.475; pred mean -2697 vs y mean 1875; pred range [-4611, -1388].
- Action-level MAE beats constant mean: False.
- Validation remaining-solves use eval_cap − prefix_A. Training used pair_eval_cap=1600. That cap mismatch inflates held-out y relative to what the frozen model was fit on; it is an implementation inconsistency, not evidence to lower the admit bar.

## 3. Selection quality on validation (do not read reject-all as success)

- Remaining-check cost = 8.
- constant first-legal: accepted 22/56 on 5/11 boxes, 1 seeds; mean remaining-saving 1805; mean net after check cost 1803; quality-loss rate 0.2273; severe losses 3 (0.1364); mean pred 31.04 vs observed 1805.
- constant all labeled placements: accepted 112/287 on 5/11 boxes, 1 seeds; mean remaining-saving 1695; mean net after check cost 1693; quality-loss rate 0.1518; severe losses 19 (0.1696); mean pred 31.04 vs observed 1695.
- frozen first-legal: **zero coverage** (0/56 accepted). Rejecting everything is not successful selection.
- frozen all labeled placements: **zero coverage** (0/287 accepted). Rejecting everything is not successful selection.
- context first-legal: **zero coverage** (0/56 accepted). Rejecting everything is not successful selection.
- context all labeled placements: **zero coverage** (0/287 accepted). Rejecting everything is not successful selection.
- action first-legal: **zero coverage** (0/56 accepted). Rejecting everything is not successful selection.
- action all labeled placements: **zero coverage** (0/287 accepted). Rejecting everything is not successful selection.

## 4. Bounded placement selection

- Skipped. Validation did not support a useful accepted subset, so extra legal placements were not promoted to a deployable search.

## 5. Whole-box confirmation

- Skipped. validation did not support a useful accepted subset. Budget 0 remains the required comparator if a later subset is ever deployed.

## Ledgers

- Diagnostic skip rollouts 1373; commit rollouts 1373; cache hits 0; feature checks 37265.

## What this does and does not show

- Do not lower the acceptance threshold just because predictions are negative. A negative mean outcome means indiscriminate acceptance can restore quality or effort damage.
- Uniformly negative predictions do not alone prove miscalibration. Distinguish implementation error, calibration to a weighted mean, and missing placement information using the audit and the three-predictor comparison.
- Offline remaining-solve benefit is not whole-box policy savings. Commitments change later states.
- Include consultation budget 0 in any later deployment comparison.

Libraries were not retrained. The question is whether inexpensive pre-commitment information about a specific placement can distinguish beneficial reuse from costly reuse.
