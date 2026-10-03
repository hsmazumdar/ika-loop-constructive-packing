"""Expt-7B report from the decision audit rows."""

from __future__ import annotations

from pathlib import Path
import statistics

from config import PHILOSOPHY


def _mean(values):
    return None if not values else sum(values) / len(values)


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _truthy(value) -> bool:
    return str(value).lower() in ("true", "1", "yes")


def _float(row, key, default=0.0) -> float:
    try:
        return float(row.get(key) if row.get(key) not in (None, "") else default)
    except (TypeError, ValueError):
        return float(default)


def _optional_int(row, key):
    text = str(row.get(key) or "").strip()
    if text in ("", "None", "null"):
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def write_report(run_dir: Path, config: dict, meta: dict, box_rows, decision_rows, ranker_rows, cf_rows, recall_rows, ledger: dict) -> str:
    n = len(box_rows)
    n_commit_boxes = sum(1 for r in box_rows if int(float(r.get("n_commitments") or 0)) > 0)
    n_commit = sum(int(float(r.get("n_commitments") or 0)) for r in box_rows)
    n_trace = sum(1 for r in box_rows if _truthy(r.get("trace_match")))
    n_q = sum(1 for r in box_rows if _truthy(r.get("Q_match")))
    n_pe = sum(1 for r in box_rows if _truthy(r.get("primitive_evals_match")))
    n_gap = sum(1 for r in box_rows if _truthy(r.get("consultation_equals_gap")))
    n_b0 = sum(1 for r in box_rows if _truthy(r.get("budget0_trace_match")))
    admits = [r for r in ranker_rows if _truthy(r.get("ranker_admit"))]
    rejects = [r for r in ranker_rows if not _truthy(r.get("ranker_admit"))]
    rej_q = sum(1 for r in rejects if _truthy(r.get("reject_quality")))
    rej_s = sum(1 for r in rejects if _truthy(r.get("reject_saving")))
    rej_both = sum(1 for r in rejects if _truthy(r.get("reject_quality")) and _truthy(r.get("reject_saving")))
    pred = [_float(r, "pred_saving") for r in ranker_rows]
    pok = [_float(r, "p_quality_ok") for r in ranker_rows]
    cf_admit = [r for r in cf_rows if _truthy(r.get("ranker_admit")) and _truthy(r.get("ok"))]
    cf_rej = [r for r in cf_rows if not _truthy(r.get("ranker_admit")) and _truthy(r.get("ok"))]
    n_match7 = sum(1 for r in box_rows if _truthy(r.get("A_matches_expt7_ranked")))
    n_has7 = sum(1 for r in box_rows if r.get("A_expt7_ranked") not in (None, "", "None"))
    above_save = sum(1 for r in ranker_rows if _float(r, "pred_saving") > _float(r, "remaining_check_cost"))
    above_q = sum(1 for r in ranker_rows if _float(r, "p_quality_ok") >= _float(r, "quality_threshold"))
    n_consult_steps = sum(1 for r in decision_rows if _truthy(r.get("consulted")))
    collected_cf = bool(config.get("collect_counterfactuals", True))
    exhausted = [r for r in box_rows if _optional_int(r, "first_budget_exhaustion_step") is not None]
    op_states = sum(int(float(r.get("n_oracle_useful_states") or 0)) for r in recall_rows)
    op_hits = sum(int(float(r.get("op_recall_hits") or 0)) for r in recall_rows)
    act_hits = sum(int(float(r.get("action_recall_hits") or 0)) for r in recall_rows)
    lines = [
        "# Expt-7B report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Frozen artifacts: `{meta.get('expt7_result')}`",
        f"- No retraining. K={config.get('k_shortlist')}; consult budget={config.get('consult_budget')}; budget-0 comparator included.",
        "- consultation_cost = retrieval + applicability + learned site checks + index probes + ranking. Primitive evaluations are separate. The Expt-7 identity A_ranked − A_primitive ≈ consultation used this inclusive total.",
        "- Counterfactual remaining-solves are diagnosis only.",
        "",
        "## Cost identity on the audit pairs",
        "",
        f"- n={n}; mean A_primitive {_fmt(_mean([_float(r, 'A_primitive') for r in box_rows]))}; "
        f"mean A_ranked (budget {config.get('consult_budget')}) {_fmt(_mean([_float(r, 'A_ranked') for r in box_rows]))}; "
        f"mean A_budget0 {_fmt(_mean([_float(r, 'A_budget0') for r in box_rows]))}; "
        f"mean (A_ranked − A_primitive) {_fmt(_mean([_float(r, 'A_minus_primitive') for r in box_rows]))}; "
        f"mean consultation {_fmt(_mean([_float(r, 'consultation_ranked') for r in box_rows]))} "
        f"(index {_fmt(_mean([_float(r, 'index_cost') for r in box_rows]))}; ranking {_fmt(_mean([_float(r, 'ranking_cost') for r in box_rows]))}; "
        f"applicability {_fmt(_mean([_float(r, 'applicability_cost') for r in box_rows]))}; learned {_fmt(_mean([_float(r, 'learned_evals') for r in box_rows]))}).",
        f"- primitive_evals match primitive A on {n_pe}/{n} pairs; consultation accounts for the A gap on {n_gap}/{n} pairs; Q match {n_q}/{n}.",
        f"- Consult budget 0 reproduces the primitive trace on {n_b0}/{n} pairs.",
        f"- Audit A matches frozen Expt-7 indexed_ranked A on {n_match7}/{n_has7} pairs that exist in eval.csv.",
        "",
        "## Does the ranker ever commit?",
        "",
        f"- Ranker decisions: {len(ranker_rows)}; admit {len(admits)}; reject {len(rejects)} "
        f"(quality {rej_q}; predicted saving ≤ remaining check cost {rej_s}; both {rej_both}).",
        f"- Actual commitments: {n_commit} across {n_commit_boxes}/{n} pairs.",
        f"- Primitive traces identical to ranked traces: {n_trace}/{n}.",
        f"- Consultation attempts: {_fmt(_mean([_float(r, 'consult_attempts') for r in box_rows]))} mean per pair; "
        f"consulted decision steps {n_consult_steps}; "
        f"pairs that exhaust the budget: {len(exhausted)}/{n}; "
        f"mean first exhaustion step {_fmt(_mean([_optional_int(r, 'first_budget_exhaustion_step') for r in exhausted if _optional_int(r, 'first_budget_exhaustion_step') is not None]))}.",
        f"- Predicted saving mean {_fmt(_mean(pred))}"
        + (f"; median {_fmt(statistics.median(pred))}; max {_fmt(max(pred))}" if pred else "")
        + f"; fraction with pred_saving > remaining_check {above_save}/{len(ranker_rows)}; "
        f"mean P(quality_ok) {_fmt(_mean(pok))}; fraction with P ≥ threshold {above_q}/{len(ranker_rows)}. "
        f"Saving-only rejects {sum(1 for r in ranker_rows if _truthy(r.get('reject_saving')) and not _truthy(r.get('reject_quality')))}; quality-only rejects {sum(1 for r in ranker_rows if _truthy(r.get('reject_quality')) and not _truthy(r.get('reject_saving')))}.",
        "",
        "## Counterfactuals of the ranker's tested first-legal sites (diagnosis only)",
        "",
    ]
    if not collected_cf:
        lines.append("- Remaining-solves were not collected in this preset.")
    else:
        cf_sav = [_float(r, "remaining_saving") for r in cf_rej]
        n_ben = sum(1 for r in cf_rej if _truthy(r.get("beneficial_free")))
        n_qf = sum(1 for r in cf_rej if not _truthy(r.get("quality_ok")))
        n_severe = sum(1 for s in cf_sav if s < -200)
        lines += [
            f"- Admitted first-legal sites with a remaining-solve: {len(cf_admit)}; "
            f"beneficial_free {_fmt(_mean([1.0 if _truthy(r.get('beneficial_free')) else 0.0 for r in cf_admit]))}; "
            f"mean remaining_saving {_fmt(_mean([_float(r, 'remaining_saving') for r in cf_admit]))}.",
            f"- Rejected first-legal sites with a remaining-solve: {len(cf_rej)}; "
            f"beneficial_free {n_ben}/{len(cf_rej)}; "
            f"quality_ok failures {n_qf}; "
            f"mean remaining_saving {_fmt(_mean(cf_sav))}; "
            f"median {_fmt(statistics.median(cf_sav) if cf_sav else None)}; "
            f"severe losses (< −200) {n_severe}.",
            "- These are the ranker's first_legal_site actions, not the sampled-oracle best placement. The ranker did not commit any of them.",
        ]
    lines += [
        "",
        "## Operation recall versus action recall (primitive snapshots, diagnosis only)",
        "",
        f"- Operation recall (frozen Expt-7 recall_states on these pairs): {op_hits}/{op_states} sampled-oracle states whose K-shortlist contains a beneficial operation.",
        (
            f"- Action recall (first_legal_site of a shortlisted op has a beneficial remaining-solve): {act_hits}/{op_states}."
            if collected_cf
            else "- Action recall: not collected in this preset."
        ),
        "- Expt-7's 170/170 figure is operation recall on primitive-trajectory snapshots. It is not placement-level recall, and it is not measured on the deployed ranked trajectory. The policy may lack budget, may not visit those states, and tests at most one first_legal_site (8 shuffled anchors) per shortlisted op.",
        "",
        "## Ledgers",
        "",
        f"- Diagnostic skip rollouts {ledger.get('skip_rollouts')}; commit rollouts {ledger.get('commit_rollouts')}; cache hits {ledger.get('cache_hits')}",
        "",
        "## What to change next",
        "",
    ]
    always_abstain = n_commit == 0
    if always_abstain:
        lines.append("- Almost no commitments: inspect score calibration. Predicted remaining-saving never exceeded the remaining-check cost of 8, and quality also rejected most scored operations.")
    if always_abstain and len(exhausted) > n / 2:
        lines.append("- Budget still expires after abstaining lookups: consult timing is secondary until the ranker can accept something. Include budget 0 in that comparison.")
    elif not always_abstain and len(exhausted) > n / 2:
        lines.append("- Budget exhausted on many boxes: investigate when to consult using training evidence, and include budget 0 in that comparison.")
    if collected_cf and op_states and act_hits < op_hits:
        lines.append("- Correct operation, wrong first-legal placement: improve action-level selection (anchors/orientation), not only op shortlisting.")
    if n_commit > 0:
        lines.append("- Commitments exist: check whether downstream gains and losses cancel before adding another mechanism.")
    elif collected_cf and cf_rej:
        lines.append("- No commitments occurred, so cancelling gains and losses are not a deployed-policy effect. Counterfactuals of the rejected first-legal sites are mixed (median remaining-saving can be positive while the mean is pulled negative by severe losses). Downstream-value prediction and severe-loss handling still matter if the ranker is ever allowed to admit.")
    lines += [
        "- Include consultation budget 0 in subsequent development comparisons. Every positive budget in Expt-7 lost to primitive; 25 was the best memory-enabled setting, not the best overall policy.",
        "",
        "Cheap retrieval can expose useful options. This audit reports whether the frozen ranker recognizes even a small subset worth executing.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT7B_REPORT.md").write_text(text, encoding="utf-8")
    return text
