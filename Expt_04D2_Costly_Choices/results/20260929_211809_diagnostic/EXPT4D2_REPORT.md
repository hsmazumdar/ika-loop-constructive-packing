# Expt-4D2 report

Expt-4D2 separates diagnostic artefacts from operation harm. Effort saving = A_primitive - A_agent. Promotion is not changed.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04D2_Costly_Choices\results\20260929_211809_diagnostic`
- Preset: `diagnostic`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Effort saving = A_primitive − A_agent. Positive means fewer evaluations.
- A = primitive_evals + retrieval_cost + applicability_cost + learned_evals.
- retrieve_check_then_primitive stops on primitive evaluations only, so consultation cannot truncate the primitive trajectory.
- Counterfactual remaining-solves are diagnosis only.
- Promotion is unchanged. This experiment does not admit a new applicability learner.

## Accounting (frozen Expt-4D CSV)

- Primitive_evals matched retrieve/check on 23/24 boxes.
- Shared-cap truncations in Expt-4D: 1.
- Mean retrieval_cost 54.96; applicability 54.96; learned site checks 2.542.
- Mean consultation 112.5; published mean ΔA 75.46.
- Retrieval cost alone does not explain net ΔA. Applicability checks are billed separately. The remaining mean gap is the eval-cap artefact.

## Corrected diagnostic modes

- retrieve_check primitive traces identical to primitive: 72/72
- A identity holds: 216/216 rows

- primitive: n=72; mean Q 75.38 (sd 2.745); mean A 1589; mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes
- retrieve_check_then_primitive: n=72; mean Q 75.38 (sd 2.745); mean A 1703; mean effort saving -113.7; quality-loss rate 0% of boxes; mean-quality preserved: yes
  - mean primitive evals 1589; mean consultation 113.7
- normal_reuse: n=72; mean Q 75.39 (sd 2.826); mean A 1816; mean effort saving -227.2; quality-loss rate 4.167% of boxes; mean-quality preserved: yes
  - mean primitive evals 1705; mean consultation 111

## Existing 15 Expt-4D replays (not re-simulated; worst first)

- Mean remaining saving -708.8; median 96.
- Repay check cost: 9/15.
- Quality preserved: 12/15.
- Acceptable successes (both): 8/15.
- Composed: 0. Mixed outcomes do not identify a predictive context; all Expt-4D cases were occupancy 0–24. Hierarchy is untested here.

- r1 33:inv_ffe570c70457:13:occ0:M0003 M0003 occ 0 empty 1/100 saving -6761 QΔ -10 [Q]
- r2 33:inv_22521942205c:2:occ16:M0004 M0004 occ 16 empty 1/84 saving -1855 QΔ -6 [Q]
- r3 33:inv_8b533a843808:11:occ8:M0004 M0004 occ 8 empty 1/92 saving -1519 QΔ -1 [A]
- r4 33:inv_22521942205c:1:occ8:M0004 M0004 occ 8 empty 1/92 saving -1384 QΔ 3 [A]
- r5 33:inv_5fc1ecabd17f:9:occ10:M0003 M0003 occ 10 empty 1/90 saving -980 QΔ 0 [A]
- r6 33:inv_115b41c2392a:7:occ10:M0004 M0004 occ 10 empty 1/90 saving -660 QΔ 1 [A]
- r7 33:inv_22521942205c:0:occ0:M0004 M0004 occ 0 empty 1/100 saving 96 QΔ -1 [ok]
- r8 33:inv_791d780fc6e4:3:occ0:M0004 M0004 occ 0 empty 1/100 saving 96 QΔ -1 [ok]
- r9 33:inv_791d780fc6e4:4:occ8:M0004 M0004 occ 8 empty 1/92 saving 96 QΔ 0 [ok]
- r10 33:inv_791d780fc6e4:5:occ16:M0004 M0004 occ 16 empty 1/84 saving 96 QΔ 3 [ok]
- r11 33:inv_115b41c2392a:6:occ0:M0003 M0003 occ 0 empty 1/100 saving 96 QΔ -3 [Q]
- r12 33:inv_5fc1ecabd17f:8:occ0:M0003 M0003 occ 0 empty 1/100 saving 96 QΔ 0 [ok]
- r13 33:inv_8b533a843808:10:occ0:M0004 M0004 occ 0 empty 1/100 saving 96 QΔ 0 [ok]
- r14 33:inv_1696d00e5191:14:occ0:M0003 M0003 occ 0 empty 1/100 saving 192 QΔ -1 [ok]
- r15 33:inv_8b533a843808:12:occ16:M0004 M0004 occ 16 empty 1/84 saving 1663 QΔ 4 [ok]

## New matched-state replays (reconstructed library, original + fresh boxes)

- n=32; mean -276.4; median 96; acceptable 15/32; composed 0
- By split: development 15, fresh 17
- 33:inv_ffe570c70457:development:0:occ0:M0003 M0003 composed=False saving -6761 [Q] remaining {"B": 6, "C": 5, "H": 4, "I": 1, "L": 1, "O": 2, "P": 1}
- 33:inv_d804ed269077:fresh:0:occ0:M0003 M0003 composed=False saving -2168 [A] remaining {"C": 8, "D": 2, "E": 5, "G": 3, "J": 2}
- 33:inv_22521942205c:development:2:occ16:M0004 M0004 composed=False saving -1855 [Q] remaining {"B": 4, "F": 1, "J": 2, "K": 4, "L": 1, "M": 5, "N": 1}
- 33:inv_8b533a843808:development:1:occ8:M0004 M0004 composed=False saving -1519 [A] remaining {"B": 5, "H": 3, "K": 2, "L": 2, "M": 8}
- 33:inv_22521942205c:development:1:occ8:M0004 M0004 composed=False saving -1384 [A] remaining {"B": 4, "F": 1, "J": 2, "K": 4, "L": 1, "M": 7, "N": 1}
- 33:inv_5fc1ecabd17f:development:1:occ10:M0003 M0003 composed=False saving -980 [A] remaining {"B": 4, "C": 4, "H": 6, "I": 4}
- 33:inv_435a7fc36658:fresh:0:occ0:M0003 M0003 composed=False saving -944 [A] remaining {"C": 7, "H": 3, "I": 6, "O": 5}
- 33:inv_77153bff044a:fresh:2:occ18:M0004 M0004 composed=False saving -756 [A] remaining {"A": 1, "B": 7, "C": 2, "D": 2, "F": 1, "I": 1, "M": 3}
- 33:inv_115b41c2392a:development:1:occ10:M0004 M0004 composed=False saving -660 [A] remaining {"B": 4, "C": 2, "E": 3, "H": 4, "I": 1, "M": 5}
- 33:inv_d99b53836623:fresh:1:occ8:M0004 M0004 composed=False saving -192 [A] remaining {"F": 2, "G": 5, "K": 5, "M": 8}
- 33:inv_22186c94b655:fresh:1:occ8:M0004 M0004 composed=False saving -144 [A] remaining {"D": 3, "E": 5, "K": 4, "M": 5, "N": 3}
- 33:inv_3f3d2af3a5f7:fresh:0:occ0:M0004 M0004 composed=False saving -96 [A] remaining {"D": 4, "E": 4, "F": 3, "H": 1, "M": 4, "N": 6}
- 33:inv_435a7fc36658:fresh:1:occ10:M0003 M0003 composed=False saving -96 [A] remaining {"C": 5, "H": 3, "I": 6, "O": 5}
- 33:inv_77153bff044a:fresh:1:occ10:M0004 M0004 composed=False saving -48 [A] remaining {"A": 1, "B": 7, "C": 2, "D": 2, "F": 1, "I": 1, "M": 5}
- 33:inv_22521942205c:development:0:occ0:M0004 M0004 composed=False saving 96 [ok] remaining {"B": 4, "F": 1, "J": 2, "K": 4, "L": 1, "M": 9, "N": 1}
- 33:inv_791d780fc6e4:development:0:occ0:M0004 M0004 composed=False saving 96 [ok] remaining {"B": 4, "F": 2, "G": 2, "H": 2, "I": 1, "K": 1, "M": 10}
- 33:inv_791d780fc6e4:development:1:occ8:M0004 M0004 composed=False saving 96 [ok] remaining {"B": 4, "F": 2, "G": 2, "H": 2, "I": 1, "K": 1, "M": 8}
- 33:inv_791d780fc6e4:development:2:occ16:M0004 M0004 composed=False saving 96 [ok] remaining {"B": 4, "F": 2, "G": 2, "H": 2, "I": 1, "K": 1, "M": 6}
- 33:inv_115b41c2392a:development:0:occ0:M0003 M0003 composed=False saving 96 [Q] remaining {"B": 4, "C": 4, "E": 3, "H": 4, "I": 1, "M": 5}
- 33:inv_5fc1ecabd17f:development:0:occ0:M0003 M0003 composed=False saving 96 [ok] remaining {"B": 4, "C": 6, "H": 6, "I": 4}

### New replays by operation

- M0003: n=12; mean saving -780.8; acceptable 5/12
- M0004: n=20; mean saving 26.15; acceptable 10/20

## What this does not conclude

- Mixed help/harm does not mean a predictive context has been found.
- With zero composed replays, hierarchy is not tested.
- Promotion is not redesigned here. A later admission rule must use repeated downstream benefit, including severe losses, and must be tested on boxes unused for learning the rule.

The broader reusable-knowledge idea remains unproven, not disproved.
