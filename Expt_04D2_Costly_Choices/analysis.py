"""Expt-4D2 report. No promotion change. No hierarchy claim without composed replays."""

from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from audit import _fmt, _mean, summarize_replays
from config import DIAGNOSTIC_MODES, PHILOSOPHY, QUALITY_LOSS_MARGIN


def attach_savings(rows: list[dict], margin: float) -> list[dict]:
    by_key = {(int(r["seed"]), r["task_id"], r["split"], r["mode"]): r for r in rows}
    out = []
    for row in rows:
        prim = by_key.get((int(row["seed"]), row["task_id"], row["split"], "primitive"))
        if prim is None:
            continue
        copied = dict(row)
        copied["effort_saving"] = float(prim["A"]) - float(row["A"])
        copied["quality_loss"] = float(row["Q"]) < float(prim["Q"]) - margin
        copied["A_primitive"] = float(prim["A"])
        copied["Q_primitive"] = float(prim["Q"])
        copied["primitive_evals_baseline"] = float(prim.get("primitive_evals") or 0)
        out.append(copied)
    return out


def _sd(values):
    return None if len(values) < 2 else statistics.stdev(values)


def write_plots(run_dir: Path, rows: list[dict], replays: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    names = list(DIAGNOSTIC_MODES)
    means = [_mean([float(r["A"]) for r in rows if r["mode"] == name]) or 0 for name in names]
    ax.bar(range(len(names)), means)
    ax.set_xticks(range(len(names)), names, rotation=18, ha="right")
    ax.set_ylabel("mean A (candidate evaluations)")
    ax.set_title("Corrected diagnostic: mean A by mode")
    fig.tight_layout()
    fig.savefig(run_dir / "plot_mode_A.png", dpi=120)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    if replays:
        ax.hist([float(r["effort_saving_remaining"]) for r in replays], bins=20)
    ax.axvline(0.0, color="#888888")
    ax.set_xlabel("remaining effort saving = A_skip - A_commit")
    ax.set_ylabel("replay count")
    ax.set_title("Matched-state remaining-solve effort saving")
    fig.tight_layout()
    fig.savefig(run_dir / "plot_replay_savings.png", dpi=120)
    plt.close(fig)


def write_report(
    run_dir: Path,
    config: dict,
    meta: dict,
    rows: list[dict],
    new_replays: list[dict],
    existing_table: list[dict],
    existing_summary: dict,
    audit: dict,
) -> str:
    margin = float(config.get("quality_loss_margin", QUALITY_LOSS_MARGIN))
    annotated = attach_savings(rows, margin)
    prim = [r for r in annotated if r["mode"] == "primitive"]
    prim_mean_q = _mean([float(r["Q"]) for r in prim])
    new_norm = []
    for rec in new_replays:
        copied = dict(rec)
        copied["effort_ok"] = str(rec.get("effort_ok")).lower() in ("true", "1")
        copied["quality_ok"] = str(rec.get("quality_ok")).lower() in ("true", "1")
        copied["acceptable_success"] = str(rec.get("acceptable_success")).lower() in ("true", "1")
        copied["composed"] = str(rec.get("composed")).lower() in ("true", "1")
        copied["effort_saving_remaining"] = float(rec["effort_saving_remaining"])
        copied["op_id"] = rec["op_id"]
        new_norm.append(copied)
    new_norm.sort(key=lambda r: r["effort_saving_remaining"])
    new_summary = summarize_replays(new_norm) if new_norm else {"n": 0}
    n_trace = sum(1 for r in annotated if r["mode"] == "retrieve_check_then_primitive" and str(r.get("primitive_trace_matches")).lower() in ("true", "1"))
    n_check = sum(1 for r in annotated if r["mode"] == "retrieve_check_then_primitive")
    n_identity = sum(1 for r in annotated if str(r.get("A_identity_ok")).lower() in ("true", "1"))
    lines = [
        "# Expt-4D2 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Python: {meta.get('python')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        "- Effort saving = A_primitive − A_agent. Positive means fewer evaluations.",
        "- A = primitive_evals + retrieval_cost + applicability_cost + learned_evals.",
        "- retrieve_check_then_primitive stops on primitive evaluations only, so consultation cannot truncate the primitive trajectory.",
        "- Counterfactual remaining-solves are diagnosis only.",
        "- Promotion is unchanged. This experiment does not admit a new applicability learner.",
        "",
        "## Accounting (frozen Expt-4D CSV)",
        "",
        f"- Primitive_evals matched retrieve/check on {audit['n_primitive_eval_match']}/{audit['n_pairs']} boxes.",
        f"- Shared-cap truncations in Expt-4D: {audit['n_cap_truncated']}.",
        f"- Mean retrieval_cost {_fmt(audit['mean_retrieval'])}; applicability {_fmt(audit['mean_applicability'])}; learned site checks {_fmt(audit['mean_learned'])}.",
        f"- Mean consultation {_fmt(audit['mean_consultation'])}; published mean ΔA {_fmt(audit['mean_delta_A'])}.",
        "- Retrieval cost alone does not explain net ΔA. Applicability checks are billed separately. The remaining mean gap is the eval-cap artefact.",
        "",
        "## Corrected diagnostic modes",
        "",
        f"- retrieve_check primitive traces identical to primitive: {n_trace}/{n_check}",
        f"- A identity holds: {n_identity}/{len(annotated)} rows",
        "",
    ]
    for mode in DIAGNOSTIC_MODES:
        subset = [r for r in annotated if r["mode"] == mode]
        q = [float(r["Q"]) for r in subset]
        a = [float(r["A"]) for r in subset]
        s = [float(r["effort_saving"]) for r in subset]
        losses = [1.0 if r["quality_loss"] else 0.0 for r in subset]
        mean_q = _mean(q)
        mean_q_ok = prim_mean_q is None or mean_q is None or mean_q >= prim_mean_q - margin
        consult = [float(r.get("consultation_cost") or 0) for r in subset]
        prim_evals = [float(r.get("primitive_evals") or 0) for r in subset]
        lines.append(
            f"- {mode}: n={len(subset)}; mean Q {_fmt(mean_q)} (sd {_fmt(_sd(q))}); "
            f"mean A {_fmt(_mean(a))}; mean effort saving {_fmt(_mean(s))}; "
            f"quality-loss rate {_fmt(100.0 * (_mean(losses) or 0))}% of boxes; "
            f"mean-quality preserved: {'yes' if mean_q_ok else 'no'}"
        )
        if mode != "primitive":
            lines.append(
                f"  - mean primitive evals {_fmt(_mean(prim_evals))}; mean consultation {_fmt(_mean(consult))}"
            )
    lines += [
        "",
        "## Existing 15 Expt-4D replays (not re-simulated; worst first)",
        "",
        f"- Mean remaining saving {_fmt(existing_summary.get('mean_saving'))}; median {_fmt(existing_summary.get('median_saving'))}.",
        f"- Repay check cost: {existing_summary.get('n_effort_ok')}/{existing_summary.get('n')}.",
        f"- Quality preserved: {existing_summary.get('n_quality_ok')}/{existing_summary.get('n')}.",
        f"- Acceptable successes (both): {existing_summary.get('n_acceptable_success')}/{existing_summary.get('n')}.",
        f"- Composed: {existing_summary.get('n_composed')}. Mixed outcomes do not identify a predictive context; all Expt-4D cases were occupancy 0–24. Hierarchy is untested here.",
        "",
    ]
    for rec in existing_table:
        flag = "ok" if rec["acceptable_success"] else ("Q" if not rec["quality_ok"] else "A")
        lines.append(
            f"- r{rec['rank']} {rec['decision_id']} {rec['op_id']} occ {rec['occupied_at_choice']} "
            f"empty {rec['empty_components']}/{rec['largest_empty_region']} saving {rec['effort_saving_remaining']:.0f} "
            f"QΔ {rec['quality_difference']:.0f} [{flag}]"
        )
    lines += ["", "## New matched-state replays (reconstructed library, original + fresh boxes)", ""]
    if not new_norm:
        lines.append("- No new legal proposals were replayed.")
    else:
        lines.append(
            f"- n={new_summary['n']}; mean {_fmt(new_summary['mean_saving'])}; median {_fmt(new_summary['median_saving'])}; "
            f"acceptable {new_summary['n_acceptable_success']}/{new_summary['n']}; composed {new_summary['n_composed']}"
        )
        by_split = defaultdict(int)
        for rec in new_norm:
            by_split[rec.get("split")] += 1
        lines.append("- By split: " + ", ".join(f"{k} {v}" for k, v in sorted(by_split.items(), key=lambda kv: str(kv[0]))))
        for rec in new_norm[:20]:
            flag = "ok" if rec["acceptable_success"] else ("Q" if not rec["quality_ok"] else "A")
            lines.append(
                f"- {rec.get('decision_id')} {rec['op_id']} composed={rec['composed']} "
                f"saving {rec['effort_saving_remaining']:.0f} [{flag}] remaining {rec.get('remaining_pieces')}"
            )
        lines += ["", "### New replays by operation", ""]
        for item in new_summary.get("by_operation") or []:
            lines.append(
                f"- {item['op_id']}: n={item['n']}; mean saving {_fmt(item['mean_saving'])}; "
                f"acceptable {item['n_acceptable']}/{item['n']}"
            )
    lines += [
        "",
        "## What this does not conclude",
        "",
        "- Mixed help/harm does not mean a predictive context has been found.",
        "- With zero composed replays, hierarchy is not tested.",
        "- Promotion is not redesigned here. A later admission rule must use repeated downstream benefit, including severe losses, and must be tested on boxes unused for learning the rule.",
        "",
        "The broader reusable-knowledge idea remains unproven, not disproved.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "EXPT4D2_REPORT.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT4D2_REPORT.md").write_text(text, encoding="utf-8")
    return text
