# Expt-11 audit

{
  "hypothesis": "declared remaining-state isometries can transform a stored continuation",
  "not_inventing_transforms": true,
  "not_general_abstraction": true,
  "engineered_and_learned_reported_separately": true,
  "A_identity": "primitive_evals + lookup + matching + transformation + validation + learning",
  "memory_sharing": "one shared ContinuationTable; first write wins",
  "symmetric_states_excluded": true,
  "family_split": "transformed versions of a donor stay in that donor's partition",
  "foils": "inventory change and near-miss geometry must reject reuse",
  "natural_frequency_separate": true,
  "candidates": [
    "rot90",
    "rot180",
    "rot270",
    "refl_x",
    "refl_y",
    "refl_d",
    "refl_ad"
  ]
}
