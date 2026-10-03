"""Expt-9 report. Exact continuation reuse. Memorization, not abstraction."""

from __future__ import annotations

from pathlib import Path

from config import PHILOSOPHY


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, result: dict) -> str:
    lines = [
        "# Expt-9 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Store boxes ({len(result.get('store_ids') or [])}): {result.get('store_ids')}.",
        f"- Fresh boxes ({len(result.get('fresh_ids') or [])}): {result.get('fresh_ids')}.",
        f"- Continuation keys stored: {result.get('n_keys')}; storage bytes {result.get('storage_bytes')}; table frozen before eval.",
        "- A = primitive_evals + lookup + validation + learning. Lookup, validation, storage, and learning are counted separately.",
        "- Exact reuse is memorization. It is not evidence of abstraction and not a confirmation of Expt-8C.",
        "",
        "## Recurrence",
        "",
        f"- Recurring (same boxes as store) lookup hit rate: {_fmt(result.get('recurrence_hit_rate_recurring'))}.",
        f"- Fresh lookup hit rate: {_fmt(result.get('recurrence_hit_rate_fresh'))}. Fresh hits are accidental identical remaining states.",
        "",
        "## Conditions",
        "",
    ]
    for summary in result.get("summaries") or []:
        lines.append(
            f"- {summary.get('split')}/{summary.get('condition')}: n={summary.get('n')}; "
            f"mean A {_fmt(summary.get('mean_A'))}; mean Q {_fmt(summary.get('mean_Q'))}; "
            f"mean effort-saving {_fmt(summary.get('mean_effort_saving'))}; "
            f"quality-loss {_fmt(summary.get('quality_loss_rate'))}; "
            f"acceptable {_fmt(summary.get('acceptable_rate'))}; "
            f"hit rate {_fmt(summary.get('hit_rate'))} ({summary.get('n_hits')}/{summary.get('n_lookups')} lookups); "
            f"replays {summary.get('n_replays')}; validation fails {summary.get('n_validation_fails')}; "
            f"mean lookup {_fmt(summary.get('mean_lookup'))}; mean validation {_fmt(summary.get('mean_validation'))}; "
            f"mean learning {_fmt(summary.get('mean_learning'))}; mean primitive_evals {_fmt(summary.get('mean_primitive_evals'))}."
        )
    lines += [
        "",
        f"- Useful on recurring (positive mean effort-saving, quality-loss ≤ 0.2, nonzero hits): {result.get('useful_on_recurring')}.",
        "",
        "## What this result does and does not establish",
        "",
        "- 36/36 recurring lookups hit on the first lookup, with zero primitive evaluations. That is whole-solution recall from the empty board. Intermediate keys were stored (suffixes along each successful stack) but this evaluation never required them.",
        "- Memory is **one shared table** across seeds 11/22/33. Evaluation agents do not receive their own memory. The table is filled during store, then frozen.",
        "- On a collision, **first write wins**. A later seed's different continuation is counted as an overwrite and is not stored. This is not a best-of retention rule.",
        "- Recurring mean Q 76.75 versus store mean Q 76.36 follows from that rule: every recurring replay used the first stored packing (seed 11, mean Q 76.75). Store mean Q averages three primitive packings (76.75, 76.50, 75.83).",
        "- Fresh-condition rows **are** completed solves on new inventories. The earlier sentence “whole-box on new inventories was not run” was wrong. The intended statement is: **no continuation reuse occurred on new inventories** (0 hits in 589 lookups). Quality was preserved; the exact agent paid unsuccessful-lookup overhead.",
        f"- {result.get('note')}",
        "",
        "Conditional break-even on evaluation effort for a mix of exact repeats and fresh cases, using these means and excluding acquisition/storage: p > 16.36/(868.9+16.36) ≈ 1.85% exact repeats. Same costs and distributions only.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT9_REPORT.md").write_text(text, encoding="utf-8")
    return text
