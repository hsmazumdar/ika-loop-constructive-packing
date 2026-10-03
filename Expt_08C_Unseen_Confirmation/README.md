# Expt-8C — Unseen confirmation of frozen 8B models

Short audit of Expt-8B provenance, then one evaluation of the frozen models on new boxes. No new retrieval or placement mechanism. Thresholds are not retuned on the new set.

```text
python -m pytest -q
python run_expt8c.py --audit
python run_expt8c.py --smoke
python run_expt8c.py --diagnostic
```
