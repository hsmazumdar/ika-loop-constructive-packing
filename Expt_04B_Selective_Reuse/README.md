# Expt-4B — Learn when to use knowledge

Expt-4 implemented remembering and composition. This folder tests whether the agent can **distinguish a recurring pattern from a useful piece of knowledge**.

Expt-1 through Expt-4 are not modified. The 10×10 world, catalogue, and quality score Q are copied from Expt-4.

## Research question

Can the agent autonomously promote a mined pattern only when it reduces deliberation while preserving the quality gate, use it only where it has been useful, and abstain otherwise?

This does not teach rectangles or any packing concept. Candidate patterns still emerge from experience.

## Conditions (same train and held-out problems)

| Condition | Question |
| --- | --- |
| `primitive` | What is the baseline? |
| `current_hierarchy` | Can the Expt-4 failure (library raises A) be reproduced? |
| `utility_promotion` | Are harmful operations being admitted? |
| `contextual_abstention` | Are operations being used in unsuitable situations? |
| `both` | Does selective acquisition plus selective use produce a benefit? |

## Rules

- New operations start **provisional**. Recurrence proposes; paired training-only validation decides promotion.
- Held-out boxes never enter mining or pairing.
- A composed operation must beat executing/selecting its constituents.
- The agent may abstain: “no stored operation is useful here; use primitives.”
- After the environment shift, old evidence is discounted and useless operations can become inactive.
- Q and A are reported separately. Q/A is the **mean of per-box ratios**, not mean Q / mean A.
- Internal execution of a committed operation is logged and **not** added to A. Applicability checks **are** added to A.

## Commands

From this directory (use the Expt-3 or Expt-4 virtualenv, or install `requirements.txt`):

```text
python -m pytest -q
python run_expt4b.py --smoke
python run_expt4b.py --diagnostic
```

`--diagnostic` is 2 seeds × 60 training boxes × 5 conditions. It is not a 10,000-box lifetime.

## Outputs

`results/<stamp>_<preset>/` contains `train_boxes.csv`, `checkpoints.csv`, `paired_validations.csv`, `operations.csv`, plots, and `EXPT4B_REPORT.md` (copied to `reports/`).
