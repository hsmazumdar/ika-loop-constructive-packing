# Expt_23_MultiProblem - README (Phase 1: design + cheap code only; no long runs)

Machine/paths: Vivobook, `D:\PaperSubmissions2026\Assembly_Skill_Learning\Expt_23_MultiProblem` (the SSD is D:, not E:).
Python 3.13.1, numpy 2.5.2, scipy 1.18.1, matplotlib 3.11.1, pytest 9.1.1. torch and numba are NOT installed.

    src/polyomino.py   polyomino pool (283 pieces, sizes 3-7), held-out piece split, legacy A-P mapping
    src/env.py         variable board / obstacles / catalogue environment, natural placing, optional 14-piece cap
    src/generator.py   problem distribution + splits (train, dev, test_iid, test_size, test_piece, test_both, legacy)
    src/baselines.py   REFERENCE policies: uniform natural, hand rule, beam search, hand-rollout beam search
    src/loop.py        domain-agnostic information -> knowledge -> information loop (Domain / KnowledgeStore / run_loop)
    tests/             pytest unit tests + sample scripts that produced results/*.txt, results/*.csv

Run the tests (about 25 s):  `python -m pytest tests -q -p no:cacheprovider`
Reference table:  `python tests\sample_reference_table2.py`;  condition grid: `python tests\sample_condition_grid.py`;
headroom: `python tests\sample_headroom_per_problem.py`.
Seeds are fixed in the code (problem index -> `default_rng((split_base, index))`; evaluation episodes `default_rng((seed0, j))`).
DESIGN.md holds the frozen plan, the statistical plan and the compute estimate.