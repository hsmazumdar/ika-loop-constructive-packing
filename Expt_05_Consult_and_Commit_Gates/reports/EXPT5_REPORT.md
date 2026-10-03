# Expt-5 report

Can experience teach the agent when accessing memory is worth its cost, and when retrieved knowledge should be acted upon? Effort saving = A_primitive - A_agent. Gate checks are billed. Counterfactual labels are a learning cost.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_05_Consult_and_Commit_Gates\results\20260929_212658_diagnostic`
- Preset: `diagnostic`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Eval boxes: 16
- Learning cost (counterfactual remaining-solves + collection retrieve/check): 486500 evaluations. This is not added to eval A.
- Eval A = primitive_evals + retrieval + applicability + learned site checks + gate checks.
- Effort saving = A_primitive − A_agent.
- Quality-loss rate is the fraction of boxes with Q_agent < Q_primitive − 1. It is separate from mean Q.
- Gates were frozen on held-out training-replay boxes before this eval.
- No handwritten reject-M0003-on-empty-board rule.

## Frozen gate

- Commit labels 143; consult states 81; selected 30; unchosen sampled 113
- Consult threshold [0.4965075395908959, 0.3, 0.20254406144797493]; commit threshold [0.5, 0.2518568049872144, 0.12942687432301636]
- Learned per-op commit bias: {11: {'M0009': -0.16512031726149898, 'M0002': 0.11130659173655005, 'M0011': -0.09717988031863616}, 22: {'M0001': 0.12525526926878464, 'M0006': 0.03043068177139514, 'M0010': -0.4121265449035752}, 33: {'M0003': -0.7623677447379468, 'M0006': 0.0977084639072257, 'M0004': -0.05094960123292967, 'M0001': 0.013186713162914148}}

Per-op bias is estimated from replay labels. A negative bias on an operation is a learned association, not a coded prohibition.

## Factorial on frozen eval boxes

- primitive: n=48; mean Q 75.6 (sd 2.181); mean A 1442 (sd 1439); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 0; mean consultation 0
- current_selective: n=48; mean Q 75.4 (sd 2.499); mean A 2158 (sd 1749); mean effort saving -715.5; quality-loss rate 4.167% of boxes; mean-quality preserved: yes; mean gate cost 0; mean consultation 520.4
- consult_gate_only: n=48; mean Q 75.6 (sd 2.181); mean A 1821 (sd 1521); mean effort saving -378.8; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 16.62; mean consultation 362.2
- commit_gate_only: n=48; mean Q 75.44 (sd 2.526); mean A 2170 (sd 1746); mean effort saving -728.1; quality-loss rate 4.167% of boxes; mean-quality preserved: yes; mean gate cost 0.3542; mean consultation 520.7
- both_gates: n=48; mean Q 75.6 (sd 2.181); mean A 1821 (sd 1521); mean effort saving -378.8; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean gate cost 16.62; mean consultation 362.2

## Answers

- Current selective vs primitive mean A: 2158 vs 1442.
- Both gates vs primitive mean A: 1821 vs 1442.
- Consultation change only vs commitment change only: see the rows above. The two decisions are not interchangeable.
- If both gates still raise A, experience has not yet taught the agent when memory is worth its cost.

These statements describe this run only. Useful knowledge must reduce future deliberation after paying for selection and use.
