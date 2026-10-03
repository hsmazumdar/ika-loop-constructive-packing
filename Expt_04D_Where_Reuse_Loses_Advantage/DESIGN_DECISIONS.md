# Expt-4D design decisions

The Expt-4B/4C learner is copied, not edited in those folders. No new intelligence mechanism is added.

## Sign convention (fixed before the run)

effort_saving = A_primitive − A_agent

- Positive: the agent used fewer candidate evaluations.
- Negative: the agent used more (worse), matching the negative ΔA values in Expt-4C.

Quality-loss rate = fraction of boxes with Q_agent < Q_primitive − 1.0. This is not the same as “mean Q is close to primitive.”

## Counterfactuals

A deployable agent cannot receive both remaining-solve outcomes. Replays are logged only for diagnosis.
