# Expt-4D2 design decisions

The Expt-4B/4C/4D learner is copied, not edited in those folders.

retrieve_check_then_primitive stops on primitive evaluations only. Consultation has its own ledger and its own RNG purposes (`retrieve-*`, `anchor-*`). `select` is untouched. `macro_fits` copies mask and counts.

normal_reuse still stops on total A, because that is the agent’s real budget.

Existing 15 replays are read from the frozen Expt-4D CSV so the costly-choice table is the actual published events, not a re-simulation.

An acceptable success requires remaining effort saving greater than check cost **and** commit Q ≥ skip Q − 1. Repaying check cost is not enough.

Zero composed replays means hierarchy is untested. Mixed occupancy-0–24 outcomes do not identify a predictive context.
