# Expt-4 — Emergent hierarchical abstraction

The objective of this experiment is not to discover a better packing heuristic. Packing is the observable environment. The experiment asks whether repeated information can autonomously become compressed reusable knowledge, and whether that knowledge allows future problems to be solved with less deliberation.

Expt-1, Expt-2, and Expt-3 are not modified. The 10×10 world and the quality score Q (occupied cells) are copied from Expt-3 so the worlds stay comparable.

## What is measured

- Q: occupied cells, the same score as Expt-3.
- A: candidate evaluations. This counts primitive rows examined, retrieved learned operations that are scored, and anchor checks. The internal placements of a learned operation that the controller has already chosen are recorded separately and are not added to A.
- A box stops when Q reaches `q_min` (default 75), or when the bounded scan cannot place anything, or when the physical or evaluation budget is exhausted.
- Q/A is recorded for every box. It is not treated as intelligence when Q is below `q_min`.

## Agents

| Name | Role |
| --- | --- |
| `primitive` | No library. Expt-3 placement score, documented below. |
| `flat` | Learns operations made only of primitive actions. |
| `hierarchical` | Learned operations may contain earlier learned operations, up to `max_depth`. |
| `hierarchical_unlimited` | Same learner with eviction and aging turned off. |
| `control` | Same support rule, but each promoted operation is replaced by a different random sequence. |

Held-out inventories are the Expt-3 test split. They are never stored or mined. After `change_at` training boxes the sampler switches to a shifted piece-count distribution. The agent is not told. A probe subset of that shift is held out of training and evaluated at checkpoints.

At the end of a hierarchical lifetime the run also transfers the operation list into a fresh controller (episodes are not transferred) and repeats the held-out set after four knockouts: all operations, highest depth, most-used half, and a random half.

## Documented human priors

These are fixed and are not discovered by the miner:

- The A–P catalogue, four rotations, and no reflection.
- Q is the number of occupied cells.
- The primitive fallback score is `area + 0.2 * contact + 0.05 * boundary`, inherited from Expt-3 so the baseline is the same search, not a new packing idea. The miner does not use this score.
- A learned operation must have a 4-connected footprint, so one decision is one spatially coherent action. Filled rectangles are not rewarded.
- Retrieval scores a bounded random pool (`retrieval_pool`) and keeps `top_k`. Similarity uses piece-count histogram, occupancy, row and column fill, and empty-region summaries. There are no shape labels.
- The episode stops at `q_min` instead of sealing the board. Expt-3's later smoke spent about 7,500 evaluations because it continued until the evaluation cap. That cap-burning stop rule is not copied.
- If a full scan finds no legal placement, every agent may undo up to `undo_budget` (default 4) pieces and must not immediately replay the undone placement. The undo is shared. It is not a shape filter. Search then stops at `q_min` rather than spending the rest of the evaluation cap.

## Commands

From this directory, using the Expt-3 virtualenv (it already has the dependencies) or any Python with `requirements.txt` installed:

```text
python run_expt4.py --smoke
python run_expt4.py --pilot
python run_expt4.py --full
```

Optional: `--seed`, `--agent`, `--train-boxes`, `--memory-capacity`, `--top-k`, `--max-depth`.

`--pilot` and `--full` run `tests/` first and do not start the lifetime if validation fails. `--full` is 10 seeds and 10,000 boxes per agent. It is not started by a smoke or pilot command.

## Outputs

Each run writes `results/<stamp>_<preset>/` with `train_boxes.csv`, `checkpoints.csv`, `special.csv`, `EXPT4_REPORT.md`, `knowledge_report.txt`, `knowledge_report.csv`, `knowledge_genealogy.png`, and the checkpoint plots. A copy of the report is also placed in `reports/EXPT4_REPORT.md`.
