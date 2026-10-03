# Expt-4D report

The broader idea remains unproven, rather than disproved. Expt-4D locates whether reuse loses its advantage in retrieval cost, harmful execution, or wrong-context selection. Effort saving = A_primitive - A_agent; positive means the agent used fewer candidate evaluations.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04D_Where_Reuse_Loses_Advantage\results\20260929_210228_smoke`
- Preset: `smoke`
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

- primitive: n=8; mean Q 76.12 (sd 1.356); mean A 1193 (sd 638.5); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved vs primitive mean: yes (mean Q 76.12 vs primitive 76.12)
- retrieve_check_then_primitive: n=8; mean Q 76.12 (sd 1.356); mean A 1193 (sd 638.5); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved vs primitive mean: yes (mean Q 76.12 vs primitive 76.12)
  - mean retrieval cost 0; mean primitive evals 1193
- normal_reuse: n=8; mean Q 76.12 (sd 1.356); mean A 1193 (sd 638.5); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved vs primitive mean: yes (mean Q 76.12 vs primitive 76.12)
  - mean retrieval cost 0; mean primitive evals 1193; mean library proposals 0; mean bypassed primitive decisions 0

## Counterfactual remaining solves

- No legal learned-operation proposals were replayed.

## Interpretation

- A decomposition: retrieve-and-check adds -0 evaluations versus primitive; then committing changes A by 0 versus retrieve-and-check (positive = committing used still more evaluations).

These statements describe this diagnostic only. The broader reusable-knowledge idea is unproven, not disproved.
