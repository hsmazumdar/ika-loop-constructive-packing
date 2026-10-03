# Expt-6 report

Does the existing learned library contain operations that could reduce future deliberation if they were selected well, or is there too little useful opportunity in the library itself? The oracle sees future outcomes and is not a deployable agent.

- Directory: `results\20260929_214518_diagnostic`
- Preset: `diagnostic`
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
- Occupancy schedule (coverage, not a learned context rule): [0, 10, 20, 30, 40, 50, 60]
- Remaining-solve budget: eval_cap - prefix_primitive_A

## Per-seed means

- seed 11: n=24; library `d0d970996e690a73db70a75608858811d0cad24b991a0bc4905dab1ea9c32a8c`; mean A primitive 1630, both_gates 1967, oracle_free 1081, oracle_scan 2917; mean saving free 548.7, scan -1288; mean Q primitive 74.92, both 74.92, oracle_free 75.25; boxes with opportunity 16; incomplete 16
- seed 22: n=24; library `9b6b3680826a683ee81a0617ef8826e0995a5f255e588dfcbc3d88bcf5f47b3b`; mean A primitive 1262, both_gates 1742, oracle_free 1100, oracle_scan 2050; mean saving free 162.3, scan -787.8; mean Q primitive 75.58, both 75.58, oracle_free 75.67; boxes with opportunity 9; incomplete 9
- seed 33: n=24; library `38239bbb08e19b38b0bfe9fe8e3c9ac38cbbab9c7fe602e9f2201d655d656df6`; mean A primitive 1303, both_gates 1683, oracle_free 894, oracle_scan 2587; mean saving free 409, scan -1284; mean Q primitive 75.67, both 75.67, oracle_free 75.5; boxes with opportunity 19; incomplete 19

## Comparison table (all library–box pairs)

- n pairs: 72 (same boxes crossed with 3 reconstructed libraries)
- primitive: mean Q 75.39; mean A 1398; Q>=75 rate 0.9028; cap hits 0
- both_gates_frozen: mean Q 75.39; mean A 1797; mean effort saving -399; quality-loss rate 0% of pairs; Q>=75 rate 0.9028; cap hits 0; mean gate 16.47; mean consultation 382.5
- oracle_single_free: mean Q 75.47; mean A 1025; mean quality-qualified saving 373.3; quality-loss rate 0% of pairs (nonzero would violate the oracle construction)
- oracle_single_scan_charged: mean A 2518; mean saving -1120; mean C_box 1494
- skip-identity failures: 0; both-gates A-identity failures: 0; incomplete pairs: 44

## Coverage and content

- Fraction of sampled states with any inventory-compatible operation: 0.5159
- Fraction with any legal placement: 0.4881
- Fraction of states with a quality-qualified beneficial action: 0.4802
- Fraction of legal states with a beneficial action: 0.9837
- Boxes with at least one remaining-level opportunity: 44 / 72 (lower bound 0.6111); complete pairs with opportunity: 0; incomplete unknown: 0; complete with none: 28
- Distinct operations responsible for opportunities: 10; depths [1]
- Flat candidates 7808; composed candidates 0; composed beneficial 0. Zero composed evidence means hierarchy is untested here.

## Candidate remaining-saving distribution

- n=7808; mean -157.1; median 96; min -7977; max 6334; p10 -1359; p90 752
- quality difference mean -0.03765; min -17; max 9
- quality_ok 6669; beneficial_free 4463

## Selection and access (read-only gate probes, diagnostic ledger only)

- Beneficial candidates the frozen gates would admit: 1150
- Beneficial candidates the frozen gates would miss: 3313
- Candidate miss rate overcounts alternative placements of the same operation. States with any beneficial action: 242; every beneficial option rejected: 177 (73.14% of those states). Consult would not look: 116; consult open but commit rejects every beneficial op: 61.
- Library–box pairs with opportunity: 44; every beneficial option rejected: 23 (52.27% of those pairs); at least one beneficial option admitted: 21.
- Distinct state–operation pairs with a beneficial placement: 354; every placement of that operation rejected: 256.
- Probe decisions are not the actual both_gates trajectory.

## Cost-sensitivity (charge C to every box)

- C=0: mean saving 373.3; fraction of boxes with free-oracle saving > C: 0.6111
- C=10: mean saving 363.3; fraction of boxes with free-oracle saving > C: 0.6111
- C=25: mean saving 348.3; fraction of boxes with free-oracle saving > C: 0.6111
- C=50: mean saving 323.3; fraction of boxes with free-oracle saving > C: 0.6111
- C=100: mean saving 273.3; fraction of boxes with free-oracle saving > C: 0.4028
- C=200: mean saving 173.3; fraction of boxes with free-oracle saving > C: 0.3333
- C=400: mean saving -26.67; fraction of boxes with free-oracle saving > C: 0.2222
- C=800: mean saving -426.7; fraction of boxes with free-oracle saving > C: 0.1528

## Ledgers

- Diagnostic skip rollouts 504; skip A 558078
- Diagnostic commit rollouts 7808; commit A 9064701
- C_box sum 107556; gate probes 504; cache hits 0
- Historical Expt-5 learning_A 486500 (Expt-5 counterfactual remaining-solves plus collection retrieve/check on training boxes)
- Counterfactual rollouts are privileged diagnostic computation, not deployment effort and not part of C_box.

## Answers

- Fraction of boxes containing useful remaining-level opportunity: 44 / 72 (lower bound 0.6111; 44 of those pairs used sampled enumeration so the whole-box magnitude is a lower bound). Complete pairs with no opportunity: 28. Incomplete with nothing found (unknown, not scored as absence): 0.
- Quality-qualified whole-box free-oracle mean saving: 373.3.
- Mean scan-charged saving: -1120 (mean C_box 1494).
- Failure mechanism: see coverage vs content vs access in the rows above. Low legal coverage supports mismatch; legal coverage with little free-oracle benefit supports poor content under this single-intervention protocol; free benefit with poor scan-charged performance supports access cost.

**The oracle uses information about future outcomes. It measures opportunity in a fixed library under this diagnostic protocol; it does not demonstrate that an agent can discover or exploit that opportunity autonomously.**

Do not retrain gates or libraries from this result. Expt-6 boxes are development evidence and cannot later be reused as untouched confirmation tests.
