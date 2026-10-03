# Expt-22d - long-horizon ablations and saturation of the organic value learner

Run `20261001_060654_main` | code hash `05907550c5739d90` | generated 2026-10-01 10:49 IST | **all 26 streams finished**

Design: `full` x 6 streams of 60000 boxes (seeds 300+; held-out checkpoints every 4k boxes after 20k); ablations x 4 streams of 32000 boxes (seeds 200+): no_meta, no_meta_matched_floor, no_dream, no_concepts, no_sleep. Reference = Expt-22c `full`, 12 streams (seeds 100-111) at 32000 boxes. Held-out = frozen memory on 1200 fresh boxes (same boxes as 22b/22c). Progress (min-max boxes done per variant): full 60000-60000, no_concepts 32000-32000, no_dream 32000-32000, no_meta_matched_floor 32000-32000, no_meta 32000-32000, no_sleep 32000-32000.

Reminder: `no_meta` = fixed hyperparameters + V21-style anneal (tau 2.0->0.35, eps 0.10->0.01 over 15k boxes, then constant); `no_meta_matched_floor` = fixed hyperparameters, tau 2.0->0.25 and eps 0.10->0.0077 linearly over 32k boxes (the floors the meta-controller reached in 22c; the meta-controller's own tau trajectory is shown in fig_self_modification_long). `no_sleep` = online TD only; `no_dream`; `no_concepts`.

## 1. Long-horizon ablations (held-out S1 after 32000 boxes)

- Reference `full` (22c, n=12): **88.28 (87.49-88.95)**. `full` streams of this run at the same 32k checkpoint (n=6): 88.32 (87.10-89.36); pooled n=18: 88.29 (87.65-88.87).

| variant | n finished (+running) | S1 | 95% CI | full(22c) minus variant | 95% CI | p (Welch) | full(pooled) minus variant (95% CI) | frac S1>=90 | train S1 last 3k |
|---|---|---|---|---|---|---|---|---|---|
| no_concepts | 4 (+0) | 87.97 | 86.74 - 89.26 | +0.31 | -1.22, +1.76 | 0.719 | +0.32 (-1.13, +1.74) | 0.314 | 86.91 |
| no_meta | 4 (+0) | 87.68 | 86.79 - 88.57 | +0.60 | -0.58, +1.71 | 0.362 | +0.62 (-0.49, +1.69) | 0.258 | 85.18 |
| no_dream | 4 (+0) | 87.47 | 86.13 - 88.65 | +0.81 | -0.65, +2.34 | 0.354 | +0.82 (-0.58, +2.31) | 0.257 | 86.88 |
| no_meta_matched_floor | 4 (+0) | 87.26 | 86.90 - 87.66 | +1.02 | +0.15, +1.82 | 0.0231 | +1.04 (+0.29, +1.73) | 0.171 | 84.50 |
| no_sleep | 4 (+0) | 86.48 | 85.97 - 86.98 | +1.81 | +0.92, +2.67 | 0.000255 | +1.82 (+1.00, +2.61) | 0.114 | 83.17 |

![bars](fig_long_ablation_bars.png)
![curves](fig_long_ablation_curves.png)

Floor diagnostic: training S1 over boxes 29000-32000: no_meta 85.18, no_meta_matched_floor 84.50, full(22c) 87.64.

## 2. Saturation run (full, long streams)

| boxes learned | S1 | 95% CI | frac S1>=90 | hidden | concepts | replicates |
|---|---|---|---|---|---|---|
| 0 | 67.51 | 66.84 - 68.22 | 0.000 | 64 | 0 | 6 |
| 500 | 71.40 | 69.98 - 72.83 | 0.000 | 64 | 0 | 6 |
| 1000 | 81.73 | 80.74 - 82.60 | 0.002 | 64 | 0 | 6 |
| 2000 | 83.14 | 82.87 - 83.35 | 0.006 | 64 | 2 | 6 |
| 3000 | 83.43 | 83.27 - 83.57 | 0.008 | 64 | 2 | 6 |
| 5000 | 83.72 | 83.51 - 83.88 | 0.010 | 64 | 3 | 6 |
| 7500 | 84.50 | 84.20 - 84.86 | 0.022 | 64 | 4 | 6 |
| 10000 | 84.87 | 84.61 - 85.17 | 0.027 | 64 | 12 | 6 |
| 15000 | 85.07 | 84.60 - 85.48 | 0.030 | 107 | 23 | 6 |
| 20000 | 85.38 | 85.04 - 85.70 | 0.039 | 160 | 73 | 6 |
| 24000 | 86.17 | 85.55 - 86.79 | 0.091 | 160 | 95 | 6 |
| 28000 | 87.13 | 86.45 - 87.82 | 0.179 | 160 | 95 | 6 |
| 32000 | 88.32 | 87.10 - 89.36 | 0.386 | 160 | 111 | 6 |
| 36000 | 89.95 | 88.75 - 91.00 | 0.650 | 160 | 136 | 6 |
| 40000 | 90.46 | 89.56 - 91.26 | 0.745 | 160 | 166 | 6 |
| 44000 | 91.22 | 90.55 - 92.12 | 0.844 | 160 | 200 | 6 |
| 48000 | 91.43 | 90.78 - 92.45 | 0.861 | 160 | 216 | 6 |
| 52000 | 91.65 | 91.09 - 92.60 | 0.898 | 160 | 230 | 6 |
| 56000 | 91.72 | 91.20 - 92.64 | 0.911 | 160 | 243 | 6 |
| 60000 | 91.76 | 91.19 - 92.68 | 0.910 | 160 | 257 | 6 |

![sat](fig_saturation.png)

Last common interval 56000->60000: change in held-out S1 +0.04 (95% CI -1.11, +1.07) over 6 replicates (independent-sample bootstrap; replicate streams are the same across checkpoints so a paired estimate would be tighter).

## 3. Self-modification in the long streams (full)

678 hyperparameter changes over 6 streams so far (113/stream), 40 capacity tests (7 accepted). eps: 209 (up 0, down 209); tau: 169 (up 0, down 169); dream: 113 (up 0, down 113); lr: 103 (up 6, down 97); sleep_every: 48 (up 48, down 0); stm: 36 (up 36, down 0). Full event list: `self_modification_events_long.csv`.

![sm](fig_self_modification_long.png)

## 4. Paper-ready findings (auto-generated from the numbers above; PARTIAL if runs unfinished)

**Supported (CI excludes 0):**
- `no_meta_matched_floor` (n=4): 22c-full minus variant +1.02 (CI +0.15, +1.82) -> full is significantly better
- `no_sleep` (n=4): 22c-full minus variant +1.81 (CI +0.92, +2.67) -> full is significantly better

**Not supported / inconclusive:**
- `no_concepts` (n=4): 22c-full minus variant +0.31 (CI -1.22, +1.76) -> not distinguishable (CI includes 0)
- `no_meta` (n=4): 22c-full minus variant +0.60 (CI -0.58, +1.71) -> not distinguishable (CI includes 0)
- `no_dream` (n=4): 22c-full minus variant +0.81 (CI -0.65, +2.34) -> not distinguishable (CI includes 0)

**Saturation:** latest long-stream checkpoint 60000 boxes: S1 91.76 (91.19-92.68), n=6; frac S1>=90 0.910. The long streams have completed; a plateau claim requires the final intervals' CIs to include 0 (see section 2).

**Caveats:** ablations use 4 replicates (low power; CIs are over replicate streams only; the 1,200 evaluation boxes are fixed and shared by all variants); the reference full(22c) used different seeds (100-111) than the ablations (200-203), which is valid but not paired; V21 CI treats V21 as a constant; hand rule is a reference only.