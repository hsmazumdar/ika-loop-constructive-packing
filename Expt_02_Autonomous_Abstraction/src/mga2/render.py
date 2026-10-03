"""Headless board and run plots."""

from __future__ import annotations

import csv
from pathlib import Path

from mga2.pieces import BOARD_SIZE, PIECE_COLORS, PIECES, orientation


def _rect(x, y, facecolor, edgecolor, lw):
    from matplotlib.patches import Rectangle

    return Rectangle((x, y), 1, 1, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw)


def draw_grid(ax, cells: list[list[str]], title: str) -> None:
    ax.set_xlim(0, BOARD_SIZE)
    ax.set_ylim(BOARD_SIZE, 0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#f4f7fb")
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            label = cells[y][x] if cells else ""
            color = PIECE_COLORS.get(label, "#ffffff") if label else "#ffffff"
            ax.add_patch(_rect(x, y, color, "#c5d0de", 0.6))
            if label:
                ax.text(x + 0.5, y + 0.5, label, ha="center", va="center", fontsize=8, color="#102033")
    ax.set_title(title, loc="left", fontsize=11, color="#1b365d")


def save_boards(real_cells, sim_cells, path: Path, footer: str = "") -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.8))
    fig.patch.set_facecolor("#eef3f9")
    draw_grid(axes[0], real_cells, "Real board")
    draw_grid(axes[1], sim_cells, "SIMULATION")
    if footer:
        fig.text(0.02, 0.02, footer, fontsize=8, color="#1b365d")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_run(csv_path: Path, run_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with Path(csv_path).open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return
    scores = [float(r["final_score"]) for r in rows]
    compute = []
    total = 0.0
    for r in rows:
        total += float(r["model_transitions"]) + float(r["candidate_evals"])
        compute.append(total)
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))
    axes[0, 0].plot(compute, scores, color="#1b365d", lw=1)
    axes[0, 0].set_title("Score vs cumulative computation")
    axes[0, 0].set_xlabel("evals + model transitions")
    axes[0, 0].set_ylabel("final score")
    phys = [float(r["physical_actions"]) for r in rows]
    axes[0, 1].plot(range(1, len(rows) + 1), phys, color="#5B8DEF", lw=1)
    axes[0, 1].set_title("Physical actions per box")
    libs = [float(r["ltm_bytes"]) for r in rows]
    axes[1, 0].scatter(libs, scores, s=12, color="#2BBBAD")
    axes[1, 0].set_title("Library bytes vs final score")
    macros = [float(r["macro_invocations"]) for r in rows]
    axes[1, 1].plot(range(1, len(rows) + 1), macros, color="#E57BA4", lw=1)
    axes[1, 1].set_title("Macro invocations per box")
    fig.tight_layout()
    fig.savefig(run_dir / "score_cost_memory.png", dpi=120)
    plt.close(fig)


def plot_box_trace(trace: list[dict], path: Path, title: str, caption: str) -> None:
    """Occupied cells against cumulative candidate evaluations for one box."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    evals = [0] + [int(row["evals_after"]) for row in trace]
    scores = [0] + [int(row["score_after"]) for row in trace]
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot(evals, scores, color="#1b365d", lw=1.6, zorder=1)
    colors = {
        "paired": "#E57BA4",
        "library_scan": "#2BBBAD",
        "placement": "#5B8DEF",
        "lookahead": "#C4A35A",
        "think": "#E57BA4",
        "other": "#8A93A6",
    }
    for row, x, y in zip(trace, evals[1:], scores[1:]):
        kind = _trace_kind(row)
        ax.scatter([x], [y], s=28, color=colors.get(kind, "#8A93A6"), zorder=2)
    ax.set_title(title, loc="left", fontsize=11, color="#1b365d")
    ax.set_xlabel("Cumulative candidate evaluations")
    ax.set_ylabel("Occupied cells")
    ax.set_ylim(bottom=0)
    fig.text(0.01, 0.01, caption, fontsize=8, color="#1b365d")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _trace_kind(row: dict) -> str:
    if int(row.get("think_span", 0)) > 0 or int(row.get("paired", 0)) > 0:
        return "paired" if int(row.get("paired", 0)) >= int(row.get("placement", 0)) else "placement"
    if int(row.get("library_scan", 0)) > int(row.get("placement", 0)):
        return "library_scan"
    if int(row.get("lookahead", 0)) > 0:
        return "lookahead"
    if int(row.get("placement", 0)) > 0:
        return "placement"
    return "other"


def catalogue_preview(path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 4)
    ax.set_ylim(4, 0)
    ax.axis("off")
    ax.set_title("Catalogue A–P")
    for i, name in enumerate(PIECES):
        gx, gy = i % 4, i // 4
        cells = orientation(PIECES[name], 0)
        for cx, cy in cells:
            ax.add_patch(
                Rectangle(
                    (gx + 0.12 + cx * 0.12, gy + 0.2 + cy * 0.12),
                    0.1,
                    0.1,
                    facecolor=PIECE_COLORS[name],
                    edgecolor="#1b365d",
                    linewidth=0.3,
                )
            )
        ax.text(gx + 0.02, gy + 0.08, name, fontsize=8, color="#1b365d")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
