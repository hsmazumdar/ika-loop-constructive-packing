"""Expt-17 report. Coverage only."""

from __future__ import annotations

import json
from pathlib import Path


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def write_report(run_dir: Path, config: dict, meta: dict, result: dict) -> None:
    acq = result["acquisition"]
    app = result["applicability"]
    decision = result["decision"]
    lines = [
        "# Expt-17 report",
        "",
        config["question"],
        "",
        "Arrangements are connected groups of a few pieces taken from acceptable primitive packings. Absolute position is removed by translation only. That normalisation is an engineered representation choice, not a discovered equivalence. Groups are not filtered for a rectangular outline and are not ordered by piece size. The dictionary is frozen before fresh trajectories are examined. A legal fit is recorded and not placed.",
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Pattern size: {config['min_pieces']} to {config['max_pieces']} pieces. Extraction cap per box: {config['max_checks_per_box']} groups.",
        f"- Recurrence: at least {config['min_inventories']} distinct training inventories. Repeats inside one trajectory count as one box.",
        f"- Stage bins: early occupied < {config['early_below']}, middle until {config['middle_below']}, then late.",
        f"- Cheap bar: matching checks below {config['cheap_fraction']} of the same workload's mean primitive effort, and at least {config['min_fit_boxes']} independent fresh boxes with an early or middle fit.",
        "",
        "## Acquisition",
        "",
        f"- Trajectories {acq['n_trajectories']}; acceptable {acq['n_acceptable']}; excluded {acq['n_excluded_unacceptable']}.",
        f"- Extraction checks {acq['extraction_checks']} ({_fmt(acq['extraction_per_acceptable_box'])} per acceptable box). Connected groups examined {acq['extraction_connected_groups']}. Boxes stopped by the extraction cap: {acq['boxes_capped']}.",
        f"- Distinct patterns {acq['n_patterns']}. Frozen because they recur across inventories: {acq['n_frozen']}.",
        f"- Frozen by piece count: {acq['frozen_by_pieces']}.",
        f"- Support by distinct inventories: {acq['support']['by_inventories']}.",
        f"- Support by independent boxes: {acq['support']['by_boxes']}.",
        f"- Store primitive effort per trajectory: {_fmt(acq['primitive_A_per_trajectory'])}. Extraction is a separate count of groups examined, not candidate-placement evaluations.",
        "",
        "## Fresh trajectories (read-only)",
        "",
    ]
    for name in ("independent_fresh", "recurring_family"):
        block = app[name]
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- Boxes {block['n_boxes']}; inventories also in the store: {block['n_inventory_in_store']}.")
        lines.append(f"- Primitive effort per box {_fmt(block['primitive_A_per_box'])}. Matching checks per box {_fmt(block['match_checks_per_box'])} ({block['match_fraction_of_primitive']:.1f} times primitive effort).")
        lines.append(f"- Boxes with any legal fit: {block['boxes_with_fit']}. Boxes with an early or middle fit: {block['boxes_with_early_or_middle_fit']}.")
        lines.append(f"- Fit events early {block['early_fits']}, middle {block['middle_fits']}, late {block['late_fits']} (a prefix and a pattern with at least one translation).")
        lines.append("")
    lines.extend([
        "## Decision",
        "",
        f"- Row: **{decision['row']}**.",
        f"- {decision['text']}",
        "- Commitment: not run. A fit is not admission into a policy.",
        "- If this census is negative, the next change is the environment or the representation, not another memory mechanism on the same late-cavity idea.",
        "",
    ])
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    report_dir = run_dir.parents[1] / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "EXPT17_REPORT.md").write_text(text, encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps({"acquisition": acq, "applicability": app, "decision": decision}, indent=2), encoding="utf-8")
