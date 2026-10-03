"""Expt-12 report. Mixed-stream recurrence frequency. Frozen Expt-11 mechanism."""

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
    selector = result.get("selector") or {}
    lines = [
        "# Expt-12 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Store boxes: {result.get('store_ids')}.",
        f"- Fresh boxes: {result.get('fresh_ids')}.",
        f"- Train families: {result.get('train_families')}. Test families: {result.get('test_families')}.",
        f"- Pools: exact {result.get('n_exact_pool')}, valid-transform {result.get('n_transform_pool')}, no-match {result.get('n_nomatch_pool')}, fresh {result.get('n_fresh_pool')}.",
        f"- Transform counts in valid-transform pool: {result.get('transform_coverage_in_pool')}.",
        f"- Frozen keys: {result.get('n_keys')}; overwrites {result.get('n_overwrites')}; bytes {result.get('storage_bytes')}.",
        f"- Selected: {selector.get('selected')}.",
        f"- Coverage (attempts / compatible / valid_replays / successes / fails): {selector.get('coverage')}.",
        "- Selection rule is the frozen Expt-11 rule (keep T iff train successes ≥ 1 and fails == 0). Expt-11 selected rot90/rot180. Expt-12 ran an additional T-first coverage pass on constructed train cases so each declared T could receive an eligible trial; rot270 then had compatible successes and was selected. That set was frozen before mixed-stream evaluation. The consult mechanism is unchanged; the selected transformation set changed.",
        "- Zero successes with zero compatible keys is insufficient coverage, not evidence the transform is useless.",
        "- A = primitive_evals + lookup + matching + transformation + validation + learning.",
        "- Task category is hidden from the agent. No-match checked against the full table under every permitted T.",
        "- Constructed useful-recurrence share is the designed slot mix (exact + valid-transform). Observed reuse is the fraction of evaluations that actually hit memory. Those are not the same number when a no-match later hits after further primitive steps.",
        "",
        "## Learned net saving by useful-recurrence rate",
        "",
    ]
    for rec in result.get("learned_by_rate") or []:
        lines.append(
            f"- p={rec.get('rate')}: n={rec.get('n')} ({rec.get('n_tasks')} task-ids × {rec.get('n_seeds')} seeds); "
            f"constructed-share {_fmt(rec.get('constructed_share') if rec.get('constructed_share') is not None else rec.get('realized_constructed_share'))}; "
            f"observed-reuse {_fmt(rec.get('observed_reuse_rate'))}; "
            f"mean A {_fmt(rec.get('mean_A'))}; mean effort-saving {_fmt(rec.get('mean_effort_saving'))}; "
            f"quality-loss {_fmt(rec.get('quality_loss_rate'))}; net-save-and-quality-ok {rec.get('net_save_quality_ok')}."
        )
    lines += [
        "",
        f"- Smallest predeclared mixture in this run at which learned netsaves and quality-loss ≤ 0.2: {_fmt(result.get('smallest_rate_learned_netsaves'))}. That is a paired result on these streams, not a general break-even threshold: each 5% stream had one useful slot, and different rates sample different boxes.",
        "",
        "## All agents by stream",
        "",
    ]
    for summary in result.get("summaries") or []:
        lines.append(
            f"- {summary.get('split')}/{summary.get('condition')}: n={summary.get('n')}; "
            f"mean A {_fmt(summary.get('mean_A'))}; mean Q {_fmt(summary.get('mean_Q'))}; "
            f"mean effort-saving {_fmt(summary.get('mean_effort_saving'))}; "
            f"quality-loss {_fmt(summary.get('quality_loss_rate'))} (n={summary.get('n_quality_loss')}); "
            f"hits exact {summary.get('n_exact_hits')} equiv {summary.get('n_equiv_hits')}; "
            f"mean lookup {_fmt(summary.get('mean_lookup'))}; matching {_fmt(summary.get('mean_matching'))}; "
            f"by hidden kind {summary.get('by_hidden_kind')}."
        )
    lines += ["", f"- {result.get('note')}", ""]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT12_REPORT.md").write_text(text, encoding="utf-8")
    return text
