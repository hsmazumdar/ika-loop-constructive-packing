# Expt-4D2 — Identify costly choices

Expt-4D is not modified. This folder audits that diagnostic, then tabulates matched-state replays.

Promotion is unchanged. There is no larger training run.

## What 4D got wrong in the mean ΔA

`retrieve_check_then_primitive` billed retrieval onto the same `Ledger.A` that stopped the primitive loop. One development box hit `eval_cap`. Retrieve/check therefore took fewer primitive evaluations (888 fewer on that box). Equal mean Q did not prove identical trajectories.

A = primitive_evals + retrieval_cost + applicability_cost + learned_evals.

## Commands

```text
python -m pytest -q
python run_expt4d2.py --audit
python run_expt4d2.py --smoke
python run_expt4d2.py --diagnostic
```

`--audit` only reads the frozen Expt-4D CSVs.
`--diagnostic` reconstructs the same 3×80 libraries and collects more replays on the original 8 development boxes plus 16 fresh boxes. Fresh boxes are disjoint from train, original development, and the Expt-4C test set.
