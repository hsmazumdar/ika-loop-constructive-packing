# Cursor AI implementation instructions: MGA Expt-1

Paste this document into Cursor Agent with the experiment folder open.

## 1. Task and location

Implement and run **Memory-Guided Assembly (MGA), Expt_01_10x10_Packing**.

Working directory:
`E:\PaperSubmissions2026\MGA_Memory_Guided_Assembly\Expt_01_10x10_Packing`

Build a working Python experiment, an interactive desktop demonstration, automated correctness tests, and a reproducible smoke experiment. Actually execute the tests and smoke experiment and deliver their real outputs. Do not merely provide code or predicted results. Do not claim that memory improves performance unless the measurements support it. Work autonomously through reversible implementation and debugging; preserve existing user files.

Inspect the folder and any applicable AGENTS.md first. Use the existing project structure if present. Use a local virtual environment. Do not change global Python settings. If a dependency, interpreter, or display is unavailable, report the specific blocked check and complete the remaining checks.

Scientific objective: measure whether experience retained within a box (STM) and across boxes (LTM) improves sequential packing under a fixed action budget. This first experiment has ONE agent. It has no reproduction, changing architecture, energy field, multi-agent interaction, or neural network requirement.

## 2. Exact environment

- Board: 10 columns × 10 rows; 100 unit cells.
- Internal coordinates: x,y = 0..9. Display row/column labels 1..10.
- Piece catalogue: 16 connected shapes A–P, listed below; unlimited copies.
- A label identifies a type, not a unique placed instance. Assign every placement a separate instance ID so adjacent copies remain distinguishable.
- Rotations: 0°, 90°, 180°, 270° clockwise in screen coordinates (y downward). Rotate, then normalize by subtracting minimum x and y. Anchor is the top-left corner of the rotated bounding box. No reflection.
- Four user-facing rotation choices are always available. Internally deduplicate identical orientations and identical placements when selecting candidates, so symmetric pieces are not oversampled.
- PLACE(type, rotation, x, y): legal only if all cells lie inside the board and none overlap. Reject atomically otherwise; do not clip the shape or partially place it.
- UNDO removes the most recently placed piece. It is a real action. Undo on an empty board is invalid.
- SUBMIT ends the current box.
- Every attempted PLACE, UNDO, or SUBMIT consumes one action, including invalid attempts. Maximum 100 actions per box.
- End automatically when all 100 cells are occupied or the 100th action has completed. Compute score after that final action. Auto-termination consumes no additional action. A terminal episode cannot accept additional actions.
- Score = occupied cells = 100 − blank cells. UNDO reduces the current score. Terminal score is the actual final board score, never the best score seen earlier.
- A new box clears the board, placement stack, action counters and STM. LTM persists within a training run unless explicitly reset.

Exact canonical piece coordinates (x,y):

```python
PIECES = {
 'A': [(1,0),(2,0),(0,1),(1,1),(1,2)],
 'B': [(0,0),(0,1),(0,2),(0,3),(0,4)],
 'C': [(0,0),(0,1),(0,2),(0,3),(1,3)],
 'D': [(0,0),(0,1),(1,1),(1,2),(1,3)],
 'E': [(0,0),(1,0),(0,1),(1,1),(0,2)],
 'F': [(0,0),(1,0),(2,0),(1,1),(1,2)],
 'G': [(0,0),(2,0),(0,1),(1,1),(2,1)],
 'H': [(0,0),(0,1),(0,2),(1,2),(2,2)],
 'I': [(0,0),(0,1),(1,1),(1,2),(2,2)],
 'J': [(1,0),(0,1),(1,1),(2,1),(1,2)],
 'K': [(0,0),(0,1),(0,2),(0,3),(1,1)],
 'L': [(0,0),(1,0),(1,1),(1,2),(2,2)],
 'M': [(0,0),(0,1),(0,2),(0,3)],
 'N': [(0,0),(0,1),(0,2),(1,2)],
 'O': [(0,0),(1,0),(2,0),(1,1)],
 'P': [(0,0),(1,0),(0,1),(0,2),(1,2),(0,3),(1,3)],
}
```

These coordinates reproduce the proposed drawing. Most shapes have 4–5 cells; P deliberately has 7. The labels are identifiers, not the names of the shapes they resemble. Do not silently redesign the catalogue. If `MGA_Expt01_Populated_Canvas.png` is available, use it as a visual reference, not as machine-readable ground truth.

## 3. Solvability validation, separate from learning

Write an independent backtracking/exact-cover validator with a configurable timeout. It must find at least two perfect tilings and save their placements as JSON. Validate each witness by replaying it through the environment API. Canonicalize complete tilings under board rotations/reflections and permutation of same-type instance IDs, so two witnesses are genuinely different. Keep labels when comparing tilings.

Use the exact catalogue and general validator to construct feasibility witnesses. Do not assume that area divisibility alone guarantees a tiling.

The validator must never provide solutions, completion lookahead, or demonstrations to the agent. A solver result is a feasibility witness, not a learning result. On timeout report UNKNOWN, not UNSOLVABLE. Do not change the catalogue merely to get a passing test.

## 4. Agent and fair memory ablations

Implement four modes using ONE shared decision-policy code path:
1. `none`: no episodic STM and no persistent learned LTM.
2. `stm`: STM only.
3. `ltm`: LTM only.
4. `both`: STM and LTM.

The visible board and environment placement stack are external state, not agent memory. Give all modes the same observations, legal-action generation, heuristic, exploration rate, action budget and computation limits. The board stack may execute UNDO; a memory-disabled policy must not read hidden historical trajectory data from it. Experiment logs must not be used as an unbounded agent memory.

Use a transparent, modest initial policy rather than a neural network or exhaustive planning:
- Enumerate unique legal placements for the current board. This one-step legality calculation is available to every mode.
- Rank placements with an explicit configurable heuristic: reward cells filled and contacts with occupied cells/boundaries; penalize newly created disconnected empty components smaller than the smallest available piece. This is an engineered heuristic, not discovered intelligence.
- Normalize feature ranges and publish the weights in the configuration.
- Use the same epsilon-greedy exploration (initially 0.15) and randomized tie-breaking in all modes.
- If no placement remains, UNDO when possible until the common budget ends, or SUBMIT when no useful permitted action remains. Any dead-end escape or early-submit rule must be shared across modes and documented.

STM (default capacity: 64 entries):
- Maintain a bounded set/queue of `(occupancy_bitmask, action_signature)` exclusions for invalid attempts and placements rejected during backtracking.
- Before undoing a dead-end placement, associate that placement with the board state preceding it. Reconstructing this state for the current undo is allowed from the piece being removed; do not give the policy a full invisible history.
- When that exact state reappears, avoid the rejected action. If all legal placements are excluded, backtrack or submit using the shared rule.
- Evict oldest entries at capacity. Clear on box reset. Never blacklist an action globally when it failed only on one board.

LTM (default capacity: 4096 entries):
- Store bounded statistics for a local context/action key. Suggested key: the 7×7 neighbourhood centred on the placement anchor, encoded with separate empty/occupied/outside values, plus piece type and canonical orientation. This is a partial context representation; identical keys need not imply identical full boards.
- Store count and mean observed return for the key. Update incrementally at episode end from executed PLACE actions.
- For an occurrence at time t, suggested return is `(terminal_occupied - occupied_before_action)/100 - 0.001 * remaining_actions_from_t`. Record the formula exactly; it supplies delayed outcome information and penalizes wasted steps. Do not add a separate positive reward for undoing and replacing the same cells.
- Bound the influence of LTM: use a configurable coefficient and count-dependent shrinkage, e.g. `n/(n+5) * mean_return`, added to the normalized base ranking. Empty entries contribute zero.
- Use deterministic least-recently-updated eviction, and log evictions and hit rates. An episode update buffer may contain at most the 100 executed actions and must be explicitly accounted for as training bookkeeping. It is not accessible for decision making and is cleared after updates.
- Persist LTM in a versioned checkpoint containing catalogue/configuration hashes; validate compatibility on load. Evaluation reads LTM but freezes its values and eviction order.

This is the first, deliberately simple memory mechanism. It does NOT claim automatic invention of compression, multi-step macros, or intelligence. Do not add these features in Expt-1. Record memory entry counts and serialized byte sizes; do not equate equal entry limits with equal byte budgets.

## 5. Desktop interface

Use Tkinter plus matplotlib only where needed; numpy, pandas and pytest are acceptable lightweight dependencies. Keep simulation logic independent of GUI imports so tests run headlessly.

The window should show:
- Large 10×10 board with cell lines, row/column numbers, coloured type labels and thick boundaries around each placed instance.
- All 16 canonical pieces in a 4×4 catalogue, with their internal cells visible.
- Score, blank cells, episode index, action count / 100, last action, invalid attempts, undos, current mode, seed, STM entries and LTM entries.
- Start/Pause, Single Step, New Box, Reset Run, Save Snapshot, speed slider, and mode selection.
- Explicitly distinguish New Box (retain LTM) from Reset Run (clear learned memory).
- Manual mode: click catalogue, select rotation, click board anchor; show valid/invalid placement preview and provide Undo/Submit. Manual episodes must not contaminate experiment metrics or trained LTM unless an explicit demonstration-learning option is added later.
- Training mode: animate one autonomous agent over successive boxes and plot terminal scores plus a labelled rolling mean.
- Switching ablation mode must start an isolated run or restore that mode's own checkpoint; never silently share learned tables across modes.

Keep the UI responsive through scheduled callbacks or safe worker/message queues. GUI calls must stay on the UI thread. The user should be able to pause before the next action. Include a deterministic saved board image showing a valid partial packing and its computed score.

## 6. Files and reproducibility

Suggested structure (adapt if an existing structure is better):

```text
README.md
requirements.txt
configs/default.json
mga/{__init__,pieces,environment,agent,memory,validation,experiment,gui}.py
run_gui.py
run_experiment.py
validate_catalogue.py
tests/
results/<run_id>/
```

Use explicit seeds via local random generators, including tie-breaking; do not rely on unordered set traversal. Store config, interpreter/package versions, catalogue hash, code revision or source hash, seeds and timing. Use separate generators for training, evaluation and visualization. Fresh output directories prevent accidental overwrite.

Episode CSV fields: mode, seed, phase, episode, terminal_score, blanks, actions, placements, invalid_attempts, undos, perfect, termination_reason, stm_entries, ltm_entries, ltm_hits, ltm_lookups, ltm_evictions, memory_serialized_bytes, candidate_evaluations, elapsed_seconds.

Keep a complete action trace for at least one episode per mode. Replay must reproduce the final board and score exactly. Full logs are experimental artifacts, not policy-readable memory.

## 7. Automated correctness tests

Run pytest and retain the actual console output. Meaningful tests must cover:
- 16 unique types up to rotation; connected cells; no duplicate coordinates; correct areas.
- Rotation normalization, four-turn identity and no accidental reflection.
- All edge/corner bounds, negative coordinates, overlap rejection, and atomic invalid placement.
- Distinct instance IDs, exact undo restoration and adjacent same-type pieces.
- Score/blank consistency after every action; action accounting and terminal-state protection.
- Empty-board submit, invalid empty undo, full-board auto-finish and action-limit finish.
- Perfect-tiling witness replay and witness non-equivalence.
- STM state-specific exclusion, eviction and clearing; LTM persistence, capacity/eviction, update arithmetic, checkpoint round trip and mismatch rejection.
- Frozen evaluation leaves LTM byte-for-byte unchanged.
- Seeded replay determinism, mode isolation, correct disabling of memory components, and no solver access in policy execution.
- At least 500 randomized action attempts with invariant checks (in-bounds pieces, no overlap, occupancy matches placements, score 0..100).

A passing test suite proves implementation behaviour, not improved intelligence or a scientific result.

## 8. Actual smoke experiment

First run a tiny execution check: all four modes, one seed, 5 boxes each, to detect crashes. Then run:
- Modes: none, stm, ltm, both.
- Independent seeds: 11, 22, 33.
- Training: 100 boxes per mode per seed, empty LTM at the start of each run.
- Evaluation: 30 boxes per mode per seed, separate seed stream; trained LTM frozen; STM still clears and operates within each box.
- Same 100-action cap and configuration across modes. No post-hoc tuning of one mode based on evaluation performance.

This is 1,560 boxes total. If runtime is excessive, save partial outputs and explicitly report the completed subset, runtime and reason. Do not silently lower the planned count.

Repeated empty 10×10 boxes with the same catalogue test practice/recall under different action randomness. They do NOT constitute transfer to unseen tasks. Restriction/quotas and harder environments are future experiments.

Generate:
1. `test_results.txt` and `test_results.xml`.
2. `catalogue_validation.json` with perfect witnesses and status.
3. `episodes.csv`, per-seed summaries, aggregate `summary.csv`.
4. `learning_curves.png`, raw per-seed curves with an explicitly labelled smoothing window.
5. `evaluation_scores.png` showing each seed's mean, not just a pooled bar.
6. `populated_canvas.png`, computed from an actual recorded state.
7. `action_trace.jsonl`, configuration and LTM checkpoints.
8. `SMOKE_TEST_REPORT.md` with actual commands, counts, results, runtime, failures, fixes and limitations.

Summary table: mode, seeds completed, train/evaluation box counts, mean terminal score, perfect-box fraction, mean actions, mean undos, LTM hit fraction, mean serialized memory bytes, and wall time. Also report perfect boxes per 1,000 actual actions; count all attempts including SUBMIT. Aggregate at seed level; show seed variation. Three seeds are a smoke check, not evidence of statistical significance.

Report whether learned entries were actually reused. Nonempty memory with zero useful retrieval is not evidence of memory helping. Do not assert that BOTH must outperform the other modes. Negative or tied results must be retained.

## 9. Execution and final handover

Create working commands equivalent to:

```powershell
python -m pytest -q --junitxml=results/tests.xml
python validate_catalogue.py --output results/catalogue_validation.json
python run_experiment.py --config configs/default.json --preset smoke
python run_gui.py
```

Use the virtual environment's interpreter and document exact Windows commands. Implement the advertised arguments; do not leave illustrative commands that do not run.

Verify a GUI launch and the key controls if a desktop is accessible. Otherwise say GUI interaction is unverified and still test rendering/headless logic. Do not claim to have clicked controls without doing so.

End with: files created, commands to launch/reproduce, exact test pass/fail counts, measured smoke summary, saved output locations, and any remaining defect. Explain plainly whether the first runs show improvement, no detectable improvement, or insufficient evidence. Do not stop at a plan: implement, execute, debug and report.
