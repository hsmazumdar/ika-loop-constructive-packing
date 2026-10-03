# Expt-4C design decisions

The Expt-4B selective mechanism is copied, not altered in the Expt-4B folder.

## Frozen before the confirmation run

- Quality-loss margin: 1.0 occupied cell.
- Primitive fallback score: area + 0.2 * contact + 0.05 * boundary.
- Q_min = 75.
- No new intelligence mechanisms (no extra features, no rectangle priors, no new miner).
- No mid-run distribution shift. 4C tests reuse on the same inventory family as training, using untouched test boxes.
- Test inventories are unique multisets, disjoint from train and development. Shuffled copies are not used as new tasks.

## Transfer

Only active operations and their applicability rules move. Episodes, RNG state, and training bookkeeping do not.

## Lesion

The trained hierarchical controller is evaluated with no operations. If savings were caused by the library, lesion should match primitive deliberation.
