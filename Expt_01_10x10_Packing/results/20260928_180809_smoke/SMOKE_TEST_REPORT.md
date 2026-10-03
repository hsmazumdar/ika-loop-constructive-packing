# SMOKE_TEST_REPORT — MGA Expt-1

- Run directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_01_10x10_Packing\results\20260928_180809_smoke`
- Preset: `smoke`
- Partial: `False`
- Wall time (s): `2276.5`
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Config hash: `d3ac29ef6b9424b4b8c85f9301c46b8bbc99e5a0a720e46d8b533e339d7288a1`
- Source hash: `dd022d5d8d0f955755f80aa75fb6aada5d94c43442041e026c4f896b40a5553a`

## Commands

```powershell
.\.venv\Scripts\python -m pytest -q --junitxml=results/tests.xml
.\.venv\Scripts\python validate_catalogue.py --output results/catalogue_validation.json
.\.venv\Scripts\python run_experiment.py --config configs/default.json --preset smoke
.\.venv\Scripts\python run_gui.py
```

## Episode counts

- Rows: 1560; modes=['both', 'ltm', 'none', 'stm']; seeds=[np.int64(11), np.int64(22), np.int64(33)]; phases=['eval', 'train']

## Summary (seed-level means, then averaged)

mode,phase,seeds_completed,train_or_eval_boxes,mean_terminal_score,seed_score_std,perfect_box_fraction,mean_actions,mean_undos,ltm_hit_fraction,mean_serialized_memory_bytes,perfect_per_1000_actions,wall_time_seconds
both,eval,3,90,91.0,1.0596994682281224,0.044444444444444446,97.16666666666667,40.9,0.032899659267330676,272534.6666666667,0.4680514005538063,137.86422739999398
both,train,3,300,90.65666666666668,0.5431594813884952,0.016666666666666666,98.62666666666667,41.65,0.017119609090794626,141030.70666666667,0.16975379616922728,456.8343502000098
ltm,eval,3,90,91.36666666666667,0.7845734863959903,0.011111111111111112,99.07777777777778,41.666666666666664,0.028825848943899193,100373.66666666667,0.11427265455376528,130.47466670000358
ltm,train,3,300,90.54333333333334,1.1476449315397546,0.0033333333333333335,99.72333333333334,42.123333333333335,0.017677799388220835,53222.81,0.033612315552418406,437.2267829000084
none,eval,3,90,90.95555555555556,0.6590303389483073,0.011111111111111112,99.07777777777778,41.87777777777777,0.0,0.0,0.11427265455376528,126.27815429999828
none,train,3,300,91.36333333333334,0.20997354330698376,0.013333333333333334,98.89333333333333,41.71,0.0,0.0,0.13615877334609353,418.28034079998906
stm,eval,3,90,90.3888888888889,0.06849348892187977,0.03333333333333333,97.23333333333333,40.922222222222224,0.0,0.0,0.3635041802980734,130.2624978999811
stm,train,3,300,89.95333333333333,0.3886157771143911,0.016666666666666666,98.64,41.74,0.0,0.0,0.16974024418230968,430.07218109999303


## Did memory help?

Mean terminal score by mode:
- `ltm`: 91.367
- `both`: 91.000
- `none`: 90.956
- `stm`: 90.389

LTM lookups=3474108, hits=107695, hit fraction=0.0310.
Nonempty memory with ~zero useful retrieval is not evidence that memory helped.

## Verdict

No detectable improvement: mode means differ by less than 1 occupied cell. Three seeds are a smoke check, not statistical significance.

## Limitations

- Repeated empty 10×10 boxes test practice on the same task, not transfer.
- The heuristic is engineered; hole-avoidance is a shared filter, not learned intelligence.
- GUI mouse-click verification is separate from this batch run.
