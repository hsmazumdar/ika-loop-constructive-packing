"""Expt-18 report. Utility of a sample, not a matcher budget."""

from __future__ import annotations

import json
from pathlib import Path


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _candidate_lines(title: str, block: dict) -> list[str]:
    lines = [f"### {title}", ""]
    valid = block.get("valid_replayed") or {}
    kept = block.get("quality_preserving") or {}
    lines.append(
        f"- Placements replayed {block.get('n_rows', 0)}; invalid commits {block.get('n_invalid', 0)}; "
        f"primitive replay failures {block.get('n_replay_failed', 0)}."
    )
    lines.append(
        f"- Candidate-level, valid replays: n={valid.get('n', 0)}, "
        f"mean saving {_fmt(valid.get('mean_effort_saving'))}, median {_fmt(valid.get('median_effort_saving'))}, "
        f"mean quality delta {_fmt(valid.get('mean_quality_delta'))}, quality losses {valid.get('n_quality_loss', 0)}."
    )
    lines.append(
        f"- Candidate-level, quality-preserving and effort-positive: n={kept.get('n', 0)}, "
        f"mean saving {_fmt(kept.get('mean_effort_saving'))}, median {_fmt(kept.get('median_effort_saving'))}."
    )
    lines.append("- These averages are not added across prefixes of the same box.")
    lines.append("")
    return lines


def write_report(run_dir: Path, config: dict, meta: dict, result: dict) -> None:
    decision = result["decision"]
    sample = result["sample"]
    cost = result["diagnostic_cost"]
    lines = [
        "# Expt-18 report",
        "",
        config["question"],
        "",
        "Expt-17 separated recurrence from applicability, and showed that exhaustive translation matching exceeds its 0.10 bar by about 456 times on fresh inventories and about 818 times on recurring families. This run does not revisit that gate and does not treat a legal fit as a reason to commit. It asks only whether the recorded arrangements have enough quality-preserving benefit, on a small predeclared sample, to justify building a cheaper matcher later.",
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Frozen dictionary: Expt-17 `20260930_090000_diagnostic`, {result['n_frozen']} patterns, sha256 `{config['frozen_sha256']}`.",
        f"- Sampled pattern indices: {sample['pattern_indices']}.",
        f"- Of those, support at least {config['high_support']} inventories: {sample['high_support_indices']}.",
        f"- Fresh box indices (stride {config['fresh_stride']}): {sample['boxes']['independent_fresh']}.",
        f"- Family box indices (stride {config['family_stride']}): {sample['boxes']['recurring_family']}.",
        f"- Stages: {sample['stages']}. One earliest legal translation per box, pattern, and stage.",
        f"- Benefit floor: remaining-effort saving at least {config['min_saving']} after commitment checks, quality within {config['quality_loss_margin']}, acceptability kept.",
        f"- Broad bar: at least {config['min_benefit_boxes']} independent fresh boxes, at least {config['min_patterns_broad']} patterns, and both early and middle.",
        "",
        "## What was measured",
        "",
        "Each sampled placement is replayed twice from the saved board, inventory, RNG state, and tabu. One branch continues with the primitive policy. The other places the pattern, after one check per piece and per cell, then continues with the primitive policy. Both branches keep the same primitive search room, `eval_cap` minus the effort already spent. Commitment checks are part of the commit branch's effort. The box-level opportunity is the single best quality-preserving candidate in that box. It is not the sum of the candidates. Within a stage the placement is the earliest fitting prefix, so an early sample is the empty board whenever the initial inventory already contains the pattern's pieces. Later prefixes in that same bin are not additional samples.",
        "",
        "## Candidate-level detail",
        "",
        "A candidate average can be dominated by many similar early placements. It is not the decision statistic.",
        "",
    ]
    for name in ("independent_fresh", "recurring_family"):
        lines.extend(_candidate_lines(name, result["candidates"][name]))
    lines.extend([
        "## Box-level opportunities",
        "",
        "Ideal selection keeps only candidates that preserve quality and acceptability and reduce remaining effort. The reported saving is the best such candidate, or zero when none exists.",
        "",
    ])
    for box in result["box_rows"]:
        lines.append(
            f"- {box['workload']} index {box['index']} `{box['task_id']}`: "
            f"candidates {box['n_candidates']}, quality-preserving {box['n_quality_preserving']}, "
            f"ideal saving {box['ideal_saving']}"
            + (
                f" (pattern {box['ideal_pattern']}, {box['ideal_stage']}, occupied {box.get('ideal_occupied')}, quality delta {_fmt(box['ideal_quality_delta'])})"
                if box["ideal_pattern"] is not None
                else ""
            )
            + f", counts as benefit: {box['counts_as_benefit']}."
            + (
                f" Largest valid saving {_fmt(box['largest_valid_saving'])} lost quality: {box['largest_valid_lost_quality']}."
                if box["largest_valid_saving"] is not None
                else ""
            )
        )
    fresh = [box for box in result["box_rows"] if box["workload"] == "independent_fresh" and box["counts_as_benefit"]]
    early_empty = [box for box in fresh if box["ideal_stage"] == "early" and box.get("ideal_occupied") == 0]
    middle = [box for box in fresh if box["ideal_stage"] == "middle"]
    dropped = [
        box for box in result["box_rows"]
        if box["workload"] == "independent_fresh" and box.get("largest_valid_lost_quality") and box["counts_as_benefit"]
    ]
    lines.extend([
        "",
        "## Where the fresh box-level benefit sits",
        "",
        f"- Fresh boxes whose best quality-preserving candidate is an empty-board early placement: {len(early_empty)}.",
        f"- Fresh boxes whose best quality-preserving candidate is a middle placement: {len(middle)}.",
        f"- On {len(dropped)} benefiting fresh boxes the largest effort cut lost more than the quality margin, and ideal selection did not take it.",
        "- A one-cell drop is inside the margin of 1.0. It is not counted as a quality loss.",
        "",
        "## Diagnostic cost",
        "",
        f"- Discovery checks to locate the sampled placements: {cost['discovery_checks']}.",
        f"- Counterfactual effort, both branches: {cost['counterfactual_A']}.",
        f"- Wall time: {_fmt(cost['seconds'])} seconds.",
        f"- {cost['role']}.",
        "",
        "## Decision",
        "",
        f"- Row: **{decision['row']}**.",
        f"- {decision['text']}",
        f"- Independent fresh boxes at or above the saving floor: {decision['n_fresh_benefit_boxes']}. Patterns {decision['fresh_patterns']}. Stages {decision['fresh_stages']}.",
        f"- Family boxes at or above the saving floor: {decision['n_family_benefit_boxes']}. Family benefit alone cannot justify a general matcher.",
        f"- Commitment: {decision['commitment']}.",
        f"- Expt-17 cost gate: {decision['cost_gate']}.",
        "",
    ])
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    report_dir = run_dir.parents[1] / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "EXPT18_REPORT.md").write_text(text, encoding="utf-8")
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "sample": sample,
                "candidates": result["candidates"],
                "diagnostic_cost": cost,
                "decision": decision,
                "box_rows": result["box_rows"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
