"""Build the training corpus. Refuses development and held-out task ids."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mga3.corpus import build_corpus  # noqa: E402
from mga3.experiment import load_config, load_split  # noqa: E402
from mga3.hardware import PlacementWorkspace  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(Path(args.config))
    train = load_split("train")
    train_ids = {task["task_id"] for task in train}
    workspace = PlacementWorkspace(config.get("device", "cuda"))
    solutions, cost = build_corpus(train, config, workspace, train_ids)
    out = ROOT / "data" / "corpus"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "solutions.jsonl").open("w", encoding="utf-8") as handle:
        for solution in solutions:
            handle.write(json.dumps(solution) + "\n")
    manifest = {
        "solutions": len(solutions),
        "tasks": len({s["task_id"] for s in solutions}),
        "cost": cost,
        "device": workspace.device_name(),
        "cuda_bytes": workspace.memory_bytes(),
        "note": "Teacher experience only. Held-out witnesses were not read.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "teacher_cost.json").write_text(json.dumps(cost, indent=2), encoding="utf-8")
    print(json.dumps({"status": "OK", "solutions": len(solutions), "tasks": manifest["tasks"]}))


if __name__ == "__main__":
    main()
