# Expt-4D — Where reuse loses its advantage

Expt-4B and Expt-4C are not modified. This folder freezes their selective mechanism, trains a library, and diagnoses **why** reuse currently raises deliberation.

Effort saving is defined as **A_primitive − A_agent**. Positive means fewer candidate evaluations than primitive. Negative means worse.

Quality-loss rate (boxes with Q_agent < Q_primitive − 1.0) is reported **separately** from whether mean Q stays within the margin.

## Diagnostics (development set only)

| Mode | Isolates |
| --- | --- |
| `primitive` | Baseline |
| `retrieve_check_then_primitive` | Retrieval and checking overhead; primitive still decides |
| `normal_reuse` | Total effect of reuse |
| Counterfactual replay | Remaining-solve effect of committing each proposed operation |

Matched-state replay starts from the same board, remaining pieces, and RNG. Branch 1 commits the operation then continues with the primitive policy. Branch 2 continues with primitive only. The whole remaining solve is measured. These two futures are **diagnosis only**.

## Commands

```text
python -m pytest -q
python run_expt4d.py --smoke
python run_expt4d.py --diagnostic
```

`--diagnostic` trains 3 seeds × 80 boxes, freezes the library, then runs the development set.
