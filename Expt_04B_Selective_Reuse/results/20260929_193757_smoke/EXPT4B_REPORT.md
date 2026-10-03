# Expt-4B report

The objective of this experiment is not to discover a better packing heuristic. Packing is the observable environment. Expt-4 has implemented remembering and composition. Expt-4B tests whether the system can learn selective, beneficial reuse.

The research question: can the agent autonomously distinguish a recurring pattern from a useful piece of knowledge?

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04B_Selective_Reuse\results\20260929_193757_smoke`
- Preset: `smoke`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Q_min: 75.0

Q/A below is the mean of per-box ratios, not mean Q divided by mean A.
Internal execution is reported and is not added to A.

## Held-out comparison

### Experience 0

- primitive: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- current_hierarchy: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- utility_promotion: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- contextual_abstention: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- both: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432

### Experience 5

- primitive: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- current_hierarchy: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- utility_promotion: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- contextual_abstention: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- both: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432

### Experience 10

- primitive: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- current_hierarchy: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- utility_promotion: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432
- contextual_abstention: Q n=3 mean 68.67 sd 8.083; A mean 2949 sd 477.9; mean Q/A 0.02402
- both: Q n=3 mean 68.67 sd 8.083; A mean 2914 sd 477.1; mean Q/A 0.02432

## Condition answers

- Primitive baseline at last checkpoint: Q 68.67, A 2914.
- Current hierarchy vs primitive A: 2914 vs 2914. The Expt-4 failure was not reproduced on this schedule.
- Utility-based promotion vs current hierarchy A: 2914 vs 2914. Utility promotion did not lower A below recurrence promotion.
- Contextual retrieval/abstention vs current hierarchy A: 2949 vs 2914. Abstention did not lower A below always-consulting retrieval.
- Both changes together vs primitive A: 2914 vs 2914. Together they did not beat the primitive baseline on this diagnostic.

## Paired validation (training-only)

- Candidates tested: 1; promoted 0; kept provisional 1.
- Held-out boxes were not used in pairing.

## Operation logs

- primitive: 0 stored records, 0 active, retrievals 0, applicability failures 0, commitments 0.
- current_hierarchy: 0 stored records, 0 active, retrievals 0, applicability failures 0, commitments 0.
- utility_promotion: 0 stored records, 0 active, retrievals 0, applicability failures 0, commitments 0.
- contextual_abstention: 1 stored records, 1 active, retrievals 0, applicability failures 0, commitments 0.
- both: 1 stored records, 0 active, retrievals 0, applicability failures 0, commitments 0.

These statements describe this diagnostic only. They do not claim that intelligence has emerged.
