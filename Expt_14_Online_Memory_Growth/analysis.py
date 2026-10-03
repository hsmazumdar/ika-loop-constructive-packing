"""Expt-14 report. Online exact-memory growth with chronological evaluation."""

from __future__ import annotations

import csv
from pathlib import Path

from config import PHILOSOPHY

TITLES = {
    "independent_fresh": "Independent fresh inventories",
    "recurring_family": "Recurring task families with varying inventories",
}


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _cond_line(cond: str, block: dict) -> str:
    return (
        f"- {cond}: streams {block.get('n_streams')}; cumulative saving per stream mean {_fmt(block.get('mean_cumulative_saving'))} "
        f"(min {_fmt(block.get('min_cumulative_saving'))}, max {_fmt(block.get('max_cumulative_saving'))}); "
        f"per-box {_fmt(block.get('mean_per_box_saving'))}; early third {_fmt(block.get('mean_early_saving'))} vs late third "
        f"{_fmt(block.get('mean_late_saving'))} (late > early in {block.get('n_streams_late_gt_early')} streams); "
        f"initial hits {block.get('total_initial_hits')}; intermediate hits {block.get('total_intermediate_hits')}; "
        f"hits on grown keys {block.get('total_hits_from_grown')}; "
        f"never-encountered rows {block.get('total_never_encountered')} (mean saving {_fmt(block.get('mean_saving_never_encountered'))}, "
        f"reuse {block.get('total_reuse_never_encountered')}, intermediate hits {block.get('total_intermediate_hits_never_encountered')}); "
        f"repeated rows {block.get('total_repeated')} (reuse {block.get('total_reuse_repeated')}, saving sum {_fmt(block.get('sum_saving_repeated'))}); "
        f"quality-loss {block.get('total_quality_loss')}; validation fails {block.get('total_validation_fails')}; "
        f"key growth factor {_fmt(block.get('mean_key_growth_factor'))}; insertion per box {_fmt(block.get('mean_insertion_per_box'))}."
    )


def _stream_line(s: dict) -> str:
    return (
        f"  - stream {s.get('stream_id')} / {s.get('condition')}: n={s.get('n')}; cumulative {_fmt(s.get('cumulative_saving'))}; "
        f"early {_fmt(s.get('early_mean_saving'))} late {_fmt(s.get('late_mean_saving'))}; "
        f"initial {s.get('n_initial_hits')} intermediate {s.get('n_intermediate_hits')} grown-key hits {s.get('n_hits_from_grown')}; "
        f"reuse {s.get('n_boxes_valid_reuse')}/{s.get('n')}; never-encountered {s.get('n_never_encountered')} "
        f"(saving {_fmt(s.get('cumulative_saving_never_encountered'))}); quality-loss {s.get('n_quality_loss')}; "
        f"validation fails {s.get('n_validation_fails')}; keys {s.get('keys_start')} → {s.get('keys_end')}; "
        f"lookup {_fmt(s.get('mean_lookup'))} insertion {_fmt(s.get('mean_insertion'))}."
    )


def _revisit_lines(run_dir: Path) -> list[str]:
    path = run_dir / "eval.csv"
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("condition") == "growing_exact"]
    lines = [
        "## State revisits at insertion time (growing memory)",
        "",
        "Each completed trajectory state is probed on insertion. A probe that finds an existing key means the agent's own trajectory passed through a stored state.",
        "",
    ]
    for workload in ("independent_fresh", "recurring_family"):
        for label, want in (("never-encountered inventories", True), ("repeated inventories", False)):
            g = [
                r for r in rows
                if r.get("workload") == workload and (r.get("inventory_never_encountered") == "True") == want
            ]
            if not g:
                continue
            probed = sum(int(float(r.get("keys_probed") or 0)) for r in g)
            written = sum(int(float(r.get("keys_written") or 0)) for r in g)
            lines.append(
                f"- {TITLES[workload]} / {label}: boxes {len(g)}; states probed {probed}; new keys {written}; "
                f"already stored {probed - written}; mean new keys per box {written / len(g):.3g}."
            )
    lines.append("")
    return lines


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, result: dict) -> str:
    lines = [
        "# Expt-14 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Independent store: {result.get('store_independent_ids')}.",
        f"- Family store: {result.get('family_store_ids')}.",
        f"- Family specs (declared before evaluation): {[s.get('type_set') for s in result.get('family_specs') or []]}.",
        f"- Base table: {result.get('n_base_keys')} keys (empty-board {result.get('n_base_initial_keys')}); frozen condition uses it unchanged; each stream's growing copy starts from it.",
        f"- Streams: {config.get('n_streams')} independent streams × {config.get('n_per_stream')} boxes per workload; one seed per stream.",
        f"- Insertion billing: {config.get('insertion_billing')}.",
        f"- A = {config.get('A_identity')}.",
        "- Retrieval is exact state identity. Transformation matching is excluded from this comparison. First write wins.",
        "- Streams are declared before evaluation; no task is chosen by checking memory. Repeated inventories are kept and reported separately.",
        "",
    ]
    decisions = result.get("decisions") or {}
    for workload in ("independent_fresh", "recurring_family"):
        block = (result.get("across") or {}).get(workload) or {}
        d = decisions.get(workload) or {}
        lines += [f"## {TITLES[workload]}", "", f"- Decision: {d.get('outcome')}."]
        if d.get("outcome_C_text"):
            lines.append(f"- Also: {d.get('outcome_C_text')}. The decisive evidence is the absence of intermediate hits, not the growth threshold.")
        if workload == "recurring_family":
            lines.append("- Compare growing against both references: positive versus primitive does not mean better than frozen. Insertion can outweigh the additional recall benefit without removing all recall benefit.")
        lines += [
            f"- Growing: intermediate hits on never-encountered inventories {d.get('intermediate_hits_never_encountered')}; "
            f"reuse on never-encountered {d.get('reuse_never_encountered')}; reuse on repeated {d.get('reuse_repeated')}; "
            f"repays on never-encountered {d.get('repays_on_never_encountered')}; key growth ×{_fmt(d.get('mean_key_growth_factor'))} "
            f"(substantial ≥ ×{config.get('growth_substantial_factor')}: {d.get('growth_substantial')}).",
            "",
        ]
        for cond in ("primitive", "frozen_exact", "growing_exact"):
            if cond == "primitive":
                continue
            lines.append(_cond_line(cond, block.get(cond) or {}))
        lines.append("")
        for cond in ("frozen_exact", "growing_exact"):
            for s in (block.get(cond) or {}).get("streams") or []:
                lines.append(_stream_line(s))
        lines.append("")
    lines += _revisit_lines(run_dir)
    lines += [f"- {result.get('note')}", ""]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT14_REPORT.md").write_text(text, encoding="utf-8")
    return text
