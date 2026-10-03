"""Expt-8C report. Frozen 8B models on unseen boxes."""

from __future__ import annotations

from pathlib import Path

from config import PHILOSOPHY


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _sel_line(name: str, sel: dict, historical: bool) -> str:
    tag = " [historical comparator]" if historical else ""
    if sel.get("zero_coverage"):
        return (
            f"- {name}{tag}: **zero coverage** ({sel.get('n_accepted', 0)}/{sel.get('n_actions', 0)} actions). "
            f"Eligible: {sel.get('n_unique_boxes')} unique boxes, {sel.get('n_seed_box_pairs')} seed–box pairs, "
            f"{sel.get('n_states')} states, {sel.get('n_actions')} actions."
        )
    return (
        f"- {name}{tag}: accepted {sel.get('n_accepted')}/{sel.get('n_actions')} actions "
        f"on {sel.get('n_accepted_unique_boxes')} unique boxes / {sel.get('n_accepted_seed_box_pairs')} seed–box pairs / "
        f"{sel.get('n_accepted_states')} states; "
        f"mean remaining-saving {_fmt(sel.get('mean_remaining_saving'))}; "
        f"mean billed examined {_fmt(sel.get('mean_examined_billed'))}; "
        f"mean net after site checks {_fmt(sel.get('mean_net_after_check'))}; "
        f"quality-loss {_fmt(sel.get('quality_loss_rate'))}; "
        f"severe losses {sel.get('severe_loss_n')} ({_fmt(sel.get('severe_loss_rate'))})."
    )


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, offline: dict, wholebox: dict, ledger: dict) -> str:
    pooled = {p["predictor"]: p for p in (offline.get("pooled") or [])}
    ident = offline.get("frozen_identity") or {}
    hold = audit.get("expt8b_holdout") or []
    fit_cmp = audit.get("fit_label_comparison") or {}
    val_cmp = audit.get("val_label_comparison") or {}
    action = pooled.get("action_unweighted") or {}
    decision = action.get("decision_costs") or {}
    lines = [
        "# Expt-8C report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        "- Frozen libraries from Expt-7. Models frozen from Expt-8B development fit labels. Thresholds not retuned on this set.",
        f"- Unseen boxes ({len(offline.get('unseen_ids') or [])}): {offline.get('unseen_ids')}.",
        f"- Label budget: {ident.get('label_remaining_budget')}. Cache key: {ident.get('cache_key')}.",
        f"- labels_fit sha256: {ident.get('labels_fit_sha256')}.",
        f"- model payload sha256: {ident.get('model_payload_sha256')}.",
        f"- frozen file sha256: {ident.get('frozen_file_sha256')}.",
        "",
        "## Provenance: Expt-8B eight-box set is not unseen",
        "",
        f"- Status: {audit.get('expt8b_holdout_status')}.",
        f"- Boxes with at least one prior data-file use: {audit.get('n_holdout_with_prior_use')} / {len(hold)}.",
    ]
    for item in hold:
        lines.append(f"- {item.get('task_id')}: {item.get('prior_uses')}")
    lines += [
        "",
        "## Corrected-label identity",
        "",
        f"- Fit y changed vs Expt-8: {fit_cmp.get('n_y_changed')} of {fit_cmp.get('n_common')} common rows.",
        f"- Val y changed vs Expt-8: {val_cmp.get('n_y_changed')} of {val_cmp.get('n_common')} common rows.",
        f"- Fit file sha256 Expt-8 {audit.get('labels_fit_sha256_expt8')}; Expt-8B {audit.get('labels_fit_sha256_expt8b')}.",
        f"- 1600-replay differs from the actual 8B/8 fit label on {audit.get('n_fit_rows_where_1600_replay_differs')} fit rows.",
        f"- {audit.get('matching_validation_numbers')}",
        "- Frozen Expt-7 rankers are historical comparators (trained under pair_eval_cap=1600). Newly fitted unweighted models are rebuilt from Expt-8B labels_fit.csv and serialized with that budget in their identity.",
        "",
        "## Unseen first-legal error",
        "",
    ]
    for kind in ("per_seed_mean", "frozen", "context_unweighted", "action_unweighted", "context_weighted", "action_weighted"):
        if kind not in pooled:
            continue
        err = pooled[kind]["errors_first_legal"]
        hist = pooled[kind].get("historical_comparator")
        tag = " [historical]" if hist else ""
        lines.append(
            f"- {kind}{tag}: n={err.get('n')}; MAE {_fmt(err.get('mae'))}; pooled Pearson {_fmt(err.get('pearson_pooled'))}; "
            f"pred mean {_fmt(err.get('pred_mean'))} vs y mean {_fmt(err.get('y_mean'))}; "
            f"pred range [{_fmt(err.get('pred_min'))}, {_fmt(err.get('pred_max'))}]."
        )
    lines += [
        f"- Unweighted action MAE beats per-seed mean: {offline.get('beats_constant')}.",
        "",
        "## Unseen selection (thresholds frozen)",
        "",
        f"- Admission bound pred_saving > {offline.get('remaining_check')}. Not changed after inspecting this set.",
    ]
    for kind in ("per_seed_mean", "frozen", "context_unweighted", "action_unweighted", "context_weighted", "action_weighted"):
        if kind in pooled:
            lines.append(_sel_line(kind, pooled[kind]["selection_first_legal"], pooled[kind].get("historical_comparator")))
    lines += [
        "",
        "## Accepted-action costs (unweighted action model)",
        "",
        f"- Accepted {decision.get('n_accepted')} actions on {decision.get('n_accepted_seeds')} seeds.",
        f"- Sum remaining-saving {_fmt(decision.get('sum_remaining_saving'))}.",
        f"- Mean net after site checks only {_fmt(decision.get('mean_net_after_site_checks'))}. Site-check net is not total deployment savings.",
        f"- Sum action decision cost (examined + feature_checks) {_fmt(decision.get('sum_action_decision_cost'))}.",
        f"- Consult cost on all scored states (index + compat + ranking, including rejects) {_fmt(decision.get('consult_cost_all_states'))}.",
        f"- Net after those decision costs {_fmt(decision.get('net_after_decision_costs'))}.",
        "- Feature-check split (action-unweighted first-legal): accepted 183, rejected 16,984, total 17,167. Remaining-solves (541 skip + 541 commit) do not produce feature checks. Every first-legal candidate was featurized to decide; rejected-candidate features are deployment-relevant. Including them (and rejected site checks 1,288) with consult 1,608 makes decision-relevant net 196 − 26 − 17,167 − 1,288 − 1,608 = −19,893. The published −1,621 billed accepted features only.",
        f"- Largest accepted box: {decision.get('largest_box')}.",
        f"- Remaining-saving without that box {_fmt(decision.get('saving_without_largest_box'))}.",
        f"- By seed: {decision.get('by_seed')}.",
        f"- {decision.get('note')}",
        "",
        "## Whole-box confirmation",
        "",
        f"- {'Ran.' if wholebox.get('ran') else 'Skipped. ' + str(wholebox.get('reason') or '')}",
        f"- Convincing unseen offline evidence: {offline.get('convincing_offline')}.",
        "- No new retrieval or placement mechanism. Thresholds were not retuned on this set.",
        "",
        "## Ledgers",
        "",
        f"- skip {ledger.get('skip_rollouts')}; commit {ledger.get('commit_rollouts')}; cache {ledger.get('cache_hits')}; feature checks {ledger.get('feature_checks')}.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT8C_REPORT.md").write_text(text, encoding="utf-8")
    return text
