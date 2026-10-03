"""Independent witness check. The agent package does not import this tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mga2.environment import Action, PackingEnv  # noqa: E402
from mga2.inventory import Inventory  # noqa: E402
from mga2.pieces import N_CELLS, PIECE_TYPES, piece_area  # noqa: E402


def validate(manifest_path: Path) -> dict:
    root = manifest_path.parents[1] if manifest_path.parent.name == "runtime" else ROOT
    # data/runtime/manifest.json -> parents[1] is data, so use known root.
    root = ROOT
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    seen = {}
    for split, ids in manifest.get("splits", {}).items():
        payload = json.loads((root / "data" / "runtime" / f"{split}.json").read_text(encoding="utf-8"))
        by_id = {t["task_id"]: t for t in payload["tasks"]}
        if "placements" in json.dumps(payload):
            errors.append(f"{split} runtime file contains placements")
        for task_id in ids:
            if task_id not in by_id:
                errors.append(f"missing runtime task {task_id}")
                continue
            task = by_id[task_id]
            witness_path = root / "validation_only" / "witnesses" / f"{task_id}.json"
            if not witness_path.exists():
                errors.append(f"missing witness {task_id}")
                continue
            witness = json.loads(witness_path.read_text(encoding="utf-8"))
            inv = task["inventory"]
            key = tuple(int(inv.get(t, 0)) for t in PIECE_TYPES)
            if key in seen:
                errors.append(f"duplicate inventory {task_id} and {seen[key]}")
            else:
                seen[key] = task_id
            area = sum(int(inv.get(t, 0)) * piece_area(t) for t in PIECE_TYPES)
            if area != N_CELLS:
                errors.append(f"{task_id} area {area}")
            env = PackingEnv(budget=max(10, len(witness["placements"]) + 2), inventory=Inventory(inv))
            for rec in witness["placements"]:
                result = env.step(Action.place(rec["type"], rec["rotation"], rec["x"], rec["y"]))
                if not result.accepted:
                    errors.append(f"{task_id} rejected {rec} ({result.reason})")
                    break
            else:
                if env.score != N_CELLS or not env.terminal:
                    errors.append(f"{task_id} score {env.score} terminal {env.terminal}")
                if any(env.inventory.counts.get(t, 0) != 0 for t in PIECE_TYPES):
                    errors.append(f"{task_id} inventory not empty")
    # Splits are disjoint by construction if no duplicate keys and ids are unique.
    all_ids = [i for ids in manifest.get("splits", {}).values() for i in ids]
    if len(all_ids) != len(set(all_ids)):
        errors.append("task ids repeat across splits")
    status = "OK" if not errors else "FAIL"
    return {"status": status, "errors": errors, "tasks": len(all_ids)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    report = validate(Path(args.manifest))
    print(json.dumps(report))
    if report["status"] != "OK":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
