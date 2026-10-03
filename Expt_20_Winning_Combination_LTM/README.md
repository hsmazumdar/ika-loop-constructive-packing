# Expt-20 - Winning-combination long-term memory (LTM)

Phase 1 only. Fill the 10x10 box 10,000 times with random legal placements, score each box, keep the top 25%, and record which pieces, pairs and triples are over-represented there. The result is stored as an LTM file for a later phase. **That later phase (filling the box with the winning combinations) is not built here.**

Uses the Expt-1 environment (`mga.environment.PackingEnv`, `Action`, 16-piece catalogue A-P). No existing experiment folder is modified.

## Trial
Fresh `PackingEnv()`. Repeat: list `legal_placements()`, pick one uniformly with `random.Random(seed*1_000_000 + trial_id)`, `step(Action.place_from(p))`, until no legal placement remains. Default seed 20260930, 10,000 trials. Every trial is independently replayable from its seed, and its placements are recorded in `trials.csv`.

## Scores
- **S1** = 100 - empty cells (counted from the grid). The run asserts every trial that this equals `env.occupied`.
- **S2** = S1 / attempts, `attempts = env.placements_count` (accepted placements = number of pieces). Every attempt is a legal placement, so there are no rejected attempts. S2 is therefore the mean piece area in the box; it is not independent of which pieces were used (P has 7 cells, M/N/O have 4).

## Ranking and top 25% (both saved)
| ranking | sort | status |
|---|---|---|
| **S2** | S2 desc, tie-break S1 desc, then trial_id asc | **DEFAULT / primary** (user decision) |
| S1 | S1 desc, tie-break S2 desc, then trial_id asc | secondary, kept and labelled |

Top 25% = first 2,500 trials of each ranking (`top25_by_S2.csv` is the default, `top25_by_S1.csv` the secondary). The LTM files carry `default_ranking = "S2"`; the S1 variant sits under `ltm["S1"]` and is labelled secondary. S1 takes few integer values and S2 is a ratio of small integers, so many trials tie at the boundary; the tie-break then the trial_id decide who is in. Boundary tie counts are in `distribution_summary.json` and `summary.md`. "Bottom" = the other 75% of the same ranking.

Note: S2 = mean piece area in the box, so the S2 ranking favours boxes that contain the large 7-cell piece P. That is inherent to S2 as defined.

## What a "piece" and a "combination" are
- **Piece** = piece type id (A-P). A finer variant, `single_oriented`, is (type, canonical rotation). Board position is ignored.
- **Combination** = an unordered multiset of piece types among one trial's placements. `{A,A,B}` needs two or more A and one B in that trial. Positions and order are ignored. Kinds `pair_type`, `triple_type`.
- **Connected combination** = the same, but the pieces must form an edge-connected group (a cell of one is a 4-neighbour of a cell of another), like the Expt-17 connected groups. Kinds `pair_conn_type`, `triple_conn_type`. Oriented versions `pair_conn_oriented`, `triple_conn_oriented` keep `(type, rotation, dx, dy)` after translation-normalising by the group's minimum cell (as Expt-17; no rotation or reflection of the whole group).
- **Counted once per trial**: a key either occurs in a trial or not.
- Columns: `n_top`, `n_bottom`, `n_all`; `frac_top = n_top / n_top_trials`; `frac_bottom`; `frac_all`; `lift_vs_bottom = frac_top / frac_bottom`; `lift_vs_all = frac_top / frac_all`; `z` = two-proportion z (top vs bottom).
- **`winning` flag** = `n_top >= 25` and `lift_vs_bottom > 1` and `z >= 1.96` (or absent from the bottom with `n_top >= 25`). Tables are sorted by `n_top` (highest frequency first), not by lift, so a frequent combination can appear with lift near 1 and `winning = False`. Frequency alone does not mean winning.
- The flag is a screening rule, not a corrected hypothesis test: many keys are tested and keys within one trial overlap.

## Layout
```
run_expt20.py            entry (runs the unit tests first unless --skip-validation)
src/config.py trials.py extract.py ltm.py
tests/test_expt20.py     extraction logic and trials
results/<timestamp>_run/
  trials.csv  top25_by_S2.csv (default)  top25_by_S1.csv (secondary)
  frequency_tables/rank_S2 (default)|rank_S1 (secondary)/<kind>.csv
  ltm/ltm.json  ltm/ltm.pkl  ltm/ltm_manifest.json
  manifest.json  distribution_summary.json  summary.md  score_distributions.png
```
`frequency_tables/*/pair_conn_oriented.csv` and `triple_conn_oriented.csv` only list patterns seen in 5 or more trials (the full set is mostly singletons). The LTM keeps the 500 most frequent keys per kind per ranking.

## LTM
`ltm.pkl` / `ltm.json`: `{schema, manifest, cutoffs, default_ranking ("S2"), ranking_status ({S2: DEFAULT/PRIMARY, S1: SECONDARY}), ltm[ranking][kind] = {entries: [{key, key_str, n_top, frac_top, lift_vs_bottom, lift_vs_all, z, winning, ...}]}, mean_copies_per_trial}`. Load with `ltm.load_ltm(path)` (pickle) or the JSON (keys become lists). `ltm_manifest.json` holds seed, trials, definitions, code hash (SHA-256 of `src/*.py` and `run_expt20.py`), catalogue hash, versions, and file hashes of the LTM files. There is no git repository here, so the git commit is recorded as unavailable.

## Run
```text
python -m pytest -q
python run_expt20.py                 # 10,000 trials, seed 20260930
python run_expt20.py --trials 200 --tag smoke
```
Run with the repository `.venv` python if it exists; on this machine `.venv\Scripts\python.exe` was not present and the system Python 3.13 with numpy, pandas, matplotlib and pytest was used (see the manifest).

## What this does not show
Enrichment in the top 25% of random fills is correlation inside random sampling. It does not show that placing those combinations causes better fills; that is the question for the next phase.

## Phases: STM fill, then LTM-guided fill (`run_expt20_phases.py`, `src/phases/`)
Output: `results/<timestamp>_phases/`. The earlier LTM run is only read (`results/20260930_131353_run_S2default/ltm/ltm.pkl`, default ranking S2); nothing existing is overwritten. The next phase that *uses* winning combinations as macro-actions is still not built.

**Phase 1 (STM fill).** 10,000 uniform random legal fills, seed 20261001 (per-trial seed `seed*1_000_000 + trial_id`, same rule as before). S1 = 100 - empty, S2 = S1/attempts. The STM keeps running once-per-trial counts of single types, unordered type pairs and triples, and connected pairs/triples (oriented kinds are not kept). Top 25% is ranked by S2 desc, tie-break S1 desc, then trial_id asc. Because membership depends on the final cutoff, the top/bottom split is recomputed from the trials seen so far at every snapshot (every 1,000 trials: the online estimate) and once at the end (the final STM). Saved: `stm/stm_after_phase1.pkl|json`. `stm1_vs_ltm.csv` lists the STM's top 25 keys per kind next to the LTM lift for the same key.

**Phase 2 (guided).** 10,000 trials, seed 20261002. Per step:
1. With probability epsilon = 0.1, pick a uniformly random legal placement.
2. Otherwise group the legal placements by piece type, weight each legal type `w(t) = single_weight(t) * boost(t)`, sample a type proportional to `w`, then take a uniformly random legal placement of that type.
   - `single_weight(t)` = smoothed LTM lift of the single type (S2 ranking): `((n_top+1)/(N_top+2)) / ((n_bottom+1)/(N_bottom+2))`, clipped to [0.25, 4].
   - `boost(t)` = the largest LTM `lift_vs_bottom` among *winning* pairs/triples (lift > 1) that placing `t` completes given the piece types already on the board, clipped to [1, 6]; 1 if none. A combination is completed when the placed multiset contains it minus one `t` and does not contain it yet (repeated types respect multiplicity). Non-winning combinations are ignored.
Weights are read from the frozen LTM; nothing is learned online. Only the 500 most frequent keys per kind are in the LTM, which limits which combinations can boost.

**Controls.** (a) Uniform control: same seed and trial ids as Phase 2, uniform random picking, so trial *i* of the control and of the guided arm share an RNG seed (the random streams diverge after the first differing choice; pairing is on seed id, not on identical boards). (b) Two ablations on the same seeds: `single_only` (boost off) and `boost_only` (single weights off).

**Comparison.** `comparison.json` and `summary.md`: S1/S2 mean, median, max and top-25% cutoff per arm; paired guided-minus-control differences with standard error and a 2,000-resample bootstrap 95% interval; fraction of trials using P; P-usage transitions; paired S1 difference stratified by P status. **S2 is mean piece area, so it rewards the only 7-cell piece P; S1 is the measure of actual packing.** Guided STM after Phase 2: `stm/stm_after_phase2_guided.*` (Phase 2 trials only) and `stm/stm_cumulative_phase1_plus_phase2.*` (20,000 trials pooled; note the pooled top 25% mixes two sampling policies).

```text
python run_expt20_phases.py                 # about 4 minutes; runs pytest first
python run_expt20_phases.py --trials 300 --tag phases_smoke   # quick check (delete the folder afterwards)
```


## Stronger guidance (`run_expt20_stronger.py`, `src/stronger/`)
Output: `results/<timestamp>_stronger/` (run used here: `20260930_210213_stronger`). Headless, process-parallel (18 workers), seed-paired. The frozen S2 LTM is only read; no existing result is changed.

**Seeds and protocol.** Builder seed 20261004 (a fresh 10k uniform run used only to build the S1/S2 LTMs and placement tables), **dev** seed 20261002 (the same seeds as the earlier Phase-2 control), **held-out** seed 20261003 (fresh). Every variant runs 10,000 trials per seed set. Gain = variant minus uniform control on the same per-trial seed, bootstrap 95% CI (2,000 resamples over trial pairs). All variants and hyperparameters were screened on dev only. The 8 variants carried to held-out were picked from the dev ranking (top 5 by S1 gain, best S2 gain, best S1 gain per extra CPU ms, best zero-cost variant, best online variant). Dev numbers are therefore optimistically biased for the selected variants; the held-out table is the unbiased estimate. One held-out run was done; it was not used to select anything.

**Families** (full definitions in `src/stronger/policies.py`):
A. type weights from the frozen S2 LTM with exponent alpha on the single lift and beta on the boost, eps sweep, single-only / boost-only, and LTM-free area weighting; B. LTMs rebuilt from the builder run (top 25% by S1, top 10% by S1, fresh S2); C. hard priority for types that complete a winning pair/triple, boosts up to 20; D. placement-level: anchoring on the first empty cell that some legal placement can cover, maximum edge-contact selection, and a learned placement table (smoothed lift of (type, rotation, x, y) in the builder run's top 25%); E. one-step lookahead that samples K legal placements and minimises dead cells (empty cells no legal placement can cover) after placing, tie-break contact; F. online bandit weights (softmax / Thompson on the running mean S1 of boxes containing each type); G. combinations of the two best type-level and two best placement-level variants.

**Cost accounting.** `enum_ops` = 3,636 per step, paid by every arm including the control (`env.legal_placements`). Extra cost of a strategy = `mask_ops` (its own bitmask tests) + `cand_evals` (candidates it scores) per box. Weight arithmetic over <=16 types per step is not counted. `cpu ms/box` is measured inside the workers under parallel load and is noisy; use the units for comparisons.

**Caveats.** The contact and anchor rules are hand-written heuristics, not derived from the LTM. The learned placement table was the only placement rule learned from top-25% boxes, and it gave little. The early ranking in the earlier phases (S2) rewards piece P; S1 is the real packing measure. The hidden 3,636-placement enumeration dominates the absolute cost of every arm. Gains are for this 16-piece, 10x10, no-rotation-restriction environment and this random-fill baseline.


## Baselines (`run_expt20_baselines.py`, `src/baselines/`)
Output: `results/<timestamp>_baselines/` (run used here: `20260930_214303_baselines`). 10,000 boxes on the held-out seed 20261003 (the same per-trial seeds as the held-out table of the stronger run), paired bootstrap 95% CIs (2,000 resamples), 18 workers. Nothing existing was changed.

**Plain rules** (`rules.py`): candidate pool = all legal placements, or (anchor) those covering the first row-major empty cell that some legal placement can cover; then a piece filter (largest / smallest area, random type, any) and a placement choice (first in catalogue order, random, earliest row-major cell, max edge contact with first or random tie-break, Expt-16 score). `FF_*` = anchored (first-fit family), `G_*` = greedy without anchor. A rule with no random step is deterministic: every box is the same box, so its S1 has std 0 and it is a single solution evaluated 10,000 times.
**Expt-1 agent** (`e1agent.py`): the unmodified `mga.agent.PackingAgent`, mode none (no STM/LTM), `Expt_01.../configs/default.json` (heuristic fill + 0.45 contact - hole penalty, avoid-new-holes, eps 0.15, UNDO on dead end, 100-action budget) on the empty Expt-20 box.
**Expt-16 primitive** (`e16_run.py`, own process because Expt-16 shares module names with Expt-20): unmodified Expt-16 `primitive_remaining` (random 48-placement scan window, score 1.0 area + 0.2 contact + 0.05 boundary, undo budget 4, physical budget 80, eval cap 8000). Two changes only: unlimited inventory, and q_min either 75 (its recorded stopping rule) or 101 (run until it cannot place or hits the cap). Expt-16 to Expt-19 use this same primitive and the same catalogue (placement list and masks verified identical to Expt-1's).
**Effort.** `extra units` = the strategy's own mask tests + scored candidates (rules and Expt-20 arms); for the Expt-1 agent its `candidate_evaluations`; for the Expt-16 primitive its A (candidates examined). `enum units` = 3,636 placement-visits per decision wherever the code enumerates the catalogue (all arms). These scales are the same kind of quantity (placements touched) but not identical bookkeeping; the Expt-1 agent additionally runs flood fills per candidate, so its true cost is higher than its count suggests. `cpu ms/box` is wall time inside busy parallel workers and is noisy. The earlier experiments' recorded effort (about 1,125 to 1,598 candidates per box) is for their inventory tasks, which stop at 75 occupied cells and are not the same task.
**Best plain baseline** is named in `manifest.json`; it was chosen after seeing the results among the 14 rules, so its advantage over the others is selected.
