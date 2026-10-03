"""Expt-13 report. Unforced reuse during ordinary search."""

from __future__ import annotations

import csv
from pathlib import Path

from config import PHILOSOPHY
from experiment import interpret


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("true", "1")


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _load_eval(run_dir: Path) -> list[dict]:
    path = run_dir / "eval.csv"
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r.get("split") != "store"]


def _decomposition(rows: list[dict]) -> list[str]:
    lines = [
        "## Decomposition by whether the inventory itself repeated a stored inventory",
        "",
        "An initial-state hit requires the whole inventory to repeat. It is exact whole-problem recall, not a reusable state reached through autonomous placements.",
        "",
    ]
    for workload in ("independent_fresh", "recurring_family"):
        for cond in ("exact", "learned"):
            for label, want in (("inventory repeats store", True), ("inventory new", False)):
                g = [
                    r for r in rows
                    if r.get("workload") == workload
                    and r.get("condition") == cond
                    and _truthy(r.get("inventory_repeats_store")) == want
                ]
                if not g:
                    continue
                n = len(g)
                saving = sum(_num(r.get("effort_saving")) for r in g) / n
                ql = sum(1 for r in g if _truthy(r.get("quality_loss")))
                qd = sum(_num(r.get("quality_delta")) for r in g) / n
                reuse = sum(1 for r in g if _truthy(r.get("valid_reuse")))
                inter = sum(int(_num(r.get("intermediate_hits"))) for r in g)
                init = sum(int(_num(r.get("initial_state_hits"))) for r in g)
                tasks = len({r.get("task_id") for r in g})
                lines.append(
                    f"- {workload} / {cond} / {label}: n={n} ({tasks} task-ids); mean effort-saving {saving:.4g}; "
                    f"mean quality delta {qd:.3g}; quality-loss {ql}/{n}; valid-reuse {reuse}/{n}; "
                    f"initial hits {init}; intermediate hits {inter}."
                )
    lines.append("")
    return lines


def _block_lines(title: str, block: dict) -> list[str]:
    n_init = int(block.get("n_initial_hits") or 0)
    n_inter = int(block.get("n_intermediate_hits") or 0)
    verdict = interpret(bool(block.get("net_save_quality_ok")), bool(block.get("reuse_present")), n_init, n_inter)
    lines = [
        f"## {title}",
        "",
        f"- Independent streams: {block.get('n_streams')}.",
        f"- Learned: across-stream mean effort-saving {_fmt(block.get('across_stream_mean_saving'))} "
        f"(min {_fmt(block.get('across_stream_min_saving'))}, max {_fmt(block.get('across_stream_max_saving'))}).",
        f"- Across-stream mean fraction of boxes with valid reuse: {_fmt(block.get('across_stream_mean_reuse_frac'))}.",
        f"- Across-stream mean quality-loss: {_fmt(block.get('across_stream_mean_quality_loss'))}.",
        f"- Initial-state hits: {n_init}. Intermediate hits after autonomous placements: {n_inter}.",
        f"- Net-save and quality ok: {block.get('net_save_quality_ok')}. Autonomous-intermediate success: {bool(block.get('net_save_quality_ok')) and n_inter > 0}.",
        f"- Verdict: {verdict}.",
        "",
    ]
    for summary in block.get("streams") or []:
        lines.append(
            f"- stream {summary.get('stream_id')} / {summary.get('condition')}: n={summary.get('n')} "
            f"({summary.get('n_tasks')} tasks × {summary.get('n_seeds')} paired seeds); "
            f"mean A {_fmt(summary.get('mean_A'))}; mean Q {_fmt(summary.get('mean_Q'))}; "
            f"mean effort-saving {_fmt(summary.get('mean_effort_saving'))}; "
            f"mean quality delta {_fmt(summary.get('mean_quality_delta'))}; "
            f"quality-loss {_fmt(summary.get('quality_loss_rate'))} (n={summary.get('n_quality_loss')}); "
            f"valid-reuse {summary.get('n_boxes_valid_reuse')}/{summary.get('n')}; "
            f"initial hits {summary.get('n_initial_hits')}; intermediate hits {summary.get('n_intermediate_hits')}; "
            f"mean primitive-evals before first hit {_fmt(summary.get('mean_primitive_before_first_hit'))}; "
            f"mean lookup {_fmt(summary.get('mean_lookup'))}; matching {_fmt(summary.get('mean_matching'))}; "
            f"constructed-prefix rows {summary.get('n_constructed_prefix')}."
        )
    lines.append("")
    return lines


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, result: dict) -> str:
    selector = result.get("selector") or {}
    coverage = result.get("coverage_pass") or {}
    lines = [
        "# Expt-13 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Independent store: {result.get('store_independent_ids')}.",
        f"- Family store: {result.get('family_store_ids')}.",
        f"- Family specs (declared before evaluation, no table consult): {result.get('family_specs')}.",
        f"- Frozen keys: {result.get('n_keys')} (empty-board {result.get('n_initial_keys')}); "
        f"overwrites {result.get('n_overwrites')}; bytes {result.get('storage_bytes')}.",
        f"- Table frozen before evaluation: {result.get('table_frozen_before_eval')}. "
        f"Selection frozen before evaluation: {result.get('selection_frozen_before_eval')}.",
        f"- Coverage pass (selection only, not evaluation): {coverage}.",
        f"- Selected: {selector.get('selected')}.",
        f"- Coverage (attempts / compatible / valid_replays / successes / fails): {selector.get('coverage')}.",
        "- Selection rule is the frozen Expt-11 rule. The T-first coverage pass is the same additional training used in Expt-12; it is not an evaluation workload. A transform with a recorded failure is excluded on evidence; one with zero compatible keys is excluded for insufficient coverage.",
        "- A = primitive_evals + lookup + matching + transformation + validation + learning.",
        "- Evaluation has no constructed prefixes, no scheduled matches, and no task-category input to the agent. Family inventories were not filtered against stored inventories.",
        "- Seeds are paired comparisons on identical starts, not independent learned memories.",
        "",
    ]
    lines += _block_lines("Independent fresh inventories", result.get("learned_fresh") or {})
    lines += _block_lines("Recurring task families with varying inventories", result.get("learned_family") or {})
    rows = _load_eval(run_dir)
    if rows:
        lines += _decomposition(rows)
    lines += [
        "## All agents by stream",
        "",
    ]
    for summary in result.get("summaries") or []:
        lines.append(
            f"- {summary.get('split')}/{summary.get('condition')}: n={summary.get('n')}; "
            f"mean A {_fmt(summary.get('mean_A'))}; mean Q {_fmt(summary.get('mean_Q'))}; "
            f"mean effort-saving {_fmt(summary.get('mean_effort_saving'))}; "
            f"quality-loss {_fmt(summary.get('quality_loss_rate'))} (n={summary.get('n_quality_loss')}); "
            f"valid-reuse {summary.get('n_boxes_valid_reuse')}/{summary.get('n')}; "
            f"initial {summary.get('n_initial_hits')} intermediate {summary.get('n_intermediate_hits')}; "
            f"mean lookup {_fmt(summary.get('mean_lookup'))}; matching {_fmt(summary.get('mean_matching'))}."
        )
    lines += ["", f"- {result.get('note')}", ""]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT13_REPORT.md").write_text(text, encoding="utf-8")
    return text
