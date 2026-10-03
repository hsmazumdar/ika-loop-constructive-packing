# Expt-7B — Decision audit of the frozen indexed ranker

No retraining. Replay the saved Expt-7 libraries, index, ranker, K, and consult budget. Log consultation, ranker scores, commitments, and primitive traces. Remaining-solves of accepted and rejected first-legal sites are diagnosis only.

Consultation cost includes index probes, ranking, applicability, and learned site checks.

Expt-7's 170/170 shortlist recall is **operation** recall on primitive-trajectory snapshots. This audit reports action recall separately.

## Commands

```text
python -m pytest -q
python run_expt7b.py --audit
python run_expt7b.py --smoke
python run_expt7b.py --diagnostic
python run_expt7b.py --report --run-dir results/<timestamp>_<preset>
```

Include consult budget 0 as a comparator: it must reproduce primitive search.
