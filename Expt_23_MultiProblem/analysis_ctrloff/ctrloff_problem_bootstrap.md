# A8 problem-resampling (hierarchical bootstrap) - descriptive, after-the-fact

Specified in DESIGN.md section 6 (second analysis: streams, then problems); not implemented in analyze_ctrloff.py; computed after the A8 verdict (3 Oct 2026 IST). Does not change the A8 decision rule or verdict.

Primary streams only (i9 seeds 2400-2405 + i7 seeds 2406-2407), final checkpoint 20,000, 4 splits x 50 problems (3 repeats averaged per problem). B = 20000, 95% percentile intervals, seed 20261003.

| variant | contrast | n | point diff | CI streams only | CI problems only | CI hierarchical | share of hierarchical draws with F higher |
|---|---|---|---|---|---|---|---|
| std | F vs N | 8 v 8 | +0.0234 | [+0.0179, +0.0292] | [+0.0213, +0.0255] | [+0.0173, +0.0298] | 1.0000 |
| std | F vs NM | 8 v 8 | +0.0266 | [+0.0207, +0.0328] | [+0.0244, +0.0289] | [+0.0199, +0.0334] | 1.0000 |
| std | F vs R | 8 v 8 | +0.0498 | [+0.0455, +0.0544] | [+0.0463, +0.0534] | [+0.0440, +0.0560] | 1.0000 |
| hard | F vs N | 8 v 8 | +0.0187 | [+0.0106, +0.0272] | [+0.0159, +0.0215] | [+0.0097, +0.0281] | 1.0000 |
| hard | F vs NM | 8 v 8 | +0.0297 | [+0.0168, +0.0446] | [+0.0267, +0.0326] | [+0.0160, +0.0453] | 1.0000 |
| hard | F vs R | 8 v 8 | +0.0719 | [+0.0683, +0.0760] | [+0.0668, +0.0770] | [+0.0652, +0.0788] | 1.0000 |
