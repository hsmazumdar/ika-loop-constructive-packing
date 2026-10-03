# POST-HOC DIAGNOSTICS (DESIGN.md amendment A7) - descriptive, not pre-registered, no significance claims
Score = mean over the four test splits of normalised to ref (S1/ref); per-unit values then averaged over seeds (n = seeds). Legacy-problem units (D2L) use the single 10x10 A-P problem.


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