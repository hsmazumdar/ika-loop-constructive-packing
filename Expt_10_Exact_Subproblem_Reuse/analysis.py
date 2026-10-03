"""Expt-10 report. Exact subproblem reuse. Memorization, not abstraction."""

from __future__ import annotations

from pathlib import Path

from config import PHILOSOPHY


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _summary_line(summary: dict) -> str:
    return (
        f"- {summary.get('split')}/{summary.get('condition')}: n={summary.get('n')}; "
        f"mean A {_fmt(summary.get('mean_A'))}; mean Q {_fmt(summary.get('mean_Q'))}; "
        f"mean effort-saving {_fmt(summary.get('mean_effort_saving'))}; "
        f"mean remaining-search-avoided {_fmt(summary.get('mean_remaining_search_avoided'))}; "
        f"mean prefix primitive {_fmt(summary.get('mean_prefix_primitive'))}; "
        f"mean prefix placements {_fmt(summary.get('mean_prefix_n_place'))}; "
        f"mean first-hit occupied {_fmt(summary.get('mean_first_hit_occupied'))}; "
        f"quality-loss {_fmt(summary.get('quality_loss_rate'))}; "
        f"acceptable {_fmt(summary.get('acceptable_rate'))}; "
        f"hit rate {_fmt(summary.get('hit_rate'))} ({summary.get('n_hits')}/{summary.get('n_lookups')} lookups); "
        f"replays {summary.get('n_replays')}; validation fails {summary.get('n_validation_fails')}; "
        f"initial-state hits {summary.get('n_initial_state_hits')}; "
        f"nonzero-prefix hits {summary.get('n_nonzero_prefix_hits')}; "
        f"mean lookup {_fmt(summary.get('mean_lookup'))}; mean validation {_fmt(summary.get('mean_validation'))}; "
        f"mean learning {_fmt(summary.get('mean_learning'))}; mean primitive_evals {_fmt(summary.get('mean_primitive_evals'))}; "
        f"mean remaining primitive {_fmt(summary.get('mean_remaining_primitive'))}; "
        f"natural-opportunity traces {summary.get('n_natural_opportunity_traces')} "
        f"(rate {_fmt(summary.get('natural_opportunity_rate'))})."
    )


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, result: dict) -> str:
    lines = [
        "# Expt-10 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Store boxes ({len(result.get('store_ids') or [])}): {result.get('store_ids')}.",
        f"- Fresh boxes ({len(result.get('fresh_ids') or [])}): {result.get('fresh_ids')}.",
        f"- Constructed boxes ({len(result.get('constructed_ids') or [])}): {result.get('constructed_ids')}.",
        f"- Continuation keys stored: {result.get('n_keys')} ({result.get('n_initial_keys')} empty-board, {result.get('n_intermediate_keys')} intermediate); storage bytes {result.get('storage_bytes')}; overwrites counted not stored {result.get('n_overwrites')}; table frozen before eval.",
        f"- Memory: {result.get('memory_sharing')}.",
        "- A = primitive_evals + lookup + validation + learning.",
        "- Exact reuse is memorization. It is not evidence of abstraction and not a confirmation of Expt-8C.",
        "- Constructed recurrence is labeled. Each constructed inventory is an alternative covering of a stored prefix region, so the remaining (mask, inventory) matches after a nonempty prefix. Empty-board matches are excluded.",
        "- Natural intermediate recurrence is counted on fresh primitive traces (occupied > 0) without taking the hit. It is not pooled with constructed hits.",
        "",
        "## Protocol",
        "",
        "- One shared continuation table across seeds. First write wins. Evaluation agents share the frozen snapshot; they do not get private memories. A later seed's better packing is not retained.",
        "- Constructed prefix: each step bills one primitive scan (same RNG stream for memory-on and memory-off), then commits the labeled alternative covering, not necessarily the scan's argmax. Lookups start only after that nonempty prefix. Empty-board matches are excluded.",
        "- Remaining search avoided = primitive evaluations after the prefix on memory-off minus those after the prefix on memory-on.",
        "- Recurring complete repeats allow an empty-board hit (Expt-9 positive control). That is whole-solution recall, not intermediate reuse.",
        "- Fresh completed solves are new inventories. Hits there would be accidental exact remaining-state matches, not abstraction.",
        "",
        "## Recurrence",
        "",
        f"- Recurring complete problems lookup hit rate: {_fmt(result.get('recurrence_hit_rate_recurring'))}.",
        f"- Constructed intermediate lookup hit rate: {_fmt(result.get('recurrence_hit_rate_constructed'))}.",
        f"- Fresh lookup hit rate: {_fmt(result.get('recurrence_hit_rate_fresh'))}. Fresh completed solves on new inventories; hits would be accidental identical remaining states.",
        f"- Natural intermediate opportunity rate on fresh primitive traces: {_fmt(result.get('natural_intermediate_opportunity_rate'))}.",
        "",
        "## Constructed donors",
        "",
    ]
    for item in result.get("constructed_meta") or []:
        lines.append(
            f"- {item.get('task_id')} from donor {item.get('donor_task_id')} (first successful seed {item.get('donor_seed')}); "
            f"cut {item.get('cut')}; prefix occupied {item.get('prefix_occupied')}; "
            f"alt prefix length {item.get('n_alt_prefix')}; stored suffix length {item.get('suffix_len')}."
        )
    lines += ["", "## Conditions", ""]
    for summary in result.get("summaries") or []:
        lines.append(_summary_line(summary))
    lines += [
        "",
        f"- Useful on recurring complete repeats: {result.get('useful_on_recurring')}.",
        f"- Useful on constructed intermediate reuse (positive remaining-search avoided, quality-loss ≤ 0.2, nonzero-prefix hits, zero initial-state hits): {result.get('useful_on_constructed_intermediate')}.",
        f"- {result.get('note')}",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT10_REPORT.md").write_text(text, encoding="utf-8")
    return text
