# Expt-5 — Learning whether to consult and whether to commit

The library learner from Expt-4B/4C is copied, not edited. Two cheap gates are trained from matched-state replays, frozen, then compared in a factorial on fresh boxes.

Gate checks are billed inside A. Counterfactual remaining-solves used as labels are a **learning cost**, reported separately.

## Conditions

| Condition | Consultation | Commitment |
| --- | --- | --- |
| primitive | none | none |
| current_selective | existing retrieve | existing applicability |
| consult_gate_only | learned | existing |
| commit_gate_only | existing | learned |
| both_gates | learned | learned |

There is no handwritten “reject M0003 on empty boards” rule. Operation identity can receive a learned bias from labels.

## Commands

```text
python -m pytest -q
python run_expt5.py --smoke
python run_expt5.py --diagnostic
```
