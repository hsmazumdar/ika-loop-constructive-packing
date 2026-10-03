"""Mine the three libraries from the training corpus prefix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mga3.corpus import chronological, prefix_by_tasks  # noqa: E402
from mga3.experiment import load_config, load_split  # noqa: E402
from mga3.mining import build_libraries, library_document  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(Path(args.config))
    order = [task["task_id"] for task in load_split("train")]
    path = ROOT / "data" / "corpus" / "solutions.jsonl"
    solutions = chronological(
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()],
        order,
    )
    n_valid = max(1, len(order) // 4)
    valid = set(order[-n_valid:])
    prefix = prefix_by_tasks(solutions, order, len(order))
    mined = build_libraries(prefix, config, valid)
    out = ROOT / "data" / "libraries"
    out.mkdir(parents=True, exist_ok=True)
    for name, ops in mined["libraries"].items():
        (out / f"{name}.json").write_text(
            json.dumps(library_document(name, ops, {"pool_ops": mined["pool_ops"]}), indent=2),
            encoding="utf-8",
        )
    (out / "rejections.json").write_text(
        json.dumps({"rejections": mined["rejections"], "mismatches": mined["mismatches"], "bytes": mined["bytes"], "neutral_rectangles": mined["neutral_rectangles"]}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "OK",
        "pool": mined["pool_ops"],
        "counts": {name: len(ops) for name, ops in mined["libraries"].items()},
        "neutral_rectangles": mined["neutral_rectangles"],
    }))


if __name__ == "__main__":
    main()
