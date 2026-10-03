"""Expt-11 report. Remaining-state equivalence. Declared isometries, not invented transforms."""

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
        f"quality-loss {_fmt(summary.get('quality_loss_rate'))} (n={summary.get('n_quality_loss')}); "
        f"acceptable {_fmt(summary.get('acceptable_rate'))}; "
        f"hits {summary.get('n_hits')} (exact {summary.get('n_exact_hits')}, equiv {summary.get('n_equiv_hits')}) "
        f"/ {summary.get('n_lookups')} lookups; "
        f"replays {summary.get('n_replays')}; validation fails {summary.get('n_validation_fails')}; "
        f"initial-state hits {summary.get('n_initial_state_hits')}; "
        f"mean lookup {_fmt(summary.get('mean_lookup'))}; matching {_fmt(summary.get('mean_matching'))}; "
        f"transformation {_fmt(summary.get('mean_transformation'))}; validation {_fmt(summary.get('mean_validation'))}; "
        f"mean primitive {_fmt(summary.get('mean_primitive_evals'))}; "
        f"natural-opportunity rate {_fmt(summary.get('natural_opportunity_rate'))}."
    )


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, result: dict) -> str:
    selector = result.get("selector") or {}
    lines = [
        "# Expt-11 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Store boxes ({len(result.get('store_ids') or [])}): {result.get('store_ids')}.",
        f"- Fresh boxes ({len(result.get('fresh_ids') or [])}): {result.get('fresh_ids')}.",
        f"- Train families: {result.get('train_families')}. Test families: {result.get('test_families')}.",
        f"- Constructed equivalence tasks: train {result.get('n_equiv_train')}, test {result.get('n_equiv_test')}.",
        f"- Continuation keys: {result.get('n_keys')} ({result.get('n_initial_keys')} empty-board); overwrites {result.get('n_overwrites')}; bytes {result.get('storage_bytes')}.",
        f"- Declared candidates: {selector.get('candidates')}.",
        f"- Train transform successes: {selector.get('success')}. Failures: {selector.get('fail')}.",
        f"- Selected from experience: {selector.get('selected')}. Rule: {selector.get('rule')}.",
        "- A = primitive_evals + lookup + matching + transformation + validation + learning.",
        "- Engineered (supplied) and learned selection are reported separately. Learning does not invent transforms.",
        "- Symmetric remaining states are excluded. Family transforms stay in the donor partition.",
        "- Foils must reject reuse. Natural opportunity on fresh traces is not pooled with constructed equivalence.",
        "",
        "## Cases",
        "",
    ]
    for item in result.get("equiv_meta") or []:
        lines.append(
            f"- {item.get('task_id')} donor {item.get('donor_task_id')} {item.get('partition')} "
            f"T={item.get('transform')} cut {item.get('cut')} kind {item.get('kind')}."
        )
    lines += ["", "## Conditions", ""]
    for summary in result.get("summaries") or []:
        lines.append(_summary_line(summary))
    lines += [
        "",
        f"- Exact matching evades transformed test remaining states: {result.get('exact_evades_transformed_test')}.",
        f"- Supplied rules save effort on unseen families: {result.get('supplied_saves_on_test')}.",
        f"- Learned selection useful on unseen families (saving > 0, quality-loss ≤ 0.2, equiv hits, no empty-board hits): {result.get('learned_useful_on_unseen_families')}.",
        f"- Foil supplied equivalence hits: {result.get('foil_supplied_equiv_hits')}. Inventory foils rejected reuse. Geometry near-miss foils can still match a different stored intermediate (declared; not pooled with constructed-equivalence success).",
        f"- Natural opportunity rate on fresh primitive traces: {_fmt(result.get('natural_opportunity_rate_fresh'))}.",
        f"- {result.get('note')}",
        "",
        "## Distinctions",
        "",
        "- Test families are unseen for the transformation-selection rule. Their donor continuations are stored; retrieval is from memory. What transfers is the selected isometry set, not a new solution.",
        "- The 33 test rows are 11 constructed tasks drawn from four families, each evaluated at three seeds (11 × 3). They are not 11 × 4 × 3 tasks, and they are not 33 independent tests of learning a transformation rule.",
        "- Zero training successes is not evidence a transform is useless unless it had enough eligible (compatible-key) trials. rot270 preserves geometry when orientations allow it; its absence from the selected set may be training coverage, not a geometric failure.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT11_REPORT.md").write_text(text, encoding="utf-8")
    return text
