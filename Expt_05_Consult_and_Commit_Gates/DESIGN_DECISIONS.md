# Expt-5 design decisions

Consultation and commitment are separate decisions. Each gate check costs 1 evaluation.

Labels come from matched-state remaining-solves on training boxes, including legal candidates the current policy did not commit. That extra computation is learning_A, not eval A.

Admission uses weighted logistic loss so a −6000 remaining-solve outweighs many +96 wins. Thresholds are frozen on held-out training boxes before eval.

Eval boxes are a new split, disjoint from train, development, Expt-4C test, and Expt-4D2 fresh.
