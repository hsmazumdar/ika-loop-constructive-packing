# Expt-4C report

The objective of this experiment is not to discover a better packing heuristic. Expt-4C keeps the Expt-4B selective mechanism unchanged and asks whether learned knowledge genuinely reduces future deliberation under transfer and lesion.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_04C_Confirm_Reusable_Knowledge\results\20260929_200422_confirm`
- Preset: `confirm`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Quality-loss margin (declared before the run): 1.0 occupied cells
- Final test boxes: 100
- Training seeds: (11, 22, 33, 44, 55, 66, 77, 88, 99, 111)
- Training boxes per seed: 200

Q/A is not the primary measure. Wins require preserved quality within the predeclared margin and strictly lower A.

## Final-test means

- primitive: Q mean 75.45 sd 2.04; A mean 1612 sd 1690; % Q>=75 88.9; wall-clock mean 0.01898 s
- selective_flat: Q mean 75.42 sd 2.172; A mean 1923 sd 1723; % Q>=75 89.2; wall-clock mean 0.01913 s
- selective_hierarchical: Q mean 75.14 sd 2.517; A mean 2251 sd 2107; % Q>=75 84.3; wall-clock mean 0.0209 s
- transfer: Q mean 75.14 sd 2.517; A mean 2251 sd 2107; % Q>=75 84.3; wall-clock mean 0.02072 s
- lesion: Q mean 75.45 sd 2.04; A mean 1612 sd 1690; % Q>=75 88.9; wall-clock mean 0.01894 s

## Per-seed wins / ties / losses versus primitive

- lesion seed 11: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.51
- lesion seed 22: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.48
- lesion seed 33: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.39
- lesion seed 44: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.4
- lesion seed 55: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.66
- lesion seed 66: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.48
- lesion seed 77: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.38
- lesion seed 88: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.07
- lesion seed 99: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.64
- lesion seed 111: wins 0, ties 100, effort losses 0, quality losses 0; mean ΔA 0; median ΔA 0; mean Q 75.49
- selective_flat seed 11: wins 13, ties 0, effort losses 78, quality losses 9; mean ΔA -302.2; median ΔA -336; mean Q 75.25
- selective_flat seed 22: wins 19, ties 0, effort losses 69, quality losses 12; mean ΔA -387.5; median ΔA -358.5; mean Q 75.6
- selective_flat seed 33: wins 12, ties 0, effort losses 75, quality losses 13; mean ΔA -508; median ΔA -349.5; mean Q 75.17
- selective_flat seed 44: wins 19, ties 0, effort losses 72, quality losses 9; mean ΔA -169.6; median ΔA -304.5; mean Q 75.5
- selective_flat seed 55: wins 18, ties 0, effort losses 70, quality losses 12; mean ΔA -347.3; median ΔA -276; mean Q 75.48
- selective_flat seed 66: wins 18, ties 0, effort losses 71, quality losses 11; mean ΔA -265.4; median ΔA -320; mean Q 75.55
- selective_flat seed 77: wins 28, ties 0, effort losses 58, quality losses 14; mean ΔA -318.9; median ΔA -261.5; mean Q 75.49
- selective_flat seed 88: wins 20, ties 0, effort losses 73, quality losses 7; mean ΔA -177.8; median ΔA -339; mean Q 75.28
- selective_flat seed 99: wins 20, ties 0, effort losses 67, quality losses 13; mean ΔA -166.7; median ΔA -290; mean Q 75.55
- selective_flat seed 111: wins 9, ties 0, effort losses 81, quality losses 10; mean ΔA -472.2; median ΔA -336.5; mean Q 75.29
- selective_hierarchical seed 11: wins 12, ties 0, effort losses 82, quality losses 6; mean ΔA -306; median ΔA -339; mean Q 75.55
- selective_hierarchical seed 22: wins 16, ties 0, effort losses 69, quality losses 15; mean ΔA -786; median ΔA -369.5; mean Q 75.12
- selective_hierarchical seed 33: wins 15, ties 0, effort losses 69, quality losses 16; mean ΔA -658.5; median ΔA -336; mean Q 75.09
- selective_hierarchical seed 44: wins 19, ties 0, effort losses 66, quality losses 15; mean ΔA -792.9; median ΔA -361.5; mean Q 75.34
- selective_hierarchical seed 55: wins 14, ties 0, effort losses 71, quality losses 15; mean ΔA -857.2; median ΔA -339; mean Q 75.03
- selective_hierarchical seed 66: wins 21, ties 0, effort losses 62, quality losses 17; mean ΔA -509.2; median ΔA -331; mean Q 75.29
- selective_hierarchical seed 77: wins 22, ties 0, effort losses 58, quality losses 20; mean ΔA -977; median ΔA -361; mean Q 75.03
- selective_hierarchical seed 88: wins 16, ties 0, effort losses 69, quality losses 15; mean ΔA -369.1; median ΔA -333.5; mean Q 74.85
- selective_hierarchical seed 99: wins 6, ties 0, effort losses 82, quality losses 12; mean ΔA -751.4; median ΔA -352; mean Q 74.98
- selective_hierarchical seed 111: wins 20, ties 0, effort losses 66, quality losses 14; mean ΔA -384; median ΔA -276; mean Q 75.15
- transfer seed 11: wins 12, ties 0, effort losses 82, quality losses 6; mean ΔA -306; median ΔA -339; mean Q 75.55
- transfer seed 22: wins 16, ties 0, effort losses 69, quality losses 15; mean ΔA -786; median ΔA -369.5; mean Q 75.12
- transfer seed 33: wins 15, ties 0, effort losses 69, quality losses 16; mean ΔA -658.5; median ΔA -336; mean Q 75.09
- transfer seed 44: wins 19, ties 0, effort losses 66, quality losses 15; mean ΔA -792.9; median ΔA -361.5; mean Q 75.34
- transfer seed 55: wins 14, ties 0, effort losses 71, quality losses 15; mean ΔA -857.2; median ΔA -339; mean Q 75.03
- transfer seed 66: wins 21, ties 0, effort losses 62, quality losses 17; mean ΔA -509.2; median ΔA -331; mean Q 75.29
- transfer seed 77: wins 22, ties 0, effort losses 58, quality losses 20; mean ΔA -977; median ΔA -361; mean Q 75.03
- transfer seed 88: wins 16, ties 0, effort losses 69, quality losses 15; mean ΔA -369.1; median ΔA -333.5; mean Q 74.85
- transfer seed 99: wins 6, ties 0, effort losses 82, quality losses 12; mean ΔA -751.4; median ΔA -352; mean Q 74.98
- transfer seed 111: wins 20, ties 0, effort losses 66, quality losses 14; mean ΔA -384; median ΔA -276; mean Q 75.15

## Decisive questions

1. Combined agent repeatedly saves effort while preserving quality? 0/10 seeds have median ΔA > 0 with quality losses ≤ 20% of boxes.
2. Fresh agent inherits savings through transferred knowledge? 0/10 seeds; transfer mean A 2251 vs hierarchical 2251.
3. Savings disappear when learned operations are disabled? lesion mean A 1612 vs primitive 1612 vs hierarchical 2251.
4. Hierarchical knowledge outperforms equally selective flat knowledge? hierarchical mean A 2251 vs flat 1923.

These statements describe this run only. They do not claim that intelligence has emerged.
