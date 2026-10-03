"""Expt-15 report. Local subproblem memory."""

from __future__ import annotations

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


def _t1_lines(t1: dict) -> list[str]:
    lines = [
        "## Test 1: constructed independent regions with assigned budgets (experimental aid)",
        "",
        "The region and its piece budget are supplied. Decomposed agents fill the region first (local memory hit, else deterministic region search billed per candidate placement), then complete the box with the primitive policy. Local savings are paired against the primitive decomposed agent; whole-box references are reported alongside.",
        "",
        f"- Library regions: {len(t1.get('library') or [])}; control regions (geometry and budget not in the library): {len(t1.get('controls') or [])}; evaluation boxes: {t1.get('n_eval_tasks')}.",
        f"- Local entries {t1.get('local_entries')} in {t1.get('local_geometries')} geometries ({t1.get('local_bytes')} bytes). Exact whole-state keys {t1.get('exact_keys')}.",
        f"- Acquisition (region search evals per library region): {[a.get('search_evals') for a in t1.get('acquisition') or []]}.",
        "",
    ]
    for s in t1.get("summaries") or []:
        lines.append(
            f"- {s.get('kind')} / {s.get('condition')} (vs {s.get('reference') or 'none'}): n={s.get('n')} ({s.get('n_tasks')} boxes × seeds); "
            f"mean A {_fmt(s.get('mean_A'))}; mean Q {_fmt(s.get('mean_Q'))}; mean saving {_fmt(s.get('mean_effort_saving'))}; "
            f"saving vs primitive whole mean {_fmt(s.get('mean_saving_vs_primitive_whole'))} median {_fmt(s.get('median_saving_vs_primitive_whole'))} "
            f"(positive {_fmt(s.get('n_positive_vs_primitive_whole'))}, negative {_fmt(s.get('n_negative_vs_primitive_whole'))}, per seed {s.get('per_seed_saving_vs_primitive_whole')}, "
            f"quality-loss vs primitive whole {_fmt(s.get('n_quality_loss_vs_primitive_whole'))}); "
            f"region search {_fmt(s.get('mean_region_search_evals'))} (avoided {_fmt(s.get('mean_region_search_avoided'))}); "
            f"local hits {s.get('n_local_hits')}; exact hits {s.get('n_exact_hits')}; validation fails {s.get('n_validation_fails')}; "
            f"quality-loss {s.get('n_quality_loss')}; allocation failures {s.get('n_allocation_failure')}; "
            f"acceptable {_fmt(s.get('acceptable_rate'))}; region filled {_fmt(s.get('region_filled_rate'))}; "
            f"lookup {_fmt(s.get('mean_lookup'))}; validation {_fmt(s.get('mean_validation'))}; seconds {_fmt(s.get('mean_seconds'))}."
        )
    lines.append("")
    return lines


def _t2_lines(t2: dict) -> list[str]:
    acq = t2.get("acquisition") or {}
    lines = [
        "## Test 2: ordinary packing, naturally occurring regions, shared inventory",
        "",
        "Region detection is an engineered flood fill of free cells next to each new placement, bounded to the configured size range and billed per free cell visited. It is not learned decomposition. A local hit commits the first stored filling whose geometry is identical and whose multiset is available, with no gate; downstream consequences are measured against the same-start primitive.",
        "",
        f"- Store boxes: {len(t2.get('store_ids') or [])} × store seeds. Exact whole-state keys {t2.get('exact_keys')}.",
        f"- Local entries {t2.get('local_entries')} in {t2.get('local_geometries')} geometries; duplicates not stored {t2.get('local_duplicates')}; bytes {t2.get('local_bytes')}.",
        f"- Local memory growth over store solves: {t2.get('local_growth')}.",
        f"- Store acquisition: extraction {acq.get('extraction_cost')}, insertion {acq.get('insertion_cost')}, entries found {acq.get('n_found')}; amortised over {t2.get('n_eval_boxes')} evaluation boxes = {_fmt(t2.get('acquisition_per_eval_box'))} per box (not included in per-box A).",
    ]
    census = t2.get("store_region_census") or {}
    if census:
        n = census.get("n_regions", 0)
        frac = census.get("covered_cells", 0) / census["region_cells"] if census.get("region_cells") else None
        lines.append(
            f"- Store region census (acceptable primitive trajectories): {n} bounded regions appeared; {census.get('n_with_inside_piece')} later received at least one piece lying wholly inside; "
            f"cells covered by such pieces {_fmt(frac)} of region cells; filled exactly {census.get('n_exact')}. "
            f"Placements remaining when a region first appeared: {dict(sorted(census.get('placements_left_hist', {}).items(), key=lambda kv: int(kv[0])))}."
        )
    lines.append("")
    for workload in ("independent_fresh", "recurring_family"):
        block = (t2.get("summaries") or {}).get(workload) or {}
        lines += [f"### {TITLES[workload]}", ""]
        for cond in ("exact_whole", "local"):
            s = block.get(cond) or {}
            if not s:
                continue
            lines.append(
                f"- {cond}: n={s.get('n')} over {s.get('n_streams')} streams; cumulative saving per stream mean {_fmt(s.get('mean_cumulative_saving'))} "
                f"(min {_fmt(s.get('min_cumulative_saving'))}, max {_fmt(s.get('max_cumulative_saving'))}); per-box {_fmt(s.get('mean_per_box_saving'))}; "
                f"local hits {s.get('n_local_hits')} in {s.get('n_boxes_local')} boxes ({_fmt(s.get('frac_boxes_local'))}); "
                f"on unseen whole inventories {s.get('n_local_hits_unseen_inventory')} hits in {s.get('n_boxes_local_unseen_inventory')}/{s.get('n_unseen_inventory')} boxes; "
                f"exact hits {s.get('n_exact_hits')} (initial {s.get('n_exact_initial')}, intermediate {s.get('n_exact_intermediate')}); "
                f"regions detected per box {_fmt(s.get('mean_regions_detected'))}; detection {_fmt(s.get('mean_detection'))}; lookup {_fmt(s.get('mean_lookup'))}; "
                f"availability {_fmt(s.get('mean_availability'))}; validation {_fmt(s.get('mean_validation'))}; "
                f"primitive before first hit {_fmt(s.get('mean_primitive_before_first_hit'))}; mean hit size {_fmt(s.get('mean_hit_size'))}; "
                f"saving on hit boxes {_fmt(s.get('mean_saving_hit_boxes'))} vs no-hit boxes {_fmt(s.get('mean_saving_no_hit_boxes'))}; "
                f"quality delta on hit boxes {_fmt(s.get('mean_quality_delta_hit_boxes'))}; quality-loss {s.get('n_quality_loss')}; "
                f"acceptability lost {s.get('n_acceptability_lost')}; allocation failures {s.get('n_allocation_failure')}; "
                f"validation fails {s.get('n_validation_fails')}; seconds {_fmt(s.get('mean_seconds'))}."
            )
        prim = block.get("primitive") or {}
        if prim:
            lines.append(f"- primitive reference: mean A {_fmt(prim.get('mean_A'))}; mean Q {_fmt(prim.get('mean_Q'))}; seconds {_fmt(prim.get('mean_seconds'))}.")
        lines.append("")
    return lines


def _interpretation(result: dict) -> list[str]:
    t1 = result.get("test1") or {}
    t2 = result.get("test2") or {}
    m = next((s for s in t1.get("summaries") or [] if s["kind"] == "matched" and s["condition"] == "local_decomposed"), {})
    c = next((s for s in t1.get("summaries") or [] if s["kind"] == "control" and s["condition"] == "local_decomposed"), {})
    component = bool(m) and (m.get("n_local_hits") or 0) > 0 and (m.get("mean_effort_saving") or 0) > 0 and (m.get("n_allocation_failure") or 0) == 0
    natural_hits = sum(int((b.get("local") or {}).get("n_local_hits") or 0) for b in (t2.get("summaries") or {}).values())
    natural_saving = [(b.get("local") or {}).get("mean_cumulative_saving") for b in (t2.get("summaries") or {}).values()]
    census = t2.get("store_region_census") or {}
    lines = ["## Interpretation", ""]
    if component:
        lines.append(
            f"- Test 1 (constructed aid): stored fillings replaced region search on matched regions ({m.get('n_local_hits')} hits, saving {_fmt(m.get('mean_effort_saving'))} per box vs the primitive decomposed agent, "
            f"no validation or allocation failures); on control regions the overhead was {_fmt(-(c.get('mean_effort_saving') or 0))} per box. "
            "A reusable component is established when the region and its budget are supplied."
        )
        lines.append(
            f"- Against the whole-box primitive, local decomposed saved mean {_fmt(m.get('mean_saving_vs_primitive_whole'))} (median {_fmt(m.get('median_saving_vs_primitive_whole'))}; "
            f"per seed {m.get('per_seed_saving_vs_primitive_whole')}; quality-loss {m.get('n_quality_loss_vs_primitive_whole')}). Forced decomposition itself is not reliably cheaper than whole-box search, so the component does not by itself establish whole-box benefit."
        )
    else:
        lines.append("- Test 1 did not establish a reusable component under the supplied-region aid.")
    if natural_hits == 0:
        extra = ""
        if census and int(census.get("n_exact", 0)) == 0:
            extra = (f" The store census explains the empty memory: of {census.get('n_regions')} bounded regions in acceptable primitive trajectories, none was filled exactly; "
                     "bounded regions form late and absorb the unfilled cells, so extraction from ordinary trajectories supplied no entries.")
        lines.append(
            f"- Test 2 (natural regions): 0 local hits; cumulative saving per stream {[_fmt(v) for v in natural_saving]} is detection overhead only.{extra} "
            "Local entries helped only in Test 1: a reusable component exists, but when decomposition is safe, and where entries come from in ordinary packing, remain open."
        )
    else:
        lines.append(f"- Test 2 (natural regions): {natural_hits} local hits; see per-workload savings, quality, and allocation failures above.")
    lines.append("")
    return lines


def write_report(run_dir: Path, config: dict, meta: dict, audit: dict, result: dict) -> str:
    lines = [
        "# Expt-15 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Region size range: {config.get('region_min_cells')}–{config.get('region_max_cells')} cells. Match rule: {config.get('local_match_rule')}.",
        f"- A = {config.get('A_identity')}.",
        "- No transformations, no hierarchy, no learned gate. Memories frozen before evaluation.",
        "- Allocation failure: a box where local memory committed at least one filling and final quality fell more than 1.0 below the same-start reference, or acceptability was lost.",
        "",
    ]
    lines += _t1_lines(result.get("test1") or {})
    lines += _t2_lines(result.get("test2") or {})
    lines += _interpretation(result)
    lines += [f"- {result.get('note')}", ""]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT15_REPORT.md").write_text(text, encoding="utf-8")
    return text
