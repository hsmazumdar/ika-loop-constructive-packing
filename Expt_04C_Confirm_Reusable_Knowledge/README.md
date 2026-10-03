# Expt-4C — Confirm that learned knowledge reduces future deliberation

Expt-4B is not modified. This folder copies its selective mechanism (`both`: provisional promotion, paired utility, applicability, abstention) and asks whether the advantage is repeatable, transferable, and caused by the stored operations.

## Predeclared quality-loss margin

`QUALITY_LOSS_MARGIN = 1.0` occupied cells, set in `config.py` **before** the confirmation run.

A per-box **win** against primitive requires:

- `Q_agent >= Q_primitive - 1.0`
- `A_agent < A_primitive`

This is an accounting rule, not a significance test.

## Conditions

| Condition | Role |
| --- | --- |
| `primitive` | Baseline, no library |
| `selective_flat` | Same 4B mechanism, depth 1 only |
| `selective_hierarchical` | Expt-4B `both` |
| `transfer` | Fresh controller; active operations + applicability rules only |
| `lesion` | Trained hierarchical agent with operations disabled |

Learning is frozen on the development checkpoints and on the final test set.

## Commands

Generate 100 disjoint test inventories (witnesses stay in `validation_only/`):

```text
python tools/generate_final_test.py
python -m pytest -q
python run_expt4c.py --smoke
python run_expt4c.py --confirm
```

`--confirm` is 10 seeds × 200 training boxes, checkpoints at 0/30/60/100/200 on the development set, then 100 identical test boxes.

## Outputs

`results/<stamp>_<preset>/` contains `final_test.csv`, `pairwise_vs_primitive.csv`, `seed_summaries.csv`, plots, and `EXPT4C_REPORT.md`.
