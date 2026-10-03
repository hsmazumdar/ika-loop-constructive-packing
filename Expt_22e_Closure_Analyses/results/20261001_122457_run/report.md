# Expt 22e - Closure analyses for "Continuous Learning and Memory Consolidation for Constructive Packing"

Run folder: `Expt_22e_Closure_Analyses/results/20261001_122457_run/`. All numbers below are read from the saved CSV/JSON files in this folder
(`code/make_report.py` generates the tables). Everything derives from saved Expt 21 / 22a-d data, plus modest new simulation that is fully logged:
(i) 1,200-episode evaluations of uniform natural placing, the hand rule, five extra simple packers and three piece-choice references (items 2/3);
(ii) re-evaluation of the two stored memories (22b s0, 22c s100); (iii) six reruns of the Expt 22d `full` streams (seeds 300-305, 60k boxes, unmodified
Expt_22d `src`) done only to obtain final agent memories, because Expt 22d did not store them (`memory_reruns/`, `progress.log`).
Times are IST (UTC+5:30). "S1" = 100 - empty cells after the episode (held-out mean over the 1,200 evaluation episodes, tau_eval 0.25, unless stated).

Status of the machines: items 1, 3, 4, 5 and the simulations were produced on HsmPc1 (python 3.13.1, numpy 2.2.0); this report was assembled on i9Win10 from the files only.

## Item 1 - Paired statistics

### 1a. 22d saturation run: paired stream-level differences (n = 6 `full` streams, seeds 300-305, same replicate streams at every checkpoint)

Difference = S1(to) - S1(from) within each stream, then averaged over the 6 streams. Bootstrap = percentile 95% CI of the mean paired difference (resampling streams, 20,000 draws, rng seed 20261001). t-CI = paired t interval (df 5). Sign-flip = exact two-sided sign-flip permutation p (2^6 flips; the smallest attainable p is 0.03125). `indep CI` = the independent-samples bootstrap CI (the way summary.md compared checkpoints), shown for contrast.

| from -> to (boxes) | mean diff | paired bootstrap 95% CI | paired-t 95% CI | p (paired t) | p (sign-flip, exact) | streams up | indep. bootstrap CI | per-stream diffs (s300..s305) |
|---|---|---|---|---|---|---|---|---|
| 20k -> 24k | +0.79 | +0.40, +1.22 | +0.20, +1.38 | 0.0184 | 0.0312 | 6/6 | +0.06, +1.50 | +0.47 +1.61 +0.51 +1.37 +0.61 +0.18 |
| 24k -> 28k | +0.96 | +0.47, +1.40 | +0.28, +1.63 | 0.0146 | 0.0312 | 6/6 | +0.03, +1.93 | +1.46 +1.40 +0.09 +0.74 +0.39 +1.66 |
| 28k -> 32k | +1.20 | +0.50, +1.84 | +0.23, +2.16 | 0.0244 | 0.0625 | 5/6 | -0.22, +2.45 | +1.36 +1.18 +0.81 +1.71 -0.31 +2.43 |
| 32k -> 36k | +1.63 | +1.28, +1.99 | +1.11, +2.14 | 0.0005 | 0.0312 | 6/6 | +0.04, +3.27 | +1.16 +1.97 +1.42 +1.05 +1.85 +2.30 |
| 36k -> 40k | +0.51 | +0.20, +0.83 | +0.05, +0.98 | 0.0363 | 0.0625 | 5/6 | -0.90, +1.98 | +0.47 -0.06 +0.78 +0.61 +1.16 +0.12 |
| 40k -> 44k | +0.76 | +0.14, +1.39 | -0.16, +1.68 | 0.0873 | 0.1250 | 4/6 | -0.31, +1.99 | -0.02 +1.73 +0.82 +0.19 +1.89 -0.06 |
| 44k -> 48k | +0.21 | -0.04, +0.45 | -0.14, +0.55 | 0.1888 | 0.1875 | 4/6 | -0.96, +1.44 | +0.14 +0.67 +0.40 -0.04 +0.33 -0.26 |
| 48k -> 52k | +0.22 | +0.09, +0.36 | +0.02, +0.43 | 0.0357 | 0.0312 | 6/6 | -1.04, +1.43 | +0.47 +0.04 +0.40 +0.14 +0.29 +0.00 |
| 52k -> 56k | +0.07 | -0.05, +0.19 | -0.12, +0.25 | 0.3866 | 0.2812 | 5/6 | -1.00, +1.29 | +0.03 +0.00 +0.27 -0.19 +0.27 +0.04 |
| 56k -> 60k | +0.04 | -0.04, +0.13 | -0.08, +0.16 | 0.4089 | 0.4688 | 4/6 | -1.15, +1.13 | -0.04 +0.03 +0.22 +0.10 +0.03 -0.10 |
| 20k -> 60k | +6.38 | +5.73, +7.33 | +5.19, +7.57 | <0.0001 | 0.0312 | 6/6 | +5.66, +7.37 | +5.52 +8.56 +5.72 +5.67 +6.51 +6.31 |
| 32k -> 60k | +3.44 | +2.36, +4.68 | +1.73, +5.15 | 0.0035 | 0.0312 | 6/6 | +2.17, +4.96 | +2.22 +4.38 +4.31 +1.86 +5.82 +2.04 |
| 48k -> 60k | +0.33 | +0.08, +0.62 | -0.06, +0.72 | 0.0802 | 0.0938 | 5/6 | -0.90, +1.48 | +0.46 +0.07 +0.89 +0.05 +0.59 -0.06 |
| 52k -> 60k | +0.11 | -0.04, +0.29 | -0.13, +0.35 | 0.3015 | 0.4375 | 3/6 | -1.01, +1.27 | -0.01 +0.03 +0.49 -0.09 +0.29 -0.06 |

No multiplicity correction is applied across these 14 contrasts; the p-values are descriptive. Figure: `fig_item1a_paired_differences.png` (left: per-stream trajectories; right: paired 4k-step differences with CIs).

**56k -> 60k, redone as paired:** mean +0.04 S1, paired bootstrap 95% CI [-0.04, +0.13], paired-t CI [-0.08, +0.16], 4 of 6 streams up, exact sign-flip p = 0.469. The independent-sample CI was [-1.15, +1.13]; the paired CI (width 0.16) is about 14x narrower than the independent one (width 2.28) because the stream-to-stream level differences are removed. So the last 4k boxes change S1 by at most about +0.13 (upper bound) and the data are consistent with zero change. Earlier steps are not zero: 48k -> 52k is +0.22 (paired bootstrap CI +0.09, +0.36; 6/6 streams up) and 32k -> 36k is +1.63 (+1.28, +1.99). 20k -> 60k is +6.38 (+5.73, +7.33), 6/6 up. The honest description is a **near-plateau** (paired gains of +0.5 to +1.6 per 4k boxes between 20k and 40k, +0.22 at 48k -> 52k, +0.07 and +0.04 over the last two 4k steps), not a proven ceiling: 6 streams, one setting, and the 52k -> 60k contrast is +0.11 (-0.04, +0.29).

### 1b. Five 22d ablations vs the 22c `full` reference at 32k boxes (multiplicity control)

Family of m = 5 comparisons (no_concepts, no_meta, no_dream, no_meta_matched_floor, no_sleep). Reference = 22c `full` streams at 32k (n = 12, seeds 100-111); each ablation has n = 4 (seeds 200-203, 22d). Difference = reference minus variant (positive = ablation worse). Four tests: `Welch normal` is the test used in the 22d summary.md (Welch standard error, normal reference); `Welch t` uses Satterthwaite df; `exact permutation` enumerates every assignment of the pooled values; `Mann-Whitney U`. Holm, Bonferroni and BH are applied within each test across the 5 variants. `survives` = adjusted p < 0.05 (Holm / Bonferroni / BH).

**Reference = 22c full, n = 12 (primary)**

| test | variant | ref / variant mean | ref - variant | bootstrap 95% CI of diff | raw p | Holm | Bonferroni | BH | survives Holm/Bonf/BH |
|---|---|---|---|---|---|---|---|---|---|
| welch_normal(as in summary.md) | no_concepts | 88.28 / 87.97 | +0.31 | -1.21, +1.77 | 0.7191 | 1.0000 | 1.0000 | 0.7191 | n/n/n |
| welch_normal(as in summary.md) | no_meta | 88.28 / 87.68 | +0.60 | -0.61, +1.72 | 0.3622 | 1.0000 | 1.0000 | 0.4527 | n/n/n |
| welch_normal(as in summary.md) | no_dream | 88.28 / 87.47 | +0.81 | -0.66, +2.37 | 0.3535 | 1.0000 | 1.0000 | 0.4527 | n/n/n |
| welch_normal(as in summary.md) | no_meta_matched_floor | 88.28 / 87.26 | +1.02 | +0.14, +1.80 | 0.0231 | 0.0924 | 0.1155 | 0.0577 | n/n/n |
| welch_normal(as in summary.md) | no_sleep | 88.28 / 86.48 | +1.81 | +0.88, +2.65 | 0.0003 | 0.0013 | 0.0013 | 0.0013 | Y/Y/Y |
| welch_t(df Satterthwaite) | no_concepts | 88.28 / 87.97 | +0.31 | -1.20, +1.76 | 0.7351 | 1.0000 | 1.0000 | 0.7351 | n/n/n |
| welch_t(df Satterthwaite) | no_meta | 88.28 / 87.68 | +0.60 | -0.60, +1.73 | 0.3957 | 1.0000 | 1.0000 | 0.5005 | n/n/n |
| welch_t(df Satterthwaite) | no_dream | 88.28 / 87.47 | +0.81 | -0.66, +2.35 | 0.4004 | 1.0000 | 1.0000 | 0.5005 | n/n/n |
| welch_t(df Satterthwaite) | no_meta_matched_floor | 88.28 / 87.26 | +1.02 | +0.14, +1.79 | 0.0399 | 0.1594 | 0.1993 | 0.0996 | n/n/n |
| welch_t(df Satterthwaite) | no_sleep | 88.28 / 86.48 | +1.81 | +0.86, +2.66 | 0.0035 | 0.0174 | 0.0174 | 0.0174 | Y/Y/Y |
| permutation_exact | no_concepts | 88.28 / 87.97 | +0.31 | -1.20, +1.72 | 0.7121 | 0.9841 | 1.0000 | 0.7121 | n/n/n |
| permutation_exact | no_meta | 88.28 / 87.68 | +0.60 | -0.58, +1.73 | 0.4352 | 0.9841 | 1.0000 | 0.5440 | n/n/n |
| permutation_exact | no_dream | 88.28 / 87.47 | +0.81 | -0.65, +2.37 | 0.3280 | 0.9841 | 1.0000 | 0.5440 | n/n/n |
| permutation_exact | no_meta_matched_floor | 88.28 / 87.26 | +1.02 | +0.15, +1.79 | 0.1555 | 0.6220 | 0.7775 | 0.3887 | n/n/n |
| permutation_exact | no_sleep | 88.28 / 86.48 | +1.81 | +0.89, +2.66 | 0.0203 | 0.1016 | 0.1016 | 0.1016 | n/n/n |
| mannwhitney_U | no_concepts | 88.28 / 87.97 | +0.31 | -1.22, +1.77 | 0.6835 | 1.0000 | 1.0000 | 0.6835 | n/n/n |
| mannwhitney_U | no_meta | 88.28 / 87.68 | +0.60 | -0.60, +1.72 | 0.4462 | 1.0000 | 1.0000 | 0.5577 | n/n/n |
| mannwhitney_U | no_dream | 88.28 / 87.47 | +0.81 | -0.64, +2.35 | 0.4462 | 1.0000 | 1.0000 | 0.5577 | n/n/n |
| mannwhitney_U | no_meta_matched_floor | 88.28 / 87.26 | +1.02 | +0.17, +1.79 | 0.0418 | 0.1670 | 0.2088 | 0.1044 | n/n/n |
| mannwhitney_U | no_sleep | 88.28 / 86.48 | +1.81 | +0.89, +2.66 | 0.0132 | 0.0659 | 0.0659 | 0.0659 | n/n/n |

**Reference = pooled 22c full (n = 12) + 22d full at 32k (n = 6) = n 18 (pooled version)**

| test | variant | ref / variant mean | ref - variant | bootstrap 95% CI of diff | raw p | Holm | Bonferroni | BH | survives Holm/Bonf/BH |
|---|---|---|---|---|---|---|---|---|---|
| welch_normal(as in summary.md) | no_concepts | 88.29 / 87.97 | +0.32 | -1.13, +1.73 | 0.6987 | 0.9798 | 1.0000 | 0.6987 | n/n/n |
| welch_normal(as in summary.md) | no_meta | 88.29 / 87.68 | +0.62 | -0.51, +1.67 | 0.3266 | 0.9798 | 1.0000 | 0.4143 | n/n/n |
| welch_normal(as in summary.md) | no_dream | 88.29 / 87.47 | +0.82 | -0.59, +2.34 | 0.3315 | 0.9798 | 1.0000 | 0.4143 | n/n/n |
| welch_normal(as in summary.md) | no_meta_matched_floor | 88.29 / 87.26 | +1.04 | +0.26, +1.74 | 0.0095 | 0.0382 | 0.0477 | 0.0239 | Y/Y/Y |
| welch_normal(as in summary.md) | no_sleep | 88.29 / 86.48 | +1.82 | +1.00, +2.60 | <0.0001 | 0.0002 | 0.0002 | 0.0002 | Y/Y/Y |
| welch_t(df Satterthwaite) | no_concepts | 88.29 / 87.97 | +0.32 | -1.13, +1.73 | 0.7179 | 1.0000 | 1.0000 | 0.7179 | n/n/n |
| welch_t(df Satterthwaite) | no_meta | 88.29 / 87.68 | +0.62 | -0.50, +1.68 | 0.3687 | 1.0000 | 1.0000 | 0.4820 | n/n/n |
| welch_t(df Satterthwaite) | no_dream | 88.29 / 87.47 | +0.82 | -0.58, +2.33 | 0.3856 | 1.0000 | 1.0000 | 0.4820 | n/n/n |
| welch_t(df Satterthwaite) | no_meta_matched_floor | 88.29 / 87.26 | +1.04 | +0.25, +1.73 | 0.0204 | 0.0817 | 0.1022 | 0.0511 | n/n/n |
| welch_t(df Satterthwaite) | no_sleep | 88.29 / 86.48 | +1.82 | +1.00, +2.61 | 0.0020 | 0.0102 | 0.0102 | 0.0102 | Y/Y/Y |
| permutation_exact | no_concepts | 88.29 / 87.97 | +0.32 | -1.13, +1.73 | 0.6928 | 0.9039 | 1.0000 | 0.6928 | n/n/n |
| permutation_exact | no_meta | 88.29 / 87.68 | +0.62 | -0.49, +1.67 | 0.4116 | 0.9039 | 1.0000 | 0.5145 | n/n/n |
| permutation_exact | no_dream | 88.29 / 87.47 | +0.82 | -0.59, +2.32 | 0.3013 | 0.9039 | 1.0000 | 0.5022 | n/n/n |
| permutation_exact | no_meta_matched_floor | 88.29 / 87.26 | +1.04 | +0.27, +1.74 | 0.1526 | 0.6103 | 0.7628 | 0.3814 | n/n/n |
| permutation_exact | no_sleep | 88.29 / 86.48 | +1.82 | +0.99, +2.62 | 0.0172 | 0.0861 | 0.0861 | 0.0861 | n/n/n |
| mannwhitney_U | no_concepts | 88.29 / 87.97 | +0.32 | -1.13, +1.73 | 0.7120 | 1.0000 | 1.0000 | 0.7120 | n/n/n |
| mannwhitney_U | no_meta | 88.29 / 87.68 | +0.62 | -0.49, +1.68 | 0.3863 | 1.0000 | 1.0000 | 0.4829 | n/n/n |
| mannwhitney_U | no_dream | 88.29 / 87.47 | +0.82 | -0.58, +2.31 | 0.3420 | 1.0000 | 1.0000 | 0.4829 | n/n/n |
| mannwhitney_U | no_meta_matched_floor | 88.29 / 87.26 | +1.04 | +0.27, +1.73 | 0.0530 | 0.2122 | 0.2652 | 0.1326 | n/n/n |
| mannwhitney_U | no_sleep | 88.29 / 86.48 | +1.82 | +1.01, +2.62 | 0.0145 | 0.0725 | 0.0725 | 0.0725 | n/n/n |

**Reading.**
- `no_sleep` (-1.81 S1 vs the 22c reference): survives Holm, Bonferroni and BH under both Welch versions (Welch normal Holm 0.0013; Welch t Holm 0.0174), also with the pooled reference (Holm 0.0002 / 0.0102). Under the exact permutation test (Holm 0.1016) and Mann-Whitney (Holm 0.0659) it does **not** reach 0.05 after correction; the raw permutation p is 0.0203 and raw Mann-Whitney 0.0132. So the conclusion "no_sleep is lower" is robust to Welch-type tests and to the direction of every test, but with only 4 ablation streams the rank/permutation tests lack the power to survive correction.
- `no_meta_matched_floor` (-1.02): raw Welch-normal p = 0.0231, but Holm 0.0924, Bonferroni 0.1155, BH 0.0577 -> **does not survive** against the 22c reference -> label **exploratory**. With the pooled reference it survives under Welch-normal (Holm 0.0382) but not under Welch t (Holm 0.0817), permutation (0.6103) or Mann-Whitney (0.2122), so it is not robust either.
- `no_concepts`, `no_meta`, `no_dream`: raw p between 0.30 and 0.74 in every test; no evidence of a difference (this is absence of evidence at n = 4, not evidence of equivalence; the bootstrap CIs of the difference all span zero and are about 3 S1 points wide, e.g. no_concepts -1.21 to +1.77).
- Caveat on the design: the reference (22c, Vivobook run 04:44) and the ablations (22d) are different runs (both compared at 32k boxes) with slightly different code (22d adds the matched_floor variant, extra checkpoints and an `on_eval` hook; policy mechanics unchanged - see item 3). The pooled version adds the six 22d `full` streams at 32k, which ran concurrently with the ablations (pooled reference mean 88.29 vs 88.28 for 22c alone).

## Item 2 - Piece-P usage

P is the 7-cell piece (area 7; most pieces have area 5, M/N/O area 4). Same 14-piece natural-placing task, same 1,200 evaluation seeds (7,700,000 + j), for all policies. The learner rows are the **frozen final memories** (the agent's value net, concept library etc. evaluated with `learner_ref`/stream evaluation code at tau_eval 0.25; each re-evaluation reproduces the saved held-out S1 exactly (8 of 8 memories, 0 differing episodes; the 22c s100 memory reproduces exactly only with single-threaded BLAS - with default threads one of 1,200 episodes differed by float noise, 87.8267 vs 87.8258). The 22d `full` memories come from the six 22e reruns (identical to the saved 22d streams, item 5), because 22d itself did not store memories; 22b s0 (at 20k) and 22c s100 (at 32k) were stored by those experiments.

| policy | S1 | mean pieces/episode | mean piece area | fraction of episodes using P | mean P pieces/episode | max P | frac >= 2 P | frac cells covered by P | frac S1 >= 90 | re-eval = saved? |
|---|---|---|---|---|---|---|---|---|---|---|
| uniform natural (1200) | 67.319 | 14.000 | 4.809 | 0.472 | 0.631 | 4 | 0.130 | 0.066 | 0.000 | - |
| hand contact/hole/area rule (1200) | 89.617 | 13.952 | 6.424 | 1.000 | 10.092 | 11 | 1.000 | 0.788 | 0.728 | - |
| 22b full s0 @20k boxes | 83.887 | 13.321 | 6.306 | 1.000 | 9.241 | 12 | 1.000 | 0.771 | 0.011 | True |
| 22c full s100 @32k boxes | 87.826 | 13.752 | 6.390 | 1.000 | 9.956 | 12 | 1.000 | 0.794 | 0.256 | True |
| 22d full s300 @60k boxes (rerun, saved memory) | 91.145 | 13.944 | 6.537 | 1.000 | 10.861 | 12 | 1.000 | 0.834 | 0.868 | True |
| 22d full s301 @60k boxes (rerun, saved memory) | 93.988 | 14.000 | 6.713 | 1.000 | 11.999 | 12 | 1.000 | 0.894 | 1.000 | True |
| 22d full s302 @60k boxes (rerun, saved memory) | 91.546 | 13.959 | 6.559 | 1.000 | 11.003 | 12 | 1.000 | 0.841 | 0.898 | True |
| 22d full s303 @60k boxes (rerun, saved memory) | 91.429 | 13.955 | 6.552 | 1.000 | 10.952 | 12 | 1.000 | 0.838 | 0.917 | True |
| 22d full s304 @60k boxes (rerun, saved memory) | 91.470 | 13.955 | 6.555 | 1.000 | 10.938 | 12 | 1.000 | 0.837 | 0.927 | True |
| 22d full s305 @60k boxes (rerun, saved memory) | 90.985 | 13.938 | 6.528 | 1.000 | 10.810 | 12 | 1.000 | 0.832 | 0.850 | True |

Mean of the six 22d memories at 60k: S1 91.761, P pieces/episode 11.094, piece area 6.574, fraction of cells covered by P 0.846; range of S1 90.985-93.988.

**S1 split by P used / not used.** (`S1_P_used`, `n_P_used`, `S1_P_not_used`, `n_P_not_used` in `item2_piece_P_usage.csv`.)

| policy | n episodes using P | S1 (P used) | n not using P | S1 (P not used) |
|---|---|---|---|---|
| uniform natural (1200) | 566 | 68.883 | 634 | 65.923 |
| hand contact/hole/area rule (1200) | 1200 | 89.617 | 0 | n/a (no such episodes) |
| 22b full s0 @20k boxes | 1200 | 83.887 | 0 | n/a (no such episodes) |
| 22c full s100 @32k boxes | 1200 | 87.826 | 0 | n/a (no such episodes) |
| 22d full s300 @60k boxes (rerun, saved memory) | 1200 | 91.145 | 0 | n/a (no such episodes) |
| 22d full s301 @60k boxes (rerun, saved memory) | 1200 | 93.988 | 0 | n/a (no such episodes) |
| 22d full s302 @60k boxes (rerun, saved memory) | 1200 | 91.546 | 0 | n/a (no such episodes) |
| 22d full s303 @60k boxes (rerun, saved memory) | 1200 | 91.429 | 0 | n/a (no such episodes) |
| 22d full s304 @60k boxes (rerun, saved memory) | 1200 | 91.470 | 0 | n/a (no such episodes) |
| 22d full s305 @60k boxes (rerun, saved memory) | 1200 | 90.985 | 0 | n/a (no such episodes) |

For every learner memory and for the hand rule the fraction of episodes using P is 1.000, so the P-used / not-used split is degenerate (nothing to compare). It is informative only for uniform natural placing (68.883 with P, n = 566; 65.923 without, n = 634).
Association between P count and S1 (descriptive, not causal), `n episodes (mean S1)` by number of P pieces:

| policy | episodes by number of P pieces (mean S1) |
|---|---|
| uniform natural (1200) | 0P: 634 (65.92); 1P: 410 (68.15); 2P: 126 (70.41); 3P: 25 (72.36); 4P: 5 (73.40) |
| hand contact/hole/area rule (1200) | 8P: 2 (86.00); 9P: 208 (87.92); 10P: 667 (89.48); 11P: 323 (91.01) |
| 22b full s0 @20k boxes | 6P: 5 (81.20); 7P: 42 (82.10); 8P: 210 (83.13); 9P: 457 (83.87); 10P: 379 (84.28); 11P: 102 (84.81); 12P: 5 (86.40) |
| 22c full s100 @32k boxes | 6P: 1 (80.00); 7P: 10 (83.20); 8P: 69 (85.00); 9P: 269 (86.79); 10P: 488 (87.99); 11P: 338 (89.07); 12P: 25 (88.88) |
| 22d full s300 @60k boxes (rerun, saved memory) | 8P: 3 (85.00); 9P: 24 (87.12); 10P: 139 (89.24); 11P: 1005 (91.59); 12P: 29 (89.00) |
| 22d full s301 @60k boxes (rerun, saved memory) | 11P: 1 (92.00); 12P: 1199 (93.99) |
| 22d full s302 @60k boxes (rerun, saved memory) | 7P: 1 (83.00); 8P: 1 (85.00); 9P: 19 (87.05); 10P: 135 (89.50); 11P: 860 (91.57); 12P: 184 (93.48) |
| 22d full s303 @60k boxes (rerun, saved memory) | 8P: 1 (86.00); 9P: 7 (87.29); 10P: 82 (89.38); 11P: 1069 (91.60); 12P: 41 (91.93) |
| 22d full s304 @60k boxes (rerun, saved memory) | 8P: 3 (85.67); 9P: 11 (87.27); 10P: 63 (89.10); 11P: 1103 (91.71); 12P: 20 (89.00) |
| 22d full s305 @60k boxes (rerun, saved memory) | 8P: 6 (84.83); 9P: 33 (87.03); 10P: 164 (89.31); 11P: 977 (91.47); 12P: 20 (89.40) |

**Piece-choice references** (new here; always choose a placement of piece P when one exists, same task and seeds; not used by any learner):

| reference | S1 | mean pieces | mean piece area | mean P/episode | frac cells in P | frac S1 >= 90 |
|---|---|---|---|---|---|---|
| P_only_uniform_natural | 82.335 | 13.239 | 6.231 | 9.328 | 0.793 | 0.002 |
| P_only_contact_greedy | 88.918 | 12.998 | 6.841 | 11.997 | 0.944 | 0.003 |
| P_only_hand_score | 88.323 | 13.505 | 6.546 | 10.992 | 0.871 | 0.459 |

**Reading.** (1) Learners and the hand rule use P in every episode (uniform: 47.2% of episodes, 0.631 P pieces/episode, mean piece area 4.809). The learned policies (6.31 -> 6.39 -> 6.53-6.71 mean piece area) and the hand rule (6.424) use almost only large pieces.
(2) A large part of the improvement over uniform natural placing is therefore **piece choice** (choose P), not only placement quality: restricting uniform natural placing to P placements alone gives S1 82.335, and P-only with contact-greedy placement gives 88.918 - already about equal to the hand rule (89.617) and above the 22b learner at 20k (83.887) and the 22c learner at 32k (87.826). The six 60k learners (90.985-93.988; mean 91.761) are above that P-only contact-greedy reference (88.918), so their placement is better than contact-greedy; the 22b/22c learners are below it.
(3) Under the 14-piece cap the area term of the hand rule is the active ingredient (item 3 table: without an area term 70.24; hole terms removed: 88.925).
(4) Why 13.3-14 pieces rather than 14: some episodes end before the cap when no natural placement remains (mean pieces/episode in the table).

## Item 3 - Baseline audit

**Verdict.** Learner (22b/c/d), uniform natural placing, V21 and the 89.61 hand rule share: the same engine file (byte-identical), the same legality and 14-piece cap, the same natural restriction (contact > 0), the same unlimited-inventory piece availability (all 16 types always offered; there is no per-box inventory in Expt 21/22), the same stopping rule, and the same evaluation seeds. They do **not** share: tau_eval and episode count between V21 and 22 (0.3 vs 0.25; 2,000 vs 1,200), the random-number stream consumption (policies draw differently), and the definition of the "uniform ~67" and "89.61" numbers in the reports (below). Details:

| item | finding | file |
|---|---|---|
| engine.py | sha-prefix 8295979bb1e6 in Expt_21, 22a, 22b, 22c, 22d (byte-identical) | item3_4_facts.json |
| learner_ref.py | sha-prefix 8fe669b8f1f3 in 22b, 22c, 22d (uniform_ref and hand_ref); agent.py, feat.py, net.py, meta.py identical in 22b/c/d | item3_4_facts.json |
| stream.py, config.py (22d vs 22b/c) | differ: 22d adds checkpoints 24k-56k, the matched_floor variant, an on_eval hook and schedule bounds; policy mechanics unchanged | diff of src files |
| Legality + 14-piece cap | Expt_22d/src/engine.py:117-121 Box.legal() returns no move once n >= budget; budget 14: Expt_22d/src/config.py:12, Expt_21/src/config.py:7 | item3_code_refs.csv |
| Piece availability | engine.py:110 `self.allowed = np.ones(N_TYPES)`: all 16 types always allowed; no inventory, no blocked cells in the 21/22 task (blocked/obstacle machinery exists but is unused) | item3_code_refs.csv |
| Natural restriction (uniform, hand, V21) | engine.natural_candidates, engine.py:172-183: legal placements with contact > 0 (touch wall or placed piece). V21 uses it at Expt_21/src/learner.py:289; uniform and hand use it in Expt_22d/src/learner_ref.py | item3_code_refs.csv |
| Natural restriction (22 learner) | its own filter, feat.step_features, Expt_22d/src/feat.py:33 `nat = (occ_c + wall) > 0`; equivalence to engine.natural_candidates checked on every decision state visited: 0 mismatches in 4,500 (uniform trajectories), 4,483 (hand), 4,350 (mixed policy), 4,424 (learner trajectories) | item3_natural_filter_equivalence.json |
| Stopping rule | every policy ends when no natural candidate remains or the 14-piece cap is hit (agent.py:98-125, learner_ref.py, learner.py:289) | item3_code_refs.csv |
| Evaluation seeds | episode j uses np.random.default_rng(eval_seed + j), eval_seed = 7,700,000 in V21 (stream.py:26) and 22 (stream.py:22, config.py:43); uniform_ref and hand_ref use the same seeds (learner_ref.py) | item3_code_refs.csv |

**Mismatches / caveats (precise):**

- V21 evaluates with tau_eval = 0.3 and 2,000 episodes (`Expt_21/src/config.py:19,56`); 22b/c/d use tau_eval = 0.25 (`Expt_22d/src/config.py:19`) and 1,200 episodes (the `Cfg` default is 2,000 at config.py:42, overridden to 1,200 in the manifests). Same seeds, first 1,200 of V21's 2,000.
- The reported "89.61" hand rule is the mean over the **first 1,000** evaluation episodes (`Expt_21/src/report.py:81-82`; `Expt_22b/src/report.py:82`). Recomputed here: 89.606 (first 1,000), 89.617 (the 1,200 evaluation episodes), 89.6475 (2,000). V21 and 22 reference code give identical numbers on the same seeds (`item3_v21refs_stdout.txt`, `item3_v22refs_stdout.txt`).
- The "uniform ~ 67" quoted in the 22b/c/d reports (`Expt_22b/src/report.py:83`) is **not** true uniform natural placing: it is the mean checkpoint-0 held-out S1 of each stream's randomly initialised value net at tau 0.25: 22b full (12 streams, seeds 0-11): 67.232 (range 65.05-68.58); 22c full (12, seeds 100-111): 67.806 (range 66.42-68.82); 22d full (6, seeds 300-305): 67.512 (range 66.33-68.86). True uniform natural placing is 67.319 on the 1,200 episodes (67.328 first 1,000; 67.297 on V21's 2,000, which is the V21 value, produced through the all-zero-score uniform branch of `choose()`).
- Stochasticity differs by policy: learner = softmax at tau 0.25 over natural placements (agent.py:117-125); hand rule = argmax of score + U(0, 0.5) noise (learner_ref.py:32); uniform = uniform draw (learner_ref.py:17). They consume the RNG differently, so the same seed id does not give identical random numbers, only the same seed. (Paired per-episode comparisons across policies are therefore comparisons of independent draws.)
- 22b/c/d training used a single continuing generator per stream (not the evaluation seeds); see item 4.
- The Expt-20 baselines (below) were evaluated on a **different task** (empty 10x10 box, unlimited pieces, 100-action budget; `Expt_20.../20260930_214303_baselines/summary.md`): its `uniform_random_control` scores 79.800 there versus 67.319 for uniform natural placing under the 14-piece cap, so numbers across the two tasks are not comparable.

### Hand rule (paper-ready definition; `Expt_22d/src/learner_ref.py:22-33`, `Expt_21/src/learner.py:296-303`)

> *Hand-written contact/hole/area reference.* At each step the rule considers all natural placements (legal placements of any of the 16 piece types in any orientation that touch the wall or a previously placed piece), scores each placement by
> `score = contact - 3 * h1 - n3 + 2 * area + u`, where `contact` is the number of cell edges of the piece touching the wall or already occupied cells, `h1` is the number of empty neighbouring cells that the placement leaves fully enclosed (one-cell holes), `n3` is the number of empty neighbouring cells left with three blocked sides (dead-end notches), `area` is the piece area (5 for most pieces, 4 for M, N, O, 7 for P) and `u ~ U(0, 0.5)` is a tie-breaking noise term, and places the arg-max. The episode ends when no natural placement remains or after 14 pieces. The rule has no learning and no memory and is used only as a reference; the weights (-3, -1, +2) are fixed constants in the code. Their origin (hand-set or tuned, and on which episodes) was not looked up in the earlier experiments' records for this report - state this in the manuscript only after checking.

Mean S1 on the 1,200 evaluation episodes: 89.617 (89.606 on the first 1,000, the "89.61" quoted in the manuscript; 89.6475 on 2,000).

### Other simple packers and whether any is evaluated under the 14-piece handicap

**Expt 20 baselines** (`Expt_20.../results/20260930_214303_baselines`; 14 rules in `rules.json`, listed in `item3_expt20_rules.csv`): first-fit and greedy rules on the unrestricted empty box (unlimited pieces, 100 actions); best: G_contact_any_first_tie 98.000, FF_contact_first_tie 97.000, Expt20_D_anchor_contact_eps0 96.253; weakest plain rules FF_largest_first_legal 84.000, G_area_any_rowmajor_tie 84.000, G_area_any_random_tie 83.436; uniform_random_control 79.800. **None is evaluated under the 14-piece cap** inside Expt 20.

**New in Expt 22e** (same 14-piece natural task, same 1,200 evaluation episodes; these are *not* the Expt-20 rules, which use anchors and other action spaces, but simple contact/area variants of the hand rule):

| rule | S1 | mean pieces | mean piece area | frac episodes with P | mean P/episode | frac S1 >= 90 |
|---|---|---|---|---|---|---|
| hand_rule (contact -3*holes -notches +2*area, noise .5) | 89.617 | 13.952 | 6.424 | 1.000 | 10.092 | 0.728 |
| contact_only_greedy (random tie) | 77.516 | 14.000 | 5.537 | 0.991 | 3.825 | 0.005 |
| contact_minus_holes (no area term) | 70.242 | 14.000 | 5.017 | 0.346 | 0.404 | 0.000 |
| area_only_greedy (largest piece, random tie) | 83.124 | 13.110 | 6.351 | 1.000 | 9.337 | 0.010 |
| contact_plus_area (no hole terms) | 88.925 | 13.000 | 6.841 | 1.000 | 11.997 | 0.003 |

The area term is essential (without it 70.24 or 77.52); the hole/notch terms add 89.617 - 88.925 = 0.69 S1 (the hand-rule noise is the same in both).

## Item 4 - Evaluation set description

**Facts (from code and saved data).**
- Seeds: evaluation episode j (j = 0..1199) uses `np.random.default_rng(7700000 + j)`, i.e. seeds 7,700,000..7,701,199 (`config.py:43`, `stream.py:22`). V21 evaluated seeds 7,700,000..7,701,999 (2,000 episodes), which contain the 1,200.
- Identical across the 1,200: the start board (empty 10 x 10; `start_board_empty` = True), the piece catalogue (all 16 types always allowed, no inventory), the 14-piece allowance and the natural-placing rule. There is **no per-episode piece draw or ordering**: the episodes differ **only** through the random number stream that drives stochastic action selection (softmax sampling for the learner, noise for the hand rule, uniform draws for uniform placing). They are 1,200 evaluation episodes of **one fixed problem**, not 1,200 distinct problems. The training "boxes" are likewise episodes of the same fixed problem.
- Distinctness of the outcomes (22c s100 memory): 1200 distinct placement sequences, 1200 distinct final placement sets, 130 distinct first placements out of 1,200 episodes. Hand rule: 1181 / 447 / 8. Uniform natural: 1200 / 1200 / 827.
- Noise: episode-level SD of S1 for the 22c s100 memory = 2.370, so the standard error of a 1,200-episode mean = 0.068.
- Disjointness from training: training of stream seed s uses `default_rng(s*7919+13)` (box generator, one continuing stream) and an agent generator `s*104729+7`; the evaluation episodes use `default_rng(7,700,000+j)` and the meta-controller's probe episodes use seeds 8,200,000+j (j < 80; `stream.py:45,74`: eval_seed + 500,000). Largest training seed values: 22b 1,152,026; 22c 11,624,926; 22d full 31,942,352; 22d ablations 21,259,994; numeric collisions with the evaluation or probe seed ranges: 22b 0, 22c 0, 22d full 0, 22d ablations 0. (Caveat: seed integers that differ are not a proof of independence of the generated streams, but PCG64 streams from distinct integer seeds are independent for practical purposes; training never uses the evaluation episodes' outcomes for updates.) Note that the meta-controller (a learned component) uses 80 probe episodes **separate** from the 1,200 evaluation episodes, so no meta decision uses held-out evaluation data.

**Where lambda = 1 was chosen on these episodes (prior use).**
- V22a pilot (NIGHT_LOG 03:03 IST, `Expt_22a.../results/pilot_*.log`, 12k boxes, **300 evaluation episodes = seeds 7,700,000..7,700,299**, i.e. the first 300 of the 1,200): `mc_only` (lambda = 1, Monte-Carlo returns) logged held-out 84.3 at 12k (82.17 at 1k, 83.76 at 4k, 84.38 at 10k) vs about 80.4-81.8 at 12k for the bootstrapped lambda = 0.9 `full` pilots (peaks 82.6/81.8/81.6 at 4-6k). Decision logged: default lambda = 1.0 (TD(0.9) kept as ablation `td090`).
- The V22a main-run manifests used eval_boxes 400 (pilot manifest), 600, 800 and 1,200 in different launches (`Expt_22a.../results/*/manifest.json`; all eval_seed 7,700,000, lam 0.95 default in those manifests), and a V22b pilot sweep (7 jobs, 10k boxes, eval = 300, NIGHT_LOG 03:0x) confirmed lambda = 1. The logs of that sweep (`results/p2_*.log`) and `q2.py` are **not on disk** (not found in `Expt_22b/...` or `Expt_22a/...`; NIGHT_LOG says the q2 sweeps were killed), so the sweep's exact evaluation seeds/size are known only from the NIGHT_LOG text - **not recoverable from files**.
- V21 used the same 2,000-episode set (seeds 7.7M..) for its final reporting and the hand-rule reference (first 1,000).
- Therefore the 1,200 episodes are "held out" in the sense that **no gradient update, sleep replay, concept extraction or meta decision used them**, but at least their first 300 members were used in pilot comparisons that selected lambda = 1 (and other early design choices), so they are **not a pristine test set**. A check that the first 300 episodes are not unusual (final `full` streams, first 300 vs the other 900 episodes):

| streams | first 300 | other 900 | diff | SD of diff over streams | streams with first300 higher |
|---|---|---|---|---|---|
| 22b full@20k (12) | 85.611 | 85.573 | +0.038 | 0.203 | 7/12 |
| 22c full@32k (12) | 88.273 | 88.284 | -0.011 | 0.112 | 6/12 |
| 22d full@60k (6) | 91.773 | 91.756 | +0.016 | 0.079 | 3/6 |

**Paper-ready paragraph (suggested).**

> *Evaluation protocol.* All reported performance numbers are means over 1,200 evaluation episodes of the same packing problem: an empty 10 x 10 box, the fixed 16-piece-type catalogue, a limit of 14 pieces, and placements restricted to positions touching the wall or a previously placed piece. The episodes are indexed by the seed of the random number generator (7,700,000 + j, j = 0..1,199) and differ only in the random draws behind stochastic action selection (softmax sampling for the learner, a small noise term for the hand-written reference, uniform draws for uniform natural placing); they are therefore 1,200 evaluation episodes of one fixed problem, not 1,200 distinct problems, and the variability across them (SD of S1 about 2.4 for a trained policy, standard error of the mean about 0.07) measures action-selection randomness, not variation across problem instances. These seeds are disjoint from the generators used for training and from the 80 probe episodes used by the meta-controller, and no learning update used them. They are, however, not an untouched test set: the first 300 of them were used in pilot runs when the return definition (lambda = 1) and other design choices were selected, and the same seeds (the first 2,000) were used for the earlier Expt 21 evaluation. Generalisation to other problem instances (other boxes, piece sets or allowances) is therefore not established by these numbers; between-stream variability is the unit of replication (12 streams at 20k and 32k boxes, 6 at 60k).

## Item 5 - Provenance

Source files: `manifest.json` / `manifest_rerun.json` of each run folder, `progress.log`, `progress_run1_stopped_0709.log`, `streams_partial_run1_stopped_0709/`, the stream pickles, NIGHT_LOG.md. Start time is **derived** (log DONE-line time minus the pickle's recorded runtime), finish time is the DONE-line time (IST). The stream seed is the training seed (generators `s*7919+13`, `s*104729+7`).

**Runs.**

| run folder | machine | created | code hash | workers | python | notes |
|---|---|---|---|---|---|---|
| `Expt_22b/results/20261001_034445_run` | Vivobook (1c7a0169) | 03:44:45 | d95b3495dd5324ec | 10 | 3.13.1 (MSC v.1942) | 44 streams; wall 7,096 s; an earlier dead launch `20261001_033100_run` is left on disk |
| `Expt_22c/results/20261001_044425_run` | Vivobook | 04:44:25 | c50aba87f089b5bd | 12 | 3.13.1 | 12 streams; wall 4,510 s |
| `Expt_22d/results/20261001_060654_main` | Vivobook | 06:06:54 | 05907550c5739d90 | 26 | 3.13.1 | 26 streams; **stopped by exact PID at 07:08:58** (13 streams finished, 13 cut) |
| same folder, `manifest_rerun.json` | **HsmPc1** (a418bb52) | 09:00:27 | 97ef4b81f9a19dd3 | 13 | 3.13.1; numpy 2.2.0 (scipy-openblas 0.3.28); matplotlib 3.10.0 | `run_expt22d.py --resume-dir ...`: reruns exactly the streams with no final pickle, **from box 0, same seed**; the hash differs from 05907550... only because `run_expt22d.py` gained the `--resume-dir` option (backup `run_expt22d.py.bak_before_resume`); `src/` files unchanged |

Software versions: python 3.13.1 in every manifest. numpy/matplotlib on the Vivobook are **not recorded in any manifest or log** (NIGHT_LOG only says "same python 3.13.1 + numpy/matplotlib/pytest"), so the numpy version used for the original runs is **not recoverable** from files. Restart policy: streams are not resumable (agent state not saved); a cut stream is restarted from box 0 with the same seed, no partial state is reused. Config: all 22b/c/d runs `OMP/BLAS = 1` threads, eval 1,200 episodes (seeds 7,700,000+), tau_eval 0.25, budget 14, hidden 64 growing in 64/128/256 steps, 22b full 12 x 20k, ablations 4 x 10k (seeds 0-11 / 0-3); 22c full 12 x 32k (seeds 100-111); 22d full 6 x 60k (300-305), ablations 4 x 32k (200-203); the full configuration is in each `manifest.json` (`cfg`, `variants`).

**Every stream** (82 streams: 22b 44, 22c 12, 22d 26; `item5_stream_provenance.csv`). `rerun` = rerun from box 0 on HsmPc1 after the 07:09 stop (13 streams).

| exp | variant | seed | boxes | machine | start IST | finish IST | code hash | rerun | final S1 |
|---|---|---|---|---|---|---|---|---|---|
| Expt_22b | badinit_fixed | 0 | 10000 | Vivobook | 05:08:51 | 05:28:37 | d95b3495 | False | 70.32 |
| Expt_22b | badinit_fixed | 1 | 10000 | Vivobook | 05:12:31 | 05:31:33 | d95b3495 | False | 69.62 |
| Expt_22b | badinit_fixed | 2 | 10000 | Vivobook | 05:14:05 | 05:33:12 | d95b3495 | False | 70.37 |
| Expt_22b | badinit_fixed | 3 | 10000 | Vivobook | 05:22:34 | 05:39:03 | d95b3495 | False | 69.83 |
| Expt_22b | badinit_meta | 0 | 10000 | Vivobook | 05:03:52 | 05:24:31 | d95b3495 | False | 69.99 |
| Expt_22b | badinit_meta | 1 | 10000 | Vivobook | 05:04:56 | 05:23:41 | d95b3495 | False | 69.84 |
| Expt_22b | badinit_meta | 2 | 10000 | Vivobook | 05:06:33 | 05:27:02 | d95b3495 | False | 70.00 |
| Expt_22b | badinit_meta | 3 | 10000 | Vivobook | 05:07:47 | 05:27:35 | d95b3495 | False | 69.76 |
| Expt_22b | frozen | 0 | 10000 | Vivobook | 05:26:24 | 05:43:01 | d95b3495 | False | 68.58 |
| Expt_22b | frozen | 1 | 10000 | Vivobook | 05:26:50 | 05:42:15 | d95b3495 | False | 67.20 |
| Expt_22b | frozen | 2 | 10000 | Vivobook | 05:26:54 | 05:42:37 | d95b3495 | False | 66.13 |
| Expt_22b | frozen | 3 | 10000 | Vivobook | 05:27:16 | 05:42:40 | d95b3495 | False | 68.11 |
| Expt_22b | full | 0 | 20000 | Vivobook | 03:51:02 | 04:27:23 | d95b3495 | False | 83.89 |
| Expt_22b | full | 1 | 20000 | Vivobook | 03:47:56 | 04:18:06 | d95b3495 | False | 85.42 |
| Expt_22b | full | 10 | 20000 | Vivobook | 04:26:11 | 05:03:42 | d95b3495 | False | 84.26 |
| Expt_22b | full | 11 | 20000 | Vivobook | 04:21:58 | 04:51:04 | d95b3495 | False | 85.01 |
| Expt_22b | full | 2 | 20000 | Vivobook | 03:49:04 | 04:24:48 | d95b3495 | False | 85.75 |
| Expt_22b | full | 3 | 20000 | Vivobook | 03:47:52 | 04:17:54 | d95b3495 | False | 86.11 |
| Expt_22b | full | 4 | 20000 | Vivobook | 03:52:04 | 04:27:38 | d95b3495 | False | 85.64 |
| Expt_22b | full | 5 | 20000 | Vivobook | 03:48:56 | 04:23:48 | d95b3495 | False | 84.47 |
| Expt_22b | full | 6 | 20000 | Vivobook | 03:51:38 | 04:23:25 | d95b3495 | False | 88.12 |
| Expt_22b | full | 7 | 20000 | Vivobook | 03:48:53 | 04:23:21 | d95b3495 | False | 86.72 |
| Expt_22b | full | 8 | 20000 | Vivobook | 03:51:25 | 04:32:24 | d95b3495 | False | 86.21 |
| Expt_22b | full | 9 | 20000 | Vivobook | 03:51:28 | 04:34:12 | d95b3495 | False | 85.40 |
| Expt_22b | no_concepts | 0 | 10000 | Vivobook | 04:45:50 | 05:06:33 | d95b3495 | False | 83.69 |
| Expt_22b | no_concepts | 1 | 10000 | Vivobook | 04:46:51 | 05:07:47 | d95b3495 | False | 83.81 |
| Expt_22b | no_concepts | 2 | 10000 | Vivobook | 04:48:55 | 05:08:50 | d95b3495 | False | 84.40 |
| Expt_22b | no_concepts | 3 | 10000 | Vivobook | 04:50:53 | 05:14:04 | d95b3495 | False | 85.30 |
| Expt_22b | no_dream | 0 | 10000 | Vivobook | 04:42:54 | 05:04:55 | d95b3495 | False | 83.46 |
| Expt_22b | no_dream | 1 | 10000 | Vivobook | 04:43:00 | 05:02:10 | d95b3495 | False | 84.60 |
| Expt_22b | no_dream | 2 | 10000 | Vivobook | 04:44:27 | 05:03:51 | d95b3495 | False | 84.23 |
| Expt_22b | no_dream | 3 | 10000 | Vivobook | 04:44:50 | 05:02:56 | d95b3495 | False | 85.83 |
| Expt_22b | no_meta | 0 | 10000 | Vivobook | 04:26:58 | 04:44:49 | d95b3495 | False | 84.11 |
| Expt_22b | no_meta | 1 | 10000 | Vivobook | 04:26:57 | 04:44:26 | d95b3495 | False | 84.37 |
| Expt_22b | no_meta | 2 | 10000 | Vivobook | 04:27:53 | 04:45:49 | d95b3495 | False | 85.25 |
| Expt_22b | no_meta | 3 | 10000 | Vivobook | 04:28:45 | 04:46:50 | d95b3495 | False | 85.33 |
| Expt_22b | no_sleep | 0 | 10000 | Vivobook | 04:27:23 | 04:42:59 | d95b3495 | False | 83.09 |
| Expt_22b | no_sleep | 1 | 10000 | Vivobook | 04:27:38 | 04:42:53 | d95b3495 | False | 84.18 |
| Expt_22b | no_sleep | 2 | 10000 | Vivobook | 04:32:25 | 04:48:55 | d95b3495 | False | 83.98 |
| Expt_22b | no_sleep | 3 | 10000 | Vivobook | 04:34:13 | 04:50:52 | d95b3495 | False | 84.22 |
| Expt_22b | td095 | 0 | 10000 | Vivobook | 04:51:04 | 05:12:30 | d95b3495 | False | 83.27 |
| Expt_22b | td095 | 1 | 10000 | Vivobook | 05:02:11 | 05:22:34 | d95b3495 | False | 84.00 |
| Expt_22b | td095 | 2 | 10000 | Vivobook | 05:02:57 | 05:23:58 | d95b3495 | False | 83.14 |
| Expt_22b | td095 | 3 | 10000 | Vivobook | 05:03:43 | 05:24:02 | d95b3495 | False | 83.77 |
| Expt_22c | full | 100 | 32000 | Vivobook | 04:48:10 | 05:41:04 | c50aba87 | False | 87.83 |
| Expt_22c | full | 101 | 32000 | Vivobook | 04:47:28 | 05:59:35 | c50aba87 | False | 87.58 |
| Expt_22c | full | 102 | 32000 | Vivobook | 04:47:32 | 05:46:20 | c50aba87 | False | 88.03 |
| Expt_22c | full | 103 | 32000 | Vivobook | 04:47:47 | 05:40:56 | c50aba87 | False | 89.17 |
| Expt_22c | full | 104 | 32000 | Vivobook | 04:47:30 | 05:47:15 | c50aba87 | False | 88.93 |
| Expt_22c | full | 105 | 32000 | Vivobook | 04:46:56 | 05:50:33 | c50aba87 | False | 89.89 |
| Expt_22c | full | 106 | 32000 | Vivobook | 04:47:56 | 05:45:29 | c50aba87 | False | 87.68 |
| Expt_22c | full | 107 | 32000 | Vivobook | 04:48:03 | 05:36:00 | c50aba87 | False | 89.35 |
| Expt_22c | full | 108 | 32000 | Vivobook | 04:47:27 | 05:41:24 | c50aba87 | False | 88.10 |
| Expt_22c | full | 109 | 32000 | Vivobook | 04:47:23 | 05:49:31 | c50aba87 | False | 88.06 |
| Expt_22c | full | 110 | 32000 | Vivobook | 04:46:43 | 05:48:12 | c50aba87 | False | 84.98 |
| Expt_22c | full | 111 | 32000 | Vivobook | 04:47:56 | 05:36:10 | c50aba87 | False | 89.76 |
| Expt_22d | full | 300 | 60000 | HsmPc1 (rerun) | 09:01:39 | 10:10:59 | 97ef4b81 | True | 91.14 |
| Expt_22d | full | 301 | 60000 | HsmPc1 (rerun) | 09:01:25 | 09:56:57 | 97ef4b81 | True | 93.99 |
| Expt_22d | full | 302 | 60000 | HsmPc1 (rerun) | 09:03:03 | 10:09:22 | 97ef4b81 | True | 91.55 |
| Expt_22d | full | 303 | 60000 | HsmPc1 (rerun) | 09:03:26 | 10:48:07 | 97ef4b81 | True | 91.43 |
| Expt_22d | full | 304 | 60000 | HsmPc1 (rerun) | 09:02:06 | 10:10:29 | 97ef4b81 | True | 91.47 |
| Expt_22d | full | 305 | 60000 | HsmPc1 (rerun) | 09:03:38 | 10:49:09 | 97ef4b81 | True | 90.98 |
| Expt_22d | no_concepts | 200 | 32000 | HsmPc1 (rerun) | 09:00:28 | 10:06:35 | 97ef4b81 | True | 88.36 |
| Expt_22d | no_concepts | 201 | 32000 | HsmPc1 (rerun) | 09:00:28 | 09:49:17 | 97ef4b81 | True | 86.20 |
| Expt_22d | no_concepts | 202 | 32000 | HsmPc1 (rerun) | 09:00:28 | 09:49:28 | 97ef4b81 | True | 89.85 |
| Expt_22d | no_concepts | 203 | 32000 | Vivobook | 06:06:56 | 07:02:42 | 05907550 | False | 87.48 |
| Expt_22d | no_dream | 200 | 32000 | HsmPc1 (rerun) | 09:00:29 | 09:50:37 | 97ef4b81 | True | 85.44 |
| Expt_22d | no_dream | 201 | 32000 | HsmPc1 (rerun) | 09:00:28 | 09:48:10 | 97ef4b81 | True | 88.21 |
| Expt_22d | no_dream | 202 | 32000 | Vivobook | 06:06:55 | 07:01:44 | 05907550 | False | 89.09 |
| Expt_22d | no_dream | 203 | 32000 | Vivobook | 06:06:55 | 06:51:58 | 05907550 | False | 87.14 |
| Expt_22d | no_meta_matched_floor | 200 | 32000 | HsmPc1 (rerun) | 09:02:27 | 09:48:12 | 97ef4b81 | True | 87.34 |
| Expt_22d | no_meta_matched_floor | 201 | 32000 | Vivobook | 06:10:04 | 07:08:20 | 05907550 | False | 86.96 |
| Expt_22d | no_meta_matched_floor | 202 | 32000 | Vivobook | 06:11:03 | 07:04:43 | 05907550 | False | 87.90 |
| Expt_22d | no_meta_matched_floor | 203 | 32000 | Vivobook | 06:11:02 | 07:03:10 | 05907550 | False | 86.84 |
| Expt_22d | no_meta | 200 | 32000 | Vivobook | 06:11:19 | 07:03:35 | 05907550 | False | 86.61 |
| Expt_22d | no_meta | 201 | 32000 | Vivobook | 06:10:06 | 07:07:20 | 05907550 | False | 88.19 |
| Expt_22d | no_meta | 202 | 32000 | Vivobook | 06:12:08 | 07:03:15 | 05907550 | False | 88.94 |
| Expt_22d | no_meta | 203 | 32000 | HsmPc1 (rerun) | 09:06:03 | 09:44:53 | 97ef4b81 | True | 86.97 |
| Expt_22d | no_sleep | 200 | 32000 | Vivobook | 06:06:57 | 06:58:42 | 05907550 | False | 87.14 |
| Expt_22d | no_sleep | 201 | 32000 | Vivobook | 06:06:56 | 06:52:47 | 05907550 | False | 85.73 |
| Expt_22d | no_sleep | 202 | 32000 | Vivobook | 06:06:56 | 06:59:47 | 05907550 | False | 86.21 |
| Expt_22d | no_sleep | 203 | 32000 | Vivobook | 06:06:55 | 06:54:25 | 05907550 | False | 86.81 |

Note: the 44 22b streams include control variants (`frozen`, `badinit_fixed`, `badinit_meta`, `td095`); their final S1 (about 66-70 for frozen/badinit) are not part of the main claims.

### Reproducibility: the 13 rerun streams vs the partial run-1 values (same seed, new machine)

Run-1 checkpoints exist for each cut stream up to the stop; rerun checkpoints are from the HsmPc1 rerun (`item5_rerun_vs_run1_checkpoints.csv`, 154 pairs).
| variant | seed | run-1 boxes reached | checkpoints identical (per-episode) | max |held-out diff| | first training-S1 divergence (box) | train S1 identical over run-1 boxes | frac train S1 equal | rerun finish IST | rerun final S1 |
|---|---|---|---|---|---|---|---|---|---|
| full | 300 | 28000 | 12/12 | 0.0000 | none | True | 1.000 | 10:10:59 | 91.14 |
| full | 301 | 36000 | 14/14 | 0.0000 | none | True | 1.000 | 09:56:57 | 93.99 |
| full | 302 | 32000 | 13/13 | 0.0000 | none | True | 1.000 | 10:09:22 | 91.55 |
| full | 303 | 20000 | 9/10 | 0.0542 | 18906 | False | 0.951 | 10:48:07 | 91.43 |
| full | 304 | 28000 | 12/12 | 0.0000 | none | True | 1.000 | 10:10:29 | 91.47 |
| full | 305 | 20000 | 10/10 | 0.0000 | none | True | 1.000 | 10:49:09 | 90.98 |
| no_concepts | 200 | 15000 | 9/9 | 0.0000 | none | True | 1.000 | 10:06:35 | 88.36 |
| no_concepts | 201 | 28000 | 12/12 | 0.0000 | none | True | 1.000 | 09:49:17 | 86.20 |
| no_concepts | 202 | 28000 | 12/12 | 0.0000 | none | True | 1.000 | 09:49:28 | 89.85 |
| no_dream | 200 | 28000 | 12/12 | 0.0000 | none | True | 1.000 | 09:50:37 | 85.44 |
| no_dream | 201 | 28000 | 12/12 | 0.0000 | none | True | 1.000 | 09:48:10 | 88.21 |
| no_meta | 203 | 32000 | 13/13 | 0.0000 | none | True | 1.000 | 09:44:53 | 86.97 |
| no_meta_matched_floor | 200 | 32000 | 13/13 | 0.0000 | none | True | 1.000 | 09:48:12 | 87.34 |

Summary: 153 of 154 checkpoint pairs are identical per episode. The only difference is `full` s303: training S1 diverges at box 18,906 (fraction of run-1 training boxes equal 0.951), and its 20k held-out is 85.809 (run 1) vs 85.755 (rerun), difference -0.054 (the largest in the set). Over the 89 pairs with checkpoint >= 5,000 boxes: mean abs diff 0.0006, SD 0.0057, max abs 0.0542; over the 37 pairs >= 20,000: mean abs 0.0015, SD 0.0089. So the rerun reproduced run 1 essentially bit-exactly in 12 of 13 streams over everything run 1 reached; the cause of the single divergence (a floating-point difference between machines/BLAS builds is the likely, but not verified, reason) was not investigated. Run 1 only reached the earlier checkpoints, so we cannot say whether the 60k endpoints would also have been identical.

**Third replication of the six 60k `full` streams (Expt 22e memory reruns).** The 22e reruns (same HsmPc1 machine, same code, single-threaded) of `full` s300-s305 reproduce the saved 22d final streams at all 120 shared checkpoints per episode (120/120 identical, max abs diff 0.0), with training S1 identical over all 60k boxes in 6/6 streams and the same final mean (91.7606). Since the saved 22d `full` streams were themselves produced by the HsmPc1 rerun, this shows determinism on one machine, **not** independent cross-machine reproducibility.

| seed | identical training S1 | boxes differing | final held-out 22d | final held-out 22e rerun |
|---|---|---|---|---|
| 300 | True | 0 | 91.145 | 91.145 |
| 301 | True | 0 | 93.988 | 93.988 |
| 302 | True | 0 | 91.546 | 91.546 |
| 303 | True | 0 | 91.429 | 91.429 |
| 304 | True | 0 | 91.470 | 91.470 |
| 305 | True | 0 | 90.985 | 90.985 |

## What this changes in the manuscript's claims

1. **Plateau (22d):** replace the independent-bootstrap statement for 56k -> 60k (CI about -1.1 to +1.1) by the paired one: +0.04 S1, 95% CI [-0.04, +0.13], 4 of 6 streams up. The data support a near-plateau (last 8k boxes +0.07 and +0.04), not a hard ceiling (48k -> 52k +0.22, CI +0.09..+0.36; 6/6 up). n = 6 streams, one configuration.
2. **Ablations:** only `no_sleep` (-1.81) is supported after multiplicity correction (Holm 0.0013 Welch-normal, 0.0174 Welch-t; does **not** survive the exact permutation test or Mann-Whitney with n = 4: Holm 0.102 / 0.066). `no_meta_matched_floor` (-1.02) does not survive Holm/Bonferroni/BH -> label **exploratory**. `no_meta`, `no_dream`, `no_concepts`: no detectable effect (n = 4 each; not evidence of no effect).
3. **Piece P:** the learned policies use P in 100% of episodes (9.2 -> 10.0 -> about 10.9 P pieces/episode at 20k/32k/60k); uniform natural placing uses P in 47.2% of episodes (0.63 per episode). A large share of the gain over uniform is piece choice: always choosing P with uniform placement already gives 82.3; P-only with contact-greedy placement 88.9 (about the hand rule 89.6). The 60k learners (mean 91.76) exceed that reference. Do not describe the learner as discovering placement skill alone.
4. **Baselines:** the "uniform ~ 67" in the 22b/c/d reports is the untrained network at checkpoint 0 (67.23-67.81), not uniform natural placing (67.32); V21's 67.30 is true uniform (2,000 episodes). "89.61" is the hand rule on the first 1,000 seeds (89.617 on the 1,200 episodes; 89.648 on 2,000). V21 used tau_eval 0.3 and 2,000 episodes; 22b-d used 0.25 and 1,200. The Expt-20 baselines (best 98.0) are on a different task (unlimited pieces, 100 actions) and none was evaluated under the 14-piece cap there; under the cap the new simple packers give 70.2-89.6.
5. **Evaluation set terminology:** "1,200 fresh/held-out boxes" -> "1,200 evaluation episodes of one fixed problem (seeds 7,700,000 + j) that differ only in the random draws of action selection". They are disjoint from training, but their first 300 were used in pilots to choose lambda = 1 (and V21 used the same seeds), so they are not a pristine test set; claims about generalisation to other box instances are not supported by this evaluation.
6. **Reproducibility wording (student write-up / manuscript):** replace "reproducible statistically, not bit for bit" by: the 13 streams rerun after the interruption matched the first run per episode at 153 of 154 shared checkpoints (one stream diverged from box 18,906 with a -0.054 difference at 20k). Held-out values of reruns agree to within 0.054 (mean absolute difference 0.0006 for checkpoints >= 5,000 boxes).
7. **Provenance statement:** 13 of the 26 22d streams (6 `full`, 3 no_concepts, 2 no_dream, 1 no_meta, 1 no_meta_matched_floor) were produced on HsmPc1 after a manual stop; the other 13 ran on the Vivobook. The numpy version used on the Vivobook is not recorded.

## Caveats and things not recoverable

- Expt 22d did not store final agent memories; item 2 used reruns (identical to the saved streams, verified at all 120 checkpoints). 22b/22c stored only seed-0 / seed-100 memories (one of 12 each).
- The Vivobook numpy / BLAS versions are not recorded. The cause of the single run-1 vs rerun divergence (full s303) was not investigated.
- The V22b pilot sweep logs (`p2_*.log`) and `q2.py` are not on disk: evaluation size/seeds of that sweep are known only from NIGHT_LOG text. The V22a main-run manifests record eval_boxes 400/600/800/1,200 across launches; lambda default in those manifests is 0.95 (the lambda = 1 default was set later in code - see NIGHT_LOG 03:03-03:04).
- The origin of the hand-rule weights (-3, -1, +2, noise 0.5) was not traced (they are constants in `learner_ref.py` / `learner.py`); whether they were tuned on the evaluation seeds is unknown to this report.
- n is small: 6 streams for saturation, 4 per ablation; permutation-based tests cannot reach strong significance with n = 4 vs 12 after correction. No power analysis was done.
- Exact-number CSVs are in the same folder; none of the existing experiment folders or the student write-up was modified.

## Table of exact numbers (headline)

| item | quantity | value |
|---|---|---|
| Item 1a | 56k -> 60k paired mean diff (95% paired bootstrap CI) | +0.04 (-0.04, +0.13); n = 6 |
| Item 1a | 20k -> 60k | +6.38 (+5.73, +7.33) |
| Item 1a | 48k -> 52k | +0.22 (+0.09, +0.36) |
| Item 1b | no_sleep, welch_normal(as in summary.md) (22c ref) | diff +1.81; raw p 0.0003, Holm 0.0013, Bonf 0.0013, BH 0.0013 |
| Item 1b | no_sleep, welch_t(df Satterthwaite) (22c ref) | diff +1.81; raw p 0.0035, Holm 0.0174, Bonf 0.0174, BH 0.0174 |
| Item 1b | no_sleep, permutation_exact (22c ref) | diff +1.81; raw p 0.0203, Holm 0.1016, Bonf 0.1016, BH 0.1016 |
| Item 1b | no_sleep, mannwhitney_U (22c ref) | diff +1.81; raw p 0.0132, Holm 0.0659, Bonf 0.0659, BH 0.0659 |
| Item 1b | no_meta_matched_floor, welch_normal(as in summary.md) (22c ref) | diff +1.02; raw p 0.0231, Holm 0.0924, Bonf 0.1155, BH 0.0577 |
| Item 1b | no_meta_matched_floor, welch_t(df Satterthwaite) (22c ref) | diff +1.02; raw p 0.0399, Holm 0.1594, Bonf 0.1993, BH 0.0996 |
| Item 1b | no_meta_matched_floor, permutation_exact (22c ref) | diff +1.02; raw p 0.1555, Holm 0.6220, Bonf 0.7775, BH 0.3887 |
| Item 1b | no_meta_matched_floor, mannwhitney_U (22c ref) | diff +1.02; raw p 0.0418, Holm 0.1670, Bonf 0.2088, BH 0.1044 |
| Item 2 | uniform natural | S1 67.319; P in 0.472 of episodes; 0.631 P/episode; area 4.809 |
| Item 2 | hand rule | S1 89.617; P in 1.000 of episodes; 10.092 P/episode; area 6.424 |
| Item 2 | 22b s0 @20k | S1 83.887; P in 1.000 of episodes; 9.241 P/episode; area 6.306 |
| Item 2 | 22c s100 @32k | S1 87.826; P in 1.000 of episodes; 9.956 P/episode; area 6.390 |
| Item 2 | 22d full @60k, mean of 6 memories | S1 91.761; P in 1.000; 11.094 P/episode; area 6.574 |
| Item 2 | P_only_uniform_natural | S1 82.335; 9.328 P/episode |
| Item 2 | P_only_contact_greedy | S1 88.918; 11.997 P/episode |
| Item 2 | P_only_hand_score | S1 88.323; 10.992 P/episode |
| Item 3 | hand rule on 1,000 / 1,200 / 2,000 episodes | 89.606 / 89.617 / 89.6475 |
| Item 3 | uniform natural on 1,000 / 1,200 / 2,000 episodes | 67.328 / 67.319 / 67.297 |
| Item 3 | checkpoint-0 mean S1 (untrained net) 22b / 22c / 22d | 67.232 / 67.806 / 67.512 |
| Item 4 | evaluation seeds; SE of mean (22c s100) | 7,700,000 + j, j < 1,200; SD 2.370, SE 0.068 |
| Item 5 | identical checkpoints rerun vs run 1 | 153/154; max abs diff 0.0542 (full s303 @20k) |
| Item 5 | abs diff, checkpoints >= 5k (n = 89) | mean 0.0006, SD 0.0057 |

## Files

`item1a_paired_saturation.csv`, `item1a_per_stream_heldout.csv`, `item1b_ablation_multiplicity.csv`, `item1_inputs.json`, `fig_item1a_paired_differences.png`; `item2_piece_P_usage.csv`, `item2b_P_only_baselines.csv`, `item2_per_box.npz`, `item2_meta.json` (the `*_before_22d_memories.*` copies are the earlier 4-policy outputs); `item3_code_refs.csv`, `item3_expt20_rules.csv`, `item3_extra_packers_under_14cap.csv`, `item3_ckpt0_vs_uniform.csv`, `item3_natural_filter_equivalence.json`, `item3_4_facts.json`, `item3_refs_v21.npz`, `item3_refs_v22.npz`; `item4_pilot_overlap_check.csv`, `item4_seed_disjointness.json`; `item5_stream_provenance.csv`, `item5_rerun_vs_run1_checkpoints.csv`, `item5_rerun_divergence.csv`, `item5_reproducibility_summary.json`, `item5_third_run_*.csv/json`; `memory_reruns/` (six final memories and streams, `progress.log`).
