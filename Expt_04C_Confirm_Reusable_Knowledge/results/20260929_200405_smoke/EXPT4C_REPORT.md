# Expt-4C report

The objective of this experiment is not to discover a better packing heuristic. Expt-4C keeps the Expt-4B selective mechanism unchanged and asks whether learned knowledge genuinely reduces future deliberation under transfer and lesion.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04C_Confirm_Reusable_Knowledge\results\20260929_200405_smoke`
- Preset: `smoke`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Quality-loss margin (declared before the run): 1.0 occupied cells
- Final test boxes: 8
- Training seeds: (11,)
- Training boxes per seed: 8

Q/A is not the primary measure. Wins require preserved quality within the predeclared margin and strictly lower A.

## Final-test means

- primitive: Q mean 75.25 sd 3.412; A mean 1272 sd 903.4; % Q>=75 87.5; wall-clock mean 0.01445 s
- selective_flat: Q mean 75.25 sd 3.412; A mean 1272 sd 903.4; % Q>=75 87.5; wall-clock mean 0.01502 s
- selective_hierarchical: Q mean 75.25 sd 3.412; A mean 1272 sd 903.4; % Q>=75 87.5; wall-clock mean 0.01494 s
- transfer: Q mean 75.25 sd 3.412; A mean 1272 sd 903.4; % Q>=75 87.5; wall-clock mean 0.0151 s
- lesion: Q mean 75.25 sd 3.412; A mean 1272 sd 903.4; % Q>=75 87.5; wall-clock mean 0.01438 s

## Per-seed wins / ties / losses versus primitive

- lesion seed 11: wins 0, ties 8, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.25
- selective_flat seed 11: wins 0, ties 8, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.25
- selective_hierarchical seed 11: wins 0, ties 8, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.25
- transfer seed 11: wins 0, ties 8, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.25

## Decisive questions

1. Combined agent repeatedly saves effort while preserving quality? 0/1 seeds have median ΔA > 0 with quality losses ≤ 20% of boxes.
2. Fresh agent inherits savings through transferred knowledge? 0/1 seeds; transfer mean A 1272 vs hierarchical 1272.
3. Savings disappear when learned operations are disabled? lesion mean A 1272 vs primitive 1272 vs hierarchical 1272.
4. Hierarchical knowledge outperforms equally selective flat knowledge? hierarchical mean A 1272 vs flat 1272.

These statements describe this run only. They do not claim that intelligence has emerged.
