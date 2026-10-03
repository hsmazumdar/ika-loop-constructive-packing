# Expt-21 - Continuous learning with sleep consolidation and growth on saturation

Successor of Expt-20. No 10,000-box batch phases: one agent plays **one box at a time**, learns after every box, consolidates during periodic **sleep**, and **grows** its memory when its learning curve saturates. No existing experiment folder is modified (the Expt-1 `mga` package is imported read-only).

## Task and handicap (why the baseline is weak)
- Same 10x10 box and 16-piece catalogue (A-P, all rotations, unlimited supply) as Expt-1/20. **S1 = 100 - empty cells**, S2 = S1/attempts (mean piece area). Every trial starts from an empty box.
- **Difficulty handicap: at most 14 pieces per box** (`config.BUDGET`). Average piece area is ~4.9 cells, so 14 pieces cover at most ~69 cells of a perfectly chosen-by-luck box and ~80+ only with large pieces (P=7). Reaching 93 needs 14 pieces averaging >= 6.6 cells, i.e. mostly P plus 5-cell pieces placed without holes - both piece choice and placement must be learned. Calibrated offline by scanning piece budget x kit size (scratch runs, not kept): uniform natural placing gives S1 of about 67 at a budget of 14; the measured number is reported in `summary.md` (held-out, 2,000 boxes).
- The handicap is deterministic (a budget), so every policy sees the same task.

## Natural placing (no layer jumping)
A placement is *natural* if it is legal and touches the wall or an already placed piece (>= 1 edge contact). The agent chooses only among natural placements. There is **no** anchor cell, no row-major order, no hand-written scoring: the first piece lands against a wall, and pieces grow outward from the frontier. (A free-floating placement can always be slid until it touches, so restricting to natural ones removes "jumping into open space" but never leaves the agent stuck.) Contact count is also an input feature, but its weight is learned.

## Agent
Score of a candidate placement = sum over active memory tables of a learned weight:

| table (feature) | key | introduced |
|---|---|---|
| `type` | piece type | stage 0 |
| `A` | oriented piece x contact count x new 1-cell holes x new dead-end notches (all read from the board) | stage 0 |
| `pair` | piece type x each type already in the box (pair combos) | G1 |
| `S1` | oriented piece x occupancy of the ring of neighbouring cells (3x3-style context) | G2 |
| `trip` | piece type x last two types placed (triple combos) | G3 |
| `S2` | S1 context x number of occupied cells in the second ring (5x5-style context) | G4 |

Policy: `softmax(score / tau)` over natural placements, mixed with uniform probability `eps`. With an empty memory all scores are 0 so the policy is exactly uniform natural placing (= the baseline). `tau` anneals 2.0 -> 0.7 and `eps` 0.10 -> 0.02 over the first 15,000 boxes and then stays at the floor (no further schedule).

**Target per placement**: advantage = (cells added from this step to the end of the box) - (running mean of that quantity at the same step index). Each table learns the *shrunk mean residual* (`w += sum(advantage - prediction)/(n + k + m)`, k = 2, prediction = sum of active tables, error split across tables), so tables are additive and learned from outcomes only.

**STM** = ring buffer of the last 1,000 boxes (placements + final S1), larger after growth stages. **Online** (no-sleep control): update tables immediately after each box. **Sleep** every 200 boxes: (1) replay the 200 new boxes for 2 epochs at full weight (evidence counts are added once), (2) rehearse 200 older STM boxes at half weight without adding evidence, (3) **dream**: `0.5 x (new boxes) x dream multiplier` rollouts, each starting from a random prefix of a stored STM episode and continued by the current policy at higher temperature (x1.5) and eps 0.2, credited at weight 0.5 (the continuation only), (4) **forgetting**: all evidence counts decay by 0.98 and entries with little evidence and near-zero weight are pruned, plus crowding-based pruning above 85% table occupancy (weakest `|w| x min(n, 10)` first).

**Memory size** = fixed-size direct-mapped hash tables (`config.bits`); a full slot is taken over only by stronger evidence.

## Growth on saturation
Every 2,000 boxes (after annealing, and after at least 2 x 6,000 boxes in a stage) a saturation test compares the last 6,000-box window with the previous one: saturated when `gain + 1.645 x SE < 0.30` S1. Then the next stage is applied automatically (new feature table + doubled capacity and/or larger STM / more dreams, see `config.stages`), new tables are filled by replaying the whole STM, and learning continues. A stage that never saturates is forced to grow after 40,000 boxes (recorded as `forced`). The stream stops after >= 60,000 boxes when two consecutive growth stages each added < 0.30 S1 or the last stage saturates; hard cap 150,000 boxes.

## Protocol and outputs
- 12 independent replicates of the full system (different seeds; parallel across replicates, each stream is strictly sequential).
- Controls / ablations, 6 replicates x 60,000 boxes each, compared at 60,000 boxes by held-out S1: `full`, `no_sleep`, `sleep_no_dream`, `no_growth`, `all_upfront`, `frozen` (learning disabled - must stay flat).
- **Held-out checkpoints**: at fixed box counts (and at the end of every stage) the memory is frozen and evaluated on a fixed set of 2,000 fresh boxes (RNG seeds `eval_seed + j`, never used in training), near-greedy (`tau_eval = 0.3`, eps = 0). Training S1 is measured while exploring, so it understates held-out S1; both are reported. CIs are bootstrap over replicate means (independent replicates).
- References (not available to the learner): uniform natural placing (baseline), a hand contact/hole/area rule under the same handicap, target 93, and the Expt-20 best hand rule (~96-98 on the unhandicapped task; different task, context only).

```
run_expt21.py            entry (runs the tests first); --smoke for a tiny end-to-end run; --report-only <dir>
src/config.py engine.py tables.py learner.py stream.py analysis.py report.py
tests/test_expt21.py     18 tests (replay in PackingEnv, natural placing, tables, learning, growth, sleep, saturation, reproducibility)
results/<timestamp>_run/ summary.md learning_curve.png/.csv heldout_checkpoints.png/.csv growth_stages.csv
                         leaderboard_ablations.csv ablation_curves.png ltm_full_seed0.pkl streams/*.pkl progress.log manifest.json
```

## Caveats
- The 14-piece budget is what makes the task hard; absolute S1 numbers are not comparable with Expt-20 (unlimited pieces).
- Hyperparameters (table sizes, decay, tau/eps schedule, saturation thresholds) were set once from short pilot runs, not tuned on the final evaluation boxes; the held-out evaluation set was never used for training.
- The saturation test uses training S1 (noisy, exploration on). Forced growth is reported separately from detected saturation.