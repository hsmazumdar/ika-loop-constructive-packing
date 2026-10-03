"""Expt-6 report from saved rows. Do not type numbers by hand."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import COST_CURVE, EXPT5_LEARNING_A, PHILOSOPHY, QUALITY_LOSS_MARGIN


def _mean(values):
    return None if not values else sum(values) / len(values)


def _sd(values):
    return None if len(values) < 2 else statistics.stdev(values)


def _quantile(values, q: float):
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _truthy(value) -> bool:
    return str(value).lower() in ("true", "1", "yes")


def _optional_bool(value):
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    return None


def _float(row, key, default=0.0) -> float:
    try:
        return float(row.get(key) if row.get(key) not in (None, "") else default)
    except (TypeError, ValueError):
        return float(default)


def cost_curve(box_rows: list[dict], costs=COST_CURVE) -> list[dict]:
    points = []
    for cost in costs:
        savings = [_float(r, "saving_oracle_free") - float(cost) for r in box_rows]
        exceed = [1.0 if _float(r, "saving_oracle_free") > float(cost) else 0.0 for r in box_rows]
        points.append(
            {
                "C": int(cost),
                "mean_saving": _mean(savings),
                "fraction_boxes_saving_gt_C": _mean(exceed),
                "n": len(box_rows),
            }
        )
    return points


def coverage(state_rows: list[dict], box_rows: list[dict], cand_rows: list[dict]) -> dict:
    n_states = len(state_rows)
    n_compat = sum(1 for r in state_rows if int(float(r.get("n_inventory_compatible") or 0)) > 0)
    n_legal = sum(1 for r in state_rows if int(float(r.get("n_ops_with_legal_placement") or 0)) > 0)
    n_ben_states = sum(1 for r in state_rows if int(float(r.get("n_beneficial_free") or 0)) > 0)
    legal_states = [r for r in state_rows if int(float(r.get("n_ops_with_legal_placement") or 0)) > 0]
    n_ben_legal = sum(1 for r in legal_states if int(float(r.get("n_beneficial_free") or 0)) > 0)
    opp = [_optional_bool(r.get("has_opportunity")) for r in box_rows]
    n_true = sum(1 for v in opp if v is True)
    n_false = sum(1 for v in opp if v is False)
    n_unknown = sum(1 for v in opp if v is None)
    complete = [r for r in box_rows if _truthy(r.get("oracle_complete"))]
    composed_cand = [r for r in cand_rows if _truthy(r.get("composed"))]
    flat_cand = [r for r in cand_rows if not _truthy(r.get("composed"))]
    ops = {(r.get("seed"), r.get("op_id"), r.get("definition_hash")) for r in cand_rows if _truthy(r.get("beneficial_free"))}
    depths = sorted({int(float(r.get("depth") or 0)) for r in cand_rows if _truthy(r.get("beneficial_free"))})
    return {
        "n_states": n_states,
        "frac_states_inventory_compatible": None if not n_states else n_compat / n_states,
        "frac_states_legal_placement": None if not n_states else n_legal / n_states,
        "frac_states_beneficial": None if not n_states else n_ben_states / n_states,
        "frac_legal_states_beneficial": None if not legal_states else n_ben_legal / len(legal_states),
        "n_boxes": len(box_rows),
        "n_boxes_with_opportunity": n_true,
        "n_boxes_complete_no_opportunity": n_false,
        "n_boxes_incomplete_unknown": n_unknown,
        "frac_boxes_with_opportunity_lower_bound": None if not box_rows else n_true / len(box_rows),
        "frac_complete_boxes_with_opportunity": None if not complete else sum(1 for r in complete if _optional_bool(r.get("has_opportunity")) is True) / len(complete),
        "n_complete_pairs": len(complete),
        "n_distinct_beneficial_ops": len(ops),
        "beneficial_depths": depths,
        "n_flat_candidates": len(flat_cand),
        "n_composed_candidates": len(composed_cand),
        "n_composed_beneficial": sum(1 for r in composed_cand if _truthy(r.get("beneficial_free"))),
        "n_active_composed_ops": sum(int(float(r.get("n_composed_active") or 0)) for r in box_rows),
    }


def candidate_stats(cand_rows: list[dict]) -> dict:
    savings = [_float(r, "remaining_saving") for r in cand_rows]
    qdiff = [_float(r, "quality_difference") for r in cand_rows]
    return {
        "n": len(cand_rows),
        "remaining_saving_mean": _mean(savings),
        "remaining_saving_median": _quantile(savings, 0.5),
        "remaining_saving_min": min(savings) if savings else None,
        "remaining_saving_max": max(savings) if savings else None,
        "remaining_saving_p10": _quantile(savings, 0.1),
        "remaining_saving_p90": _quantile(savings, 0.9),
        "quality_difference_mean": _mean(qdiff),
        "quality_difference_median": _quantile(qdiff, 0.5),
        "quality_difference_min": min(qdiff) if qdiff else None,
        "quality_difference_max": max(qdiff) if qdiff else None,
        "n_quality_ok": sum(1 for r in cand_rows if _truthy(r.get("quality_ok"))),
        "n_beneficial_free": sum(1 for r in cand_rows if _truthy(r.get("beneficial_free"))),
        "n_gate_would_select_beneficial": sum(
            1 for r in cand_rows if _truthy(r.get("beneficial_free")) and _truthy(r.get("gate_would_select"))
        ),
        "n_gate_would_miss_beneficial": sum(
            1 for r in cand_rows if _truthy(r.get("beneficial_free")) and not _truthy(r.get("gate_would_select"))
        ),
    }


def gate_miss_levels(cand_rows: list[dict]) -> dict:
    """Candidate counts overcount placements. Also report states and boxes."""
    beneficial = [r for r in cand_rows if _truthy(r.get("beneficial_free"))]
    by_state: dict[tuple, list[dict]] = {}
    by_box: dict[tuple, list[dict]] = {}
    by_op: dict[tuple, list[dict]] = {}
    for row in beneficial:
        sk = (str(row.get("seed")), str(row.get("task_id")), str(row.get("state_index")))
        bk = (str(row.get("seed")), str(row.get("task_id")))
        ok = sk + (str(row.get("op_id")), str(row.get("definition_hash")))
        by_state.setdefault(sk, []).append(row)
        by_box.setdefault(bk, []).append(row)
        by_op.setdefault(ok, []).append(row)

    def any_select(items: list[dict]) -> bool:
        return any(_truthy(r.get("gate_would_select")) for r in items)

    n_states = len(by_state)
    n_states_all = sum(1 for items in by_state.values() if not any_select(items))
    n_boxes = len(by_box)
    n_boxes_all = sum(1 for items in by_box.values() if not any_select(items))
    n_consult_closed = 0
    n_commit_all = 0
    for items in by_state.values():
        consult = any(_truthy(r.get("consult_gate_would_admit")) for r in items)
        commit_any = any(_truthy(r.get("commit_gate_would_admit")) for r in items)
        if not consult:
            n_consult_closed += 1
        elif not commit_any:
            n_commit_all += 1
    n_ops = len(by_op)
    n_ops_all = sum(1 for items in by_op.values() if not any_select(items))
    return {
        "n_states_with_beneficial": n_states,
        "n_states_any_beneficial_admitted": n_states - n_states_all,
        "n_states_every_beneficial_rejected": n_states_all,
        "frac_states_every_beneficial_rejected": None if not n_states else n_states_all / n_states,
        "n_states_consult_would_not_look": n_consult_closed,
        "n_states_consult_open_but_commit_rejects_all": n_commit_all,
        "n_boxes_with_beneficial": n_boxes,
        "n_boxes_any_beneficial_admitted": n_boxes - n_boxes_all,
        "n_boxes_every_beneficial_rejected": n_boxes_all,
        "frac_boxes_every_beneficial_rejected": None if not n_boxes else n_boxes_all / n_boxes,
        "n_state_op_with_beneficial": n_ops,
        "n_state_op_every_placement_rejected": n_ops_all,
    }


def per_seed(box_rows: list[dict]) -> list[dict]:
    seeds = sorted({int(float(r["seed"])) for r in box_rows})
    out = []
    for seed in seeds:
        subset = [r for r in box_rows if int(float(r["seed"])) == seed]
        out.append(
            {
                "seed": seed,
                "n": len(subset),
                "mean_A_primitive": _mean([_float(r, "A_primitive") for r in subset]),
                "mean_A_both_gates": _mean([_float(r, "A_both_gates") for r in subset]),
                "mean_A_oracle_free": _mean([_float(r, "A_oracle_free") for r in subset]),
                "mean_A_oracle_scan": _mean([_float(r, "A_oracle_scan") for r in subset]),
                "mean_saving_free": _mean([_float(r, "saving_oracle_free") for r in subset]),
                "mean_saving_scan": _mean([_float(r, "saving_oracle_scan") for r in subset]),
                "mean_Q_primitive": _mean([_float(r, "Q_primitive") for r in subset]),
                "mean_Q_both": _mean([_float(r, "Q_both_gates") for r in subset]),
                "mean_Q_oracle_free": _mean([_float(r, "Q_oracle_free") for r in subset]),
                "n_opportunity": sum(1 for r in subset if _optional_bool(r.get("has_opportunity")) is True),
                "n_incomplete": sum(1 for r in subset if not _truthy(r.get("oracle_complete"))),
                "library_hash": subset[0].get("library_hash") if subset else None,
            }
        )
    return out


def write_plots(run_dir: Path, box_rows: list[dict], state_rows: list[dict], cand_rows: list[dict]) -> None:
    fig_dir = run_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    labels = ["primitive", "both_gates", "oracle_free", "oracle_scan"]
    means = [
        _mean([_float(r, "A_primitive") for r in box_rows]) or 0,
        _mean([_float(r, "A_both_gates") for r in box_rows]) or 0,
        _mean([_float(r, "A_oracle_free") for r in box_rows]) or 0,
        _mean([_float(r, "A_oracle_scan") for r in box_rows]) or 0,
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.bar(range(len(labels)), means)
    ax.set_xticks(range(len(labels)), labels, rotation=15, ha="right")
    ax.set_ylabel("mean A")
    ax.set_title("Expt-6 paired effort (quality-qualified oracle)")
    fig.tight_layout()
    fig.savefig(fig_dir / "plot_paired_A.png", dpi=120)
    plt.close(fig)

    bands = sorted({int(float(r.get("occupancy_target") or 0)) for r in state_rows})
    rates = []
    for band in bands:
        subset = [r for r in state_rows if int(float(r.get("occupancy_target") or 0)) == band]
        rates.append(0 if not subset else sum(1 for r in subset if int(float(r.get("n_beneficial_free") or 0)) > 0) / len(subset))
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.bar([str(b) for b in bands], rates)
    ax.set_xlabel("occupancy schedule threshold")
    ax.set_ylabel("fraction of sampled states with beneficial_free")
    ax.set_title("Opportunity rate by occupancy coverage band")
    fig.tight_layout()
    fig.savefig(fig_dir / "plot_opportunity_by_occupancy.png", dpi=120)
    plt.close(fig)

    savings = [_float(r, "remaining_saving") for r in cand_rows]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    if savings:
        ax.hist(savings, bins=min(40, max(8, int(len(savings) ** 0.5))))
    ax.set_xlabel("remaining_saving (skip A − commit A)")
    ax.set_ylabel("candidates")
    ax.set_title("Candidate remaining-saving distribution (harmful tail visible)")
    fig.tight_layout()
    fig.savefig(fig_dir / "plot_candidate_savings.png", dpi=120)
    plt.close(fig)

    curve = cost_curve(box_rows)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot([p["C"] for p in curve], [p["mean_saving"] or 0 for p in curve], marker="o")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("hypothetical per-box access cost C")
    ax.set_ylabel("mean (saving_oracle_free − C)")
    ax.set_title("Optimistic savings vs hypothetical access cost")
    fig.tight_layout()
    fig.savefig(fig_dir / "plot_cost_sensitivity.png", dpi=120)
    plt.close(fig)


def write_report(
    run_dir: Path,
    config: dict,
    meta: dict,
    box_rows: list[dict],
    state_rows: list[dict],
    cand_rows: list[dict],
    ledger: dict,
    audit: dict,
) -> str:
    cov = coverage(state_rows, box_rows, cand_rows)
    stats = candidate_stats(cand_rows)
    miss = gate_miss_levels(cand_rows)
    seeds = per_seed(box_rows)
    curve = cost_curve(box_rows)
    margin = float(config.get("quality_loss_margin", QUALITY_LOSS_MARGIN))
    n_ql_both = sum(1 for r in box_rows if _float(r, "Q_both_gates") < _float(r, "Q_primitive") - margin)
    n_ql_free = sum(1 for r in box_rows if _float(r, "Q_oracle_free") < _float(r, "Q_primitive") - margin)
    n_cap_p = sum(1 for r in box_rows if _truthy(r.get("cap_hit_primitive")))
    n_cap_f = sum(1 for r in box_rows if _truthy(r.get("cap_hit_frozen")))
    n_incomplete = sum(1 for r in box_rows if not _truthy(r.get("oracle_complete")))
    n_skip_fail = sum(1 for r in box_rows if not _truthy(r.get("skip_identity_ok")))
    n_a_fail = sum(1 for r in box_rows if str(r.get("A_identity_ok_both")).lower() in ("false", "0"))
    sampled = any(str(r.get("oracle_kind")) == "sampled_candidate_oracle" for r in box_rows)
    mean_free = _mean([_float(r, "saving_oracle_free") for r in box_rows])
    mean_scan = _mean([_float(r, "saving_oracle_scan") for r in box_rows])
    mean_c = _mean([_float(r, "C_box") for r in box_rows])
    frac_opp = cov["frac_complete_boxes_with_opportunity"]
    lines = [
        "# Expt-6 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Python: {meta.get('python')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Git: `{meta.get('git')}`",
        f"- Reconstruction: {audit.get('reconstruction_required')} — {audit.get('reconstruction_note')}",
        f"- Historical Expt-5 learning cost (reference, not billed here): {EXPT5_LEARNING_A}",
        f"- Oracle kind: {'sampled_candidate_oracle' if sampled else 'exhaustive'}",
        "- Effort saving = A_primitive − A_condition (positive = fewer evaluations).",
        "- Quality-loss rate is separate from mean Q. Margin = 1 occupied cell.",
        "- The oracle uses information about future outcomes and is not a deployable agent.",
        "",
        "## Frozen sources",
        "",
        f"- Expt-5 result: `{audit.get('expt5_result')}`",
        f"- Missing Expt-5 library files: {audit.get('missing_library_files')}",
        f"- Occupancy schedule (coverage, not a learned context rule): {config.get('occupancy_schedule')}",
        f"- Remaining-solve budget: {config.get('remaining_budget')}",
        "",
        "## Per-seed means",
        "",
    ]
    for row in seeds:
        lines.append(
            f"- seed {row['seed']}: n={row['n']}; library `{row['library_hash']}`; "
            f"mean A primitive {_fmt(row['mean_A_primitive'])}, both_gates {_fmt(row['mean_A_both_gates'])}, "
            f"oracle_free {_fmt(row['mean_A_oracle_free'])}, oracle_scan {_fmt(row['mean_A_oracle_scan'])}; "
            f"mean saving free {_fmt(row['mean_saving_free'])}, scan {_fmt(row['mean_saving_scan'])}; "
            f"mean Q primitive {_fmt(row['mean_Q_primitive'])}, both {_fmt(row['mean_Q_both'])}, "
            f"oracle_free {_fmt(row['mean_Q_oracle_free'])}; boxes with opportunity {row['n_opportunity']}; "
            f"incomplete {row['n_incomplete']}"
        )
    lines += [
        "",
        "## Comparison table (all library–box pairs)",
        "",
        f"- n pairs: {len(box_rows)} (same boxes crossed with {len(seeds)} reconstructed libraries)",
        f"- primitive: mean Q {_fmt(_mean([_float(r, 'Q_primitive') for r in box_rows]))}; "
        f"mean A {_fmt(_mean([_float(r, 'A_primitive') for r in box_rows]))}; "
        f"Q>=75 rate {_fmt(_mean([1.0 if _truthy(r.get('Q_ge_75_primitive')) else 0.0 for r in box_rows]))}; "
        f"cap hits {n_cap_p}",
        f"- both_gates_frozen: mean Q {_fmt(_mean([_float(r, 'Q_both_gates') for r in box_rows]))}; "
        f"mean A {_fmt(_mean([_float(r, 'A_both_gates') for r in box_rows]))}; "
        f"mean effort saving {_fmt(_mean([_float(r, 'A_primitive') - _float(r, 'A_both_gates') for r in box_rows]))}; "
        f"quality-loss rate {_fmt(100.0 * n_ql_both / len(box_rows) if box_rows else None)}% of pairs; "
        f"Q>=75 rate {_fmt(_mean([1.0 if _truthy(r.get('Q_ge_75_both')) else 0.0 for r in box_rows]))}; "
        f"cap hits {n_cap_f}; mean gate {_fmt(_mean([_float(r, 'gate_cost_both') for r in box_rows]))}; "
        f"mean consultation {_fmt(_mean([_float(r, 'consultation_both') for r in box_rows]))}",
        f"- oracle_single_free: mean Q {_fmt(_mean([_float(r, 'Q_oracle_free') for r in box_rows]))}; "
        f"mean A {_fmt(_mean([_float(r, 'A_oracle_free') for r in box_rows]))}; "
        f"mean quality-qualified saving {_fmt(mean_free)}; "
        f"quality-loss rate {_fmt(100.0 * n_ql_free / len(box_rows) if box_rows else None)}% of pairs "
        f"(nonzero would violate the oracle construction)",
        f"- oracle_single_scan_charged: mean A {_fmt(_mean([_float(r, 'A_oracle_scan') for r in box_rows]))}; "
        f"mean saving {_fmt(mean_scan)}; mean C_box {_fmt(mean_c)}",
        f"- skip-identity failures: {n_skip_fail}; both-gates A-identity failures: {n_a_fail}; incomplete pairs: {n_incomplete}",
        "",
        "## Coverage and content",
        "",
        f"- Fraction of sampled states with any inventory-compatible operation: {_fmt(cov['frac_states_inventory_compatible'])}",
        f"- Fraction with any legal placement: {_fmt(cov['frac_states_legal_placement'])}",
        f"- Fraction of states with a quality-qualified beneficial action: {_fmt(cov['frac_states_beneficial'])}",
        f"- Fraction of legal states with a beneficial action: {_fmt(cov['frac_legal_states_beneficial'])}",
        f"- Boxes with at least one remaining-level opportunity: {cov['n_boxes_with_opportunity']} / {cov['n_boxes']} "
        f"(lower bound {_fmt(cov['frac_boxes_with_opportunity_lower_bound'])}); "
        f"complete pairs with opportunity: {_fmt(cov['frac_complete_boxes_with_opportunity'])}; "
        f"incomplete unknown: {cov['n_boxes_incomplete_unknown']}; complete with none: {cov['n_boxes_complete_no_opportunity']}",
        f"- Distinct operations responsible for opportunities: {cov['n_distinct_beneficial_ops']}; depths {cov['beneficial_depths']}",
        f"- Flat candidates {cov['n_flat_candidates']}; composed candidates {cov['n_composed_candidates']}; "
        f"composed beneficial {cov['n_composed_beneficial']}. Zero composed evidence means hierarchy is untested here.",
        "",
        "## Candidate remaining-saving distribution",
        "",
        f"- n={stats['n']}; mean {_fmt(stats['remaining_saving_mean'])}; median {_fmt(stats['remaining_saving_median'])}; "
        f"min {_fmt(stats['remaining_saving_min'])}; max {_fmt(stats['remaining_saving_max'])}; "
        f"p10 {_fmt(stats['remaining_saving_p10'])}; p90 {_fmt(stats['remaining_saving_p90'])}",
        f"- quality difference mean {_fmt(stats['quality_difference_mean'])}; min {_fmt(stats['quality_difference_min'])}; "
        f"max {_fmt(stats['quality_difference_max'])}",
        f"- quality_ok {stats['n_quality_ok']}; beneficial_free {stats['n_beneficial_free']}",
        "",
        "## Selection and access (read-only gate probes, diagnostic ledger only)",
        "",
        f"- Beneficial candidates the frozen gates would admit: {stats['n_gate_would_select_beneficial']}",
        f"- Beneficial candidates the frozen gates would miss: {stats['n_gate_would_miss_beneficial']}",
        f"- Candidate miss rate overcounts alternative placements of the same operation. "
        f"States with any beneficial action: {miss['n_states_with_beneficial']}; "
        f"every beneficial option rejected: {miss['n_states_every_beneficial_rejected']} "
        f"({_fmt(None if not miss['n_states_with_beneficial'] else 100.0 * miss['frac_states_every_beneficial_rejected'])}% of those states). "
        f"Consult would not look: {miss['n_states_consult_would_not_look']}; consult open but commit rejects every beneficial op: {miss['n_states_consult_open_but_commit_rejects_all']}.",
        f"- Library–box pairs with opportunity: {miss['n_boxes_with_beneficial']}; "
        f"every beneficial option rejected: {miss['n_boxes_every_beneficial_rejected']} "
        f"({_fmt(None if not miss['n_boxes_with_beneficial'] else 100.0 * miss['frac_boxes_every_beneficial_rejected'])}% of those pairs); "
        f"at least one beneficial option admitted: {miss['n_boxes_any_beneficial_admitted']}.",
        f"- Distinct state–operation pairs with a beneficial placement: {miss['n_state_op_with_beneficial']}; "
        f"every placement of that operation rejected: {miss['n_state_op_every_placement_rejected']}.",
        "- Probe decisions are not the actual both_gates trajectory.",
        "",
        "## Cost-sensitivity (charge C to every box)",
        "",
    ]
    for point in curve:
        lines.append(
            f"- C={point['C']}: mean saving {_fmt(point['mean_saving'])}; "
            f"fraction of boxes with free-oracle saving > C: {_fmt(point['fraction_boxes_saving_gt_C'])}"
        )
    lines += [
        "",
        "## Ledgers",
        "",
        f"- Diagnostic skip rollouts {ledger.get('skip_rollouts')}; skip A {ledger.get('skip_A')}",
        f"- Diagnostic commit rollouts {ledger.get('commit_rollouts')}; commit A {ledger.get('commit_A')}",
        f"- C_box sum {ledger.get('C_box_sum')}; gate probes {ledger.get('gate_probes')}; cache hits {ledger.get('cache_hits')}",
        f"- Historical Expt-5 learning_A {ledger.get('historical_expt5_learning_A')} ({ledger.get('historical_expt5_learning_scope')})",
        "- Counterfactual rollouts are privileged diagnostic computation, not deployment effort and not part of C_box.",
        "",
        "## Answers",
        "",
        f"- Fraction of boxes containing useful remaining-level opportunity: {cov['n_boxes_with_opportunity']} / {cov['n_boxes']} "
        f"(lower bound {_fmt(cov['frac_boxes_with_opportunity_lower_bound'])}; {n_incomplete} of those pairs used sampled enumeration so the whole-box magnitude is a lower bound). "
        f"Complete pairs with no opportunity: {cov['n_boxes_complete_no_opportunity']}. "
        f"Incomplete with nothing found (unknown, not scored as absence): {cov['n_boxes_incomplete_unknown']}.",
        f"- Quality-qualified whole-box free-oracle mean saving: {_fmt(mean_free)}.",
        f"- Mean scan-charged saving: {_fmt(mean_scan)} (mean C_box {_fmt(mean_c)}).",
        "- Failure mechanism: see coverage vs content vs access in the rows above. "
        "Low legal coverage supports mismatch; legal coverage with little free-oracle benefit supports poor content "
        "under this single-intervention protocol; free benefit with poor scan-charged performance supports access cost.",
        "",
        "**The oracle uses information about future outcomes. It measures opportunity in a fixed library under this "
        "diagnostic protocol; it does not demonstrate that an agent can discover or exploit that opportunity autonomously.**",
        "",
        "Do not retrain gates or libraries from this result. Expt-6 boxes are development evidence and cannot later be reused as untouched confirmation tests.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT6_REPORT.md").write_text(text, encoding="utf-8")
    (run_dir / "cost_curve.json").write_text(json.dumps(curve, indent=2), encoding="utf-8")
    (run_dir / "coverage.json").write_text(json.dumps(cov, indent=2), encoding="utf-8")
    (run_dir / "gate_miss_levels.json").write_text(json.dumps(miss, indent=2), encoding="utf-8")
    return text
