# Expt-6 report

Does the existing learned library contain operations that could reduce future deliberation if they were selected well, or is there too little useful opportunity in the library itself? The oracle sees future outcomes and is not a deployable agent.

- Directory: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_06_Frozen_Library_Opportunity\results\20260929_214446_smoke`
- Preset: `smoke`
- Python: 3.13.1
- Catalogue hash: `3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14`
- Git: `unavailable`
- Reconstruction: True — Expt-5 stored frozen gates only. Libraries are reconstructed from the recorded 80-box training streams and marked reconstruction=True. Exact library-hash match with the unpublished in-memory Expt-5 objects cannot be verified.
- Historical Expt-5 learning cost (reference, not billed here): 486500
- Oracle kind: sampled_candidate_oracle
- Effort saving = A_primitive − A_condition (positive = fewer evaluations).
- Quality-loss rate is separate from mean Q. Margin = 1 occupied cell.
- The oracle uses information about future outcomes and is not a deployable agent.

## Frozen sources

- Expt-5 result: `E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_05_Consult_and_Commit_Gates\results\20260929_212658_diagnostic`
- Missing Expt-5 library files: ['E:\\PaperSubmissions2026\\MGA_Memory_Guided_Assembly\\Expt_05_Consult_and_Commit_Gates\\results\\20260929_212658_diagnostic\\library_seed11.json', 'E:\\PaperSubmissions2026\\MGA_Memory_Guided_Assembly\\Expt_05_Consult_and_Commit_Gates\\results\\20260929_212658_diagnostic\\library_seed22.json', 'E:\\PaperSubmissions2026\\MGA_Memory_Guided_Assembly\\Expt_05_Consult_and_Commit_Gates\\results\\20260929_212658_diagnostic\\library_seed33.json']
- Occupancy schedule (coverage, not a learned context rule): (0, 10, 20, 30)
- Remaining-solve budget: eval_cap - prefix_primitive_A

## Per-seed means

- seed 11: n=4; library `d0d970996e690a73db70a75608858811d0cad24b991a0bc4905dab1ea9c32a8c`; mean A primitive 1706, both_gates 1939, oracle_free 1635, oracle_scan 2355; mean saving free 71.5, scan -649; mean Q primitive 76, both 76, oracle_free 76; boxes with opportunity 2; incomplete 2

## Comparison table (all library–box pairs)

- n pairs: 4 (same boxes crossed with 1 reconstructed libraries)
- primitive: mean Q 76; mean A 1706; Q>=75 rate 1; cap hits 0
- both_gates_frozen: mean Q 76; mean A 1939; mean effort saving -232.5; quality-loss rate 0% of pairs; Q>=75 rate 1; cap hits 0; mean gate 16.75; mean consultation 215.8
- oracle_single_free: mean Q 76; mean A 1635; mean quality-qualified saving 71.5; quality-loss rate 0% of pairs (nonzero would violate the oracle construction)
- oracle_single_scan_charged: mean A 2355; mean saving -649; mean C_box 721
- skip-identity failures: 0; both-gates A-identity failures: 0; incomplete pairs: 2

## Coverage and content

- Fraction of sampled states with any inventory-compatible operation: 0.5
- Fraction with any legal placement: 0.5
- Fraction of states with a quality-qualified beneficial action: 0.5
- Fraction of legal states with a beneficial action: 1
- Boxes with at least one remaining-level opportunity: 2 / 4 (lower bound 0.5); complete pairs with opportunity: 0; incomplete unknown: 0; complete with none: 2
- Distinct operations responsible for opportunities: 3; depths [1]
- Flat candidates 80; composed candidates 0; composed beneficial 0. Zero composed evidence means hierarchy is untested here.

## Candidate remaining-saving distribution

- n=80; mean -191.2; median 48; min -4536; max 144; p10 -428.4; p90 144
- quality difference mean -0.3; min -8; max 0
- quality_ok 75; beneficial_free 54

## Selection and access (read-only gate probes, diagnostic ledger only)

- Beneficial candidates the frozen gates would admit: 0
- Beneficial candidates the frozen gates would miss: 54
- Probe decisions are not the actual both_gates trajectory.

## Cost-sensitivity (charge C to every box)

- C=0: mean saving 71.5; fraction of boxes with free-oracle saving > C: 0.5
- C=10: mean saving 61.5; fraction of boxes with free-oracle saving > C: 0.5
- C=25: mean saving 46.5; fraction of boxes with free-oracle saving > C: 0.5
- C=50: mean saving 21.5; fraction of boxes with free-oracle saving > C: 0.5
- C=100: mean saving -28.5; fraction of boxes with free-oracle saving > C: 0.5
- C=200: mean saving -128.5; fraction of boxes with free-oracle saving > C: 0
- C=400: mean saving -328.5; fraction of boxes with free-oracle saving > C: 0
- C=800: mean saving -728.5; fraction of boxes with free-oracle saving > C: 0

## Ledgers

- Diagnostic skip rollouts 16; skip A 24996
- Diagnostic commit rollouts 80; commit A 70593
- C_box sum 2884; gate probes 16; cache hits 0
- Historical Expt-5 learning_A 486500 (Expt-5 counterfactual remaining-solves plus collection retrieve/check on training boxes)
- Counterfactual rollouts are privileged diagnostic computation, not deployment effort and not part of C_box.

## Answers

- Fraction of boxes containing useful remaining-level opportunity: 0 among complete pairs (found 2 of 4; unknown 0).
- Quality-qualified whole-box free-oracle mean saving: 71.5.
- Mean scan-charged saving: -649 (mean C_box 721).
- Failure mechanism: see coverage vs content vs access in the rows above. Low legal coverage supports mismatch; legal coverage with little free-oracle benefit supports poor content under this single-intervention protocol; free benefit with poor scan-charged performance supports access cost.

**The oracle uses information about future outcomes. It measures opportunity in a fixed library under this diagnostic protocol; it does not demonstrate that an agent can discover or exploit that opportunity autonomously.**

Do not retrain gates or libraries from this result. Expt-6 boxes are development evidence and cannot later be reused as untouched confirmation tests.
