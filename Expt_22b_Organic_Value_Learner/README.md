# Expt-22b - Organic self-improving value learner (successor of Expt-21)

Same task as Expt-21: 10x10 box, 16-piece catalogue, **handicap of at most 14 pieces per box**, **natural placing** (only legal placements that touch the wall or an already placed piece; no anchor cell, no row-major order, no layer jumping), S1 = 100 - empty cells. Untrained uniform natural placing scores S1 about 67.3 on the fixed held-out boxes. Continuous learning, one box at a time, no 10,000-box batch phases. No existing experiment folder is modified (`Expt_22a_*` was a parallel, partly overlapping attempt; 22b is self-contained and fixes the defects listed below).

## What changed compared with Expt-21
| | Expt-21 | Expt-22b |
|---|---|---|
| policy | softmax over additive hash-table weights | softmax over a **learned afterstate value function** V(board after placement), 1-step lookahead over natural candidates |
| representation | hashed features | 2-layer numpy MLP (29 board features: piece type, area, contacts, new 1-cell holes / dead-end notches, frontier size, 2nd-ring occupancy, pieces left, global holes, concept column) |
| credit | advantage vs running mean | **Monte-Carlo / lambda-returns of the final S1** per afterstate (lambda = 1.0 by default; lambda < 1 bootstraps from the slow net and was unstable in the pilot) |
| memory | STM ring buffer -> additive tables | STM -> sleep -> **LTM = slow (EMA-consolidated) network weights + concept library** |
| hyperparameters | fixed, anneal schedule | **meta-controller changes tau, eps, lr, lambda, dream ratio, sleep interval and STM size online** and logs every change |
| growth | staged feature addition on saturation | **capacity growth only if a shadow test says capacity is the bottleneck** (function-preserving widening of the MLP must beat a same-width control on held-out replay by >7%) |

## Components (src/)
- `engine.py` bitmask packing engine (copied unchanged from Expt-21; every placement replays in `mga.environment.PackingEnv`, tested).
- `feat.py` afterstate features; `net.py` MLP with Adam and function-preserving widening.
- `agent.py` acting (softmax(V/tau) mixed with eps uniform), online step, **sleep**: replays new boxes + prioritised old boxes (priority = TD/return error), **dreams** (prefix of a stored box continued by the current policy at higher temperature and eps, credited at 0.5 for the dreamed part), trains the fast net, then moves the slow net towards it (EMA 0.3). **Concept library**: local arrangements (oriented piece + 1-ring occupancy) whose value residual against the concept-free net is large and significant (n >= 25, z >= 3, |mean| >= 0.3 cells) are promoted and fed back as an extra feature column.
- `meta.py` meta-controller, driven by a fixed probe (80 boxes, near-greedy) every 1,000 boxes plus loss diagnostics from sleeps: stagnation -> re-explore (unless the probe is already strong) and more dreams; steady progress -> cool tau/eps; loss rising inside sleeps -> lower lr, raise lambda; old-episode loss >> new -> larger STM; new >> old -> sleep more often; plateau at a strong level -> cool and consolidate. All moves are multiplicative within bounds; every event is stored with its reason.
- `stream.py` one continuous stream; `run_expt22b.py` parallel replicates (strictly sequential inside a stream); `report.py` tables + PNG/PDF figures; `learner_ref.py` uniform and hand-rule references (the hand rule is **only** a reference line; the learner never calls it).

## Evaluation
- Held-out: fixed 1,200 fresh boxes (seeds 7,700,000+j, never used in training), frozen memory (slow net + concept library), near-greedy softmax (tau 0.25), no learning. CIs are bootstrap over independent replicates.
- Ablations (fewer boxes and replicates than the main variant, see `summary.md`): `no_meta`, `no_sleep` (memory = fast net; V22a evaluated the never-updated slow net here, a bug fixed in 22b), `no_dream`, `no_concepts`, `td095` (bootstrapped returns), `badinit_meta` / `badinit_fixed` (poor initial hyperparameters with / without the meta-controller), `frozen`.
- Transfer: the frozen final memory (trained at 14 pieces) tested at 12 / 14 / 16 / 20 / 40 pieces per box.
- Reference lines: uniform natural, Expt-21 final held-out 83.70, hand contact/hole/area rule under the same handicap.

## Run
```
python run_expt22b.py --workers 10 --reps 12 --abl-reps 4 --boxes 20000 --abl-boxes 10000 --eval-boxes 1200
python run_expt22b.py --report-only results/<dir>
python -m pytest -q
```
BLAS threads are pinned to 1 (otherwise workers oversubscribe the CPU and run several times slower).

## Caveats
Hyperparameters (network size, step counts, meta thresholds) were set from two short pilots (12k boxes, 1-3 seeds each), not tuned on the held-out boxes. Streams are shorter than Expt-21's (20k vs 60-98k boxes) because of the overnight deadline; saturation is judged from the curves in `summary.md`. The equal-length design gives every checkpoint the full replicate count.