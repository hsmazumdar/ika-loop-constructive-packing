# Expt-7 report

Can bounded indexed retrieval with selective commitment convert frozen-library opportunity into cheaper deployable decisions? The agent cannot see remaining-solve futures.

- Directory: `results\20260929_220030_diagnostic`
- Preset: `diagnostic`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Frozen K=2; consult budget=25 (frozen on development before eval)
- Libraries loaded from Expt-6 snapshots; reconstruction=False
- Effort saving = A_primitive − A_agent. Quality-loss rate is separate from mean Q.
- Index lookup is billed. The agent does not see remaining-solve futures.
- consultation_cost = retrieval + applicability + learned site checks + index probes + ranking. It does not include primitive evaluations. Gate checks are a separate column (zero under indexed conditions).
- Shortlist opportunity recall counts states where some shortlisted *operation* has a beneficial remaining-solve in the sampled oracle. It is not action-level (orientation/anchor) recall, and it is measured on primitive-trajectory snapshots, not on the deployed ranked policy's visited states.

## Frozen selection

- Development shortlist recall: [{'k': 1, 'n_states_with_oracle_useful': 242, 'n_shortlist_contains_useful': 240, 'recall': 0.9917355371900827}, {'k': 2, 'n_states_with_oracle_useful': 242, 'n_shortlist_contains_useful': 242, 'recall': 1.0}, {'k': 4, 'n_states_with_oracle_useful': 242, 'n_shortlist_contains_useful': 242, 'recall': 1.0}]
- Budget table: [{'consult_budget': 25, 'n': 72, 'mean_saving': -22.36111111111111, 'quality_loss_rate': 0.0}, {'consult_budget': 50, 'n': 72, 'mean_saving': -34.97222222222222, 'quality_loss_rate': 0.0}, {'consult_budget': 100, 'n': 72, 'mean_saving': -41.708333333333336, 'quality_loss_rate': 0.0}, {'consult_budget': 200, 'n': 72, 'mean_saving': -41.708333333333336, 'quality_loss_rate': 0.0}]
- Index build: [{'seed': 11, 'build_s': 0.0003397999971639365, 'n_bytes': 1080, 'n_entries': 3}, {'seed': 22, 'build_s': 0.0001453000004403293, 'n_bytes': 1080, 'n_entries': 3}, {'seed': 33, 'build_s': 0.00023729998792987317, 'n_bytes': 1176, 'n_entries': 4}]

## Factorial on fresh eval boxes

- primitive: n=48; mean Q 75.54 (sd 1.414); mean A 1449 (sd 1617); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation 0; mean index 0; mean ranking 0
- both_gates_frozen: n=48; mean Q 75.54 (sd 1.414); mean A 1838 (sd 1690); mean effort saving -389; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation 373; mean index 0; mean ranking 0
- indexed_retrieval: n=48; mean Q 75.27 (sd 2.181); mean A 1656 (sd 1872); mean effort saving -207; quality-loss rate 10.42% of boxes; mean-quality preserved: yes; mean consultation 21.65; mean index 11.29; mean ranking 0
- indexed_ranked: n=48; mean Q 75.54 (sd 1.414); mean A 1471 (sd 1618); mean effort saving -22.19; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation 22.19; mean index 10.73; mean ranking 5.604

## Cost identity

- Mean (A_indexed_ranked − A_primitive) = 22.19; mean consultation_cost = 22.19; mean ranked primitive_evals = 1449 vs primitive mean A 1449.
- If those two differences match, remaining extra A is consultation overhead (index + ranking + applicability + site checks), not extra primitive search.

## Shortlist opportunity recall (diagnosis only)

- Among sampled-oracle primitive-trajectory states with a beneficial *operation*, the K-shortlist contained at least one such operation in 170 / 170 states (operation recall 1). This is not placement-level recall and is not measured on the deployed trajectory.
- High recall is insufficient without whole-box effort and quality above.

## Ledgers

- Ranker learning remaining-solves: 435332
- Eval diagnostic oracle (recall only): skip 336; commit 4788
- Historical Expt-5 learning_A 486500 (not billed here)

## Answers

- Does indexed access beat current gates on frozen libraries? See mean A and quality-loss above.
- Does learned ranking add anything over the index shortlist alone? Compare indexed_retrieval vs indexed_ranked.
- If free-oracle opportunity existed in Expt-6 and this policy still raises A, the remaining failure is inexpensive selection, not library content.

The agent cannot see remaining-solve futures. Expt-7 eval boxes cannot later be reused as untouched confirmation tests.
