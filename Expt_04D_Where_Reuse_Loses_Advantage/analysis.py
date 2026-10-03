"""Expt-4D report. Effort saving = A_primitive - A_agent. Quality-loss rate is separate."""

from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import DIAGNOSTIC_MODES, PHILOSOPHY, QUALITY_LOSS_MARGIN


def _mean(values):
    return None if not values else sum(values) / len(values)


def _sd(values):
    return None if len(values) < 2 else statistics.stdev(values)


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _truthy(value) -> bool:
    return value in (True, "True", "true", 1, "1")


def _occupancy_bin(occupied) -> str:
    value = float(occupied)
    if value < 25:
        return "0-24"
    if value < 50:
        return "25-49"
    if value < 75:
        return "50-74"
    return "75+"


def attach_savings(rows: list[dict], margin: float) -> list[dict]:
    by_key = {(int(r["seed"]), r["task_id"], r["mode"]): r for r in rows}
    out = []
    for row in rows:
        prim = by_key.get((int(row["seed"]), row["task_id"], "primitive"))
        if prim is None:
            continue
        effort_saving = float(prim["A"]) - float(row["A"])
        quality_loss = float(row["Q"]) < float(prim["Q"]) - margin
        copied = dict(row)
        copied["effort_saving"] = effort_saving
        copied["quality_loss"] = quality_loss
        copied["A_primitive"] = float(prim["A"])
        copied["Q_primitive"] = float(prim["Q"])
        copied["primitive_evals_baseline"] = float(prim.get("primitive_evals") or 0)
        out.append(copied)
    return out


def interpret(rows: list[dict], replays: list[dict]) -> list[str]:
    def mean_saving(mode):
        vals = [float(r["effort_saving"]) for r in rows if r["mode"] == mode]
        return _mean(vals)

    overhead = mean_saving("retrieve_check_then_primitive")
    total = mean_saving("normal_reuse")
    remaining = [float(r["effort_saving_remaining"]) for r in replays]
    remaining_mean = _mean(remaining)
    check_costs = [float(r["check_cost"]) for r in replays]
    composed = [r for r in replays if _truthy(r.get("composed"))]
    flat = [r for r in replays if not _truthy(r.get("composed"))]
    help_effort = [r for r in replays if _truthy(r.get("helps_effort"))]
    harm_effort = [r for r in replays if not _truthy(r.get("helps_effort"))]
    lines = []
    if (
        overhead is not None
        and overhead < 0
        and remaining_mean is not None
        and remaining_mean > 0
    ):
        lines.append(
            "Useful execution, expensive retrieval: remaining-solve effort saving is positive after a commit, "
            "but retrieve-and-check already uses extra evaluations. Improve indexing and early abstention."
        )
    median_remaining = statistics.median(remaining) if remaining else None
    if remaining and remaining_mean is not None and remaining_mean < 0:
        if median_remaining is not None and median_remaining > 0:
            lines.append(
                "Harmful execution is concentrated in a minority of commits: mean remaining-solve A after committing "
                "is higher than primitive from the same state, but the median remaining effort saving is positive. "
                "Revise candidate generation and promotion so those tail cases are not admitted."
            )
        else:
            lines.append(
                "Harmful execution even without retrieval cost: remaining-solve A after committing is higher than primitive "
                "from the same state. Revise candidate generation and promotion."
            )
    if replays and 0 < len(help_effort) < len(replays):
        lines.append(
            "Benefits are restricted to identifiable contexts: some operations help remaining effort, others do not. "
            "Improve the applicability learner."
        )
        by_bin = defaultdict(lambda: {"n": 0, "help": 0, "saving": []})
        for rec in replays:
            bucket = by_bin[_occupancy_bin(rec.get("occupied_at_choice") or 0)]
            bucket["n"] += 1
            bucket["help"] += int(_truthy(rec.get("helps_effort")))
            bucket["saving"].append(float(rec["effort_saving_remaining"]))
        parts = []
        for name in ("0-24", "25-49", "50-74", "75+"):
            bucket = by_bin.get(name)
            if not bucket:
                continue
            parts.append(
                f"{name} occupied: {bucket['help']}/{bucket['n']} help remaining effort "
                f"(mean remaining saving {_fmt(_mean(bucket['saving']))})"
            )
        if parts:
            lines.append("Help/harm by occupancy at the choice: " + "; ".join(parts) + ".")
    if composed and flat:
        flat_s = _mean([float(r["effort_saving_remaining"]) for r in flat])
        comp_s = _mean([float(r["effort_saving_remaining"]) for r in composed])
        if flat_s is not None and comp_s is not None and flat_s > 0 and comp_s <= 0:
            lines.append(
                "Flat operations help but compositions hurt: suspend higher-level promotion until compositions beat their components."
            )
    reuse = [r for r in rows if r["mode"] == "normal_reuse"]
    check = [r for r in rows if r["mode"] == "retrieve_check_then_primitive"]
    bypass = _mean([float(r.get("bypassed_primitive_decisions") or 0) for r in reuse])
    proposals = _mean([float(r.get("library_proposals") or 0) for r in reuse])
    prim_evals_reuse = _mean([float(r.get("primitive_evals") or 0) for r in reuse])
    prim_evals_base = _mean([float(r.get("primitive_evals_baseline") or r.get("primitive_evals") or 0) for r in reuse])
    if proposals and bypass is not None and proposals > 0 and (bypass < proposals or (prim_evals_reuse is not None and prim_evals_base is not None and prim_evals_reuse >= prim_evals_base)):
        lines.append(
            "Successful retrieval often does not replace primitive deliberation: proposals were found but the primitive "
            "scan was still largely evaluated, so remembering added options rather than bypassing search."
        )
    if overhead is not None and total is not None:
        extra_retrieval = -overhead
        extra_execution = overhead - total
        lines.append(
            f"A decomposition: retrieve-and-check adds {_fmt(extra_retrieval)} evaluations versus primitive; "
            f"then committing changes A by {_fmt(extra_execution)} versus retrieve-and-check "
            f"(positive = committing used still more evaluations)."
        )
    if not lines:
        lines.append("No single failure mode dominated this diagnostic. See the tables.")
    if check_costs:
        lines.append(f"Mean retrieval-and-check cost per proposed commit: {_fmt(_mean(check_costs))} evaluations.")
    if help_effort or harm_effort:
        lines.append(
            f"Replays that more than repaid their check cost: {len(help_effort)}/{len(replays)}; "
            f"replays that did not: {len(harm_effort)}/{len(replays)}."
        )
    return lines


def write_plots(run_dir: Path, rows: list[dict], replays: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    names = list(DIAGNOSTIC_MODES)
    means = [_mean([float(r["A"]) for r in rows if r["mode"] == name]) or 0 for name in names]
    ax.bar(range(len(names)), means)
    ax.set_xticks(range(len(names)), names, rotation=18, ha="right")
    ax.set_ylabel("mean A (candidate evaluations)")
    ax.set_title("Development-set deliberation by diagnostic mode")
    fig.tight_layout()
    fig.savefig(run_dir / "plot_mode_A.png", dpi=120)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    if replays:
        ax.hist([float(r["effort_saving_remaining"]) for r in replays], bins=20)
    ax.axvline(0.0, color="#888888")
    ax.set_xlabel("effort saving remaining = A_primitive_branch - A_commit_branch")
    ax.set_ylabel("replay count")
    ax.set_title("Counterfactual remaining-solve effort saving")
    fig.tight_layout()
    fig.savefig(run_dir / "plot_replay_savings.png", dpi=120)
    plt.close(fig)


def write_report(run_dir: Path, config: dict, meta: dict, rows: list[dict], replays: list[dict]) -> None:
    margin = float(config.get("quality_loss_margin", QUALITY_LOSS_MARGIN))
    annotated = attach_savings(rows, margin)
    prim = [r for r in annotated if r["mode"] == "primitive"]
    prim_mean_q = _mean([float(r["Q"]) for r in prim])
    lines = [
        "# Expt-4D report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Python: {meta.get('python')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Development boxes: {meta.get('n_development')}",
        f"- Quality-loss margin (declared before the run): {margin} occupied cells",
        "- Effort saving = A_primitive − A_agent. Positive means the agent used fewer evaluations.",
        "- Quality-loss rate = fraction of boxes with Q_agent < Q_primitive − margin.",
        "- Mean-quality preservation = whether mean Q is within the margin of the primitive mean. This is not the 20% box-rate gate.",
        "- The 'quality losses ≤ 20%' criterion is the per-box quality-loss rate. It allows one in five boxes to exceed the margin even when mean Q looks fine.",
        "- Counterfactual remaining-solves are diagnosis only. A deployed agent does not receive both futures.",
        "",
        "## Diagnostic modes on the development set",
        "",
    ]
    for mode in DIAGNOSTIC_MODES:
        subset = [r for r in annotated if r["mode"] == mode]
        q = [float(r["Q"]) for r in subset]
        a = [float(r["A"]) for r in subset]
        s = [float(r["effort_saving"]) for r in subset]
        losses = [1.0 if r["quality_loss"] else 0.0 for r in subset]
        mean_q = _mean(q)
        mean_q_ok = (
            prim_mean_q is None or mean_q is None or mean_q >= prim_mean_q - margin
        )
        bypass = [float(r.get("bypassed_primitive_decisions") or 0) for r in subset]
        proposals = [float(r.get("library_proposals") or 0) for r in subset]
        prim_evals = [float(r.get("primitive_evals") or 0) for r in subset]
        retrieval = [float(r.get("retrieval_cost") or 0) for r in subset]
        lines.append(
            f"- {mode}: n={len(subset)}; mean Q {_fmt(mean_q)} (sd {_fmt(_sd(q))}); "
            f"mean A {_fmt(_mean(a))} (sd {_fmt(_sd(a))}); mean effort saving {_fmt(_mean(s))}; "
            f"quality-loss rate {_fmt(100.0 * (_mean(losses) or 0))}% of boxes; "
            f"mean-quality preserved vs primitive mean: {'yes' if mean_q_ok else 'no'} "
            f"(mean Q {_fmt(mean_q)} vs primitive {_fmt(prim_mean_q)})"
        )
        extra = []
        if mode != "primitive":
            extra.append(f"mean retrieval cost {_fmt(_mean(retrieval))}")
            extra.append(f"mean primitive evals {_fmt(_mean(prim_evals))}")
        if mode == "normal_reuse":
            extra.append(f"mean library proposals {_fmt(_mean(proposals))}")
            extra.append(f"mean bypassed primitive decisions {_fmt(_mean(bypass))}")
        if extra:
            lines.append("  - " + "; ".join(extra))
    lines += ["", "## Counterfactual remaining solves", ""]
    if not replays:
        lines.append("- No legal learned-operation proposals were replayed.")
    else:
        rem = [float(r["effort_saving_remaining"]) for r in replays]
        qd = [float(r["quality_difference"]) for r in replays]
        help_e = sum(1 for r in replays if _truthy(r.get("helps_effort")))
        composed = [r for r in replays if _truthy(r.get("composed"))]
        flat = [r for r in replays if not _truthy(r.get("composed"))]
        median_rem = statistics.median(rem) if rem else None
        lines.append(f"- Replays: {len(replays)}; flat {len(flat)}; composed {len(composed)}")
        lines.append(
            f"- Mean remaining effort saving {_fmt(_mean(rem))}; median {_fmt(median_rem)} "
            "(positive = commit then primitive used fewer remaining evaluations than primitive-only)"
        )
        lines.append(f"- Mean final quality difference (commit − skip) {_fmt(_mean(qd))}")
        lines.append(f"- Replays whose remaining effort saving exceeded check cost: {help_e}/{len(replays)}")
        if flat:
            lines.append(f"- Flat remaining effort saving {_fmt(_mean([float(r['effort_saving_remaining']) for r in flat]))}")
        if composed:
            lines.append(
                f"- Composed remaining effort saving {_fmt(_mean([float(r['effort_saving_remaining']) for r in composed]))}"
            )
    lines += ["", "## Interpretation", ""]
    for item in interpret(annotated, replays):
        lines.append(f"- {item}")
    lines += [
        "",
        "These statements describe this diagnostic only. The broader reusable-knowledge idea is unproven, not disproved.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "EXPT4D_REPORT.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT4D_REPORT.md").write_text(text, encoding="utf-8")
