# Expt-18 — Bounded utility of recurring arrangements

Expt-17 found 58 arrangements that recur across inventories and often fit in free space. Recognising them by scanning every translation at every prefix costs about 456 times the predeclared 0.10 budget on fresh inventories and about 818 times on recurring families. This experiment does not relax that gate and does not build a matcher.

It replays a predeclared sample of those legal placements. One placement is kept per box, pattern, and early or middle stage: the earliest prefix in that stage, and the first fitting translation. From that saved state, "commit the pattern, then primitive" is compared with "primitive only". Commitment checks are part of the commit cost. The box-level result is the best quality-preserving candidate, not the sum of overlapping suffixes. All of that computation is diagnostic.

The decision is one of:

- little quality-preserving benefit even with ideal selection: stop this pattern-reuse branch
- benefit concentrated in a few patterns or contexts: a narrowly targeted retrieval rule would be the next question
- substantial benefit across independent boxes, stages, and patterns: a later experiment may build a budgeted matcher

```text
python -m pytest -q
python run_expt18.py --smoke
python run_expt18.py --diagnostic
```
