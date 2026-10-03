# Expt-4B report

The objective of this experiment is not to discover a better packing heuristic. Packing is the observable environment. Expt-4 has implemented remembering and composition. Expt-4B tests whether the system can learn selective, beneficial reuse.

The research question: can the agent autonomously distinguish a recurring pattern from a useful piece of knowledge?

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04B_Selective_Reuse\results\20260929_193923_diagnostic`
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
- current_hierarchy: Q n=24 mean 74.79 sd 3.336; A mean 2498 sd 2438; mean Q/A 0.05599
- utility_promotion: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- contextual_abstention: Q n=24 mean 74.92 sd 3.189; A mean 2453 sd 2330; mean Q/A 0.05536
- both: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059

### Experience 30

- primitive: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- current_hierarchy: Q n=24 mean 74.79 sd 3.107; A mean 2847 sd 2228; mean Q/A 0.04484
- utility_promotion: Q n=24 mean 74.96 sd 3.014; A mean 2510 sd 2516; mean Q/A 0.05522
- contextual_abstention: Q n=24 mean 74.17 sd 3.608; A mean 3000 sd 2710; mean Q/A 0.05086
- both: Q n=24 mean 74.88 sd 2.879; A mean 2289 sd 2334; mean Q/A 0.05695

### Experience 60

- primitive: Q n=24 mean 75.12 sd 3.012; A mean 2268 sd 2348; mean Q/A 0.06059
- current_hierarchy: Q n=24 mean 73.67 sd 4.32; A mean 3003 sd 2498; mean Q/A 0.04506
- utility_promotion: Q n=24 mean 74.58 sd 2.933; A mean 2768 sd 2609; mean Q/A 0.05023
- contextual_abstention: Q n=24 mean 74.46 sd 3.217; A mean 2854 sd 2663; mean Q/A 0.0514
- both: Q n=24 mean 75.08 sd 2.948; A mean 2108 sd 2284; mean Q/A 0.06061

## Condition answers

- Primitive baseline at last checkpoint: Q 75.12, A 2268.
- Current hierarchy vs primitive A: 3003 vs 2268. The Expt-4 failure (library raises A) was reproduced.
- Utility-based promotion vs current hierarchy A: 2768 vs 3003. Harmful admissions look reduced.
- Contextual retrieval/abstention vs current hierarchy A: 2854 vs 3003. Unsuitable uses look reduced.
- Both changes together vs primitive A: 2108 vs 2268. Selective acquisition plus selective use produced a benefit.

## Paired validation (training-only)

- Candidates tested: 28; promoted 8; kept provisional 20.
- Held-out boxes were not used in pairing.

## Operation logs

- primitive: 0 stored records, 0 active, retrievals 0, applicability failures 0, commitments 0.
- current_hierarchy: 8 stored records, 8 active, retrievals 2827, applicability failures 0, commitments 185.
- utility_promotion: 10 stored records, 3 active, retrievals 1225, applicability failures 0, commitments 101.
- contextual_abstention: 8 stored records, 8 active, retrievals 2988, applicability failures 2754, commitments 115.
- both: 18 stored records, 5 active, retrievals 2015, applicability failures 1925, commitments 61.

These statements describe this diagnostic only. They do not claim that intelligence has emerged.
