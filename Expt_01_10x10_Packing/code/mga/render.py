"""Board rendering with matplotlib (headless-safe when using the Agg backend)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mga.pieces import BOARD_SIZE, PIECE_COLORS, PIECES, orientation

if TYPE_CHECKING:
    from mga.environment import PackingEnv


def draw_board(ax, env: "PackingEnv", title: str | None = None) -> None:
    ax.set_xlim(0, BOARD_SIZE)
    ax.set_ylim(BOARD_SIZE, 0)
    ax.set_aspect("equal")
    ax.set_xticks([i + 0.5 for i in range(BOARD_SIZE)])
    ax.set_yticks([i + 0.5 for i in range(BOARD_SIZE)])
    ax.set_xticklabels([str(i + 1) for i in range(BOARD_SIZE)])
    ax.set_yticklabels([str(i + 1) for i in range(BOARD_SIZE)])
    ax.tick_params(length=0)
    ax.set_facecolor("#f4f7fb")
    for spine in ax.spines.values():
        spine.set_color("#1b365d")
        spine.set_linewidth(1.4)

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            cell = env.cells[y][x]
            if cell is None:
                ax.add_patch(
                    __rect(x, y, facecolor="#ffffff", edgecolor="#c5d0de", lw=0.8)
                )
                continue
            ptype, iid = cell
            ax.add_patch(
                __rect(x, y, facecolor=PIECE_COLORS[ptype], edgecolor="#dfe7f0", lw=0.4)
            )
            ax.text(
                x + 0.5,
                y + 0.5,
                ptype,
                ha="center",
                va="center",
                fontsize=9,
                color="#102033",
                fontweight="bold",
            )

    for inst in env.stack:
        _outline_instance(ax, inst.cells)

    if title is None:
        title = f"Score {env.score}/100   {env.blanks} blank"
    ax.set_title(title, loc="left", fontsize=11, color="#1b365d", pad=8)


def __rect(x, y, facecolor, edgecolor, lw):
    from matplotlib.patches import Rectangle

    return Rectangle((x, y), 1, 1, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw)


def _outline_instance(ax, cells) -> None:
    cellset = set(cells)
    for x, y in cells:
        if (x, y - 1) not in cellset:
            ax.plot([x, x + 1], [y, y], color="#1b365d", lw=2.2, solid_capstyle="butt")
        if (x, y + 1) not in cellset:
            ax.plot([x, x + 1], [y + 1, y + 1], color="#1b365d", lw=2.2, solid_capstyle="butt")
        if (x - 1, y) not in cellset:
            ax.plot([x, x], [y, y + 1], color="#1b365d", lw=2.2, solid_capstyle="butt")
        if (x + 1, y) not in cellset:
            ax.plot([x + 1, x + 1], [y, y + 1], color="#1b365d", lw=2.2, solid_capstyle="butt")


def draw_catalogue(ax) -> None:
    ax.set_xlim(0, 4)
    ax.set_ylim(4, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Piece catalogue A–P", loc="left", fontsize=11, color="#1b365d")
    names = list(PIECES)
    for i, name in enumerate(names):
        gx, gy = i % 4, i // 4
        ox, oy = gx, gy
        ax.add_patch(__rect(ox, oy, facecolor="#ffffff", edgecolor="#d5deea", lw=0.6))
        cells = orientation(PIECES[name], 0)
        max_x = max(c[0] for c in cells)
        max_y = max(c[1] for c in cells)
        scale = 0.72 / max(max_x + 1, max_y + 1, 3)
        sx = ox + 0.14
        sy = oy + 0.18
        for cx, cy in cells:
            ax.add_patch(
                __rect_xy(
                    sx + cx * scale,
                    sy + cy * scale,
                    scale * 0.92,
                    scale * 0.92,
                    PIECE_COLORS[name],
                )
            )
        ax.text(ox + 0.88, oy + 0.14, name, fontsize=8, color="#1b365d", ha="right", va="top")


def __rect_xy(x, y, w, h, color):
    from matplotlib.patches import Rectangle

    return Rectangle((x, y), w, h, facecolor=color, edgecolor="#1b365d", linewidth=0.4)


def save_populated_canvas(env: "PackingEnv", path: Path, extra: str | None = None) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 6.2), gridspec_kw={"width_ratios": [1.15, 0.85]})
    fig.patch.set_facecolor("#eef3f9")
    title = f"Score {env.score}/100   {env.blanks} blank cells"
    if extra:
        title = f"{title}\n{extra}"
    draw_board(axes[0], env, title=title)
    draw_catalogue(axes[1])
    fig.suptitle("MGA  /  Expt-1: 10 × 10 Packing", fontsize=16, color="#1b365d", x=0.04, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
