# Expt-6 — Opportunity in the Frozen Knowledge Library

Diagnostic experiment. Libraries and gates from Expt-5 are frozen. No learning, promotion, or threshold updates occur.

The question is whether the existing library contains operations that could reduce future deliberation if selected well, or whether useful opportunity in the library is too small. The oracle sees future remaining-solves and is **not** a deployable agent.

## Conditions

| Condition | What it measures |
| --- | --- |
| primitive | Audited primitive solver |
| both_gates_frozen | Unmodified Expt-5 consult+commit policy, billed |
| oracle_single_free | At most one existing operation at one sampled primitive-trajectory state; discovery is free; chosen-action validation remains |
| oracle_single_scan_charged | Same intervention, plus the full prospective scan cost `C_box` on every box |

Occupancy 0/10/20/30/40/50/60 is a coverage schedule, not a learned context rule.

Expt-5 did not serialize libraries. This experiment reconstructs them from the recorded 80-box streams and marks `reconstruction=True`. Exact in-memory library-hash match with Expt-5 cannot be verified.

## Commands

Use the project interpreter (`Expt_01_10x10_Packing/.venv/Scripts/python.exe` on this machine). Do not hardcode a drive letter.

```text
python -m pytest -q
python run_expt6.py --audit
python run_expt6.py --smoke
python run_expt6.py --diagnostic
python run_expt6.py --report --run-dir results/<timestamp>_<preset>
python run_expt6.py --resume --run-dir results/<timestamp>_<preset>
```

Smoke uses seed 11 and 4 boxes. Diagnostic uses seeds 11, 22, 33 and the same 24 boxes on each library (72 library–box pairs). Resume skips completed `(seed, task_id)` rows.

## Accounting

`A = primitive_evals + retrieval + applicability + learned_site_checks + gate_checks`

Remaining-solve budget is `eval_cap − prefix_primitive_A`. Counterfactual rollouts belong in the diagnostic ledger, not in deployment A and not in `C_box`.
