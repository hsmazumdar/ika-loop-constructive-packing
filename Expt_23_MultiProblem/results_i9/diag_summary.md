# POST-HOC DIAGNOSTICS (DESIGN.md amendment A7) - descriptive, not pre-registered, no significance claims
Score = mean over the four test splits of normalised to ref (S1/ref); per-unit values then averaged over seeds (n = seeds). Legacy-problem units (D2L) use the single 10x10 A-P problem.


## D1

### D1 / F / hard  (seeds 2300,2301,2302,2303; final checkpoint 20000)

| ckpt | fast t0.05 | fast t0.1 | fast t0.25 noconc | fast t0.25 | fast t0.5 | fast t1.0 | slow t0.05 | slow t0.1 | slow t0.25 noconc | slow t0.25 | slow t0.5 | slow t1.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | - | - | - | 0.753 (0.750-0.757) | - | - | - | - | - | 0.753 (0.750-0.757) | - | - |
| 1000 | - | - | - | 0.766 (0.750-0.777) | - | - | - | - | - | 0.754 (0.749-0.758) | - | - |
| 2000 | - | - | - | 0.785 (0.770-0.798) | - | - | - | - | - | 0.781 (0.775-0.788) | - | - |
| 5000 | 0.774 (0.768-0.781) | 0.774 (0.770-0.780) | 0.770 (0.769-0.773) | 0.771 (0.770-0.773) | 0.766 (0.763-0.767) | 0.762 (0.760-0.764) | 0.781 (0.772-0.791) | 0.779 (0.772-0.787) | 0.778 (0.770-0.785) | 0.777 (0.768-0.785) | 0.771 (0.768-0.774) | 0.762 (0.757-0.766) |
| 10000 | 0.788 (0.780-0.798) | 0.787 (0.780-0.794) | 0.783 (0.773-0.792) | 0.782 (0.774-0.789) | 0.775 (0.768-0.782) | 0.767 (0.760-0.772) | 0.785 (0.777-0.790) | 0.784 (0.777-0.788) | 0.783 (0.778-0.788) | 0.783 (0.776-0.789) | 0.775 (0.770-0.782) | 0.767 (0.766-0.769) |
| 20000 | 0.793 (0.781-0.799) | 0.793 (0.782-0.797) | 0.790 (0.780-0.794) | 0.791 (0.781-0.796) | 0.780 (0.770-0.785) | 0.770 (0.764-0.773) | 0.793 (0.788-0.798) | 0.795 (0.792-0.798) | 0.793 (0.790-0.795) | 0.793 (0.791-0.794) | 0.782 (0.779-0.783) | 0.771 (0.766-0.774) |

### D1 / F / std  (seeds 2300,2301,2302,2303; final checkpoint 20000)

| ckpt | fast t0.05 | fast t0.1 | fast t0.25 noconc | fast t0.25 | fast t0.5 | fast t1.0 | slow t0.05 | slow t0.1 | slow t0.25 noconc | slow t0.25 | slow t0.5 | slow t1.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | - | - | - | 0.759 (0.753-0.766) | - | - | - | - | - | 0.759 (0.753-0.766) | - | - |
| 1000 | - | - | - | 0.818 (0.808-0.829) | - | - | - | - | - | 0.795 (0.778-0.807) | - | - |
| 2000 | - | - | - | 0.815 (0.811-0.820) | - | - | - | - | - | 0.814 (0.810-0.821) | - | - |
| 5000 | 0.830 (0.826-0.833) | 0.829 (0.827-0.831) | 0.821 (0.816-0.827) | 0.820 (0.816-0.826) | 0.809 (0.805-0.813) | 0.792 (0.789-0.797) | 0.831 (0.827-0.835) | 0.831 (0.828-0.836) | 0.825 (0.822-0.828) | 0.824 (0.821-0.829) | 0.813 (0.811-0.814) | 0.796 (0.794-0.797) |
| 10000 | 0.834 (0.829-0.846) | 0.833 (0.829-0.842) | 0.828 (0.821-0.837) | 0.828 (0.821-0.836) | 0.814 (0.807-0.821) | 0.798 (0.792-0.802) | 0.835 (0.830-0.841) | 0.834 (0.831-0.838) | 0.828 (0.824-0.832) | 0.827 (0.824-0.831) | 0.814 (0.812-0.817) | 0.798 (0.796-0.800) |
| 20000 | 0.847 (0.840-0.851) | 0.845 (0.841-0.849) | 0.837 (0.834-0.842) | 0.835 (0.833-0.839) | 0.820 (0.816-0.825) | 0.800 (0.796-0.803) | 0.851 (0.847-0.855) | 0.850 (0.846-0.856) | 0.841 (0.837-0.844) | 0.841 (0.835-0.846) | 0.824 (0.821-0.827) | 0.803 (0.799-0.805) |

Main-run reference (same variant, 20k episodes, all available seeds; slow net, tau 0.25):
- F / hard: mean 0.791 (n=8; min 0.788, max 0.793)
- F / std: mean 0.841 (n=8; min 0.838, max 0.845)
- N / hard: mean 0.861 (n=8; min 0.853, max 0.869)
- N / std: mean 0.879 (n=8; min 0.871, max 0.890)
- NM / hard: mean 0.841 (n=8; min 0.805, max 0.858)
- NM / std: mean 0.869 (n=8; min 0.855, max 0.882)
- R / hard: mean 0.797 (n=8; min 0.793, max 0.803)
- R / std: mean 0.848 (n=8; min 0.842, max 0.852)
- RN / hard: mean 0.789 (n=8; min 0.769, max 0.802)
- RN / std: mean 0.842 (n=8; min 0.828, max 0.856)

## D2

### D2 / F_w64 / std  (seeds 2300,2301,2302,2303,2304,2305,2306,2307; final checkpoint 20000)

| ckpt | fast t0.1 | fast t0.25 | fast t0.5 | slow t0.1 | slow t0.25 | slow t0.5 |
|---|---|---|---|---|---|---|
| 0 | - | 0.762 (0.755-0.769) | - | - | 0.762 (0.755-0.769) | - |
| 1000 | - | 0.817 (0.807-0.824) | - | - | 0.782 (0.767-0.798) | - |
| 2000 | - | 0.821 (0.811-0.832) | - | - | 0.815 (0.805-0.828) | - |
| 5000 | - | 0.815 (0.808-0.821) | - | - | 0.818 (0.811-0.826) | - |
| 10000 | - | 0.829 (0.825-0.833) | - | - | 0.827 (0.823-0.831) | - |
| 20000 | 0.849 (0.834-0.863) | 0.843 (0.831-0.862) | 0.829 (0.816-0.857) | 0.855 (0.847-0.867) | 0.847 (0.841-0.860) | 0.834 (0.826-0.852) |

Main-run reference (same variant, 20k episodes, all available seeds; slow net, tau 0.25):
- F / std: mean 0.841 (n=8; min 0.838, max 0.845)
- N / std: mean 0.879 (n=8; min 0.871, max 0.890)
- NM / std: mean 0.869 (n=8; min 0.855, max 0.882)
- R / std: mean 0.848 (n=8; min 0.842, max 0.852)
- RN / std: mean 0.842 (n=8; min 0.828, max 0.856)

## D2L

### D2L / F / legacy  (seeds 2300,2301,2302,2303; final checkpoint 20000)

| ckpt | fast t0.1 | fast t0.25 | fast t0.5 | slow t0.1 | slow t0.25 | slow t0.5 |
|---|---|---|---|---|---|---|
| 0 | - | 0.726 (0.719-0.734) | - | - | 0.726 (0.719-0.734) | - |
| 1000 | - | 0.782 (0.772-0.793) | - | - | 0.759 (0.754-0.768) | - |
| 2000 | - | 0.841 (0.828-0.853) | - | - | 0.818 (0.813-0.825) | - |
| 5000 | - | 0.883 (0.874-0.891) | - | - | 0.883 (0.878-0.888) | - |
| 10000 | - | 0.893 (0.890-0.896) | - | - | 0.894 (0.888-0.899) | - |
| 20000 | 0.927 (0.922-0.930) | 0.912 (0.906-0.917) | 0.845 (0.841-0.854) | 0.924 (0.918-0.930) | 0.909 (0.906-0.915) | 0.844 (0.839-0.846) |

### D2L / F_w64 / legacy  (seeds 2300,2301,2302,2303; final checkpoint 20000)

| ckpt | fast t0.1 | fast t0.25 | fast t0.5 | slow t0.1 | slow t0.25 | slow t0.5 |
|---|---|---|---|---|---|---|
| 0 | - | 0.726 (0.723-0.731) | - | - | 0.726 (0.723-0.731) | - |
| 1000 | - | 0.770 (0.757-0.785) | - | - | 0.748 (0.743-0.754) | - |
| 2000 | - | 0.833 (0.816-0.860) | - | - | 0.810 (0.800-0.821) | - |
| 5000 | - | 0.882 (0.876-0.890) | - | - | 0.885 (0.881-0.887) | - |
| 10000 | - | 0.892 (0.879-0.898) | - | - | 0.892 (0.888-0.896) | - |
| 20000 | 0.924 (0.917-0.933) | 0.910 (0.904-0.918) | 0.843 (0.835-0.849) | 0.922 (0.918-0.927) | 0.910 (0.905-0.920) | 0.848 (0.841-0.852) |

## D3

### D3 / F_s1000 / std  (seeds 2300,2301,2302,2303; final checkpoint 20000)

| ckpt | fast t0.1 | fast t0.25 | fast t0.5 | slow t0.1 | slow t0.25 | slow t0.5 |
|---|---|---|---|---|---|---|
| 0 | - | 0.759 (0.753-0.766) | - | - | 0.759 (0.753-0.766) | - |
| 1000 | - | 0.811 (0.809-0.815) | - | - | 0.765 (0.759-0.770) | - |
| 2000 | - | 0.819 (0.812-0.826) | - | - | 0.779 (0.767-0.790) | - |
| 5000 | - | 0.816 (0.809-0.821) | - | - | 0.809 (0.805-0.813) | - |
| 10000 | - | 0.825 (0.818-0.832) | - | - | 0.823 (0.820-0.824) | - |
| 20000 | 0.862 (0.849-0.875) | 0.860 (0.847-0.871) | 0.847 (0.839-0.858) | 0.858 (0.849-0.870) | 0.852 (0.841-0.861) | 0.840 (0.832-0.848) |

### D3 / F_s200 / std  (seeds 2300,2301,2302,2303; final checkpoint 20000)

| ckpt | fast t0.1 | fast t0.25 | fast t0.5 | slow t0.1 | slow t0.25 | slow t0.5 |
|---|---|---|---|---|---|---|
| 0 | - | 0.759 (0.753-0.766) | - | - | 0.759 (0.753-0.766) | - |
| 1000 | - | 0.818 (0.808-0.829) | - | - | 0.795 (0.778-0.807) | - |
| 2000 | - | 0.815 (0.811-0.820) | - | - | 0.814 (0.810-0.821) | - |
| 5000 | - | 0.824 (0.818-0.828) | - | - | 0.822 (0.816-0.827) | - |
| 10000 | - | 0.832 (0.829-0.838) | - | - | 0.827 (0.823-0.831) | - |
| 20000 | 0.854 (0.847-0.867) | 0.847 (0.839-0.864) | 0.834 (0.823-0.852) | 0.855 (0.847-0.868) | 0.847 (0.838-0.864) | 0.833 (0.824-0.849) |

Main-run reference (same variant, 20k episodes, all available seeds; slow net, tau 0.25):
- F / std: mean 0.841 (n=8; min 0.838, max 0.845)
- N / std: mean 0.879 (n=8; min 0.871, max 0.890)
- NM / std: mean 0.869 (n=8; min 0.855, max 0.882)
- R / std: mean 0.848 (n=8; min 0.842, max 0.852)
- RN / std: mean 0.842 (n=8; min 0.828, max 0.856)

## D4

### D4 / F_nometa / hard  (seeds 2300,2301,2302,2303,2304,2305,2306,2307; final checkpoint 20000)

| ckpt | fast t0.1 | fast t0.25 | fast t0.5 | slow t0.1 | slow t0.25 | slow t0.5 |
|---|---|---|---|---|---|---|
| 0 | - | 0.753 (0.750-0.758) | - | - | 0.753 (0.750-0.758) | - |
| 1000 | - | 0.770 (0.756-0.793) | - | - | 0.756 (0.746-0.768) | - |
| 2000 | - | 0.779 (0.773-0.786) | - | - | 0.776 (0.764-0.786) | - |
| 5000 | - | 0.778 (0.766-0.790) | - | - | 0.777 (0.764-0.788) | - |
| 10000 | - | 0.838 (0.812-0.855) | - | - | 0.836 (0.807-0.859) | - |
| 20000 | 0.868 (0.862-0.875) | 0.867 (0.861-0.874) | 0.861 (0.855-0.869) | 0.872 (0.862-0.879) | 0.870 (0.861-0.879) | 0.863 (0.856-0.869) |

### D4 / F_nometa / std  (seeds 2300,2301,2302,2303,2304,2305,2306,2307; final checkpoint 20000)

| ckpt | fast t0.1 | fast t0.25 | fast t0.5 | slow t0.1 | slow t0.25 | slow t0.5 |
|---|---|---|---|---|---|---|
| 0 | - | 0.759 (0.753-0.766) | - | - | 0.759 (0.753-0.766) | - |
| 1000 | - | 0.817 (0.811-0.820) | - | - | 0.794 (0.774-0.811) | - |
| 2000 | - | 0.819 (0.816-0.822) | - | - | 0.815 (0.810-0.820) | - |
| 5000 | - | 0.822 (0.815-0.830) | - | - | 0.821 (0.817-0.830) | - |
| 10000 | - | 0.857 (0.846-0.870) | - | - | 0.855 (0.848-0.868) | - |
| 20000 | 0.896 (0.883-0.906) | 0.893 (0.885-0.904) | 0.881 (0.873-0.892) | 0.897 (0.883-0.908) | 0.892 (0.883-0.903) | 0.881 (0.873-0.888) |

Main-run reference (same variant, 20k episodes, all available seeds; slow net, tau 0.25):
- F / hard: mean 0.791 (n=8; min 0.788, max 0.793)
- F / std: mean 0.841 (n=8; min 0.838, max 0.845)
- N / hard: mean 0.861 (n=8; min 0.853, max 0.869)
- N / std: mean 0.879 (n=8; min 0.871, max 0.890)
- NM / hard: mean 0.841 (n=8; min 0.805, max 0.858)
- NM / std: mean 0.869 (n=8; min 0.855, max 0.882)
- R / hard: mean 0.797 (n=8; min 0.793, max 0.803)
- R / std: mean 0.848 (n=8; min 0.842, max 0.852)
- RN / hard: mean 0.789 (n=8; min 0.769, max 0.802)
- RN / std: mean 0.842 (n=8; min 0.828, max 0.856)

## Meta-controller state at checkpoints (mean over units; tau, eps, lr, sleep_every, hidden, concepts)
- D1 F hard ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D1 F hard ckpt 1000: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D1 F hard ckpt 2000: tau 1.76, eps 0.088, lr 0.001, sleep_every 215, hidden 128, concepts 1.5
- D1 F hard ckpt 5000: tau 1.2, eps 0.06, lr 0.001, sleep_every 286, hidden 128, concepts 17.5
- D1 F hard ckpt 10000: tau 1.24, eps 0.0704, lr 0.000754, sleep_every 400, hidden 128, concepts 40.8
- D1 F hard ckpt 20000: tau 1.12, eps 0.0759, lr 0.000506, sleep_every 400, hidden 128, concepts 87
- D1 F std ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D1 F std ckpt 1000: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D1 F std ckpt 2000: tau 1.76, eps 0.088, lr 0.00103, sleep_every 220, hidden 128, concepts 7.25
- D1 F std ckpt 5000: tau 1.36, eps 0.0698, lr 0.0012, sleep_every 293, hidden 128, concepts 28.5
- D1 F std ckpt 10000: tau 1.09, eps 0.0596, lr 0.00124, sleep_every 400, hidden 128, concepts 67.5
- D1 F std ckpt 20000: tau 1.17, eps 0.0821, lr 0.00086, sleep_every 400, hidden 128, concepts 139
- D2 F_w64 std ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 64, concepts 0
- D2 F_w64 std ckpt 1000: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 64, concepts 0
- D2 F_w64 std ckpt 2000: tau 1.76, eps 0.088, lr 0.00103, sleep_every 220, hidden 64, concepts 4
- D2 F_w64 std ckpt 5000: tau 1.26, eps 0.0635, lr 0.00114, sleep_every 293, hidden 64, concepts 26.9
- D2 F_w64 std ckpt 10000: tau 0.917, eps 0.0484, lr 0.00121, sleep_every 400, hidden 64, concepts 56
- D2 F_w64 std ckpt 20000: tau 0.752, eps 0.0483, lr 0.00126, sleep_every 400, hidden 64, concepts 119
- D2L F legacy ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D2L F legacy ckpt 1000: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D2L F legacy ckpt 2000: tau 1.76, eps 0.088, lr 0.001, sleep_every 220, hidden 128, concepts 11.8
- D2L F legacy ckpt 5000: tau 1.2, eps 0.06, lr 0.001, sleep_every 293, hidden 128, concepts 28.5
- D2L F legacy ckpt 10000: tau 0.633, eps 0.0316, lr 0.00103, sleep_every 400, hidden 128, concepts 72.5
- D2L F legacy ckpt 20000: tau 0.28, eps 0.013, lr 0.000771, sleep_every 400, hidden 128, concepts 119
- D2L F_w64 legacy ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 64, concepts 0
- D2L F_w64 legacy ckpt 1000: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 64, concepts 0.5
- D2L F_w64 legacy ckpt 2000: tau 1.76, eps 0.088, lr 0.001, sleep_every 220, hidden 64, concepts 11.5
- D2L F_w64 legacy ckpt 5000: tau 1.2, eps 0.06, lr 0.001, sleep_every 293, hidden 64, concepts 34.8
- D2L F_w64 legacy ckpt 10000: tau 0.649, eps 0.0325, lr 0.001, sleep_every 400, hidden 64, concepts 61.5
- D2L F_w64 legacy ckpt 20000: tau 0.322, eps 0.0149, lr 0.000693, sleep_every 400, hidden 64, concepts 104
- D3 F_s1000 std ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 1e+03, hidden 128, concepts 0
- D3 F_s1000 std ckpt 1000: tau 2, eps 0.1, lr 0.001, sleep_every 1e+03, hidden 128, concepts 15.2
- D3 F_s1000 std ckpt 2000: tau 1.76, eps 0.088, lr 0.00103, sleep_every 1e+03, hidden 128, concepts 15.2
- D3 F_s1000 std ckpt 5000: tau 1.2, eps 0.06, lr 0.00119, sleep_every 1e+03, hidden 128, concepts 15.2
- D3 F_s1000 std ckpt 10000: tau 0.633, eps 0.0316, lr 0.00159, sleep_every 1e+03, hidden 128, concepts 47.8
- D3 F_s1000 std ckpt 20000: tau 0.308, eps 0.0156, lr 0.00224, sleep_every 1e+03, hidden 128, concepts 95.2
- D3 F_s200 std ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D3 F_s200 std ckpt 1000: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D3 F_s200 std ckpt 2000: tau 1.76, eps 0.088, lr 0.00103, sleep_every 200, hidden 128, concepts 7.25
- D3 F_s200 std ckpt 5000: tau 1.2, eps 0.06, lr 0.00124, sleep_every 200, hidden 128, concepts 14.2
- D3 F_s200 std ckpt 10000: tau 1.05, eps 0.0582, lr 0.00129, sleep_every 200, hidden 128, concepts 55
- D3 F_s200 std ckpt 20000: tau 0.725, eps 0.0467, lr 0.00148, sleep_every 200, hidden 128, concepts 125
- D4 F_nometa hard ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D4 F_nometa hard ckpt 1000: tau 1.65, eps 0.082, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D4 F_nometa hard ckpt 2000: tau 1.3, eps 0.064, lr 0.001, sleep_every 200, hidden 128, concepts 2.38
- D4 F_nometa hard ckpt 5000: tau 0.25, eps 0.01, lr 0.001, sleep_every 200, hidden 128, concepts 14.6
- D4 F_nometa hard ckpt 10000: tau 0.25, eps 0.01, lr 0.001, sleep_every 200, hidden 128, concepts 35.5
- D4 F_nometa hard ckpt 20000: tau 0.25, eps 0.01, lr 0.001, sleep_every 200, hidden 128, concepts 136
- D4 F_nometa std ckpt 0: tau 2, eps 0.1, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D4 F_nometa std ckpt 1000: tau 1.65, eps 0.082, lr 0.001, sleep_every 200, hidden 128, concepts 0
- D4 F_nometa std ckpt 2000: tau 1.3, eps 0.064, lr 0.001, sleep_every 200, hidden 128, concepts 4.62
- D4 F_nometa std ckpt 5000: tau 0.25, eps 0.01, lr 0.001, sleep_every 200, hidden 128, concepts 17.1
- D4 F_nometa std ckpt 10000: tau 0.25, eps 0.01, lr 0.001, sleep_every 200, hidden 128, concepts 68.5
- D4 F_nometa std ckpt 20000: tau 0.25, eps 0.01, lr 0.001, sleep_every 200, hidden 128, concepts 173

## D1 reproduction check (retrained stream vs main-run stream, identical numbers expected)
- D1_F_hard_capped_nat_s2300: main-run file found=True, all evaluations identical=False, training outcomes identical=False
- D1_F_hard_capped_nat_s2301: main-run file found=True, all evaluations identical=True, training outcomes identical=True
- D1_F_hard_capped_nat_s2302: main-run file found=True, all evaluations identical=False, training outcomes identical=False
- D1_F_hard_capped_nat_s2303: main-run file found=True, all evaluations identical=False, training outcomes identical=False
- D1_F_std_capped_nat_s2300: main-run file found=True, all evaluations identical=False, training outcomes identical=False
- D1_F_std_capped_nat_s2301: main-run file found=True, all evaluations identical=False, training outcomes identical=False
- D1_F_std_capped_nat_s2302: main-run file found=True, all evaluations identical=False, training outcomes identical=False
- D1_F_std_capped_nat_s2303: main-run file found=True, all evaluations identical=False, training outcomes identical=False