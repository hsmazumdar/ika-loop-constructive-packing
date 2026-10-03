# Expt-8B — Consistent remaining-budget labels

Repair of Expt-8. Same libraries, features, and admission bar. Fit and validation both use remaining budget `eval_cap − prefix_primitive_A`. Primary saving predictor is unweighted. Severe-loss-weighted fit is an explicit comparison. No new retrieval or placement mechanism.

Diagnostic: `results/20260929_231956_diagnostic`. Report: `reports/EXPT8B_REPORT.md`.

```text
python -m pytest -q
python run_expt8b.py --audit
python run_expt8b.py --smoke
python run_expt8b.py --diagnostic
```
