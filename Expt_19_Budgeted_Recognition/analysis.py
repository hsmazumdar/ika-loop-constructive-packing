"""Expt-19 report. Recognition only."""

from __future__ import annotations

import json
from pathlib import Path


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _block(title: str, block: dict) -> list[str]:
    lines = [
        f"### {title}",
        "",
        f"- Boxes {block['n_boxes']}. Mean primitive effort {_fmt(block['mean_primitive'])}. Mean recognition {_fmt(block['mean_recognition'])}. Mean ratio {_fmt(block['mean_ratio'])}.",
        f"- Boxes under the 0.10 gate: {block['boxes_under_gate']}. Budget exhausted: {block['boxes_budget_exhausted']}.",
        f"- Audited states with a useful reference action: {block['n_audited_states_with_useful']}. State recall {_fmt(block['state_recall'])}. Action recall {_fmt(block['action_recall'])} of {block['n_useful_actions']} useful actions.",
        f"- Boxes with a reference opportunity: {block['n_boxes_with_reference']}. Mean oracle saving {_fmt(block['mean_oracle_saving'])}. Mean retained {_fmt(block['mean_retained_saving'])}. Mean retention {_fmt(block['mean_retention'])}.",
        f"- Miss reasons among useful actions: {block['miss_reasons']}.",
        f"- Stronger support (at least 3 inventories): {block['high_support']}.",
        f"- Support-two patterns: {block['support_two']}.",
        f"- Unlabeled exposures (not in the sampled reference): {block['unlabeled_exposures']}.",
        f"- Diagnostic enumeration and replays, not recognition cost: {block['diagnostic_checks']} discovery checks, {block['diagnostic_A']} counterfactual evaluations.",
        "",
    ]
    return lines


def write_report(run_dir: Path, config: dict, meta: dict, result: dict) -> None:
    decision = result["decision"]
    lines = [
        "# Expt-19 report",
        "",
        config["question"],
        "",
        "The 58 arrangements stay frozen. The matcher may only propose a placement; commitment is disabled. Development manifests set one absolute recognition budget from their mean primitive effort. Validation fresh is the decision set. Counterfactual replays that label the reference are a separate diagnostic ledger. Recall is against that sample, not against every legal placement.",
        "",
        "The advice note recommended this recognition step only after Expt-18, and it kept a commitment rule as a later experiment. It also suggested a learned embedding and a risk gate. Those are not part of this run. The anchor rule was not adjusted to the ten Expt-18 boxes or the five patterns those boxes used.",
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Frozen patterns: {result['n_frozen']}. Reference sample indices: {result['reference_indices']}.",
        f"- Stronger-support indices inside that sample: {result['high_support_indices']}.",
        f"- Development boxes: {result['development_n']}. Mean primitive effort {_fmt(result['development_mean_primitive'])}. Absolute budget {result['budget']}.",
        f"- Validation tasks excluded because their id was in the development manifests: {len(result['excluded_family_ids'])}.",
        f"- Anchors: {config['anchors']}",
        f"- Gate: {config['evaluation_gate']}. Recall floor {config['min_state_recall']}. Retention floor {config['min_retention']}. At least {config['min_boxes_with_reference']} fresh boxes with a reference opportunity.",
        "",
        "## Validation fresh (decision set)",
        "",
    ]
    lines.extend(_block("validation_fresh", result["fresh"]))
    lines.extend(["## Validation family (not the decision)", ""])
    lines.extend(_block("validation_family", result["family"]))
    lines.extend([
        "## Decision",
        "",
        f"- Row: **{decision['row']}**.",
        f"- {decision['text']}",
        f"- Fresh recognition / primitive: {_fmt(decision['fresh_ratio'])}. Cheap: {decision['cheap']}.",
        f"- State recall {_fmt(decision['state_recall'])}. Mean retention {_fmt(decision['mean_retention'])}.",
        f"- Commitment: {decision['commitment']}.",
        f"- {decision['cost_gate']}.",
        "- A successful recogniser would still not establish cheaper autonomous solving. That needs a frozen commitment policy that preserves whole-box quality and repays recognition, including rejected consultations.",
        "",
    ])
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    report_dir = run_dir.parents[1] / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "EXPT19_REPORT.md").write_text(text, encoding="utf-8")
    persist = {
        "budget": result["budget"],
        "development_mean_primitive": result["development_mean_primitive"],
        "development_n": result["development_n"],
        "n_frozen": result["n_frozen"],
        "reference_indices": result["reference_indices"],
        "high_support_indices": result["high_support_indices"],
        "n_excluded": len(result["excluded_family_ids"]),
        "fresh": result["fresh"],
        "family": result["family"],
        "decision": decision,
    }
    (run_dir / "summary.json").write_text(json.dumps(persist, indent=2), encoding="utf-8")
