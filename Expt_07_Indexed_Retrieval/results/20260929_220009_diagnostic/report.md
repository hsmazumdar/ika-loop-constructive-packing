# Expt-7 report

Can bounded indexed retrieval with selective commitment convert frozen-library opportunity into cheaper deployable decisions? The agent cannot see remaining-solve futures.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_07_Indexed_Retrieval\results\20260929_220009_diagnostic`
- Preset: `diagnostic`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Frozen K=2; consult budget=25 (frozen on development before eval)
- Libraries loaded from Expt-6 snapshots; reconstruction=False
- Effort saving = A_primitive − A_agent. Quality-loss rate is separate from mean Q.
- Index lookup is billed. The agent does not see remaining-solve futures.

## Frozen selection

- Development shortlist recall: [{'k': 1, 'n_states_with_oracle_useful': 242, 'n_shortlist_contains_useful': 240, 'recall': 0.9917355371900827}, {'k': 2, 'n_states_with_oracle_useful': 242, 'n_shortlist_contains_useful': 242, 'recall': 1.0}, {'k': 4, 'n_states_with_oracle_useful': 242, 'n_shortlist_contains_useful': 242, 'recall': 1.0}]
- Budget table: [{'consult_budget': 25, 'n': 72, 'mean_saving': -22.36111111111111, 'quality_loss_rate': 0.0}, {'consult_budget': 50, 'n': 72, 'mean_saving': -34.97222222222222, 'quality_loss_rate': 0.0}, {'consult_budget': 100, 'n': 72, 'mean_saving': -41.708333333333336, 'quality_loss_rate': 0.0}, {'consult_budget': 200, 'n': 72, 'mean_saving': -41.708333333333336, 'quality_loss_rate': 0.0}]
- Index build: [{'seed': 11, 'build_s': 0.00016739999409765005, 'n_bytes': 1080, 'n_entries': 3}, {'seed': 22, 'build_s': 0.00019530000281520188, 'n_bytes': 1080, 'n_entries': 3}, {'seed': 33, 'build_s': 0.00017430000298190862, 'n_bytes': 1176, 'n_entries': 4}]

## Factorial on fresh eval boxes

- primitive: n=48; mean Q 75.54 (sd 1.414); mean A 1449 (sd 1617); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation 0; mean index 0; mean ranking 0
- both_gates_frozen: n=0; mean Q NA (sd NA); mean A NA (sd NA); mean effort saving NA; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation NA; mean index NA; mean ranking NA
- indexed_retrieval: n=48; mean Q 75.27 (sd 2.181); mean A 1656 (sd 1872); mean effort saving -207; quality-loss rate 10.42% of boxes; mean-quality preserved: yes; mean consultation 21.65; mean index 11.29; mean ranking 0
- indexed_ranked: n=48; mean Q 75.54 (sd 1.414); mean A 1471 (sd 1618); mean effort saving -22.19; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation 22.19; mean index 10.73; mean ranking 5.604

## Shortlist opportunity recall (diagnosis only)

- Among sampled-oracle states with a useful action, the inexpensive K-shortlist contained at least one useful action in 170 / 170 states (recall 1).
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
