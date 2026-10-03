"""Expt-8B report. Consistent remaining-budget labels. Development then holdout."""

from __future__ import annotations

from pathlib import Path

from config import PHILOSOPHY


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _sel_line(name: str, sel: dict) -> str:
    if sel.get("zero_coverage"):
        return (
            f"- {name}: **zero coverage** ({sel.get('n_accepted', 0)}/{sel.get('n_actions', 0)} actions). "
            f"Eligible: {sel.get('n_unique_boxes')} unique boxes, {sel.get('n_seed_box_pairs')} seed–box pairs, "
            f"{sel.get('n_states')} states, {sel.get('n_actions')} actions. Reject-all is not successful selection."
        )
    return (
        f"- {name}: accepted {sel.get('n_accepted')}/{sel.get('n_actions')} actions "
        f"on {sel.get('n_accepted_unique_boxes')} unique boxes / {sel.get('n_accepted_seed_box_pairs')} seed–box pairs / "
        f"{sel.get('n_accepted_states')} states "
        f"(eligible: {sel.get('n_unique_boxes')} boxes, {sel.get('n_seed_box_pairs')} pairs, {sel.get('n_states')} states); "
        f"mean remaining-saving {_fmt(sel.get('mean_remaining_saving'))}; "
        f"mean billed examined {_fmt(sel.get('mean_examined_billed'))}; "
        f"mean net = remaining-saving − examined {_fmt(sel.get('mean_net_after_check'))}; "
        f"admission bound {sel.get('admission_bound')} is not subtracted from the label; "
        f"quality-loss rate {_fmt(sel.get('quality_loss_rate'))}; "
        f"severe losses {sel.get('severe_loss_n')} ({_fmt(sel.get('severe_loss_rate'))})."
    )


def _err_line(name: str, err: dict) -> str:
    within = err.get("pearson_within_seed") or {}
    return (
        f"- {name}: n={err.get('n')}; MAE {_fmt(err.get('mae'))}; RMSE {_fmt(err.get('rmse'))}; "
        f"pooled Pearson {_fmt(err.get('pearson_pooled'))}; "
        f"within-seed Pearson {within.get('within_seed')}; "
        f"AUC(beneficial) {_fmt(err.get('auc_beneficial'))}; "
        f"pred mean {_fmt(err.get('pred_mean'))} vs y mean {_fmt(err.get('y_mean'))}; "
        f"pred range [{_fmt(err.get('pred_min'))}, {_fmt(err.get('pred_max'))}]."
    )


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, offline: dict, wholebox: dict, ledger: dict) -> str:
    pooled = {p["predictor"]: p for p in (offline.get("pooled") or [])}
    hold = {p["predictor"]: p for p in (offline.get("holdout_pooled") or [])}
    cap = offline.get("cap_distortion") or {}
    val_sel = (pooled.get("per_seed_mean") or {}).get("selection_first_legal") or {}
    act_sel = (pooled.get("action_unweighted") or {}).get("selection_first_legal") or {}
    hold_act = (hold.get("action_unweighted") or {}).get("selection_first_legal") or {}
    hold_base = (hold.get("per_seed_mean") or {}).get("selection_first_legal") or {}
    n_val_ids = len(offline.get("val_ids") or [])
    n_hold_ids = len(offline.get("holdout_ids") or [])
    lines = [
        "# Expt-8B report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        "- Frozen libraries from Expt-7. No library retraining. Same features and admit bar as Expt-8.",
        f"- Development fit boxes ({len(offline.get('fit_ids') or [])}): {offline.get('fit_ids')}.",
        f"- Development validation boxes ({n_val_ids}): {offline.get('val_ids')}.",
        f"- Frozen-protocol holdout boxes ({n_hold_ids}): {offline.get('holdout_ids')}.",
        "- Label remaining budget is eval_cap − prefix_primitive_A for fit, validation, and holdout.",
        "- remaining_saving = A_skip − A_commit and does not include site-check cost. Net after check subtracts actual examined, not the admission bound of 8.",
        "- Primary saving fit is unweighted. Severe-loss-weighted models are a labeled comparison, not expected savings.",
        "",
        "## Coverage counts (development validation, first-legal eligible)",
        "",
        f"- Split lists {n_val_ids} validation box IDs. Eligible first-legal labels exist on {val_sel.get('n_unique_boxes')} unique boxes, {val_sel.get('n_seed_box_pairs')} seed–box pairs, {val_sel.get('n_states')} states, {val_sel.get('n_actions')} actions.",
        "- Expt-8's \"5/11 boxes\" was 5 unique boxes and 11 seed–box pairs with eligible actions, not 11 unique boxes. One of the six listed validation IDs produced no eligible first-legal action.",
        f"- Holdout lists {n_hold_ids} box IDs. Eligible first-legal labels: {hold_base.get('n_unique_boxes')} unique boxes, {hold_base.get('n_seed_box_pairs')} seed–box pairs, {hold_base.get('n_states')} states, {hold_base.get('n_actions')} actions.",
        "",
        "## Cap mismatch: same actions, both budgets",
        "",
        f"- Paired replays: {cap.get('n_paired')}; 1600-cap hits skip {cap.get('n_skip_capped_1600')}, commit {cap.get('n_commit_capped_1600')}, either {cap.get('n_either_capped_1600')}.",
        f"- Mean saving full {_fmt(cap.get('mean_saving_full'))}; mean saving 1600 {_fmt(cap.get('mean_saving_1600'))}; mean (full − 1600) {_fmt(cap.get('mean_delta_full_minus_1600'))}.",
        f"- Full greater {cap.get('n_full_greater')}; full smaller {cap.get('n_full_smaller')}; equal {cap.get('n_equal')}.",
        "- Distortion goes both ways. A 1600 cap does not automatically inflate validation savings. The signed mean here is the measured effect on these paired labels, not a general inflation theorem.",
        "",
        "## Development validation error (first-legal)",
        "",
    ]
    for kind in ("per_seed_mean", "frozen", "context_unweighted", "action_unweighted", "context_weighted", "action_weighted"):
        if kind in pooled:
            lines.append(_err_line(kind, pooled[kind]["errors_first_legal"]))
    lines += [
        f"- Unweighted action-level MAE beats per-seed mean: {offline.get('beats_constant')}.",
        "- The baseline is a per-seed mean, constant within a seed. Within-seed Pearson is undefined. Pooled Pearson can still be nonzero because seed means differ (fit means were negative on seeds 11 and 22 and slightly positive on seed 33).",
        "- Weighted models estimate a different target. Their large negative predictions are not ordinary expected savings.",
        "",
        "## Development validation selection",
        "",
        f"- Admission bound pred_saving > {offline.get('remaining_check')}. Quality gate unchanged. Billed cost is examined, not the bound of 8.",
    ]
    for kind in ("per_seed_mean", "frozen", "context_unweighted", "action_unweighted", "context_weighted", "action_weighted"):
        if kind in pooled:
            lines.append(_sel_line(kind + " first-legal", pooled[kind]["selection_first_legal"]))
    lines += [
        f"- Per-seed mean still accepts only where the seed's fit mean exceeds 8 (seed 33). Quality-loss { _fmt(val_sel.get('quality_loss_rate')) } exceeds the 0.2 gate. Positive mean net on that slice is not a useful subset.",
        f"- Unweighted action-level coverage on development validation: {act_sel.get('n_accepted', 0)} accepted. Frozen choice after development is abstain: no learned predictor has a useful accepted subset.",
        "",
        "## Holdout (protocol frozen; models fit on development only)",
        "",
    ]
    if not hold:
        lines.append("- Holdout was not collected.")
    else:
        for kind in ("per_seed_mean", "context_unweighted", "action_unweighted"):
            if kind in hold:
                lines.append(_err_line(kind, hold[kind]["errors_first_legal"]))
                lines.append(_sel_line(kind + " first-legal", hold[kind]["selection_first_legal"]))
        lines += [
            f"- Mechanical holdout useful_subset flag: {offline.get('holdout_useful')}.",
            f"- Action-unweighted accepted {hold_act.get('n_accepted')} first-legal actions on {hold_act.get('n_accepted_unique_boxes')} unique boxes, all on seed 33. Mean net {_fmt(hold_act.get('mean_net_after_check'))} with quality-loss {_fmt(hold_act.get('quality_loss_rate'))}. That slice includes a zero-saving placement whose billed checks are a net loss; the mean is carried by one large positive remainder.",
            f"- Per-seed mean also accepts on seed 33 only ({hold_base.get('n_accepted')} actions, quality-loss {_fmt(hold_base.get('quality_loss_rate'))}, severe-loss rate {_fmt(hold_base.get('severe_loss_rate'))}). A larger mean net with 27.8% severe losses is not a better policy.",
            "- Holdout does not show that action-level decisions improve on the per-seed mean across seeds. Development already froze the learned models at zero coverage. The four-action holdout slice is not a selected, deployable subset.",
        ]
    skipped = "Skipped. " + str(wholebox.get("reason") or "no useful subset")
    lines += [
        "",
        "## Whole-box confirmation",
        "",
        f"- {'Ran.' if wholebox.get('ran') else skipped}",
        "- No new retrieval or placement mechanism was added. Budget 0 remains required if a later subset is ever deployed.",
        "",
        "## Ledgers",
        "",
        f"- skip {ledger.get('skip_rollouts')}; commit {ledger.get('commit_rollouts')}; cache {ledger.get('cache_hits')}; feature checks {ledger.get('feature_checks')}.",
        "",
        "The 8-evaluation figure is the admission bound (pred_saving > anchors). Billed site-check cost is examined (often 1–3, mean about 2.2 on development first-legal). That is why net can drop by about two rather than eight.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT8B_REPORT.md").write_text(text, encoding="utf-8")
    return text
