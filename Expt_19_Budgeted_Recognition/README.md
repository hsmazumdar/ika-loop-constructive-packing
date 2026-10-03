# Expt-19 — Budgeted recognition

Expt-18 found quality-preserving opportunities in the frozen 58 arrangements, including midway through packing. It did not show that those actions can be found cheaply, and 25 of 91 fresh candidates lost more than one quality cell. This experiment tests recognition only. Commitment is disabled.

The matcher is developed as a fixed rule. Development manifests supply the absolute per-box budget: one tenth of their mean primitive effort. The agent does not know an eval box's primitive cost. Validation fresh is the decision set. Eight validation-family tasks that also appear in the development family manifest are excluded.

The rule:

- drop patterns whose pieces are unavailable, and bill the check
- look only at a small deterministic frontier, or at `(0, 0)` when the board is empty
- cache compatibility, and bill creation, update, and invalidation
- stop consulting when the absolute budget is spent, and do not place

Recall is whether the matcher exposes the same pattern at the same origin as a sampled reference action that preserves quality. A different placement of the same pattern is not a hit. The reference is not an exhaustive catalogue. Stronger-support patterns are reported separately from support-two patterns.

Diagnostic `20260930_092450` failed the 0.10 cost gate on validation fresh (recognition was 0.113 of primitive effort). Recall does not override that failure. The access design is stopped, and commitment was not opened. The result is a failed recognizer: the stored arrangements are not thereby useless, and a learned embedding was not tested.

```text
python -m pytest -q
python run_expt19.py --smoke
python run_expt19.py --diagnostic
```
