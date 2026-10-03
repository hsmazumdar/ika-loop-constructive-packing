"""Expt-16 report. Search-acquired local memory."""

from __future__ import annotations

from pathlib import Path

from config import PHILOSOPHY

TITLES = {"independent_fresh": "Independent fresh inventories", "recurring_family": "Recurring task families"}


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _acq_lines(config: dict, s: dict) -> list[str]:
    st = s.get("status") or {}
    c = s.get("costs") or {}
    return [
        "## Acquisition (offline search at recorded region snapshots; store trajectories unchanged)",
        "",
        f"- Store trajectories {s.get('n_trajectories')} (excluded as not acceptable: {s.get('n_excluded_unacceptable')}); bounded region snapshots {s.get('n_snapshots')}.",
        f"- Search budget per region: {config.get('search_budget')} candidate placements examined (predeclared).",
        f"- Outcomes: exact filling found {st.get('found', 0)}; proven impossible {st.get('impossible', 0)}; budget exhausted, feasibility unknown {st.get('budget_exhausted', 0)}. Fill rate {_fmt(s.get('fill_rate'))}.",
        f"- Of the proven-impossible regions, {s.get('n_impossible_by_area')} were ruled out at the root by area alone (region size not a sum of available piece sizes, 4/5/7 cells); the rest by exhaustive shape search.",
        f"- Fillings validated on the rebuilt board: {s.get('n_valid')}. Fillings using only pieces the store trajectory left unused at the end: {s.get('n_uses_only_end_unused')}.",
        f"- By region size: {s.get('by_size')}.",
        f"- By placements remaining when the region appeared: {s.get('by_placements_left')}.",
        f"- Search evals when found: {s.get('search_evals_found')}; when proven impossible: {s.get('search_evals_impossible')}.",
        f"- Acquisition costs (separate): detection {c.get('detection')}, search {c.get('search')}, validation {c.get('validation')}, insertion {c.get('insertion')}.",
        f"- Table: {s.get('n_entries')} entries in {s.get('n_geometries')} geometries; insertion outcomes {s.get('insertion_outcomes')}; entries with alternative placements {s.get('n_entries_with_alternatives')}; geometries with more than one multiset {s.get('geometries_with_multiple_multisets')}.",
        "",
    ]


def _app_lines(app: dict | None, stopped: str | None) -> list[str]:
    lines = ["## Applicability (read-only matching on fresh ordinary trajectories)", ""]
    if not app:
        lines += [f"- Not run: {stopped}.", ""]
        return lines
    lines.append("The detector is the unchanged Expt-15 flood fill, billed per free cell visited. Its overhead is reported explicitly and has not been optimised.")
    lines.append("")
    for w, v in app.items():
        lines.append(
            f"- {TITLES[w]}: {v['n_boxes']} boxes ({v['n_inventory_in_store']} repeat a store inventory); regions per box {_fmt(v['regions_per_box'])}; "
            f"detector {_fmt(v['detection_per_box'])} per box, lookup {_fmt(v['lookup_per_box'])}, availability {_fmt(v['availability_per_box'])} "
            f"(total detector/lookup {v['detector_lookup_total']}; primitive A per box {_fmt(v['primitive_A_per_box'])}); "
            f"geometry matches {v['geometry_matches']} in {v['boxes_with_geometry_match']} boxes; inventory-compatible matches {v['compatible_matches']} in "
            f"{v['boxes_with_compatible_match']} boxes ({v['boxes_with_compatible_match_new_inventory']} on new whole inventories)."
        )
    if stopped:
        lines.append(f"- {stopped}.")
    lines.append("")
    return lines


def _cf_line(name: str, s: dict) -> str:
    if not s or not s.get("n"):
        return f"- {name}: none."
    return (
        f"- {name}: n={s['n']} in {s['n_boxes']} boxes; valid {s['n_valid']}; remaining-effort saving mean {_fmt(s['mean_effort_saving'])} "
        f"median {_fmt(s['median_effort_saving'])} (positive {s['n_positive']}, negative {s['n_negative']}); quality delta mean {_fmt(s['mean_quality_delta'])}; "
        f"quality-loss {s['n_quality_loss']} ({_fmt(s['quality_loss_rate'])}), gain {s['n_quality_gain']}; acceptability lost {s['n_acceptability_lost']}; "
        f"mean region size {_fmt(s['mean_region_size'])}."
    )


def _cf_lines(cf: dict | None) -> list[str]:
    lines = ["## Downstream consequences at compatible matches (diagnostic counterfactuals)", ""]
    if not cf:
        lines += ["- Not run.", ""]
        return lines
    lines += [
        "Both branches start from the same saved state (board, inventory, RNG state, tabu) with remaining cap eval_cap − prefix A. Commit branch: validate and place the stored filling, then primitive. Primitive branch: primitive only. These are diagnostic work, not information available to an agent.",
        "",
        f"- Primitive branch reproduced the original trajectory at {cf.get('primitive_branch_reproduces')} of {cf.get('primitive_branch_checked')} matches.",
        _cf_line("First compatible match per box, first stored entry (primary)", cf.get("first_match_first_entry")),
        _cf_line("All matches, first entry", cf.get("all_first_entries")),
        _cf_line("All matches, all diagnosed entries", cf.get("all")),
    ]
    for w, s in (cf.get("by_workload_first") or {}).items():
        lines.append(_cf_line(f"Primary, {TITLES[w]}", s))
    lines.append("")
    return lines


def write_report(run_dir: Path, config: dict, meta: dict, result: dict) -> str:
    d = result.get("decision") or {}
    lines = [
        "# Expt-16 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`; problem sets from frozen manifests (hash-checked).",
        f"- Region size range {config.get('region_min_cells')}–{config.get('region_max_cells')} cells; entry key {config.get('entry_key')}.",
        "- No transformations, hierarchy, learned gate, or partial fillings.",
        "",
    ]
    lines += _acq_lines(config, result.get("acquisition") or {})
    lines += _app_lines(result.get("applicability"), result.get("stopped"))
    lines += _cf_lines(result.get("counterfactuals"))
    lines += [
        "## Decision",
        "",
        f"- Primary row: **{d.get('row')}**. {d.get('implication')}",
        f"- All rows whose predeclared condition holds: {'; '.join(f'{r} ({t})' for r, t in (d.get('implications') or {}).items())}",
        (f"- Counterfactuals were computed because compatible matches existed, but they fall below the recurrence threshold and are descriptive only." if d.get("counterfactuals_below_recurrence_threshold") else ""),
        f"- Few-fillings flag (fill rate < {config.get('few_fill_rate')} or no entries): {d.get('few_fillings')}. Fresh boxes with a compatible match: {d.get('boxes_with_compatible_match')} (recurrence threshold {config.get('min_recur_boxes')}).",
        f"- {result.get('deployment')}.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT16_REPORT.md").write_text(text, encoding="utf-8")
    return text
