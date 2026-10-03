# Expt-12 report

At what predeclared useful-recurrence frequency does frozen learned isometry selection produce a net evaluation-effort saving after unsuccessful consultations, while preserving quality? Task category is hidden. This does not expand the abstraction claim.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_12_Mixed_Stream_Recurrence\results\20260930_061841_smoke`
- Preset: `smoke`
- Store boxes: ['inv_a0fc2242608a', 'inv_3fce6425e7c8'].
- Fresh boxes: ['inv_2f4940dd8206', 'inv_82c6d6f9ea01'].
- Train families: ['inv_3fce6425e7c8']. Test families: ['inv_a0fc2242608a'].
- Pools: exact 2, valid-transform 4, no-match 6, fresh 2.
- Transform counts in valid-transform pool: {'rot90': 2, 'rot180': 1, 'rot270': 1, 'refl_x': 0, 'refl_y': 0, 'refl_d': 0, 'refl_ad': 0}.
- Frozen keys: 32; overwrites 0; bytes 4680.
- Selected: ['rot90', 'rot180', 'rot270'].
- Coverage (attempts / compatible / valid_replays / successes / fails): {'rot90': {'attempts': 3, 'compatible': 1, 'valid_replays': 1, 'successes': 1, 'fails': 0, 'insufficient_coverage': False}, 'rot180': {'attempts': 3, 'compatible': 1, 'valid_replays': 1, 'successes': 1, 'fails': 0, 'insufficient_coverage': False}, 'rot270': {'attempts': 3, 'compatible': 1, 'valid_replays': 1, 'successes': 1, 'fails': 0, 'insufficient_coverage': False}, 'refl_x': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_y': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_d': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}, 'refl_ad': {'attempts': 3, 'compatible': 0, 'valid_replays': 0, 'successes': 0, 'fails': 0, 'insufficient_coverage': True}}.
- Zero successes with zero compatible keys is insufficient coverage, not evidence the transform is useless.
- A = primitive_evals + lookup + matching + transformation + validation + learning.
- Task category is hidden from the agent. No-match checked against the full table under every permitted T.

## Learned net saving by useful-recurrence rate

- p=0.0: n=6 (4 task-ids × 1 seeds); mean A 1062; mean effort-saving -57.33; quality-loss 0; net-save-and-quality-ok False.
- p=1.0: n=6 (4 task-ids × 1 seeds); mean A 56.33; mean effort-saving 973; quality-loss 0; net-save-and-quality-ok True.

- Smallest predeclared rate at which learned netsaves and quality-loss ≤ 0.2: 1.

## All agents by stream

- mix_p000/primitive: n=6; mean A 1005; mean Q 77; mean effort-saving 0; quality-loss 0 (n=0); hits exact 0 equiv 0; mean lookup 0; matching 0; by hidden kind {'fresh': {'n': 3, 'mean_A': 752.0, 'mean_effort_saving': 0.0, 'n_hits': 0}, 'no_match': {'n': 3, 'mean_A': 1257.3333333333333, 'mean_effort_saving': 0.0, 'n_hits': 0}}.
- mix_p000/exact: n=6; mean A 1019; mean Q 77; mean effort-saving -14.33; quality-loss 0 (n=0); hits exact 0 equiv 0; mean lookup 14.33; matching 0; by hidden kind {'fresh': {'n': 3, 'mean_A': 767.0, 'mean_effort_saving': -15.0, 'n_hits': 0}, 'no_match': {'n': 3, 'mean_A': 1271.0, 'mean_effort_saving': -13.666666666666666, 'n_hits': 0}}.
- mix_p000/supplied: n=6; mean A 1119; mean Q 77; mean effort-saving -114.7; quality-loss 0 (n=0); hits exact 0 equiv 0; mean lookup 14.33; matching 100.3; by hidden kind {'fresh': {'n': 3, 'mean_A': 872.0, 'mean_effort_saving': -120.0, 'n_hits': 0}, 'no_match': {'n': 3, 'mean_A': 1366.6666666666667, 'mean_effort_saving': -109.33333333333333, 'n_hits': 0}}.
- mix_p000/learned: n=6; mean A 1062; mean Q 77; mean effort-saving -57.33; quality-loss 0 (n=0); hits exact 0 equiv 0; mean lookup 14.33; matching 43; by hidden kind {'fresh': {'n': 3, 'mean_A': 812.0, 'mean_effort_saving': -60.0, 'n_hits': 0}, 'no_match': {'n': 3, 'mean_A': 1312.0, 'mean_effort_saving': -54.666666666666664, 'n_hits': 0}}.
- mix_p100/primitive: n=6; mean A 1029; mean Q 76.17; mean effort-saving 0; quality-loss 0 (n=0); hits exact 0 equiv 0; mean lookup 0; matching 0; by hidden kind {'exact_recurrence': {'n': 3, 'mean_A': 768.0, 'mean_effort_saving': 0.0, 'n_hits': 0}, 'valid_transform': {'n': 3, 'mean_A': 1290.6666666666667, 'mean_effort_saving': 0.0, 'n_hits': 0}}.
- mix_p100/exact: n=6; mean A 661; mean Q 76.17; mean effort-saving 368.3; quality-loss 0 (n=0); hits exact 3 equiv 0; mean lookup 7.667; matching 0; by hidden kind {'exact_recurrence': {'n': 3, 'mean_A': 17.0, 'mean_effort_saving': 751.0, 'n_hits': 3}, 'valid_transform': {'n': 3, 'mean_A': 1305.0, 'mean_effort_saving': -14.333333333333334, 'n_hits': 0}}.
- mix_p100/supplied: n=6; mean A 56.33; mean Q 76.33; mean effort-saving 973; quality-loss 0 (n=0); hits exact 3 equiv 3; mean lookup 1; matching 0.6667; by hidden kind {'exact_recurrence': {'n': 3, 'mean_A': 17.0, 'mean_effort_saving': 751.0, 'n_hits': 3}, 'valid_transform': {'n': 3, 'mean_A': 95.66666666666667, 'mean_effort_saving': 1195.0, 'n_hits': 3}}.
- mix_p100/learned: n=6; mean A 56.33; mean Q 76.33; mean effort-saving 973; quality-loss 0 (n=0); hits exact 3 equiv 3; mean lookup 1; matching 0.6667; by hidden kind {'exact_recurrence': {'n': 3, 'mean_A': 17.0, 'mean_effort_saving': 751.0, 'n_hits': 3}, 'valid_transform': {'n': 3, 'mean_A': 95.66666666666667, 'mean_effort_saving': 1195.0, 'n_hits': 3}}.

- Useful recurrence rate is the hidden share of exact plus valid-transform tasks. No-match tasks were checked against the entire frozen table under every permitted T. A match to another stored intermediate is valid retrieval and was excluded from no-match. Evaluations at a rate are stream slots crossed with seeds, not independent learning tests. Natural unforced encounter frequency is not measured here.
