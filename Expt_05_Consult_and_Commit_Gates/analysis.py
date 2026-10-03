"""Expt-5 factorial report. Gate costs are inside A. Learning cost is separate."""

from __future__ import annotations

import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import EVAL_CONDITIONS, PHILOSOPHY, QUALITY_LOSS_MARGIN


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


def attach_savings(rows: list[dict], margin: float) -> list[dict]:
    by_key = {(int(r["seed"]), r["task_id"], r["condition"]): r for r in rows}
    out = []
    for row in rows:
        prim = by_key.get((int(row["seed"]), row["task_id"], "primitive"))
        if prim is None:
            continue
        copied = dict(row)
        copied["effort_saving"] = float(prim["A"]) - float(row["A"])
        copied["quality_loss"] = float(row["Q"]) < float(prim["Q"]) - margin
        copied["A_primitive"] = float(prim["A"])
        copied["Q_primitive"] = float(prim["Q"])
        out.append(copied)
    return out


def write_plots(run_dir: Path, rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    names = list(EVAL_CONDITIONS)
    means = [_mean([float(r["A"]) for r in rows if r["condition"] == name]) or 0 for name in names]
    ax.bar(range(len(names)), means)
    ax.set_xticks(range(len(names)), names, rotation=18, ha="right")
    ax.set_ylabel("mean A (includes gate checks)")
    ax.set_title("Expt-5 factorial: mean deliberation")
    fig.tight_layout()
    fig.savefig(run_dir / "plot_condition_A.png", dpi=120)
    plt.close(fig)


def write_report(run_dir: Path, config: dict, meta: dict, rows: list[dict], gate_summary: dict, learning_a: float) -> str:
    margin = float(config.get("quality_loss_margin", QUALITY_LOSS_MARGIN))
    annotated = attach_savings(rows, margin)
    prim = [r for r in annotated if r["condition"] == "primitive"]
    prim_mean_q = _mean([float(r["Q"]) for r in prim])
    prim_mean_a = _mean([float(r["A"]) for r in prim])
    lines = [
        "# Expt-5 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Python: {meta.get('python')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Eval boxes: {meta.get('n_eval')}",
        f"- Learning cost (counterfactual remaining-solves + collection retrieve/check): {_fmt(learning_a)} evaluations. This is not added to eval A.",
        "- Eval A = primitive_evals + retrieval + applicability + learned site checks + gate checks.",
        "- Effort saving = A_primitive − A_agent.",
        "- Quality-loss rate is the fraction of boxes with Q_agent < Q_primitive − 1. It is separate from mean Q.",
        "- Gates were frozen on held-out training-replay boxes before this eval.",
        "- No handwritten reject-M0003-on-empty-board rule.",
        "",
        "## Frozen gate",
        "",
        f"- Commit labels {gate_summary.get('n_commit_labels')}; consult states {gate_summary.get('n_consult_states')}; "
        f"selected {gate_summary.get('n_selected')}; unchosen sampled {gate_summary.get('n_unchosen')}",
        f"- Consult threshold {_fmt(gate_summary.get('consult_threshold'))}; commit threshold {_fmt(gate_summary.get('commit_threshold'))}",
        f"- Learned per-op commit bias: {gate_summary.get('commit_op_bias')}",
        "",
        "Per-op bias is estimated from replay labels. A negative bias on an operation is a learned association, not a coded prohibition.",
        "",
        "## Factorial on frozen eval boxes",
        "",
    ]
    for name in EVAL_CONDITIONS:
        subset = [r for r in annotated if r["condition"] == name]
        q = [float(r["Q"]) for r in subset]
        a = [float(r["A"]) for r in subset]
        s = [float(r["effort_saving"]) for r in subset]
        losses = [1.0 if r["quality_loss"] else 0.0 for r in subset]
        gates = [float(r.get("gate_cost") or 0) for r in subset]
        consult = [float(r.get("consultation_cost") or 0) for r in subset]
        mean_q = _mean(q)
        mean_q_ok = prim_mean_q is None or mean_q is None or mean_q >= prim_mean_q - margin
        lines.append(
            f"- {name}: n={len(subset)}; mean Q {_fmt(mean_q)} (sd {_fmt(_sd(q))}); mean A {_fmt(_mean(a))} "
            f"(sd {_fmt(_sd(a))}); mean effort saving {_fmt(_mean(s))}; "
            f"quality-loss rate {_fmt(100.0 * (_mean(losses) or 0))}% of boxes; "
            f"mean-quality preserved: {'yes' if mean_q_ok else 'no'}; "
            f"mean gate cost {_fmt(_mean(gates))}; mean consultation {_fmt(_mean(consult))}"
        )
    if prim_mean_a:
        both = _mean([float(r["A"]) for r in annotated if r["condition"] == "both_gates"])
        current = _mean([float(r["A"]) for r in annotated if r["condition"] == "current_selective"])
        lines += [
            "",
            "## Answers",
            "",
            f"- Current selective vs primitive mean A: {_fmt(current)} vs {_fmt(prim_mean_a)}.",
            f"- Both gates vs primitive mean A: {_fmt(both)} vs {_fmt(prim_mean_a)}.",
            "- Consultation change only vs commitment change only: see the rows above. The two decisions are not interchangeable.",
            "- If both gates still raise A, experience has not yet taught the agent when memory is worth its cost.",
            "",
            "These statements describe this run only. Useful knowledge must reduce future deliberation after paying for selection and use.",
            "",
        ]
    text = "\n".join(lines)
    (run_dir / "EXPT5_REPORT.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT5_REPORT.md").write_text(text, encoding="utf-8")
    return text
