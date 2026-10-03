# Expt-7 — Bounded indexed retrieval with selective commitment

Frozen Expt-6 libraries. Do not retrain the library. Build a compatibility index, retrieve at most K operations, optionally rank them from training-only remaining-solves, and cap consultation per box.

Expt-6 eval boxes are development for choosing K and the consult budget. Fresh eval boxes are the confirmation split.

## Conditions

| Condition | Access |
| --- | --- |
| primitive | no library |
| both_gates_frozen | unmodified Expt-5 consult+commit policy |
| indexed_retrieval | index shortlist of K, first legal site, per-box budget |
| indexed_ranked | same shortlist, learned benefit + quality-loss ranking with abstention |

Index lookup, compatibility checks, placement checks, and ranking are billed. An index lookup is not free.

## Commands

Use `Expt_01_10x10_Packing/.venv/Scripts/python.exe`. Do not hardcode a drive letter.

```text
python -m pytest -q
python run_expt7.py --audit
python run_expt7.py --smoke
python run_expt7.py --diagnostic
python run_expt7.py --report --run-dir results/<timestamp>_<preset>
```

## Diagnostic

Shortlist opportunity recall: among sampled-oracle states with a useful action, how often does the inexpensive shortlist contain at least one useful action? High recall is not enough without whole-box effort and quality.
