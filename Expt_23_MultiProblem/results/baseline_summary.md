
### hard / capped_nat  (final checkpoint 20000; reference means on the same test problems: uniform 0.751, hand 0.888, CEM-hand 0.897, rollout-beam 0.999)

| arm | streams | 0 | 1k | 2k | 5k | 10k | 20k | final mean [95% CI] | median | IQM | frac. test_iid..test_both (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| N | 8 | 0.753 | 0.748 | 0.768 | 0.775 | 0.821 | 0.861 | 0.861 [0.857, 0.865] | 0.859 | 0.861 | 0.861, 0.860, 0.858, 0.866 |
| DQN | 8 | 0.750 | 0.744 | 0.746 | 0.742 | 0.772 | 0.785 | 0.785 [0.780, 0.789] | 0.785 | 0.785 | 0.780, 0.792, 0.779, 0.787 |
| PPO | 8 | 0.750 | 0.752 | 0.763 | 0.813 | 0.836 | 0.853 | 0.853 [0.847, 0.857] | 0.856 | 0.855 | 0.860, 0.854, 0.848, 0.849 |

PPO pre-declared 4-seed subset (seeds 2300-2303; A4): mean 0.854 (n=4) vs all-streams mean 0.853 (n=8)

| comparison (final ckpt) | mean diff | Welch-t p | Holm(Welch) | permutation p | Mann-Whitney p |
|---|---|---|---|---|---|
| N vs DQN | +0.077 | 7.859e-13 | 9.431e-12 | 0.0001554 | 0.0001554 |
| N vs PPO | +0.009 | 0.02469 | 0.02469 | 0.01725 | 0.02067 |
| DQN vs PPO | -0.068 | 3.474e-11 | 3.821e-10 | 0.0001554 | 0.0001554 |
| N vs uniform (ref mean 0.751) | +0.110 | 2.679e-10 | 2.679e-09 | nan | nan |
| N vs hand (ref mean 0.888) | -0.027 | 4.968e-06 | 1.138e-05 | nan | nan |
| N vs cemhand (ref mean 0.897) | -0.035 | 7.433e-07 | 4.46e-06 | nan | nan |
| DQN vs uniform (ref mean 0.751) | +0.034 | 1.624e-06 | 6.495e-06 | nan | nan |
| DQN vs hand (ref mean 0.888) | -0.103 | 7.068e-10 | 5.654e-09 | nan | nan |
| DQN vs cemhand (ref mean 0.897) | -0.112 | 4.046e-10 | 3.642e-09 | nan | nan |
| PPO vs uniform (ref mean 0.751) | +0.102 | 2.647e-09 | 1.853e-08 | nan | nan |
| PPO vs hand (ref mean 0.888) | -0.035 | 3.792e-06 | 1.138e-05 | nan | nan |
| PPO vs cemhand (ref mean 0.897) | -0.044 | 8.666e-07 | 4.46e-06 | nan | nan |

### std / capped_any  (final checkpoint 10000; reference means on the same test problems: uniform 0.757, hand 0.931, CEM-hand 0.930, rollout-beam 0.999)

| arm | streams | 0 | 1k | 2k | 5k | 10k | final mean [95% CI] | median | IQM | frac. test_iid..test_both (final) |
|---|---|---|---|---|---|---|---|---|---|
| N | 6 | 0.758 | 0.806 | 0.810 | 0.815 | 0.844 | 0.844 [0.838, 0.849] | 0.846 | 0.844 | 0.852, 0.849, 0.836, 0.838 |
| DQN | 4 | 0.758 | 0.751 | 0.772 | 0.793 | 0.824 | 0.824 [0.822, 0.827] | 0.825 | 0.825 | 0.828, 0.828, 0.823, 0.818 |
| PPO | 1 | 0.757 | 0.809 | 0.855 | 0.867 | 0.872 | 0.872 [nan, nan] | 0.872 | 0.872 | 0.881, 0.873, 0.871, 0.863 |

| comparison (final ckpt) | mean diff | Welch-t p | Holm(Welch) | permutation p | Mann-Whitney p |
|---|---|---|---|---|---|
| N vs DQN | +0.019 | 0.0008698 | 0.005219 | 0.009524 | 0.009524 |
| N vs PPO | -0.029 | nan | 1 | nan | nan |
| DQN vs PPO | -0.048 | nan | 1 | nan | nan |
| N vs uniform (ref mean 0.757) | +0.087 | 1.133e-06 | 1.294e-05 | nan | nan |
| N vs hand (ref mean 0.931) | -0.088 | 1.078e-06 | 1.294e-05 | nan | nan |
| N vs cemhand (ref mean 0.930) | -0.087 | 1.136e-06 | 1.294e-05 | nan | nan |
| DQN vs uniform (ref mean 0.757) | +0.068 | 2.709e-05 | 0.0001896 | nan | nan |
| DQN vs hand (ref mean 0.931) | -0.107 | 6.845e-06 | 6.16e-05 | nan | nan |
| DQN vs cemhand (ref mean 0.930) | -0.106 | 7.025e-06 | 6.16e-05 | nan | nan |
| PPO vs uniform (ref mean 0.757) | +0.115 | nan | 1 | nan | nan |
| PPO vs hand (ref mean 0.931) | -0.059 | nan | 1 | nan | nan |
| PPO vs cemhand (ref mean 0.930) | -0.058 | nan | 1 | nan | nan |

### std / capped_nat  (final checkpoint 20000; reference means on the same test problems: uniform 0.760, hand 0.931, CEM-hand 0.930, rollout-beam 0.999)

| arm | streams | 0 | 1k | 2k | 5k | 10k | 20k | final mean [95% CI] | median | IQM | frac. test_iid..test_both (final) |
|---|---|---|---|---|---|---|---|---|---|---|
| N | 8 | 0.761 | 0.803 | 0.813 | 0.814 | 0.843 | 0.879 | 0.879 [0.875, 0.883] | 0.878 | 0.877 | 0.883, 0.885, 0.872, 0.874 |
| DQN | 8 | 0.761 | 0.755 | 0.771 | 0.796 | 0.826 | 0.825 | 0.825 [0.824, 0.827] | 0.826 | 0.826 | 0.830, 0.831, 0.820, 0.821 |
| PPO | 8 | 0.760 | 0.792 | 0.842 | 0.863 | 0.875 | 0.883 | 0.883 [0.880, 0.886] | 0.883 | 0.882 | 0.893, 0.881, 0.881, 0.876 |

PPO pre-declared 4-seed subset (seeds 2300-2303; A4): mean 0.882 (n=4) vs all-streams mean 0.883 (n=8)

| comparison (final ckpt) | mean diff | Welch-t p | Holm(Welch) | permutation p | Mann-Whitney p |
|---|---|---|---|---|---|
| N vs DQN | +0.053 | 1.748e-08 | 6.992e-08 | 0.0001554 | 0.0001554 |
| N vs PPO | -0.004 | 0.1503 | 0.1503 | 0.1465 | 0.1605 |
| DQN vs PPO | -0.057 | 4.931e-11 | 3.945e-10 | 0.0001554 | 0.0001554 |
| N vs uniform (ref mean 0.760) | +0.119 | 2.821e-10 | 1.975e-09 | nan | nan |
| N vs hand (ref mean 0.931) | -0.052 | 8.767e-08 | 2.63e-07 | nan | nan |
| N vs cemhand (ref mean 0.930) | -0.051 | 9.546e-08 | 2.63e-07 | nan | nan |
| DQN vs uniform (ref mean 0.760) | +0.066 | 2.012e-12 | 2.012e-11 | nan | nan |
| DQN vs hand (ref mean 0.931) | -0.105 | 7.443e-14 | 8.932e-13 | nan | nan |
| DQN vs cemhand (ref mean 0.930) | -0.105 | 7.767e-14 | 8.932e-13 | nan | nan |
| PPO vs uniform (ref mean 0.760) | +0.123 | 1.382e-11 | 1.244e-10 | nan | nan |
| PPO vs hand (ref mean 0.931) | -0.048 | 1.02e-08 | 6.119e-08 | nan | nan |
| PPO vs cemhand (ref mean 0.930) | -0.047 | 1.12e-08 | 6.119e-08 | nan | nan |