"""Replay figures from logged events. Manual play is not a scientific run."""

from __future__ import annotations

import json
from pathlib import Path

from mga3.pieces import PIECE_COLORS


def _paint(ax, placements: list[dict], title: str, highlight: set[tuple[int, int]] | None = None) -> None:
    import matplotlib.pyplot as plt

    ax.set_xlim(0, 10)
    ax.set_ylim(10, 0)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=9)
    ax.set_xticks(range(11))
    ax.set_yticks(range(11))
    ax.grid(True, color="#dddddd")
    highlight = highlight or set()
    for placement in placements:
        color = PIECE_COLORS.get(placement["type"], "#888888")
        cells = [tuple(c) for c in placement["cells"]]
        for x, y in cells:
            edge = "black" if (x, y) in highlight else color
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=color, edgecolor=edge, linewidth=1.5))
        if cells:
            cx = sum(x for x, _ in cells) / len(cells)
            cy = sum(y for _, y in cells) / len(cells)
            ax.text(cx + 0.5, cy + 0.5, placement["type"], ha="center", va="center", fontsize=7, color="black")


def _load_traces(run_dir: Path) -> list[dict]:
    path = run_dir / "traces.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_replay_snapshot(run_dir: Path, solutions: list[dict], mined_by_size: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    traces = _load_traces(run_dir)
    transfer = None
    rejected = None
    for trace in traces:
        row = trace["row"]
        if str(row.get("phase")) != "heldout":
            continue
        if transfer is None and int(row.get("macros_completed", 0)) > 0:
            transfer = trace
        if rejected is None and int(row.get("library_ops", 0)) > 0 and int(row.get("macros_completed", 0)) == 0:
            rejected = trace
    example = None
    for mined in mined_by_size.values():
        for ops in mined["libraries"].values():
            if ops:
                example = ops[0]
                break
        if example:
            break
    figure, axes = plt.subplots(1, 3, figsize=(12, 4))
    if example and example.get("example"):
        placed = example["example"]["placements"]
        cells = {tuple(c) for placement in placed for c in placement["cells"]}
        _paint(axes[0], placed, f"source {example['example']['task_id']}\n{example['op_id']} rect={example['rectangular']}", cells)
    else:
        axes[0].set_title("no admitted operation")
    if transfer is not None:
        _paint(axes[1], transfer.get("placements", []), f"transfer {transfer['row']['arm']}\nQ={transfer['row']['Q']} P={transfer['row']['P']}")
    else:
        axes[1].set_title("no completed macro on held-out")
    if rejected is not None:
        _paint(axes[2], rejected.get("placements", []), f"no completed macro\n{rejected['row']['arm']} Q={rejected['row']['Q']}")
    else:
        axes[2].set_title("no rejected-retrieval episode")
    figure.suptitle("Logged boards. This figure does not claim that rectangles are always best.")
    figure.tight_layout()
    figure.savefig(run_dir / "replay_snapshot.png", dpi=120)
    plt.close(figure)
    (run_dir / "replay_transfer.json").write_text(json.dumps(transfer, indent=2), encoding="utf-8")
    (run_dir / "replay_rejected.json").write_text(json.dumps(rejected, indent=2), encoding="utf-8")
    if solutions:
        (run_dir / "corpus_index.json").write_text(
            json.dumps(
                [{"solution_id": s["solution_id"], "task_id": s["task_id"], "Q": s["Q"], "solver": s["solver"]} for s in solutions],
                indent=2,
            ),
            encoding="utf-8",
        )


def show_replay(path: Path) -> None:
    """Interactive window. Scientific numbers stay in the logged JSON."""
    import matplotlib.pyplot as plt

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload:
        raise SystemExit(f"no replay payload in {path}")
    figure, ax = plt.subplots(figsize=(5, 5))
    row = payload.get("row", {})
    _paint(
        ax,
        payload.get("placements", []),
        f"{row.get('arm', '')} {row.get('task_id', '')} Q={row.get('Q')} P={row.get('P')}",
    )
    figure.tight_layout()
    plt.show()
