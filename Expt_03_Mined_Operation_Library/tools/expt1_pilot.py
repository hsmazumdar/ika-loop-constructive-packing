"""Exploratory pilot on Expt-1 unlimited-piece traces.

These boxes are not inventory-constrained. The pilot only asks how often a
connected pair from a high-scoring trace has a piece multiset that some
Expt-2 training inventory can supply. It does not enter the main libraries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from mga3.environment import Action, ActionKind, PackingEnv  # noqa: E402
from mga3.inventory import Inventory  # noqa: E402
from mga3.mining import enumerate_groups  # noqa: E402


def _final_placements(trace: list[dict]) -> tuple[int, list[dict]]:
    env = PackingEnv(budget=120, inventory=Inventory(None))
    for record in trace:
        action = record["action"]
        kind = ActionKind(action["kind"])
        if kind is ActionKind.PLACE:
            env.step(Action.place(action["piece_type"], action["rotation"], action["x"], action["y"]))
        elif kind is ActionKind.UNDO:
            env.step(Action.undo())
        else:
            env.step(Action.submit())
        if env.terminal and env.termination_reason == "action_limit":
            break
    return env.score, env.snapshot_placements()


def main() -> None:
    trace_path = REPO / "Expt_01_10x10_Packing" / "results" / "20260928_180809_smoke" / "action_trace.jsonl"
    train = json.loads((ROOT / "data" / "runtime" / "train.json").read_text(encoding="utf-8"))["tasks"]
    inventories = [task["inventory"] for task in train]
    kept = []
    seen = 0
    with trace_path.open(encoding="utf-8") as handle:
        for line in handle:
            seen += 1
            if seen > 12:
                break
            episode = json.loads(line)
            score, placements = _final_placements(episode["trace"])
            if score >= 80 and len(placements) >= 2:
                kept.append({
                    "task_id": f"expt1_{episode['mode']}_{episode['seed']}_{episode['episode']}",
                    "solution_id": f"pilot_{seen}",
                    "placements": placements,
                    "Q": score,
                })
            if len(kept) >= 4:
                break
    groups = enumerate_groups(kept, window=6) if kept else []
    fit = 0
    for group in groups:
        demand = group["demand"]
        if any(Inventory(inv).fits_multiset(demand) for inv in inventories):
            fit += 1
    report = {
        "source": str(trace_path),
        "episodes_scanned": seen,
        "boards_q_at_least_80": len(kept),
        "connected_groups": len(groups),
        "groups_whose_multiset_fits_some_training_inventory": fit,
        "fit_rate": (fit / len(groups)) if groups else None,
        "note": "Unlimited-piece Expt-1 traces. Not used for the held-out comparison.",
    }
    out = ROOT / "data" / "expt1_pilot.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
