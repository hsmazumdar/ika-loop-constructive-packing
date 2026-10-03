# Expt-7B report

Does the frozen indexed ranker ever commit, or does it only pay consultation and then copy primitive search? Counterfactual remaining-solves are diagnosis only.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_07B_Decision_Audit\results\20260929_223725_smoke`
- Preset: `smoke`
- Frozen artifacts: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_07_Indexed_Retrieval\results\20260929_220030_diagnostic`
- No retraining. K=2; consult budget=25; budget-0 comparator included.
- consultation_cost = retrieval + applicability + learned site checks + index probes + ranking. Primitive evaluations are separate. The Expt-7 identity A_ranked − A_primitive ≈ consultation used this inclusive total.
- Counterfactual remaining-solves are diagnosis only.

## Cost identity on the audit pairs

- n=4; mean A_primitive 816; mean A_ranked (budget 25) 841.5; mean A_budget0 816; mean (A_ranked − A_primitive) 25.5; mean consultation 25.5 (index 6; ranking 9.75; applicability 9.75; learned 0).
- primitive_evals match primitive A on 4/4 pairs; consultation accounts for the A gap on 4/4 pairs; Q match 4/4.
- Consult budget 0 reproduces the primitive trace on 4/4 pairs.
- Audit A matches frozen Expt-7 indexed_ranked A on 4/4 pairs that exist in eval.csv.

## Does the ranker ever commit?

- Ranker decisions: 39; admit 0; reject 39 (quality 39; predicted saving ≤ remaining check cost 39; both 39).
- Actual commitments: 0 across 0/4 pairs.
- Primitive traces identical to ranked traces: 4/4.
- Consultation attempts: 6 mean per pair; consulted decision steps 24; pairs that exhaust the budget: 4/4; mean first exhaustion step 6.
- Predicted saving mean -237.6; fraction with pred_saving > remaining_check 0/39; mean P(quality_ok) 0.5202; fraction with P ≥ threshold 0/39.

## Counterfactuals of the ranker's tested first-legal sites (diagnosis only)

- Remaining-solves were not collected in this preset.

## Operation recall versus action recall (primitive snapshots, diagnosis only)

- Operation recall (frozen Expt-7 recall_states on these pairs): 21/21 sampled-oracle states whose K-shortlist contains a beneficial operation.
- Action recall: not collected in this preset.
- Expt-7's 170/170 figure is operation recall on primitive-trajectory snapshots. It is not placement-level recall, and it is not measured on the deployed ranked trajectory. The policy may lack budget, may not visit those states, and tests at most one first_legal_site (8 shuffled anchors) per shortlisted op.

## Ledgers

- Diagnostic skip rollouts 0; commit rollouts 0; cache hits 0

## What to change next

- Almost no commitments: inspect score calibration, the remaining-check comparison pred_saving ≤ anchors, and the quality threshold.
- Budget still expires after abstaining lookups: consult timing is secondary until the ranker can accept something.
- Include consultation budget 0 in subsequent development comparisons. Every positive budget in Expt-7 lost to primitive; 25 was the best memory-enabled setting, not the best overall policy.

Cheap retrieval can expose useful options. This audit reports whether the frozen ranker recognizes even a small subset worth executing.
