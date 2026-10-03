# Expt-4B design decisions

The objective of this experiment is not to discover a better packing heuristic. Packing is the observable environment. Expt-4B tests whether the system can learn selective, beneficial reuse.

## Designer-provided (not discoveries)

- A–P catalogue, four rotations, no reflection.
- Q = occupied cells, Q_min = 75 (configurable).
- A = candidate evaluations, including retrieval scores, applicability checks, learned-site checks, and primitive rows. Internal cells of a committed operation are recorded separately.
- Primitive fallback score `area + 0.2 * contact + 0.05 * boundary` (Expt-3 prior).
- 4-connected footprint for a learned operation (one decision = one coherent action). Not a rectangle reward.
- Neutral state features: piece-count histogram, occupancy, row/column fill, empty-region summaries. No shape labels.
- Train-val tasks used for pairing are reserved from the training split. The Expt-4 held-out test set is never used for promotion.

## Condition mechanics

- `current_hierarchy`: recurrence immediately activates an operation (Expt-4 admission).
- `utility_promotion`: provisional until a paired with/without solve on a train-val box shows lower A and preserved quality. Depth > 1 must also beat a children-only library.
- `contextual_abstention`: Expt-4 admission, but retrieval checks a learned applicability rule and may skip the library.
- `both`: utility promotion plus abstention.

## Retirement

After `change_at`, success/failure counts and savings are multiplied by `env_discount`. Active operations with utility below `retire_utility` become inactive and leave the retrieval pool.
