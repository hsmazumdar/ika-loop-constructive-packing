# Expt-7 report

Can bounded indexed retrieval with selective commitment convert frozen-library opportunity into cheaper deployable decisions? The agent cannot see remaining-solve futures.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_07_Indexed_Retrieval\results\20260929_215949_smoke`
- Preset: `smoke`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Frozen K=2; consult budget=50 (frozen on development before eval)
- Libraries loaded from Expt-6 snapshots; reconstruction=False
- Effort saving = A_primitive − A_agent. Quality-loss rate is separate from mean Q.
- Index lookup is billed. The agent does not see remaining-solve futures.

## Frozen selection

- Development shortlist recall: [{'k': 2, 'n_states_with_oracle_useful': 8, 'n_shortlist_contains_useful': 8, 'recall': 1.0}]
- Budget table: [{'consult_budget': 50, 'note': 'smoke: frozen without sweep'}]
- Index build: [{'seed': 11, 'build_s': 0.0001686000032350421, 'n_bytes': 1080, 'n_entries': 3}]

## Factorial on fresh eval boxes

- primitive: n=4; mean Q 75 (sd 2.16); mean A 2335 (sd 2976); mean effort saving 0; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation 0; mean index 0; mean ranking 0
- both_gates_frozen: n=0; mean Q NA (sd NA); mean A NA (sd NA); mean effort saving NA; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation NA; mean index NA; mean ranking NA
- indexed_retrieval: n=4; mean Q 74.5 (sd 3.109); mean A 1752 (sd 1329); mean effort saving 583.8; quality-loss rate 25% of boxes; mean-quality preserved: yes; mean consultation 27.5; mean index 15.75; mean ranking 0
- indexed_ranked: n=4; mean Q 75 (sd 2.16); mean A 2370 (sd 2986); mean effort saving -34.25; quality-loss rate 0% of boxes; mean-quality preserved: yes; mean consultation 34.25; mean index 15; mean ranking 9.25

## Shortlist opportunity recall (diagnosis only)

- Among sampled-oracle states with a useful action, the inexpensive K-shortlist contained at least one useful action in 10 / 10 states (recall 1).
- High recall is insufficient without whole-box effort and quality above.

## Ledgers

- Ranker learning remaining-solves: 51219
- Eval diagnostic oracle (recall only): skip 16; commit 112
- Historical Expt-5 learning_A 486500 (not billed here)

## Answers

- Does indexed access beat current gates on frozen libraries? See mean A and quality-loss above.
- Does learned ranking add anything over the index shortlist alone? Compare indexed_retrieval vs indexed_ranked.
- If free-oracle opportunity existed in Expt-6 and this policy still raises A, the remaining failure is inexpensive selection, not library content.

The agent cannot see remaining-solve futures. Expt-7 eval boxes cannot later be reused as untouched confirmation tests.
