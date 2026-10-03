"""State- and box-level frozen-gate misses. Candidate counts overcount placements."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results" / "20260929_214518_diagnostic"


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def analyze() -> dict:
    cand_path = RUN / "candidate_replays.csv"
    rows = list(csv.DictReader(cand_path.open(encoding="utf-8")))
    beneficial = [r for r in rows if _truthy(r.get("beneficial_free"))]
    by_state: dict[tuple, list[dict]] = defaultdict(list)
    by_box: dict[tuple, list[dict]] = defaultdict(list)
    by_state_op: dict[tuple, list[dict]] = defaultdict(list)
    for row in beneficial:
        sk = (row["seed"], row["task_id"], row["library_hash"], row["state_index"])
        bk = (row["seed"], row["task_id"], row["library_hash"])
        ok = sk + (row["op_id"], row["definition_hash"])
        by_state[sk].append(row)
        by_box[bk].append(row)
        by_state_op[ok].append(row)

    def any_select(items: list[dict]) -> bool:
        return any(_truthy(r.get("gate_would_select")) for r in items)

    n_states = len(by_state)
    n_states_all_rejected = sum(1 for items in by_state.values() if not any_select(items))
    n_states_any_admitted = n_states - n_states_all_rejected
    n_boxes = len(by_box)
    n_boxes_all_rejected = sum(1 for items in by_box.values() if not any_select(items))
    n_boxes_any_admitted = n_boxes - n_boxes_all_rejected

    n_states_consult_closed = 0
    n_states_consult_open_commit_all_reject = 0
    for items in by_state.values():
        consult = any(_truthy(r.get("consult_gate_would_admit")) for r in items)
        commit_any = any(_truthy(r.get("commit_gate_would_admit")) for r in items)
        if not consult:
            n_states_consult_closed += 1
        elif not commit_any:
            n_states_consult_open_commit_all_reject += 1

    n_ops = len(by_state_op)
    n_ops_all_rejected = sum(1 for items in by_state_op.values() if not any_select(items))

    out = {
        "n_beneficial_candidates": len(beneficial),
        "n_gate_would_select": sum(1 for r in beneficial if _truthy(r.get("gate_would_select"))),
        "n_gate_would_miss": sum(1 for r in beneficial if not _truthy(r.get("gate_would_select"))),
        "n_states_with_beneficial": n_states,
        "n_states_any_beneficial_admitted": n_states_any_admitted,
        "n_states_every_beneficial_rejected": n_states_all_rejected,
        "frac_states_every_beneficial_rejected": None if not n_states else n_states_all_rejected / n_states,
        "n_states_consult_would_not_look": n_states_consult_closed,
        "n_states_consult_open_but_commit_rejects_all_ops": n_states_consult_open_commit_all_reject,
        "n_boxes_with_beneficial": n_boxes,
        "n_boxes_any_beneficial_admitted": n_boxes_any_admitted,
        "n_boxes_every_beneficial_rejected": n_boxes_all_rejected,
        "frac_boxes_every_beneficial_rejected": None if not n_boxes else n_boxes_all_rejected / n_boxes,
        "n_state_op_with_beneficial": n_ops,
        "n_state_op_every_placement_rejected": n_ops_all_rejected,
        "note": (
            "A state/box 'every beneficial rejected' means no beneficial_free candidate has gate_would_select. "
            "Consult is a state decision; commit is per operation. Candidate counts overcount placements of the same op."
        ),
    }
    (RUN / "gate_miss_levels.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    analyze()
