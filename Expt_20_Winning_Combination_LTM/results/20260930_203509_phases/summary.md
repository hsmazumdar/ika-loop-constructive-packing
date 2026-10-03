# Expt-20 phases summary (20260930_203509)

- Phase 1 seed 20261001, Phase 2 seed 20261002, 10000 trials per arm, epsilon 0.1; LTM = `E:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_20_Winning_Combination_LTM\results\20260930_131353_run_S2default\ltm\ltm.pkl` (default ranking S2)
- total runtime 252.5s

S2 = S1/attempts is the mean piece area in the box, so it rewards the only 7-cell piece P. Read the S1 rows to judge actual packing.

## Arms

| arm | S1 mean | S1 median | S1 max | S1 top25 cutoff | S2 mean | S2 median | S2 max | S2 top25 cutoff | frac trials w/ P | mean attempts | frac S1>=85 | runtime s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phase1_uniform | 79.8703 | 80.0000 | 94.0000 | 83 | 4.7158 | 4.7059 | 5.3571 | 4.8125 | 0.4460 | 16.9562 | 0.1252 | 25.7000 |
| phase2_control_uniform_same_seeds | 79.8561 | 80.0000 | 94.0000 | 83 | 4.7185 | 4.7059 | 5.5714 | 4.8125 | 0.4582 | 16.9439 | 0.1275 | 32.2000 |
| phase2_guided | 80.7963 | 81.0000 | 95.0000 | 84 | 5.0313 | 5.0000 | 5.5385 | 5.1250 | 0.9898 | 16.0726 | 0.1844 | 46.3000 |
| phase2_ablation_single_only | 80.7603 | 81.0000 | 95.0000 | 84 | 4.9766 | 4.9412 | 5.7692 | 5.1176 | 0.8542 | 16.2538 | 0.1797 | 33.6000 |
| phase2_ablation_boost_only | 80.5593 | 81.0000 | 96.0000 | 83 | 4.9216 | 4.9375 | 5.5714 | 5.0000 | 0.8685 | 16.3843 | 0.1652 | 46.9000 |

## Paired difference (same seeds; guided/ablation minus uniform control)

| comparison | metric | mean diff | SE | 95% boot low | 95% boot high | frac better | frac worse |
|---|---|---|---|---|---|---|---|
| guided - control | S1 | 0.9402 | 0.0567 | 0.8321 | 1.0489 | 0.5315 | 0.3983 |
| guided - control | S2 | 0.3128 | 0.0020 | 0.3087 | 0.3165 | 0.9330 | 0.0537 |
| guided - control | attempts | -0.8713 | 0.0143 | -0.8986 | -0.8447 | 0.1654 | 0.6078 |
| guided - control | empty_cells | -0.9402 | 0.0567 | -1.0489 | -0.8321 | 0.3983 | 0.5315 |
| guided - control | uses_P | 0.5316 | 0.0051 | 0.5218 | 0.5417 | 0.5360 | 0.0044 |
| ablation_single_only - control | S1 | 0.9042 | 0.0564 | 0.7963 | 1.0145 | 0.5332 | 0.4006 |
| ablation_single_only - control | S2 | 0.2580 | 0.0025 | 0.2532 | 0.2626 | 0.8483 | 0.1307 |
| ablation_single_only - control | attempts | -0.6901 | 0.0148 | -0.7179 | -0.6615 | 0.2060 | 0.5501 |
| ablation_single_only - control | empty_cells | -0.9042 | 0.0564 | -1.0145 | -0.7963 | 0.4006 | 0.5332 |
| ablation_single_only - control | uses_P | 0.3960 | 0.0061 | 0.3841 | 0.4085 | 0.4612 | 0.0652 |
| ablation_boost_only - control | S1 | 0.7032 | 0.0571 | 0.5869 | 0.8164 | 0.5139 | 0.4160 |
| ablation_boost_only - control | S2 | 0.2031 | 0.0020 | 0.1989 | 0.2071 | 0.8324 | 0.1414 |
| ablation_boost_only - control | attempts | -0.5596 | 0.0145 | -0.5873 | -0.5302 | 0.2301 | 0.5184 |
| ablation_boost_only - control | empty_cells | -0.7032 | 0.0571 | -0.8164 | -0.5869 | 0.4160 | 0.5139 |
| ablation_boost_only - control | uses_P | 0.4103 | 0.0060 | 0.3982 | 0.4227 | 0.4707 | 0.0604 |

## Unpaired: Phase 2 guided minus Phase 1 (different seeds)

```json
{
 "S1": {
  "key": "S1",
  "mean_diff": 0.9260000000000019,
  "ci95_boot_low": 0.817594999999999,
  "ci95_boot_high": 1.0363075000000108
 },
 "S2": {
  "key": "S2",
  "mean_diff": 0.31553043626694866,
  "ci95_boot_low": 0.311778274018261,
  "ci95_boot_high": 0.31932592267114396
 }
}
```

## P usage transitions (control -> guided, same seeds)

```json
{"P_both": 4538, "P_control_only": 44, "P_guided_only": 5360, "P_neither": 58}
```

## Paired S1 difference by P status

```json
{
 "P_in_both": {
  "n": 4538,
  "mean_S1_diff": 0.7966064345526663
 },
 "P_guided_only": {
  "n": 5360,
  "mean_S1_diff": 1.0766791044776118
 },
 "P_control_only": {
  "n": 44,
  "mean_S1_diff": 0.7954545454545454
 },
 "P_in_neither": {
  "n": 58,
  "mean_S1_diff": -0.3275862068965517
 }
}
```

Guided share of the pooled top-25% (guided+control): by S1 0.586, by S2 0.945 (0.5 = no effect)

## STM after Phase 1: final cutoff

```json
{"n_trials": 10000, "n_top": 2500, "cutoff_S1": 77, "cutoff_S2": 4.8125}
```

### STM Phase 1 top 10: single_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| P | 2183 | 0.8732 | 2277 | 2.8762 | True |
| N | 2024 | 0.8096 | 7025 | 0.8643 | False |
| E | 1931 | 0.7724 | 5587 | 1.0369 | True |
| O | 1923 | 0.7692 | 6913 | 0.8345 | False |
| G | 1787 | 0.7148 | 5211 | 1.0288 | False |
| M | 1738 | 0.6952 | 6403 | 0.8143 | False |
| C | 1709 | 0.6836 | 4893 | 1.0478 | True |
| H | 1675 | 0.6700 | 4780 | 1.0513 | True |
| K | 1615 | 0.6460 | 4650 | 1.0419 | True |
| D | 1586 | 0.6344 | 4472 | 1.0640 | True |

### STM Phase 1 top 10: pair_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| N+P | 1820 | 0.7280 | 2170 | 2.5161 | True |
| O+P | 1731 | 0.6924 | 2137 | 2.4300 | True |
| E+P | 1652 | 0.6608 | 1597 | 3.1033 | True |
| M+P | 1562 | 0.6248 | 2027 | 2.3118 | True |
| E+N | 1549 | 0.6196 | 5218 | 0.8906 | False |
| G+P | 1525 | 0.6100 | 1472 | 3.1080 | True |
| N+O | 1521 | 0.6084 | 6446 | 0.7079 | False |
| E+O | 1481 | 0.5924 | 5129 | 0.8663 | False |
| C+P | 1468 | 0.5872 | 1371 | 3.2123 | True |
| H+P | 1425 | 0.5700 | 1324 | 3.2289 | True |

### STM Phase 1 top 10: triple_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| N+O+P | 1421 | 0.5684 | 2030 | 2.1000 | True |
| E+N+P | 1372 | 0.5488 | 1524 | 2.7008 | True |
| E+O+P | 1313 | 0.5252 | 1497 | 2.6313 | True |
| M+N+P | 1272 | 0.5088 | 1923 | 1.9844 | True |
| G+N+P | 1256 | 0.5024 | 1403 | 2.6857 | True |
| C+N+P | 1209 | 0.4836 | 1302 | 2.7857 | True |
| G+O+P | 1207 | 0.4828 | 1388 | 2.6088 | True |
| M+O+P | 1194 | 0.4776 | 1891 | 1.8942 | True |
| E+M+P | 1173 | 0.4692 | 1419 | 2.4799 | True |
| H+N+P | 1170 | 0.4680 | 1263 | 2.7791 | True |

### STM Phase 1 top 10: pair_conn_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| N+P | 909 | 0.3636 | 1164 | 2.3428 | True |
| O+P | 833 | 0.3332 | 1039 | 2.4052 | True |
| E+P | 728 | 0.2912 | 525 | 4.1600 | True |
| M+P | 720 | 0.2880 | 919 | 2.3504 | True |
| E+N | 709 | 0.2836 | 2774 | 0.7668 | False |
| E+O | 682 | 0.2728 | 2685 | 0.7620 | False |
| C+P | 677 | 0.2708 | 471 | 4.3121 | True |
| H+P | 677 | 0.2708 | 500 | 4.0620 | True |
| H+N | 666 | 0.2664 | 2556 | 0.7817 | False |
| C+N | 661 | 0.2644 | 2634 | 0.7528 | False |

### STM Phase 1 top 10: triple_conn_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| E+N+P | 420 | 0.1680 | 435 | 2.8966 | True |
| N+O+P | 417 | 0.1668 | 738 | 1.6951 | True |
| H+N+P | 394 | 0.1576 | 422 | 2.8009 | True |
| C+N+P | 394 | 0.1576 | 425 | 2.7812 | True |
| D+N+P | 378 | 0.1512 | 400 | 2.8350 | True |
| E+O+P | 378 | 0.1512 | 412 | 2.7524 | True |
| M+N+P | 377 | 0.1508 | 655 | 1.7267 | True |
| C+O+P | 358 | 0.1432 | 356 | 3.0169 | True |
| G+N+P | 352 | 0.1408 | 380 | 2.7789 | True |
| G+O+P | 350 | 0.1400 | 385 | 2.7273 | True |

## STM focus keys over snapshots (Phase 1, frac of top-25% containing key / lift)

- single_type:P: 1000: 0.904/2.81; 2000: 0.898/2.93; 3000: 0.897/2.93; 4000: 0.889/2.89; 5000: 0.885/2.86; 6000: 0.873/2.90; 7000: 0.878/2.95; 8000: 0.870/2.91; 9000: 0.874/2.89; 10000: 0.873/2.88
- pair_type:N+P: 1000: 0.752/2.51; 2000: 0.758/2.64; 3000: 0.748/2.58; 4000: 0.748/2.57; 5000: 0.738/2.51; 6000: 0.731/2.56; 7000: 0.736/2.61; 8000: 0.732/2.58; 9000: 0.731/2.55; 10000: 0.728/2.52
- pair_type:O+P: 1000: 0.708/2.40; 2000: 0.704/2.45; 3000: 0.720/2.51; 4000: 0.716/2.50; 5000: 0.707/2.46; 6000: 0.697/2.48; 7000: 0.704/2.52; 8000: 0.692/2.47; 9000: 0.696/2.46; 10000: 0.692/2.43
- pair_type:E+P: 1000: 0.668/2.96; 2000: 0.688/3.07; 3000: 0.675/3.06; 4000: 0.660/2.99; 5000: 0.659/3.01; 6000: 0.652/3.06; 7000: 0.666/3.19; 8000: 0.660/3.16; 9000: 0.662/3.12; 10000: 0.661/3.10
- triple_type:N+O+P: 1000: 0.572/2.09; 2000: 0.582/2.17; 3000: 0.585/2.16; 4000: 0.588/2.18; 5000: 0.579/2.13; 6000: 0.573/2.16; 7000: 0.581/2.20; 8000: 0.572/2.17; 9000: 0.571/2.13; 10000: 0.568/2.10
- triple_type:E+N+P: 1000: 0.532/2.49; 2000: 0.566/2.67; 3000: 0.548/2.61; 4000: 0.547/2.60; 5000: 0.542/2.60; 6000: 0.539/2.65; 7000: 0.553/2.77; 8000: 0.551/2.77; 9000: 0.551/2.73; 10000: 0.549/2.70

### STM Phase 2 guided top 10: single_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| P | 2500 | 1.0000 | 7398 | 1.0138 | True |
| B | 1904 | 0.7616 | 5608 | 1.0185 | False |
| E | 1841 | 0.7364 | 5381 | 1.0264 | False |
| H | 1803 | 0.7212 | 5354 | 1.0103 | False |
| G | 1793 | 0.7172 | 5146 | 1.0453 | True |
| C | 1791 | 0.7164 | 5366 | 1.0013 | False |
| K | 1784 | 0.7136 | 5253 | 1.0188 | False |
| D | 1653 | 0.6612 | 4865 | 1.0193 | False |
| F | 1643 | 0.6572 | 4847 | 1.0169 | False |
| A | 1642 | 0.6568 | 4651 | 1.0591 | True |

### STM Phase 2 guided top 10: pair_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| P+P | 2483 | 0.9932 | 6215 | 1.1986 | True |
| B+P | 1904 | 0.7616 | 5534 | 1.0322 | True |
| E+P | 1841 | 0.7364 | 5298 | 1.0425 | True |
| H+P | 1803 | 0.7212 | 5280 | 1.0244 | False |
| G+P | 1793 | 0.7172 | 5072 | 1.0605 | True |
| C+P | 1791 | 0.7164 | 5287 | 1.0163 | False |
| K+P | 1784 | 0.7136 | 5182 | 1.0328 | True |
| D+P | 1653 | 0.6612 | 4796 | 1.0340 | True |
| F+P | 1643 | 0.6572 | 4778 | 1.0316 | False |
| A+P | 1642 | 0.6568 | 4586 | 1.0741 | True |

### STM Phase 2 guided top 10: triple_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| B+P+P | 1890 | 0.7560 | 4600 | 1.2326 | True |
| E+P+P | 1829 | 0.7316 | 4423 | 1.2406 | True |
| H+P+P | 1789 | 0.7156 | 4407 | 1.2178 | True |
| C+P+P | 1780 | 0.7120 | 4442 | 1.2022 | True |
| G+P+P | 1777 | 0.7108 | 4237 | 1.2582 | True |
| K+P+P | 1771 | 0.7084 | 4327 | 1.2279 | True |
| D+P+P | 1641 | 0.6564 | 4002 | 1.2301 | True |
| F+P+P | 1633 | 0.6532 | 3962 | 1.2365 | True |
| A+P+P | 1629 | 0.6516 | 3827 | 1.2770 | True |
| N+P+P | 1610 | 0.6440 | 5578 | 0.8659 | False |

### STM Phase 2 guided top 10: triple_conn_type

| key | n_top | frac_top | n_bottom | lift_vs_bottom | winning |
|---|---|---|---|---|---|
| B+H+P | 527 | 0.2108 | 1230 | 1.2854 | True |
| H+P+P | 512 | 0.2048 | 843 | 1.8221 | True |
| B+P+P | 507 | 0.2028 | 770 | 1.9753 | True |
| K+P+P | 500 | 0.2000 | 766 | 1.9582 | True |
| C+H+P | 500 | 0.2000 | 1231 | 1.2185 | True |
| B+K+P | 497 | 0.1988 | 1092 | 1.3654 | True |
| C+P+P | 495 | 0.1980 | 785 | 1.8917 | True |
| B+C+P | 494 | 0.1976 | 1202 | 1.2329 | True |
| C+K+P | 492 | 0.1968 | 1145 | 1.2891 | True |
| G+K+P | 480 | 0.1920 | 1056 | 1.3636 | True |