# Measured difference after the cap reserve

Same seeds and task schedule as `20260929_100457_diagnostic_baseline_policy`. The only policy change is the cheap-scan reserve. The config omits `cheap_scan_reserve`, so the reserve is one catalogue pass, 3636 evaluations. Deliberation stops at 46,364. UCB and delayed THINK credit were not retuned.

416 of 416 boxes finished. Every box still ends on `compute_budget`. Think-batch evaluations top out at 46,364. Hierarchical and flat boxes each take one cheap legal primitive (104/104 and 104/104). Hierarchical boxes with zero physical actions fall from 41 to 0.

| mode | seed | phase | final mean | physical mean | macros / box |
| --- | --- | --- | --- | --- | --- |
| hierarchical_library | 11 | train | 5.88 → 14.07 | 1.23 → 2.95 | 0.100 → 0.050 |
| hierarchical_library | 11 | eval | 0.00 → 13.83 | 0.00 → 2.83 | 0.000 → 0.000 |
| hierarchical_library | 22 | train | 11.00 → 16.15 | 2.33 → 3.40 | 0.050 → 0.050 |
| hierarchical_library | 22 | eval | 17.67 → 22.17 | 3.67 → 4.58 | 0.000 → 0.000 |
| flat_library | both | both | 26.17 → 30.39 overall | 5.45 → 6.29 | 1.163 → 0.923 |
| primitive | both | both | about 65–67, within 0.3 | about 13.9 | 0 |

The higher hierarchical scores are occupied cells from placements the old cap skipped, including that one reserved primitive. They are not a better packing policy. Macro use fell. There is no `think_outcome` in this run, so the seed-11 selector does not keep the 0.374 credit seen in the diagnostic. Think is still the most chosen arm (108 think, 96 primitive, 95 stm, 45 ltm): with exploration 0.5, an unseen arm's bonus stays above ltm's mean of 0.096. No operation of depth above 1 has positive real utility. Evidence level remains 2.

This does not show improved packing, a useful hierarchy, or amortized discovery cost.
