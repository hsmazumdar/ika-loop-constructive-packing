# Expt-5 report

Can experience teach the agent when accessing memory is worth its cost, and when retrieved knowledge should be acted upon? Effort saving = A_primitive - A_agent. Gate checks are billed. Counterfactual labels are a learning cost.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_05_Consult_and_Commit_Gates\results\20260929_212640_smoke`
- Preset: `smoke`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Eval boxes: 4
- Learning cost (counterfactual remaining-solves + collection retrieve/check): 5840 evaluations. This is not added to eval A.
- Eval A = primitive_evals + retrieval + applicability + learned site checks + gate checks.
- Effort saving = A_primitive − A_agent.
- Quality-loss rate is the fraction of boxes with Q_agent < Q_primitive − 1. It is separate from mean Q.
- Gates were frozen on held-out training-replay boxes before this eval.
- No handwritten reject-M0003-on-empty-board rule.

## Frozen gate

- Commit labels 0; consult states 0; selected 0; unchosen sampled 0
- Consult threshold [1.0]; commit threshold [1.0]
- Learned per-op commit bias: {11: {}}

Per-op bias is estimated from replay labels. A negative bias on an operation is a learned association, not a coded prohibition.

## Factorial on frozen eval boxes

- primitive: n=4; mean Q 73.25 (sd 6.185); mean A 1834 (sd 717.4); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 0; mean consultation 0
- current_selective: n=4; mean Q 73.25 (sd 6.185); mean A 1834 (sd 717.4); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 0; mean consultation 0
- consult_gate_only: n=4; mean Q 73.25 (sd 6.185); mean A 1851 (sd 719.9); mean effort saving -17.25; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 17.25; mean consultation 0
- commit_gate_only: n=4; mean Q 73.25 (sd 6.185); mean A 1834 (sd 717.4); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 0; mean consultation 0
- both_gates: n=4; mean Q 73.25 (sd 6.185); mean A 1851 (sd 719.9); mean effort saving -17.25; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 17.25; mean consultation 0

## Answers

- Current selective vs primitive mean A: 1834 vs 1834.
- Both gates vs primitive mean A: 1851 vs 1834.
- Consultation change only vs commitment change only: see the rows above. The two decisions are not interchangeable.
- If both gates still raise A, experience has not yet taught the agent when memory is worth its cost.

These statements describe this run only. Useful knowledge must reduce future deliberation after paying for selection and use.
