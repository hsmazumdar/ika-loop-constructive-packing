"""Open a logged replay. Add --snapshot to write a PNG without a window."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mga3.experiment import EXPT_ROOT  # noqa: E402
from mga3.gui import show_replay  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", required=True)
    parser.add_argument("--snapshot", default=None)
    args = parser.parse_args()
    path = Path(args.replay)
    if not path.is_absolute():
        path = EXPT_ROOT / path
    if args.snapshot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from mga3.gui import _paint
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        figure, ax = plt.subplots(figsize=(5, 5))
        row = (payload or {}).get("row", {})
        _paint(ax, (payload or {}).get("placements", []), f"Q={row.get('Q')} P={row.get('P')} {row.get('arm', '')}")
        figure.tight_layout()
        figure.savefig(args.snapshot, dpi=120)
        plt.close(figure)
        print(args.snapshot)
        return
    show_replay(path)


if __name__ == "__main__":
    main()
