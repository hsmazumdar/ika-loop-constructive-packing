# Expt-20 baselines (20260930_214303)

- 10000 boxes per arm, seed 20261003 (the held-out seed of the stronger run), paired by per-trial seed id. Bootstrap 95% CI, 2000 resamples over trial pairs. Total 2337s.
- Best plain baseline (picked after seeing results, from 14 rules): **G_contact_any_first_tie** (S1 98.000). Best non-deterministic plain rule: G_contact_any_random_tie (95.749).
- Rules marked deterministic have no random step: every box is identical, S1 std 0. They are one solution, evaluated 10,000 times; a CI on them is a CI on the control's variation.
- Effort: `extra units` = strategy's own mask tests + scored candidates (rules, Expt-20 arms); for the Expt-1 agent it is its `candidate_evaluations`; for the Expt-16 primitive it is its A (candidates examined). `enum units` = 3,636 placement-visits per decision, where the code enumerates the catalogue. These scales are similar in spirit but not identical.

| rank | variant | family | S1 mean | S1 std | S1 max | gain vs uniform [95% CI] | gain vs best plain [95% CI] | gain vs D_anchor_contact [95% CI] | S2 mean | attempts | extra units/box | enum units/box | full boxes | S1>=95 | cpu ms/box |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | G_contact_any_first_tie | plain rule | 98.000 | 0.00 | 98 | +18.200 [+18.123, +18.281] | +0.000 [+0.000, +0.000] | +1.747 [+1.712, +1.786] | 5.1579 | 19.00 | 32346 | 72720 | 0.0000 | 1.000 | 22.22 |
| 2 | FF_contact_first_tie | plain rule | 97.000 | 0.00 | 97 | +17.200 [+17.118, +17.282] | -1.000 [-1.000, -1.000] | +0.747 [+0.712, +0.786] | 5.1053 | 19.00 | 4302 | 72720 | 0.0000 | 1.000 | 14.46 |
| 3 | Expt20_D_anchor_contact_eps0 | Expt-20 | 96.253 | 1.83 | 100 | +16.453 [+16.363, +16.542] | -1.747 [-1.782, -1.710] | +0.000 [+0.000, +0.000] | 5.4225 | 17.78 | 4457 | 68215 | 0.0171 | 0.840 | 12.48 |
| 4 | FF_smallest_first_legal | plain rule | 96.000 | 0.00 | 96 | +16.200 [+16.123, +16.279] | -2.000 [-2.000, -2.000] | -0.253 [-0.288, -0.214] | 4.0000 | 24.00 | 4202 | 90900 | 0.0000 | 1.000 | 16.46 |
| 5 | Expt20_D_contact_all_eps0 | Expt-20 | 95.749 | 1.98 | 100 | +15.949 [+15.855, +16.038] | -2.251 [-2.289, -2.213] | -0.504 [-0.554, -0.451] | 5.5616 | 17.25 | 28748 | 66273 | 0.0203 | 0.760 | 30.66 |
| 6 | G_contact_any_random_tie | plain rule | 95.749 | 1.98 | 100 | +15.949 [+15.861, +16.039] | -2.251 [-2.289, -2.213] | -0.504 [-0.554, -0.451] | 5.5616 | 17.25 | 28748 | 66273 | 0.0203 | 0.760 | 29.49 |
| 7 | FF_first_legal_any_orientation | plain rule | 94.000 | 0.00 | 94 | +14.200 [+14.119, +14.281] | -4.000 [-4.000, -4.000] | -2.253 [-2.288, -2.214] | 4.9474 | 19.00 | 8532 | 72720 | 0.0000 | 0.000 | 14.91 |
| 8 | FF_largest_contact_tie | plain rule | 93.345 | 2.52 | 99 | +13.545 [+13.451, +13.640] | -4.655 [-4.705, -4.604] | -2.908 [-2.967, -2.848] | 6.0172 | 15.52 | 6492 | 60077 | 0.0000 | 0.330 | 12.13 |
| 9 | Expt20_E_joint_look_K8_eps0 | Expt-20 | 93.190 | 2.73 | 100 | +13.390 [+13.296, +13.483] | -4.810 [-4.864, -4.757] | -3.063 [-3.131, -2.997] | 4.7913 | 19.47 | 165160 | 74415 | 0.0019 | 0.332 | 53.48 |
| 10 | FF_E16score_random_tie | plain rule | 92.645 | 3.75 | 100 | +12.845 [+12.749, +12.955] | -5.355 [-5.428, -5.279] | -3.608 [-3.695, -3.525] | 6.1423 | 15.13 | 7589 | 58333 | 0.0880 | 0.271 | 11.25 |
| 11 | FF_smallest_random_tie | plain rule | 92.100 | 2.76 | 100 | +12.300 [+12.204, +12.398] | -5.900 [-5.954, -5.846] | -4.153 [-4.218, -4.085] | 4.0242 | 22.89 | 9871 | 86849 | 0.0006 | 0.165 | 17.52 |
| 12 | Expt1_agent_none_eps0.15 | earlier expt | 91.374 | 4.00 | 100 | +11.575 [+11.462, +11.690] | -6.626 [-6.703, -6.545] | -4.879 [-4.966, -4.787] | 1.6488 | 57.06 | 19743 | 358734 | 0.0162 | 0.233 | 3508.18 |
| 13 | FF_random_type_random_orient | plain rule | 90.311 | 3.02 | 100 | +10.512 [+10.414, +10.611] | -7.689 [-7.747, -7.631] | -5.942 [-6.009, -5.873] | 4.7978 | 18.84 | 10533 | 72141 | 0.0001 | 0.078 | 14.40 |
| 14 | FF_largest_random_tie | plain rule | 88.205 | 3.09 | 99 | +8.406 [+8.300, +8.507] | -9.795 [-9.854, -9.735] | -8.048 [-8.119, -7.977] | 6.3432 | 13.97 | 10574 | 54431 | 0.0000 | 0.016 | 12.04 |
| 15 | G_E16score_any_random_tie | plain rule | 87.998 | 0.21 | 90 | +8.198 [+8.122, +8.279] | -10.002 [-10.006, -9.998] | -8.255 [-8.290, -8.215] | 6.7665 | 13.01 | 19541 | 50923 | 0.0000 | 0.000 | 35.13 |
| 16 | FF_largest_first_legal | plain rule | 84.000 | 0.00 | 84 | +4.200 [+4.118, +4.280] | -14.000 [-14.000, -14.000] | -12.253 [-12.288, -12.214] | 7.0000 | 12.00 | 10123 | 47268 | 0.0000 | 0.000 | 9.76 |
| 17 | G_area_any_rowmajor_tie | plain rule | 84.000 | 0.00 | 84 | +4.200 [+4.119, +4.278] | -14.000 [-14.000, -14.000] | -12.253 [-12.288, -12.214] | 7.0000 | 12.00 | 20828 | 47268 | 0.0000 | 0.000 | 11.47 |
| 18 | G_area_any_random_tie | plain rule | 83.436 | 3.43 | 94 | +3.637 [+3.532, +3.740] | -14.564 [-14.630, -14.497] | -12.817 [-12.891, -12.737] | 6.2686 | 13.34 | 13277 | 52124 | 0.0000 | 0.000 | 10.91 |
| 19 | Expt20_A_ltmS2_eps0.05_a3b1 | Expt-20 | 81.454 | 3.91 | 95 | +1.654 [+1.543, +1.768] | -16.546 [-16.622, -16.469] | -14.799 [-14.880, -14.711] | 5.3002 | 15.39 | 0 | 59602 | 0.0000 | 0.000 | 15.15 |
| 20 | Expt20_LTM_guided_earlier | Expt-20 | 80.803 | 4.02 | 94 | +1.003 [+0.895, +1.114] | -17.197 [-17.276, -17.118] | -15.450 [-15.541, -15.360] | 5.0293 | 16.08 | 0 | 62103 | 0.0000 | 0.000 | 13.01 |
| 21 | uniform_random_control | control | 79.800 | 4.09 | 93 | +0.000 [+0.000, +0.000] | -18.200 [-18.281, -18.117] | -16.453 [-16.544, -16.362] | 4.7194 | 16.93 | 0 | 65187 | 0.0000 | 0.000 | 4.59 |
| 22 | Expt16_primitive_run_to_cap_Q101 | earlier expt | 79.760 | 4.28 | 93 | -0.040 [-0.155, +0.084] | -18.240 [-18.322, -18.159] | -16.493 [-16.584, -16.407] | 5.5633 | 14.36 | 8381 | 91292 | 0.0000 | 0.000 | 94.72 |
| 23 | Expt16_primitive_recorded_stop_Q75 | earlier expt | 76.718 | 1.64 | 81 | -3.082 [-3.171, -2.999] | -21.282 [-21.313, -21.250] | -19.535 [-19.583, -19.486] | 5.7855 | 13.28 | 3706 | 66954 | 0.0000 | 0.000 | 67.96 |

## Recorded numbers of the earlier experiments (saved authoritative runs, different tasks)

```json
{
  "Expt-1 smoke (results/episodes.csv), mode none, eval boxes": {
    "n_boxes": 90,
    "mean_terminal_occupied": 88.28888888888889,
    "max": 98.0,
    "mean_candidate_evaluations": 19660.277777777777,
    "mean_actions": 100.0,
    "mean_undos": 42.9,
    "task": "empty 10x10 box, unlimited pieces, 100-action budget (same task as Expt-20)",
    "note": "run folder pointed to by LATEST_RUN.txt is not the same as this summary file's; this is the repo-root episodes.csv as saved"
  },
  "Expt-2 primitive (authoritative run 20260929_092518_discovery_smoke)": {
    "n_boxes": 104,
    "mean_final_occupied": 65.57692307692308,
    "max": 74.0,
    "mean_candidate_evals": 50000.0,
    "task": "inventory tasks (limited pieces per box), compute budget 50,000 evals, about 14 placements; different boxes"
  },
  "Expt-16 primitive (authoritative 20260930_071552), independent_fresh": {
    "n_boxes": 60,
    "mean_Q_occupied": 75.66666666666667,
    "min": 68.0,
    "max": 79.0,
    "mean_A_candidates": 1597.7166666666667,
    "median_A": 888.0,
    "task": "inventory tasks; the policy stops once occupied >= 75 (q_min) or at eval_cap 8000, so its Q is a floor-stop, not a best effort"
  },
  "Expt-16 primitive (authoritative 20260930_071552), recurring_family": {
    "n_boxes": 60,
    "mean_Q_occupied": 75.76666666666667,
    "min": 68.0,
    "max": 78.0,
    "mean_A_candidates": 1138.1666666666667,
    "median_A": 816.0,
    "task": "inventory tasks; the policy stops once occupied >= 75 (q_min) or at eval_cap 8000, so its Q is a floor-stop, not a best effort"
  }
}
```