"""Plots and EXPT4B_REPORT.md. Q and A stay separate. Q/A is the mean of ratios."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import CONDITION_NAMES, PHILOSOPHY


def _mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _sd(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return statistics.stdev(values)


def _ci(values: list[float]) -> tuple[float | None, float | None]:
    if len(values) < 2:
        return None, None
    mean = sum(values) / len(values)
    se = statistics.stdev(values) / math.sqrt(len(values))
    return mean - 1.96 * se, mean + 1.96 * se


def _fmt(value) -> str:
    if value is None:
        return "NA"
    return f"{value:.4g}" if isinstance(value, float) else str(value)


def summarise(rows: list[dict], field: str) -> dict:
    values = [float(row[field]) for row in rows if row.get(field) not in (None, "")]
    lo, hi = _ci(values)
    return {
        "n": len(values),
        "mean": _mean(values),
        "sd": _sd(values),
        "median": None if not values else statistics.median(values),
        "ci_lo": lo,
        "ci_hi": hi,
    }


def _held(rows: list[dict], experience: int) -> list[dict]:
    return [row for row in rows if row.get("split") == "heldout" and int(row["experience"]) == experience]


def write_plots(run_dir: Path, checkpoints: list[dict], train_rows: list[dict]) -> None:
    held = [row for row in checkpoints if row.get("split") == "heldout"]
    _line(run_dir / "plot_quality.png", held, "Q", "Held-out quality vs experience", "mean Q")
    _line(run_dir / "plot_thinking.png", held, "A", "Held-out thinking effort vs experience", "mean A")
    _line(run_dir / "plot_efficiency.png", held, "efficiency", "Held-out mean of Q/A vs experience", "mean of Q/A")
    _line(run_dir / "plot_memory.png", train_rows, "library_size", "Active library size", "active operations")
    _line(run_dir / "plot_wall.png", held, "elapsed_s", "Held-out wall-clock vs experience", "seconds")
    _line(run_dir / "plot_internal.png", held, "internal_execution", "Internal execution (excluded from A)", "placements")


def _line(path: Path, rows: list[dict], field: str, title: str, ylabel: str) -> None:
    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row.get(field) in (None, ""):
            continue
        grouped[str(row.get("condition", "?"))][int(row["experience"])].append(float(row[field]))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not grouped:
        ax.text(0.5, 0.5, "no rows", ha="center", va="center")
        ax.set_axis_off()
    else:
        for name, points in sorted(grouped.items()):
            xs = sorted(points)
            ys = [sum(points[x]) / len(points[x]) for x in xs]
            ax.plot(xs, ys, marker="o", label=name)
        ax.set_xlabel("previously solved training boxes")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=7)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def write_report(run_dir: Path, config: dict, meta: dict, checkpoints: list[dict], pair_rows: list[dict], op_rows: list[dict]) -> None:
    last = max((int(row["experience"]) for row in checkpoints if row.get("split") == "heldout"), default=0)
    first = 0
    lines = [
        "# Expt-4B report",
        "",
        PHILOSOPHY,
        "",
        "The research question: can the agent autonomously distinguish a recurring pattern from a useful piece of knowledge?",
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Python: {meta.get('python')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Q_min: {config.get('q_min')}",
        "",
        "Q/A below is the mean of per-box ratios, not mean Q divided by mean A.",
        "Internal execution is reported and is not added to A.",
        "",
        "## Held-out comparison",
        "",
    ]
    for exp in sorted({int(row["experience"]) for row in checkpoints if row.get("split") == "heldout"}):
        lines.append(f"### Experience {exp}")
        lines.append("")
        for name in CONDITION_NAMES:
            subset = [row for row in _held(checkpoints, exp) if row["condition"] == name]
            if not subset:
                continue
            q = summarise(subset, "Q")
            a = summarise(subset, "A")
            e = summarise(subset, "efficiency")
            lines.append(
                f"- {name}: Q n={q['n']} mean {_fmt(q['mean'])} sd {_fmt(q['sd'])}; "
                f"A mean {_fmt(a['mean'])} sd {_fmt(a['sd'])}; "
                f"mean Q/A {_fmt(e['mean'])}"
            )
        lines.append("")
    lines += ["## Condition answers", ""]
    def _a(name, exp):
        subset = [row for row in _held(checkpoints, exp) if row["condition"] == name]
        return summarise(subset, "A")["mean"], summarise(subset, "Q")["mean"]

    pA, pQ = _a("primitive", last)
    hA, hQ = _a("current_hierarchy", last)
    uA, uQ = _a("utility_promotion", last)
    cA, cQ = _a("contextual_abstention", last)
    bA, bQ = _a("both", last)
    pA0, _ = _a("primitive", first)
    hA0, _ = _a("current_hierarchy", first)
    lines.append(f"- Primitive baseline at last checkpoint: Q {_fmt(pQ)}, A {_fmt(pA)}.")
    if hA is not None and pA is not None:
        reproduced = hA > pA
        lines.append(
            f"- Current hierarchy vs primitive A: {_fmt(hA)} vs {_fmt(pA)}. "
            + ("The Expt-4 failure (library raises A) was reproduced." if reproduced else "The Expt-4 failure was not reproduced on this schedule.")
        )
    if uA is not None and hA is not None:
        lines.append(
            f"- Utility-based promotion vs current hierarchy A: {_fmt(uA)} vs {_fmt(hA)}. "
            + ("Harmful admissions look reduced." if uA < hA else "Utility promotion did not lower A below recurrence promotion.")
        )
    if cA is not None and hA is not None:
        lines.append(
            f"- Contextual retrieval/abstention vs current hierarchy A: {_fmt(cA)} vs {_fmt(hA)}. "
            + ("Unsuitable uses look reduced." if cA < hA else "Abstention did not lower A below always-consulting retrieval.")
        )
    if bA is not None and pA is not None:
        lines.append(
            f"- Both changes together vs primitive A: {_fmt(bA)} vs {_fmt(pA)}. "
            + ("Selective acquisition plus selective use produced a benefit." if bA < pA and (bQ or 0) >= (pQ or 0) - 1 else "Together they did not beat the primitive baseline on this diagnostic.")
        )
    promoted = [row for row in pair_rows if row.get("promoted") in (True, "True", "true", 1, "1")]
    rejected = [row for row in pair_rows if row.get("promoted") in (False, "False", "false", 0, "0")]
    lines += [
        "",
        "## Paired validation (training-only)",
        "",
        f"- Candidates tested: {len(pair_rows)}; promoted {len(promoted)}; kept provisional {len(rejected)}.",
        "- Held-out boxes were not used in pairing.",
        "",
        "## Operation logs",
        "",
    ]
    for name in CONDITION_NAMES:
        subset = [row for row in op_rows if row.get("condition") == name]
        active = [row for row in subset if row.get("status") == "active"]
        lines.append(
            f"- {name}: {len(subset)} stored records, {len(active)} active, "
            f"retrievals {sum(int(row.get('retrievals') or 0) for row in subset)}, "
            f"applicability failures {sum(int(row.get('applicability_failures') or 0) for row in subset)}, "
            f"commitments {sum(int(row.get('commitments') or 0) for row in subset)}."
        )
    lines += [
        "",
        "These statements describe this diagnostic only. They do not claim that intelligence has emerged.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "EXPT4B_REPORT.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT4B_REPORT.md").write_text(text, encoding="utf-8")
