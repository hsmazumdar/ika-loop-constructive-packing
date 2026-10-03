"""Expt-8 report. Offline prediction first. Whole-box only if a useful subset exists."""

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
        return f"- {name}: **zero coverage** ({sel.get('n_accepted', 0)}/{sel.get('n_actions', 0)} accepted). Rejecting everything is not successful selection."
    return (
        f"- {name}: accepted {sel.get('n_accepted')}/{sel.get('n_actions')} "
        f"on {sel.get('n_boxes_covered')}/{sel.get('n_boxes')} boxes, {sel.get('n_seeds_covered')} seeds; "
        f"mean remaining-saving {_fmt(sel.get('mean_remaining_saving'))}; "
        f"mean net after check cost {_fmt(sel.get('mean_net_after_check'))}; "
        f"quality-loss rate {_fmt(sel.get('quality_loss_rate'))}; "
        f"severe losses {sel.get('severe_loss_n')} ({_fmt(sel.get('severe_loss_rate'))}); "
        f"mean pred {_fmt(sel.get('mean_pred'))} vs observed {_fmt(sel.get('mean_observed'))}."
    )


def _err_line(name: str, err: dict) -> str:
    return (
        f"- {name}: n={err.get('n')}; MAE {_fmt(err.get('mae'))}; RMSE {_fmt(err.get('rmse'))}; "
        f"Pearson {_fmt(err.get('pearson'))}; AUC(beneficial) {_fmt(err.get('auc_beneficial'))}; "
        f"pred mean {_fmt(err.get('pred_mean'))} vs y mean {_fmt(err.get('y_mean'))}; "
        f"pred range [{_fmt(err.get('pred_min'))}, {_fmt(err.get('pred_max'))}]."
    )


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, offline: dict, wholebox: dict, ledger: dict) -> str:
    pooled = offline.get("pooled") or []
    by = {p["predictor"]: p for p in pooled}
    lines = [
        "# Expt-8 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Frozen libraries: `{meta.get('expt7_result')}` (no library retraining).",
        f"- Fit boxes: {offline.get('fit_ids')}; validation boxes: {offline.get('val_ids')}.",
        "- Remaining-solves are diagnosis only. consultation_cost includes index probes and ranking.",
        "- Accept if predicted remaining-saving > remaining-check cost (anchors) AND P(quality_ok) ≥ threshold. The saving bar is not lowered.",
        "",
        "## 1. Prediction-target audit",
        "",
        f"- Training action: {audit.get('training_action')}.",
        f"- Deployment action: {audit.get('deployment_action')}.",
        f"- Train/deploy action mismatch: {audit.get('train_deploy_action_mismatch')} (both are first_legal_site, not the oracle-best placement).",
        f"- Sign: {audit.get('remaining_saving_sign')}. Units: {audit.get('training_units')}. No inverse scaling. No prediction clipping.",
        f"- Training remaining-solve cap: {audit.get('training_remaining_cap')}. Expt-7B used {audit.get('expt7b_remaining_cap')}. Cap mismatch: {audit.get('cap_mismatch')}.",
        f"- Training labels n={audit.get('n_training_labels')}; unweighted mean remaining-saving {_fmt(audit.get('training_saving_mean'))}; severe-loss-weighted mean {_fmt(audit.get('training_saving_weighted_mean'))}.",
        f"- Benefit model has no operation identifier; quality model has per-op bias. Context features have no orientation/anchor/local geometry.",
        f"- {audit.get('note')}",
        "",
        "## 2. Held-out prediction error (first-legal actions)",
        "",
    ]
    for kind in ("constant", "frozen", "context", "action"):
        if kind in by:
            lines.append(_err_line(kind, by[kind]["errors_first_legal"]))
    lines += [
        f"- Action-level MAE beats constant mean: {offline.get('beats_constant')}.",
        "- Validation remaining-solves use eval_cap − prefix_A. Training used pair_eval_cap=1600. That cap mismatch inflates held-out y relative to what the frozen model was fit on; it is an implementation inconsistency, not evidence to lower the admit bar.",
        "",
        "## 3. Selection quality on validation (do not read reject-all as success)",
        "",
        f"- Remaining-check cost = {offline.get('remaining_check')}.",
    ]
    for kind in ("constant", "frozen", "context", "action"):
        if kind in by:
            lines.append(_sel_line(f"{kind} first-legal", by[kind]["selection_first_legal"]))
            lines.append(_sel_line(f"{kind} all labeled placements", by[kind]["selection_all_placements"]))
    lines += [
        "",
        "## 4. Bounded placement selection",
        "",
    ]
    if not offline.get("proceed_placement"):
        lines.append("- Skipped. Validation did not support a useful accepted subset, so extra legal placements were not promoted to a deployable search.")
    else:
        lines.append(f"- Frozen n_placements on development: {offline.get('chosen_n_placements')}.")
        for rec in offline.get("placement_table") or []:
            lines.append(f"- n={rec['n_placements']} fit useful={rec.get('useful_on_fit')}; val " + _sel_line("selection", rec["val"]).removeprefix("- selection: "))
    lines += [
        "",
        "## 5. Whole-box confirmation",
        "",
    ]
    if not wholebox.get("ran"):
        lines.append(f"- Skipped. {wholebox.get('reason')}. Budget 0 remains the required comparator if a later subset is ever deployed.")
    else:
        lines.append(f"- Fresh boxes n_fresh={wholebox.get('n_fresh')}; n_placements={wholebox.get('n_placements')}.")
        rows = wholebox.get("rows") or []
        by_c = {}
        for row in rows:
            by_c.setdefault(row["condition"], []).append(row)
        for name, group in by_c.items():
            mean_a = sum(float(r["A"]) for r in group) / len(group)
            mean_s = sum(float(r["effort_saving"]) for r in group) / len(group)
            ql = sum(1.0 for r in group if r["quality_loss"] in (True, "True", "true")) / len(group)
            lines.append(f"- {name}: n={len(group)}; mean A {_fmt(mean_a)}; mean effort saving {_fmt(mean_s)}; quality-loss rate {_fmt(ql)}.")
    lines += [
        "",
        "## Ledgers",
        "",
        f"- Diagnostic skip rollouts {ledger.get('skip_rollouts')}; commit rollouts {ledger.get('commit_rollouts')}; cache hits {ledger.get('cache_hits')}; feature checks {ledger.get('feature_checks')}.",
        "",
        "## What this does and does not show",
        "",
        "- Do not lower the acceptance threshold just because predictions are negative. A negative mean outcome means indiscriminate acceptance can restore quality or effort damage.",
        "- Uniformly negative predictions do not alone prove miscalibration. Distinguish implementation error, calibration to a weighted mean, and missing placement information using the audit and the three-predictor comparison.",
        "- Offline remaining-solve benefit is not whole-box policy savings. Commitments change later states.",
        "- Include consultation budget 0 in any later deployment comparison.",
        "",
        "Libraries were not retrained. The question is whether inexpensive pre-commitment information about a specific placement can distinguish beneficial reuse from costly reuse.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT8_REPORT.md").write_text(text, encoding="utf-8")
    return text
