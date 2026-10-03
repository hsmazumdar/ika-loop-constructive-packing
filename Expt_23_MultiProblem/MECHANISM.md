# MECHANISM.md - what the learners actually do (read from code, 2026-10-02 06:35 IST)
Sources: Expt_22d `src/agent.py, config.py, net.py, meta.py, stream.py`; Expt_23 `src/learner.py, learner_full.py, nn_agents.py, run_streams.py, run_e_streams.py`; manuscript section 4. Read-only; no run was touched. "measured" = computed/observed now, "derived" = arithmetic from code constants, "est." = estimate.

## 0. Terminology (paper vs code)
- **Fast network** = the net acting and learning online. **STM** = buffer of recent whole episodes (the replay store). **Sleep** = periodic replay training. **LTM** = the slow net, an EMA copy of the fast net (plus the concept library). There is no separate "working memory" object: the nearest thing is the current episode's trajectory list (Xs) held while the box is played.
- The manuscript itself says these are labels for a schedule (buffer, replay, EMA), not biological claims.
- Expt_20's `ltm.pkl` (575 KB, a lookup-style memory) is a different object and is NOT in the 22d or 23 learners.

## 1. Short-term memory
| item | 22d full | Expt_23 F/R (learner_full.py) | N arm | DQN | PPO |
|---|---|---|---|---|---|
| what | ring buffer of whole episodes | same | none (only the episode just played, used once, then dropped) | transition ring buffer | on-policy buffer, cleared every update |
| capacity | 1000 episodes (meta may move 300-4000) | 1000 episodes (same bounds) | 0 | 6000 transitions (about 450 episodes) | 16 episodes (about 212 steps) |
| per item | X (T x 29 float32), concept keys, values, weights, placed list, final S1 | X (T x 257 float32), keys, placed, problem ref, normalised return y | - | afterstate x (256 f32), next-candidate set 32 x 256 f16, mask, terminal flag, y | all candidate vectors of each step (about 387 x 256 f32 = 396 KB/step on std), chosen index, old log-prob, return |
| size | about 2-3 MB (est.) | about 13.6 MB (derived: 13.25 steps x 257 x 4 B x 1000); up to about 54 MB at cap 4000 | - | about 104.6 MB (derived: 6.1 MB x + 98.3 MB next-set) | about 84 MB average per update (derived), more on big boards |
- Written: after every episode (`remember`). Overwritten: oldest deleted when over cap (FIFO). Priorities start at 1.0, are reset to mean |error| after each replay.
- Used: (a) sleep sampling (all new episodes + 150 priority-sampled old ones, p proportional to prio^0.6 + 1e-3), (b) dream prefixes. DQN samples uniformly, 64 per update.
- Episode length measured on train problems: std 13.25 afterstates/episode (budget 14), hard 11.25; candidates per step std mean 387 (max 1510), hard mean 150 (max 690).

## 2. Long-term memory and consolidation
| item | 22d | Expt_23 F | N | DQN | PPO |
|---|---|---|---|---|---|
| value net | 29-64-64-1, 6,145 params (final widths per seed: 64,128,128,256,128,256 -> 20,481 / 73,729 params) | 257-128-128-1, 49,665 params (about 199 KB f32, x3 with Adam moments) | 256-128-128-1, 49,537 params | 256-256-128-128-1, 115,329 params (461 KB), plus target net | policy net 115,329 + value net 115,329 = 230,658 |
| slow net | EMA copy | EMA copy (same size) | none (eval uses the fast net) | target net, hard copy every 500 episodes, used only for targets | none |
| concepts | 206-366 promoted per stream at 60k boxes (about 12 B each) | up to 6000 cap; none promoted before about 1000+ episodes | none | none | none |
- Sleep (22d and 23 F identical constants): every 200 new episodes (meta range 100-400), so about 100 sleeps per 20k episodes. Batch = 200 new + 150 old + about 100 dream episodes (about 450 episodes, about 5.9k rows). 40 Adam steps, batch 256 rows, lr 1e-3. Then **slow = 0.7 slow + 0.3 fast** (EMA rate 0.3, every sleep). Concept stats are updated from the new episodes' residuals each sleep; promotion every 5 sleeps (n>=25, z>=3, |mean|>=0.3, cap 6000); stored value = clip(mean residual / 3, +-2), fed as the last input column.
- Dreams: int(0.5 x n_new) = 100 per sleep. A stored episode is cut at a random point; the prefix is replayed; the rest is re-played by the current policy at tau = max(tau,0.3) x 1.5 and eps 0.15, weight 0.5. Dreams are not stored in the STM.
- Decision time: the agent scores every candidate afterstate with the net (fast net while learning; **slow net + library** for evaluation when sleep is on) and picks by softmax(value / tau) mixed with eps uniform. Tau is in "cells per 100-cell board" units (value unit 0.15 of free cells = 15 units). Evaluation: tau 0.25, eps 0, no learning.
- The slow net is a read-only shadow: it never feeds back into the fast net. With lambda = 1 (initial and the usual value) the target is just the final return, so the slow net is NOT used in targets.

## 3. Operational memory at run time
- RAM measured now: the 12 baseline workers hold 323-429 MB each (mixed arms; torch workers are heavier), parent 40 MB (Task Manager working set, measured).
- Evaluation "freezing" = no learning call is made and the memory net is selected (slow if sleep else fast); the net is NOT copied. Eval episodes use fresh seeds and are not recorded.
- Env cache: F/R keep up to 48 (Env, encoder) pairs so dreams can revisit stored problems. Concept stats dict is uncapped (all observed keys, 3 numbers each; size not measured). Meta-controller state: EMA of probe, gains, event log, hyperparameter dict h (tau, eps, lr, lam, dream, sleep_every, stm). Probe = 20 dev problems per epoch of 1000 episodes (23) / 80 boxes (22d). Meta acts from epoch 2; growth is OFF in Expt_23 (hidden fixed 128). Exploration floors in meta: tau >= 0.25, eps >= 0.005.

## 4. One episode and one sleep, step by step (Expt_23 F, std, capped_nat)
1. Draw a train problem (pool of 20,000) -> build Env + encoder. 2. Repeat up to 14 times: list natural placements (about 387), encode each (9x9 3-channel window = 243 + 6 shape numbers + 7 globals = 256, +1 concept column), score with the fast net, sample by softmax(v/tau) with eps mix; place; remember the chosen row. tau/eps follow a linear anneal 2.0 -> 0.25 and 0.10 -> 0.01 over the first 5000 episodes in the fixed schedule (N, DQN; F uses the same schedule only if meta is off, otherwise meta moves them). 3. Episode return y = (filled/free_cells - 0.7)/0.15, assigned to every row (lambda = 1, no discount). 4. `remember` (STM), then one Adam step on those about 13 rows at lr 5e-4 (= 1e-3 x 0.5). 5. When 200 new episodes have accumulated: sleep as in section 2 (about 450 episodes, 40 steps x 256 rows, EMA 0.3, update priorities, concept statistics). 6. Every 1000 episodes: meta probe and hyperparameter adjustment. 7. Checkpoints 0, 1k, 2k, 5k, 10k, 20k: frozen evaluation on 4 test splits x 50 problems x 3 reps = 600 episodes.

## 5. Arms in Expt_23
- **N** (`learner.py`, online only): fast net, one Adam step per episode on that episode's rows, MC target, softmax acting with the anneal. No replay, slow net, dreams, concepts, meta. Evaluated with the fast net.
- **DQN** (`nn_agents.py`): same encoder and annealed softmax acting; bigger net; replay 6000 transitions; 4 updates/episode of 64 after 500 warm-up transitions; lr 5e-4; smooth-L1; target net synced every 500 episodes; target = terminal y or max over a 32-candidate subset (24 best by behaviour value + 8 random) of next afterstates from the target net; no discount. No sleep, dreams, concepts.
- **PPO**: policy and value nets; every 16 episodes, 2 epochs, minibatch 64 steps, lr 3e-4, clip 0.2, entropy 0.01; advantage = terminal return - V(mean candidate vector), normalised; no GAE; acts by sampling the raw softmax (temperature 1, no tau/eps anneal); evaluated by sampling at temperature 1 (main) and argmax.
- **F / R / RN** (E-streams, not yet run): F = 22d machinery ported (sleep, dreams, slow net, concepts, meta, no growth); R = same but data from uniformly random placements (including dream continuations); RN = random data, online update only.

## 6. Mismatches / things to check
1. Manuscript 4.2 says targets are "lambda-returns computed against the slow network" with lambda = 1. With lambda = 1 the slow net is not touched by the targets (only the td095 ablation uses it). Reword.
2. Manuscript 4.3 says online batch size 64; the code takes `min(64, rows)`, and an episode has at most 14 rows, so the batch is the episode itself.
3. Compute matching: DESIGN says arms are matched on experiences and learner updates. F does 200 online + 40 sleep Adam steps per 200 episodes (240 vs N's 200) and about 12.8k vs 2.6k gradient rows per 200 episodes (derived). Not matched in rows; report it.
4. 23 vs 22d: dream continuations always use natural placements (ignoring the `any` condition); the prefix rows are not trained on (22d gives them weight 0, same effect); concept residuals are in 15-cells-per-unit (22d: 10), so thresholds 0.3 and /3 mean slightly different things; hidden 128 from the start (22d starts at 64); D = 257.
5. PPO and DQN use different acting rules from N (PPO has no tau/eps schedule), so they are generic baselines, not matched in exploration.
6. Concept library statistics are not capped, so RAM in F could grow; not measured.