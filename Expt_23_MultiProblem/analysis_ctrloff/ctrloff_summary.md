# A8 controller-off confirmation - analysis (stream level)

Machines/libraries present: i7Win11B (python 3.12.10, numpy 2.4.6); i9Win10 (python 3.12.4, numpy 2.0.0)

Streams loaded: 80


## std / capped_nat  (final checkpoint 20000)

| arm | streams | 0 | 1000 | 2000 | 5000 | 10000 | 20000 | final mean [95% CI] | median | IQM | final by split (test_iid, test_size, test_piece, test_both) |
|---|---|---|---|---|---|---|---|---|---|---|
| F | 8 | 0.760 | 0.792 | 0.809 | 0.819 | 0.859 | 0.900 | 0.8996 [0.8954, 0.9041] | 0.8989 | 0.8989 | 0.903, 0.907, 0.895, 0.894 |
| R | 8 | 0.760 | 0.793 | 0.822 | 0.825 | 0.843 | 0.850 | 0.8498 [0.8489, 0.8508] | 0.8498 | 0.8499 | 0.856, 0.855, 0.843, 0.845 |
| RN | 8 | 0.765 | 0.787 | 0.827 | 0.818 | 0.831 | 0.844 | 0.8437 [0.8403, 0.8466] | 0.8458 | 0.8450 | 0.850, 0.847, 0.839, 0.838 |
| NM | 8 | 0.765 | 0.808 | 0.803 | 0.812 | 0.851 | 0.873 | 0.8730 [0.8687, 0.8771] | 0.8734 | 0.8737 | 0.875, 0.880, 0.868, 0.869 |
| N | 8 | 0.765 | 0.797 | 0.809 | 0.817 | 0.842 | 0.876 | 0.8762 [0.8727, 0.8797] | 0.8763 | 0.8765 | 0.879, 0.883, 0.871, 0.872 |

References from the EARLIER runs (not rerun, not part of the A8 tests unless stated): uniform 0.760; hand 0.931; cemhand 0.930; N (earlier baseline, seeds 2300+, n=8) 0.8786; DQN (earlier baseline, seeds 2300+, n=8) 0.8255; PPO (earlier baseline, seeds 2300+, n=8) 0.8829; F (earlier controller-ON E-run, n=8) 0.8412; NM (earlier controller-ON E-run, n=8) 0.8691; R (earlier controller-ON E-run, n=8) 0.8484; RN (earlier controller-ON E-run, n=8) 0.8423

**PRIMARY family (pre-registered)** (Holm over 3)

| comparison | n | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | Holm(perm) | MWU p | Holm(MWU) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| F vs N (E2, consolidation vs plain) | 8 v 8 | +0.0234 | [+0.018, +0.029] | 2.994e-06 | 2.994e-06 | 0.0001554 | 0.0004662 | 0.0001554 | 0.0004662 | supported |
| F vs NM (E2, matched compute) | 8 v 8 | +0.0266 | [+0.021, +0.033] | 1.233e-06 | 2.466e-06 | 0.0001554 | 0.0004662 | 0.0001554 | 0.0004662 | supported |
| F vs R (E1, guided vs random data) | 8 v 8 | +0.0498 | [+0.045, +0.054] | 5.528e-08 | 1.659e-07 | 0.0001554 | 0.0004662 | 0.0001554 | 0.0004662 | supported |

**SECONDARY family (Holm over 5)** (Holm over 5)

| comparison | n | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | Holm(perm) | MWU p | Holm(MWU) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| F vs RN | 8 v 8 | +0.0559 | [+0.051, +0.061] | 9.723e-11 | 4.862e-10 | 0.0001554 | 0.000777 | 0.0001554 | 0.000777 | supported |
| F vs DQN (earlier run, seeds 2300+) | 8 v 8 | +0.0742 | [+0.070, +0.079] | 1.627e-09 | 6.508e-09 | 0.0001554 | 0.000777 | 0.0001554 | 0.000777 | supported |
| F vs PPO (earlier run, seeds 2300+) | 8 v 8 | +0.0167 | [+0.011, +0.022] | 7.331e-05 | 7.331e-05 | 0.0003108 | 0.0009324 | 0.0003108 | 0.0009324 | supported |
| F vs hand (ref mean 0.931) | 8 v ref | -0.0311 |  | 3.524e-06 | 1.057e-05 | nan | 1 | nan | 1 | opposite direction (F worse) |
| F vs cemhand (ref mean 0.930) | 8 v ref | -0.0305 |  | 4.052e-06 | 1.057e-05 | nan | 1 | nan | 1 | opposite direction (F worse) |

**SENSITIVITY: primary family on i9Win10 streams only (Holm over 3)** (Holm over 3)

| comparison | n | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | Holm(perm) | MWU p | Holm(MWU) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| F vs N (E2, consolidation vs plain) [i9 streams only] | 6 v 6 | +0.0235 | [+0.017, +0.031] | 0.000209 | 0.000209 | 0.002165 | 0.006494 | 0.002165 | 0.006494 | supported |
| F vs NM (E2, matched compute) [i9 streams only] | 6 v 6 | +0.0259 | [+0.019, +0.033] | 0.0001029 | 0.0002058 | 0.002165 | 0.006494 | 0.002165 | 0.006494 | supported |
| F vs R (E1, guided vs random data) [i9 streams only] | 6 v 6 | +0.0502 | [+0.045, +0.056] | 1.124e-05 | 3.371e-05 | 0.002165 | 0.006494 | 0.002165 | 0.006494 | supported |

Descriptive contrasts (no tests, 95% bootstrap CI): R-RN +0.0061 [+0.0031, +0.0096]; NM-N -0.0032 [-0.0088, +0.0021]; E1xE2 interaction (F-R)-(N-RN) +0.0173 [+0.0109, +0.0237]

**E3 transfer (final checkpoint): split score and gap to test_iid, mean [95% CI over streams]**

| arm | test_iid | test_size | test_piece | test_both | gap size | gap piece | gap both |
|---|---|---|---|---|---|---|---|
| F | 0.903 | 0.907 | 0.895 | 0.894 | +0.004 [-0.000, +0.008] | -0.008 [-0.014, -0.002] | -0.008 [-0.012, -0.004] |
| R | 0.856 | 0.855 | 0.843 | 0.845 | -0.001 [-0.004, +0.002] | -0.013 [-0.016, -0.010] | -0.012 [-0.014, -0.010] |
| RN | 0.850 | 0.847 | 0.839 | 0.838 | -0.003 [-0.007, +0.001] | -0.011 [-0.015, -0.007] | -0.012 [-0.014, -0.009] |
| NM | 0.875 | 0.880 | 0.868 | 0.869 | +0.006 [+0.001, +0.009] | -0.006 [-0.011, -0.000] | -0.006 [-0.010, -0.001] |
| N | 0.879 | 0.883 | 0.871 | 0.872 | +0.004 [+0.000, +0.007] | -0.008 [-0.012, -0.003] | -0.007 [-0.011, -0.003] |

F minus N per split (descriptive): test_iid +0.024 [+0.018, +0.031]; test_size +0.024 [+0.019, +0.029]; test_piece +0.023 [+0.016, +0.031]; test_both +0.022 [+0.016, +0.029]

**E4 improvement across iterations (checkpoints), within-stream**
- F change ckpt 0->20000: +0.1392 [+0.1338, +0.1446], n=8
- F change ckpt 2000->20000: +0.0910 [+0.0840, +0.0987], n=8
- F change ckpt 10000->20000: +0.0408 [+0.0360, +0.0454], n=8
- F stream-level slope over ckpts 2k..20k: +0.00520 per 1000 episodes [+0.00484, +0.00559], n=8
- N change ckpt 0->20000: +0.1107 [+0.1021, +0.1194], n=8
- N change ckpt 2000->20000: +0.0672 [+0.0598, +0.0752], n=8
- N change ckpt 10000->20000: +0.0341 [+0.0299, +0.0380], n=8
- N stream-level slope over ckpts 2k..20k: +0.00383 per 1000 episodes [+0.00345, +0.00424], n=8
- NM change ckpt 0->20000: +0.1075 [+0.1027, +0.1129], n=8
- NM change ckpt 2000->20000: +0.0696 [+0.0653, +0.0739], n=8
- NM change ckpt 10000->20000: +0.0223 [+0.0160, +0.0286], n=8
- NM stream-level slope over ckpts 2k..20k: +0.00400 per 1000 episodes [+0.00375, +0.00425], n=8
- R change ckpt 0->20000: +0.0894 [+0.0851, +0.0940], n=8
- R change ckpt 2000->20000: +0.0281 [+0.0242, +0.0317], n=8
- R change ckpt 10000->20000: +0.0067 [+0.0042, +0.0088], n=8
- R stream-level slope over ckpts 2k..20k: +0.00162 per 1000 episodes [+0.00145, +0.00178], n=8
- generated-data quality F (mean S1/free of training episodes per 1000-episode round): 0.698, 0.714, 0.720, 0.731, 0.744, 0.758, 0.763, 0.770, 0.778, 0.785, 0.790, 0.796, 0.800, 0.800, 0.805, 0.807, 0.813, 0.813, 0.817, 0.817
- generated-data quality R (mean S1/free of training episodes per 1000-episode round): 0.694, 0.693, 0.694, 0.693, 0.693, 0.694, 0.693, 0.691, 0.692, 0.693, 0.692, 0.693, 0.693, 0.693, 0.692, 0.694, 0.692, 0.693, 0.692, 0.692
- generated-data quality RN (mean S1/free of training episodes per 1000-episode round): 0.694, 0.693, 0.694, 0.693, 0.693, 0.694, 0.693, 0.691, 0.692, 0.693, 0.692, 0.693, 0.693, 0.693, 0.692, 0.694, 0.692, 0.693, 0.692, 0.692
- generated-data quality N (mean S1/free of training episodes per 1000-episode round): 0.693, 0.710, 0.715, 0.723, 0.739, 0.751, 0.757, 0.761, 0.766, 0.770, 0.772, 0.776, 0.777, 0.783, 0.786, 0.791, 0.793, 0.796, 0.796, 0.802
- generated-data quality NM (mean S1/free of training episodes per 1000-episode round): 0.696, 0.710, 0.716, 0.723, 0.736, 0.750, 0.760, 0.767, 0.774, 0.776, 0.780, 0.783, 0.786, 0.788, 0.786, 0.792, 0.792, 0.797, 0.796, 0.796

## hard / capped_nat  (final checkpoint 20000)

| arm | streams | 0 | 1000 | 2000 | 5000 | 10000 | 20000 | final mean [95% CI] | median | IQM | final by split (test_iid, test_size, test_piece, test_both) |
|---|---|---|---|---|---|---|---|---|---|---|
| F | 8 | 0.753 | 0.752 | 0.777 | 0.776 | 0.839 | 0.872 | 0.8717 [0.8688, 0.8752] | 0.8703 | 0.8702 | 0.878, 0.875, 0.864, 0.870 |
| R | 8 | 0.753 | 0.750 | 0.781 | 0.791 | 0.791 | 0.800 | 0.7998 [0.7978, 0.8017] | 0.7997 | 0.8002 | 0.798, 0.805, 0.786, 0.810 |
| RN | 8 | 0.756 | 0.742 | 0.759 | 0.782 | 0.783 | 0.783 | 0.7828 [0.7772, 0.7882] | 0.7818 | 0.7834 | 0.778, 0.789, 0.770, 0.793 |
| NM | 8 | 0.756 | 0.748 | 0.758 | 0.777 | 0.814 | 0.842 | 0.8420 [0.8270, 0.8546] | 0.8462 | 0.8464 | 0.841, 0.844, 0.836, 0.846 |
| N | 8 | 0.756 | 0.745 | 0.761 | 0.773 | 0.825 | 0.853 | 0.8530 [0.8451, 0.8605] | 0.8549 | 0.8543 | 0.850, 0.858, 0.846, 0.858 |

References from the EARLIER runs (not rerun, not part of the A8 tests unless stated): uniform 0.751; hand 0.888; cemhand 0.897; N (earlier baseline, seeds 2300+, n=8) 0.8613; DQN (earlier baseline, seeds 2300+, n=8) 0.7847; PPO (earlier baseline, seeds 2300+, n=8) 0.8525; F (earlier controller-ON E-run, n=8) 0.7907; NM (earlier controller-ON E-run, n=8) 0.8411; R (earlier controller-ON E-run, n=8) 0.7969; RN (earlier controller-ON E-run, n=8) 0.7889

**PRIMARY family (pre-registered)** (Holm over 3)

| comparison | n | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | Holm(perm) | MWU p | Holm(MWU) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| F vs N (E2, consolidation vs plain) | 8 v 8 | +0.0187 | [+0.011, +0.027] | 0.002601 | 0.005201 | 0.000777 | 0.000777 | 0.001865 | 0.001865 | supported |
| F vs NM (E2, matched compute) | 8 v 8 | +0.0297 | [+0.017, +0.045] | 0.005207 | 0.005207 | 0.0001554 | 0.0004662 | 0.0001554 | 0.0004662 | supported |
| F vs R (E1, guided vs random data) | 8 v 8 | +0.0719 | [+0.068, +0.076] | 3.345e-13 | 1.004e-12 | 0.0001554 | 0.0004662 | 0.0001554 | 0.0004662 | supported |

**SECONDARY family (Holm over 5)** (Holm over 5)

| comparison | n | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | Holm(perm) | MWU p | Holm(MWU) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| F vs RN | 8 v 8 | +0.0890 | [+0.083, +0.095] | 2.415e-11 | 9.658e-11 | 0.0001554 | 0.000777 | 0.0001554 | 0.000777 | supported |
| F vs DQN (earlier run, seeds 2300+) | 8 v 8 | +0.0871 | [+0.082, +0.092] | 1.723e-13 | 8.616e-13 | 0.0001554 | 0.000777 | 0.0001554 | 0.000777 | supported |
| F vs PPO (earlier run, seeds 2300+) | 8 v 8 | +0.0192 | [+0.014, +0.026] | 7.36e-05 | 7.485e-05 | 0.0001554 | 0.000777 | 0.0001554 | 0.000777 | supported |
| F vs hand (ref mean 0.888) | 8 v ref | -0.0162 |  | 3.742e-05 | 7.485e-05 | nan | 1 | nan | 1 | opposite direction (F worse) |
| F vs cemhand (ref mean 0.897) | 8 v ref | -0.0248 |  | 2.2e-06 | 6.599e-06 | nan | 1 | nan | 1 | opposite direction (F worse) |

**SENSITIVITY: primary family on i9Win10 streams only (Holm over 3)** (Holm over 3)

| comparison | n | diff (norm. units) | 95% boot CI | Welch p | Holm(Welch) | perm p | Holm(perm) | MWU p | Holm(MWU) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| F vs N (E2, consolidation vs plain) [i9 streams only] | 6 v 6 | +0.0224 | [+0.014, +0.032] | 0.003535 | 0.007071 | 0.002165 | 0.006494 | 0.002165 | 0.006494 | supported |
| F vs NM (E2, matched compute) [i9 streams only] | 6 v 6 | +0.0255 | [+0.014, +0.037] | 0.007422 | 0.007422 | 0.002165 | 0.006494 | 0.002165 | 0.006494 | supported |
| F vs R (E1, guided vs random data) [i9 streams only] | 6 v 6 | +0.0726 | [+0.068, +0.077] | 5.182e-10 | 1.555e-09 | 0.002165 | 0.006494 | 0.002165 | 0.006494 | supported |

Descriptive contrasts (no tests, 95% bootstrap CI): R-RN +0.0170 [+0.0114, +0.0229]; NM-N -0.0110 [-0.0280, +0.0043]; E1xE2 interaction (F-R)-(N-RN) +0.0016 [-0.0083, +0.0118]

**E3 transfer (final checkpoint): split score and gap to test_iid, mean [95% CI over streams]**

| arm | test_iid | test_size | test_piece | test_both | gap size | gap piece | gap both |
|---|---|---|---|---|---|---|---|
| F | 0.878 | 0.875 | 0.864 | 0.870 | -0.003 [-0.007, +0.001] | -0.014 [-0.018, -0.011] | -0.008 [-0.012, -0.004] |
| R | 0.798 | 0.805 | 0.786 | 0.810 | +0.007 [+0.002, +0.011] | -0.012 [-0.017, -0.007] | +0.012 [+0.009, +0.015] |
| RN | 0.778 | 0.789 | 0.770 | 0.793 | +0.011 [+0.006, +0.016] | -0.008 [-0.015, -0.001] | +0.015 [+0.009, +0.022] |
| NM | 0.841 | 0.844 | 0.836 | 0.846 | +0.003 [-0.002, +0.007] | -0.005 [-0.012, +0.002] | +0.005 [-0.001, +0.010] |
| N | 0.850 | 0.858 | 0.846 | 0.858 | +0.008 [+0.003, +0.013] | -0.004 [-0.008, +0.000] | +0.008 [+0.001, +0.015] |

F minus N per split (descriptive): test_iid +0.028 [+0.017, +0.039]; test_size +0.018 [+0.011, +0.024]; test_piece +0.018 [+0.008, +0.028]; test_both +0.012 [+0.001, +0.023]

**E4 improvement across iterations (checkpoints), within-stream**
- F change ckpt 0->20000: +0.1186 [+0.1146, +0.1229], n=8
- F change ckpt 2000->20000: +0.0948 [+0.0875, +0.1024], n=8
- F change ckpt 10000->20000: +0.0324 [+0.0268, +0.0383], n=8
- F stream-level slope over ckpts 2k..20k: +0.00572 per 1000 episodes [+0.00537, +0.00610], n=8
- N change ckpt 0->20000: +0.0974 [+0.0884, +0.1061], n=8
- N change ckpt 2000->20000: +0.0917 [+0.0795, +0.1028], n=8
- N change ckpt 10000->20000: +0.0278 [+0.0190, +0.0343], n=8
- N stream-level slope over ckpts 2k..20k: +0.00528 per 1000 episodes [+0.00462, +0.00587], n=8
- NM change ckpt 0->20000: +0.0863 [+0.0702, +0.1005], n=8
- NM change ckpt 2000->20000: +0.0844 [+0.0696, +0.0977], n=8
- NM change ckpt 10000->20000: +0.0285 [+0.0110, +0.0462], n=8
- NM stream-level slope over ckpts 2k..20k: +0.00464 per 1000 episodes [+0.00375, +0.00541], n=8
- R change ckpt 0->20000: +0.0467 [+0.0421, +0.0511], n=8
- R change ckpt 2000->20000: +0.0189 [+0.0131, +0.0248], n=8
- R change ckpt 10000->20000: +0.0091 [+0.0062, +0.0115], n=8
- R stream-level slope over ckpts 2k..20k: +0.00091 per 1000 episodes [+0.00063, +0.00119], n=8
- generated-data quality F (mean S1/free of training episodes per 1000-episode round): 0.676, 0.683, 0.685, 0.687, 0.694, 0.702, 0.717, 0.729, 0.741, 0.751, 0.757, 0.764, 0.768, 0.771, 0.773, 0.775, 0.779, 0.779, 0.781, 0.782
- generated-data quality R (mean S1/free of training episodes per 1000-episode round): 0.676, 0.676, 0.675, 0.678, 0.677, 0.677, 0.677, 0.676, 0.677, 0.676, 0.676, 0.678, 0.676, 0.676, 0.677, 0.676, 0.675, 0.676, 0.676, 0.676
- generated-data quality RN (mean S1/free of training episodes per 1000-episode round): 0.676, 0.676, 0.675, 0.678, 0.677, 0.677, 0.677, 0.676, 0.677, 0.676, 0.676, 0.678, 0.676, 0.676, 0.677, 0.676, 0.675, 0.676, 0.676, 0.676
- generated-data quality N (mean S1/free of training episodes per 1000-episode round): 0.673, 0.677, 0.680, 0.685, 0.690, 0.700, 0.706, 0.718, 0.726, 0.734, 0.742, 0.750, 0.751, 0.758, 0.761, 0.765, 0.769, 0.768, 0.772, 0.773
- generated-data quality NM (mean S1/free of training episodes per 1000-episode round): 0.675, 0.676, 0.677, 0.683, 0.691, 0.703, 0.711, 0.718, 0.720, 0.727, 0.734, 0.739, 0.743, 0.741, 0.747, 0.758, 0.756, 0.761, 0.763, 0.767

## Machine as a nuisance factor (final checkpoint)

| variant | arm | machine | n | mean | i9Win10 mean (n) | offset (this - i9Win10) | in units of i9Win10 SD |
|---|---|---|---|---|---|---|---|
| std | F | i7Win11B | 2 | 0.8989 | 0.8998 (6) | -0.0009 | -0.12 |
| std | R | i7Win11B | 2 | 0.8505 | 0.8496 (6) | +0.0009 | +0.52 |
| std | RN | i7Win11B | 2 | 0.8429 | 0.8440 (6) | -0.0010 | -0.20 |
| std | NM | i7Win11B | 2 | 0.8702 | 0.8739 (6) | -0.0037 | -0.63 |
| std | N | i7Win11B | 2 | 0.8760 | 0.8763 (6) | -0.0003 | -0.06 |
| hard | F | i7Win11B | 2 | 0.8684 | 0.8728 (6) | -0.0044 | -0.87 |
| hard | R | i7Win11B | 2 | 0.7986 | 0.8002 (6) | -0.0016 | -0.47 |
| hard | RN | i7Win11B | 2 | 0.7823 | 0.7829 (6) | -0.0005 | -0.06 |
| hard | NM | i7Win11B | 2 | 0.8260 | 0.8473 (6) | -0.0213 | -1.42 |
| hard | N | i7Win11B | 2 | 0.8608 | 0.8505 (6) | +0.0103 | +0.89 |

Mean offset over the 10 (arm x condition) cells: -0.0023 (SD 0.0078); one-sample t p = 0.381. Reading rule (declared in A8): machine counts as a nuisance factor if |mean offset| > 0.004 normalised units (about half a stream SD) or p < 0.05; then the i9-only sensitivity family above is the one to quote alongside the full analysis.

### Replicate streams (same arm, condition and seed run on another machine/folder; NOT used in any test)

| variant | arm | seed | replicate machine/folder | replicate score | primary score (machine) | difference |
|---|---|---|---|---|---|---|
| hard | F | 2406 | i9Win10 / results_ctrloff_i9b | 0.8774 | 0.8656 (i7Win11B) | +0.0118 |
| hard | F | 2407 | i9Win10 / results_ctrloff_i9b | 0.8709 | 0.8712 (i7Win11B) | -0.0003 |
| hard | N | 2406 | i9Win10 / results_ctrloff_i9b | 0.8652 | 0.8703 (i7Win11B) | -0.0051 |
| hard | N | 2407 | i9Win10 / results_ctrloff_i9b | 0.8572 | 0.8512 (i7Win11B) | +0.0060 |
| hard | NM | 2406 | i9Win10 / results_ctrloff_i9b | 0.8437 | 0.8520 (i7Win11B) | -0.0084 |
| hard | NM | 2407 | i9Win10 / results_ctrloff_i9b | 0.8675 | 0.7999 (i7Win11B) | +0.0675 |
| hard | R | 2406 | i9Win10 / results_ctrloff_i9b | 0.8003 | 0.8003 (i7Win11B) | +0.0000 |
| hard | R | 2407 | i9Win10 / results_ctrloff_i9b | 0.7969 | 0.7969 (i7Win11B) | +0.0000 |
| hard | RN | 2406 | i9Win10 / results_ctrloff_i9b | 0.7910 | 0.7910 (i7Win11B) | +0.0000 |
| hard | RN | 2407 | i9Win10 / results_ctrloff_i9b | 0.7737 | 0.7737 (i7Win11B) | +0.0000 |
| std | F | 2406 | i9Win10 / results_ctrloff_i9b | 0.9011 | 0.9004 (i7Win11B) | +0.0007 |
| std | F | 2407 | i9Win10 / results_ctrloff_i9b | 0.9041 | 0.8974 (i7Win11B) | +0.0067 |
| std | N | 2406 | i9Win10 / results_ctrloff_i9b | 0.8718 | 0.8812 (i7Win11B) | -0.0094 |
| std | N | 2407 | i9Win10 / results_ctrloff_i9b | 0.8627 | 0.8708 (i7Win11B) | -0.0081 |
| std | NM | 2406 | i9Win10 / results_ctrloff_i9b | 0.8589 | 0.8631 (i7Win11B) | -0.0043 |
| std | NM | 2407 | i9Win10 / results_ctrloff_i9b | 0.8574 | 0.8773 (i7Win11B) | -0.0200 |
| std | R | 2406 | i9Win10 / results_ctrloff_i9b | 0.8505 | 0.8498 (i7Win11B) | +0.0007 |
| std | R | 2407 | i9Win10 / results_ctrloff_i9b | 0.8493 | 0.8512 (i7Win11B) | -0.0018 |
| std | RN | 2406 | i9Win10 / results_ctrloff_i9b | 0.8376 | 0.8394 (i7Win11B) | -0.0018 |
| std | RN | 2407 | i9Win10 / results_ctrloff_i9b | 0.8456 | 0.8465 (i7Win11B) | -0.0009 |

Paired replicate difference (replicate - primary) over 20 streams: mean +0.0017, SD 0.0169, one-sample t p = 0.664; max |difference| 0.0675. Same reading rule as above (|mean| > 0.004 or p < 0.05 = nuisance).