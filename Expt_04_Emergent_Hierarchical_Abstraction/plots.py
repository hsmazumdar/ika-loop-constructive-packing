"""Checkpoint plots. Empty series are drawn as a labelled panel, not omitted."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _mean_by_experience(rows: list[dict], split: str, field: str) -> dict[str, list[tuple[int, float]]]:
    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row.get("split") != split:
            continue
        value = row.get(field)
        if value is None or value == "":
            continue
        grouped[str(row["agent"])][int(row["experience"])].append(float(value))
    out = {}
    for agent, points in grouped.items():
        out[agent] = [(exp, sum(vals) / len(vals)) for exp, vals in sorted(points.items())]
    return out


def _line_plot(path: Path, series: dict[str, list[tuple[int, float]]], title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not series:
        ax.text(0.5, 0.5, "no checkpoint rows", ha="center", va="center")
        ax.set_axis_off()
    else:
        for agent, points in sorted(series.items()):
            ax.plot([p[0] for p in points], [p[1] for p in points], marker="o", label=agent)
        ax.set_xlabel("previously solved training boxes")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def write_plots(run_dir: Path, checkpoints: list[dict], train_rows: list[dict]) -> None:
    held = [row for row in checkpoints if row.get("split") == "heldout"]
    _line_plot(run_dir / "plot_quality.png", _mean_by_experience(held, "heldout", "Q"), "Quality vs experience", "mean Q")
    _line_plot(run_dir / "plot_thinking.png", _mean_by_experience(held, "heldout", "A"), "Thinking effort vs experience", "mean A")
    _line_plot(run_dir / "plot_efficiency.png", _mean_by_experience(held, "heldout", "efficiency"), "Q/A vs experience", "mean Q/A")
    _line_plot(run_dir / "plot_memory.png", _mean_by_experience(train_rows, "train", "library_size"), "Surviving learned operations", "library size")
    _line_plot(run_dir / "plot_depth_mean.png", _mean_by_experience(train_rows, "train", "mean_depth"), "Mean abstraction depth", "mean depth")
    _line_plot(run_dir / "plot_depth_max.png", _mean_by_experience(train_rows, "train", "max_depth"), "Maximum abstraction depth", "max depth")
    _usage_plot(run_dir / "plot_usage.png", held)
    _composition_plot(run_dir / "plot_search.png", held)
    _probe_plot(run_dir / "plot_environment.png", checkpoints)


def _usage_plot(path: Path, held: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not held:
        ax.text(0.5, 0.5, "no held-out rows", ha="center", va="center")
        ax.set_axis_off()
    else:
        largest = max(int(row["experience"]) for row in held)
        agents = sorted({row["agent"] for row in held if int(row["experience"]) == largest})
        labels = ["depth0", "depth1", "depth2", "depth3plus"]
        x = list(range(len(agents)))
        bottom = [0.0] * len(agents)
        for label in labels:
            heights = []
            for agent in agents:
                rows = [row for row in held if row["agent"] == agent and int(row["experience"]) == largest]
                total = sum(float(row[name]) for row in rows for name in labels) or 1.0
                heights.append(sum(float(row[label]) for row in rows) / total)
            ax.bar(x, heights, bottom=bottom, label=label)
            bottom = [b + h for b, h in zip(bottom, heights)]
        ax.set_xticks(x, agents, rotation=20, ha="right")
        ax.set_ylabel("fraction of decisions")
        ax.legend(fontsize=8)
    ax.set_title("Decision level at the last held-out checkpoint")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _composition_plot(path: Path, held: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fields = ["retrieval_cost", "learned_evals", "primitive_evals", "failed_attempts"]
    if not held:
        ax.text(0.5, 0.5, "no held-out rows", ha="center", va="center")
        ax.set_axis_off()
    else:
        largest = max(int(row["experience"]) for row in held)
        agents = sorted({row["agent"] for row in held if int(row["experience"]) == largest})
        x = list(range(len(agents)))
        bottom = [0.0] * len(agents)
        for label in fields:
            heights = []
            for agent in agents:
                rows = [row for row in held if row["agent"] == agent and int(row["experience"]) == largest]
                heights.append(sum(float(row[label]) for row in rows) / len(rows))
            ax.bar(x, heights, bottom=bottom, label=label)
            bottom = [b + h for b, h in zip(bottom, heights)]
        ax.set_xticks(x, agents, rotation=20, ha="right")
        ax.set_ylabel("mean count per held-out box")
        ax.legend(fontsize=8)
    ax.set_title("Search composition at the last held-out checkpoint")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _probe_plot(path: Path, checkpoints: list[dict]) -> None:
    probe = [row for row in checkpoints if row.get("split") == "probe"]
    _line_plot(path, _mean_by_experience(probe, "probe", "A"), "Probe-set thinking after the distribution shift", "mean A")


def write_genealogy(path: Path, operations: list) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    if not operations:
        ax.text(0.5, 0.5, "no learned operations", ha="center", va="center")
        ax.set_axis_off()
    else:
        by_depth: dict[int, list] = defaultdict(list)
        for op in operations:
            by_depth[int(op.depth)].append(op)
        pos = {}
        for depth, ops in sorted(by_depth.items()):
            for index, op in enumerate(ops):
                pos[op.op_id] = (depth, index)
                ax.scatter([depth], [index], s=40)
                ax.text(depth + 0.05, index, op.op_id, fontsize=8)
        for op in operations:
            if op.op_id not in pos:
                continue
            for child in op.children:
                if child in pos:
                    x0, y0 = pos[child]
                    x1, y1 = pos[op.op_id]
                    ax.plot([x0, x1], [y0, y1], color="0.4", linewidth=0.8)
        ax.set_xlabel("abstraction depth")
        ax.set_ylabel("operation index within depth")
    ax.set_title("Knowledge genealogy")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
