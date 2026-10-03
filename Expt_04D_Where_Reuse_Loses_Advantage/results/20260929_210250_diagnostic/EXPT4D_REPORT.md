# Expt-4D report

The broader idea remains unproven, rather than disproved. Expt-4D locates whether reuse loses its advantage in retrieval cost, harmful execution, or wrong-context selection. Effort saving = A_primitive - A_agent; positive means the agent used fewer candidate evaluations.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04D_Where_Reuse_Loses_Advantage\results\20260929_210250_diagnostic`
- Preset: `diagnostic`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Development boxes: 8
- Quality-loss margin (declared before the run): 1.0 occupied cells
- Effort saving = A_primitive − A_agent. Positive means the agent used fewer evaluations.
- Quality-loss rate = fraction of boxes with Q_agent < Q_primitive − margin.
- Mean-quality preservation = whether mean Q is within the margin of the primitive mean. This is not the 20% box-rate gate.
- The 'quality losses ≤ 20%' criterion is the per-box quality-loss rate. It allows one in five boxes to exceed the margin even when mean Q looks fine.
- Counterfactual remaining-solves are diagnosis only. A deployed agent does not receive both futures.

## Diagnostic modes on the development set

- primitive: n=24; mean Q 76.17 (sd 1.579); mean A 1621 (sd 1792); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved vs primitive mean: yes (mean Q 76.17 vs primitive 76.17)
- retrieve_check_then_primitive: n=24; mean Q 76.17 (sd 1.579); mean A 1696 (sd 1649); mean effort saving -75.46; quality-loss rate 0% of boxes; mean-quality preserved vs primitive mean: yes (mean Q 76.17 vs primitive 76.17)
  - mean retrieval cost 54.96; mean primitive evals 1584
- normal_reuse: n=24; mean Q 76.25 (sd 1.622); mean A 1652 (sd 1666); mean effort saving -31.17; quality-loss rate 4.167% of boxes; mean-quality preserved vs primitive mean: yes (mean Q 76.25 vs primitive 76.17)
  - mean retrieval cost 52.96; mean primitive evals 1545; mean library proposals 0.625; mean bypassed primitive decisions 0.625

## Counterfactual remaining solves

- Replays: 15; flat 15; composed 0
- Mean remaining effort saving -708.8; median 96 (positive = commit then primitive used fewer remaining evaluations than primitive-only)
- Mean final quality difference (commit − skip) -0.8
- Replays whose remaining effort saving exceeded check cost: 9/15
- Flat remaining effort saving -708.8

## Interpretation

- Harmful execution is concentrated in a minority of commits: mean remaining-solve A after committing is higher than primitive from the same state, but the median remaining effort saving is positive. Revise candidate generation and promotion so those tail cases are not admitted.
- Benefits are restricted to identifiable contexts: some operations help remaining effort, others do not. Improve the applicability learner.
- Help/harm by occupancy at the choice: 0-24 occupied: 9/15 help remaining effort (mean remaining saving -708.8).
- A decomposition: retrieve-and-check adds 75.46 evaluations versus primitive; then committing changes A by -44.29 versus retrieve-and-check (positive = committing used still more evaluations).
- Mean retrieval-and-check cost per proposed commit: 9.467 evaluations.
- Replays that more than repaid their check cost: 9/15; replays that did not: 6/15.

These statements describe this diagnostic only. The broader reusable-knowledge idea is unproven, not disproved.
