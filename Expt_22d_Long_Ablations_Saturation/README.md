# Expt-22d - long-horizon ablations and saturation of the organic value learner

Copy of the Expt-22b/22c code (value MLP, Monte-Carlo returns, sleep/dream, slow-weight LTM, concept library, meta-controller, shadow-tested growth) with:
- `config.py`: held-out checkpoints every 4k boxes from 20k to 60k; new variant `no_meta_matched_floor` (fixed hyperparameters, tau/eps annealed linearly 2.0->0.25 and 0.10->0.0077 over 32k boxes = floors the meta-controller reaches in 22c).
- `stream.py`: per-variant schedule bounds; `on_eval` callback writes partial snapshots (`streams_partial/`) at each checkpoint so summaries can be produced while streams still run.
- `run_expt22d.py`, `src/report.py` (+`report_utils.py`): long-horizon ablation table/bars vs the 22c `full` reference (n=12, seeds 100-111), saturation curve with replicate band, self-modification timeline, auto-generated findings section.

Design: `full` x 6 streams x 60,000 boxes (seeds 300-305) + ablations no_meta, no_meta_matched_floor, no_dream, no_concepts, no_sleep x 4 streams x 32,000 boxes (seeds 200-203). 26 streams in parallel, OMP/BLAS=1. Eval = 1,200 fresh boxes, frozen memory.

Run: `launch_main.bat` -> `results/20261001_060654_main`. Check: `progress.log` (CKPT lines), `main_stdout.txt`, `streams/` (finished), `streams_partial/` (running).
Partial/final report: `python run_expt22d.py --report-only results\20261001_060654_main` (rewrites summary.md, figures, csv; takes ~1-2 min under load).
Tests: `python -m pytest -q tests` (13 passed).
