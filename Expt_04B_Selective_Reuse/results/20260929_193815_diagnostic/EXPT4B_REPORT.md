# Expt-4B report

The objective of this experiment is not to discover a better packing heuristic. Packing is the observable environment. Expt-4 has implemented remembering and composition. Expt-4B tests whether the system can learn selective, beneficial reuse.

The research question: can the agent autonomously distinguish a recurring pattern from a useful piece of knowledge?

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04B_Selective_Reuse\results\20260929_193815_diagnostic`
- Preset: `diagnostic`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Q_min: 75.0

Q/A below is the mean of per-box ratios, not mean Q divided by mean A.
Internal execution is reported and is not added to A.

## Held-out comparison

### Experience 0

- primitive: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- current_hierarchy: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- utility_promotion: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- contextual_abstention: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- both: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059

### Experience 15

- primitive: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- current_hierarchy: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- utility_promotion: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- contextual_abstention: Q n=24 mean 75.12 sd 3.012; A mean 2283 sd 2341; mean Q/A 0.05929
- both: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059

### Experience 30

- primitive: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- current_hierarchy: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- utility_promotion: Q n=24 mean 74.96 sd 3.014; A mean 2510 sd 2516; mean Q/A 0.05522
- contextual_abstention: Q n=24 mean 75.12 sd 3.012; A mean 2315 sd 2327; mean Q/A 0.05697
- both: Q n=24 mean 75.12 sd 3.012; A mean 2320 sd 2366; mean Q/A 0.05811

### Experience 60

- primitive: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- current_hierarchy: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- utility_promotion: Q n=24 mean 74.58 sd 2.933; A mean 2768 sd 2609; mean Q/A 0.05023
- contextual_abstention: Q n=24 mean 75.12 sd 3.012; A mean 2519 sd 2368; mean Q/A 0.04854
- both: Q n=24 mean 75.12 sd 3.012; A mean 2421 sd 2382; mean Q/A 0.0532

## Condition answers

- Primitive baseline at last checkpoint: Q 75.12, A 2268.
- Current hierarchy vs primitive A: 2268 vs 2268. The Expt-4 failure was not reproduced on this schedule.
- Utility-based promotion vs current hierarchy A: 2768 vs 2268. Utility promotion did not lower A below recurrence promotion.
- Contextual retrieval/abstention vs current hierarchy A: 2519 vs 2268. Abstention did not lower A below always-consulting retrieval.
- Both changes together vs primitive A: 2421 vs 2268. Together they did not beat the primitive baseline on this diagnostic.

## Paired validation (training-only)

- Candidates tested: 31; promoted 12; kept provisional 19.
- Held-out boxes were not used in pairing.

## Operation logs

- primitive: 0 stored records, 0 active, retrievals 0, applicability failures 0, commitments 0.
- current_hierarchy: 25 stored records, 0 active, retrievals 431, applicability failures 0, commitments 27.
- utility_promotion: 10 stored records, 3 active, retrievals 1225, applicability failures 0, commitments 101.
- contextual_abstention: 23 stored records, 20 active, retrievals 3059, applicability failures 3059, commitments 0.
- both: 21 stored records, 9 active, retrievals 3057, applicability failures 3057, commitments 0.

These statements describe this diagnostic only. They do not claim that intelligence has emerged.
