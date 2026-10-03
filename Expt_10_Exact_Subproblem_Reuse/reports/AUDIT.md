# Expt-10 audit

{
  "hypothesis": "exact subproblem reuse after a nonempty prefix; whole-problem recall is the positive control",
  "not_abstraction": true,
  "not_expt8c_rescue": true,
  "A_identity": "primitive_evals + lookup + validation + learning",
  "catalogue_note": "same A\u2013P catalogue; no Expt-7 libraries",
  "memory_sharing": "one shared ContinuationTable across seeds; frozen before eval",
  "retention": "first write wins; not best-of",
  "constructed_recurrence_labeled": true,
  "natural_recurrence_separate": true,
  "exclude_initial_state_on_constructed": true,
  "require_nonzero_prefix_on_constructed": true,
  "key": "(mask, inventory counts)",
  "empty_store_on_unsuccessful": true
}
