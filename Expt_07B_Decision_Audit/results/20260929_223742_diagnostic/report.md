# Expt-7B report

Does the frozen indexed ranker ever commit, or does it only pay consultation and then copy primitive search? Counterfactual remaining-solves are diagnosis only.

- Directory: `results\20260929_223742_diagnostic`
- Preset: `diagnostic`
- Frozen artifacts: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_07_Indexed_Retrieval\results\20260929_220030_diagnostic`
- No retraining. K=2; consult budget=25; budget-0 comparator included.
- consultation_cost = retrieval + applicability + learned site checks + index probes + ranking. Primitive evaluations are separate. The Expt-7 identity A_ranked − A_primitive ≈ consultation used this inclusive total.
- Counterfactual remaining-solves are diagnosis only.

## Cost identity on the audit pairs

- n=48; mean A_primitive 1449; mean A_ranked (budget 25) 1471; mean A_budget0 1449; mean (A_ranked − A_primitive) 22.19; mean consultation 22.19 (index 10.73; ranking 5.604; applicability 5.854; learned 0).
- primitive_evals match primitive A on 48/48 pairs; consultation accounts for the A gap on 48/48 pairs; Q match 48/48.
- Consult budget 0 reproduces the primitive trace on 48/48 pairs.
- Audit A matches frozen Expt-7 indexed_ranked A on 48/48 pairs that exist in eval.csv.

## Does the ranker ever commit?

- Ranker decisions: 269; admit 0; reject 269 (quality 246; predicted saving ≤ remaining check cost 269; both 246).
- Actual commitments: 0 across 0/48 pairs.
- Primitive traces identical to ranked traces: 48/48.
- Consultation attempts: 10.73 mean per pair; consulted decision steps 515; pairs that exhaust the budget: 29/48; mean first exhaustion step 7.31.
- Predicted saving mean -506.8; median -665.6; max -192.4; fraction with pred_saving > remaining_check 0/269; mean P(quality_ok) 0.5865; fraction with P ≥ threshold 23/269. Saving-only rejects 23; quality-only rejects 0.

## Counterfactuals of the ranker's tested first-legal sites (diagnosis only)

- Admitted first-legal sites with a remaining-solve: 0; beneficial_free NA; mean remaining_saving NA.
- Rejected first-legal sites with a remaining-solve: 247; beneficial_free 134/247; quality_ok failures 29; mean remaining_saving -326.6; median 48; severe losses (< −200) 82.
- These are the ranker's first_legal_site actions, not the sampled-oracle best placement. The ranker did not commit any of them.

## Operation recall versus action recall (primitive snapshots, diagnosis only)

- Operation recall (frozen Expt-7 recall_states on these pairs): 170/170 sampled-oracle states whose K-shortlist contains a beneficial operation.
- Action recall (first_legal_site of a shortlisted op has a beneficial remaining-solve): 77/170.
- Expt-7's 170/170 figure is operation recall on primitive-trajectory snapshots. It is not placement-level recall, and it is not measured on the deployed ranked trajectory. The policy may lack budget, may not visit those states, and tests at most one first_legal_site (8 shuffled anchors) per shortlisted op.

## Ledgers

- Diagnostic skip rollouts 423; commit rollouts 423; cache hits 0

## What to change next

- Almost no commitments: inspect score calibration. Predicted remaining-saving never exceeded the remaining-check cost of 8, and quality also rejected most scored operations.
- Budget still expires after abstaining lookups: consult timing is secondary until the ranker can accept something. Include budget 0 in that comparison.
- Correct operation, wrong first-legal placement: improve action-level selection (anchors/orientation), not only op shortlisting.
- No commitments occurred, so cancelling gains and losses are not a deployed-policy effect. Counterfactuals of the rejected first-legal sites are mixed (median remaining-saving can be positive while the mean is pulled negative by severe losses). Downstream-value prediction and severe-loss handling still matter if the ranker is ever allowed to admit.
- Include consultation budget 0 in subsequent development comparisons. Every positive budget in Expt-7 lost to primitive; 25 was the best memory-enabled setting, not the best overall policy.

Cheap retrieval can expose useful options. This audit reports whether the frozen ranker recognizes even a small subset worth executing.
