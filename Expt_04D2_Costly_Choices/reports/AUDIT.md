# Expt-4D2 accounting audit

This audit reads the frozen Expt-4D diagnostic CSV. The learner is not retrained.

## Why retrieve/check primitive evaluations differed

- Pairs: 24; primitive_evals identical on 23/24 boxes.
- Boxes where the shared evaluation cap truncated retrieve/check: 1.
- Mean ΔA (retrieve/check − primitive): 75.46.
- Mean retrieval_cost: 54.96.
- Mean applicability_cost: 54.96.
- Mean learned_evals (site checks): 2.542.
- Mean consultation (retrieval + applicability + learned): 112.5.
- Mean drop in primitive_evals: 37.

A identity: A = primitive_evals + retrieval_cost + applicability_cost + learned_evals.
Retrieval cost alone does not equal net ΔA. Applicability checks are the same order as retrieval.
The remaining gap in the published mean ΔA (+75.46 vs consultation) is the eval-cap truncation:
one box hit the cap, retrieve/check stopped earlier, and primitive_evals fell by 888 on that box alone.
Equal mean Q does not prove identical trajectories on that box.

RNG: retrieve and site search use purpose-tagged streams (`retrieve-*`, `anchor-*`), not `select`.
Board: `macro_fits` copies mask and inventory counts; first_legal_site does not call env.step.
The implementation bug was sharing one Ledger.A between consultation charges and the primitive stopping cap.

## Existing 15 matched-state replays (worst remaining-effort-saving first)

- n=15; mean remaining saving -708.8; median 96.
- Repay check cost: 9/15.
- Preserve quality (commit Q ≥ skip Q − 1): 12/15.
- Acceptable successes (effort and quality): 8/15.
- Composed-operation replays: 0.

Mixed outcomes show that a context predictor is needed. Occupancy band 0–24 does not identify one.
Zero composed replays means this table does not speak to hierarchy.

1. `33:inv_ffe570c70457:13:occ0:M0003` op M0003 size 2 occ 0 empty 1/100 mix B:0.30,C:0.25,H:0.20,O:0.10,I:0.05,L:0.05 A 7481 vs 720 (saving -6761, check 10) Q 65 vs 75 [quality-fail]
2. `33:inv_22521942205c:2:occ16:M0004` op M0004 size 2 occ 16 empty 1/84 mix M:0.28,B:0.22,K:0.22,J:0.11,F:0.06,L:0.06 A 3959 vs 2104 (saving -1855, check 9) Q 72 vs 78 [quality-fail]
3. `33:inv_8b533a843808:11:occ8:M0004` op M0004 size 2 occ 8 empty 1/92 mix M:0.40,B:0.25,H:0.15,K:0.10,L:0.10 A 2191 vs 672 (saving -1519, check 10) Q 75 vs 76 [effort-fail]
4. `33:inv_22521942205c:1:occ8:M0004` op M0004 size 2 occ 8 empty 1/92 mix M:0.35,B:0.20,K:0.20,J:0.10,F:0.05,L:0.05 A 2104 vs 720 (saving -1384, check 9) Q 78 vs 75 [effort-fail]
5. `33:inv_5fc1ecabd17f:9:occ10:M0003` op M0003 size 2 occ 10 empty 1/90 mix H:0.33,B:0.22,C:0.22,I:0.22 A 1652 vs 672 (saving -980, check 9) Q 75 vs 75 [effort-fail]
6. `33:inv_115b41c2392a:7:occ10:M0004` op M0004 size 2 occ 10 empty 1/90 mix M:0.26,B:0.21,H:0.21,E:0.16,C:0.11,I:0.05 A 1332 vs 672 (saving -660, check 9) Q 76 vs 75 [effort-fail]
7. `33:inv_22521942205c:0:occ0:M0004` op M0004 size 2 occ 0 empty 1/100 mix M:0.41,B:0.18,K:0.18,J:0.09,F:0.05,L:0.05 A 720 vs 816 (saving 96, check 9) Q 75 vs 76 [acceptable]
8. `33:inv_791d780fc6e4:3:occ0:M0004` op M0004 size 2 occ 0 empty 1/100 mix M:0.45,B:0.18,F:0.09,G:0.09,H:0.09,I:0.05 A 720 vs 816 (saving 96, check 9) Q 75 vs 76 [acceptable]
9. `33:inv_791d780fc6e4:4:occ8:M0004` op M0004 size 2 occ 8 empty 1/92 mix M:0.40,B:0.20,F:0.10,G:0.10,H:0.10,I:0.05 A 624 vs 720 (saving 96, check 9) Q 75 vs 75 [acceptable]
10. `33:inv_791d780fc6e4:5:occ16:M0004` op M0004 size 2 occ 16 empty 1/84 mix M:0.33,B:0.22,F:0.11,G:0.11,H:0.11,I:0.06 A 528 vs 624 (saving 96, check 10) Q 78 vs 75 [acceptable]
11. `33:inv_115b41c2392a:6:occ0:M0003` op M0003 size 2 occ 0 empty 1/100 mix M:0.24,B:0.19,C:0.19,H:0.19,E:0.14,I:0.05 A 672 vs 768 (saving 96, check 10) Q 75 vs 78 [quality-fail]
12. `33:inv_5fc1ecabd17f:8:occ0:M0003` op M0003 size 2 occ 0 empty 1/100 mix C:0.30,H:0.30,B:0.20,I:0.20 A 672 vs 768 (saving 96, check 9) Q 75 vs 75 [acceptable]
13. `33:inv_8b533a843808:10:occ0:M0004` op M0004 size 2 occ 0 empty 1/100 mix M:0.45,B:0.23,H:0.14,K:0.09,L:0.09 A 672 vs 768 (saving 96, check 9) Q 76 vs 76 [acceptable]
14. `33:inv_1696d00e5191:14:occ0:M0003` op M0003 size 2 occ 0 empty 1/100 mix B:0.33,K:0.24,N:0.24,C:0.19 A 672 vs 864 (saving 192, check 10) Q 76 vs 77 [acceptable]
15. `33:inv_8b533a843808:12:occ16:M0004` op M0004 size 2 occ 16 empty 1/84 mix M:0.33,B:0.28,H:0.17,K:0.11,L:0.11 A 528 vs 2191 (saving 1663, check 11) Q 79 vs 75 [acceptable]

## By operation

- M0003: n=5; mean remaining saving -1471; acceptable 2/5; quality failures 2
- M0004: n=10; mean remaining saving -327.5; acceptable 6/10; quality failures 1

Promotion is not changed in this experiment. Admission later must use repeated downstream benefit,
with attention to severe losses, and an applicability rule evaluated on different boxes from those used to learn it.
