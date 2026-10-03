"""Cumulative box manifest and Expt-8 vs 8B label/model identity audit."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from config import EXPT8_RESULT, EXPT8B_RESULT

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
EIGHT_B_HOLDOUT = (
    "inv_22521942205c",
    "inv_791d780fc6e4",
    "inv_115b41c2392a",
    "inv_5fc1ecabd17f",
    "inv_8b533a843808",
    "inv_bce49701ff81",
    "inv_ffe570c70457",
    "inv_1696d00e5191",
)
LABEL_BUDGET = "eval_cap - prefix_primitive_A"
CACHE_KEY = "(state_fingerprint, action_key, remaining_cap)"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _row_key(row: dict) -> tuple:
    return (
        str(row["seed"]),
        str(row["task_id"]),
        str(row["state_index"]),
        str(row["op_id"]),
        str(row.get("action_key") or ""),
        str(row.get("source") or ""),
    )


def load_csv(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def collect_box_uses() -> dict[str, list[str]]:
    uses: dict[str, list[str]] = defaultdict(list)
    skip = {".venv", "results", "__pycache__", "node_modules", "canvases"}
    for path in PARENT.rglob("*.json"):
        if skip.intersection(path.parts):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        tasks = payload.get("tasks") if isinstance(payload, dict) else None
        if not isinstance(tasks, list):
            continue
        rel = str(path.relative_to(PARENT)).replace("\\", "/")
        for task in tasks:
            if isinstance(task, dict) and task.get("task_id"):
                uses[str(task["task_id"])].append(rel)
    return dict(uses)


def compare_labels(old_rows: list[dict], new_rows: list[dict]) -> dict:
    old = {_row_key(r): r for r in old_rows}
    new = {_row_key(r): r for r in new_rows}
    common = set(old) & set(new)
    changed = []
    for key in common:
        y_old = float(old[key]["remaining_saving"])
        y_new = float(new[key]["remaining_saving"])
        if abs(y_old - y_new) > 1e-9:
            changed.append({"key": list(key), "y_expt8": y_old, "y_expt8b": y_new})
    return {
        "n_expt8": len(old_rows),
        "n_expt8b": len(new_rows),
        "n_common": len(common),
        "n_only_expt8": len(set(old) - set(new)),
        "n_only_expt8b": len(set(new) - set(old)),
        "n_y_changed": len(changed),
        "n_y_same": len(common) - len(changed),
        "examples_changed": changed[:8],
    }


def build_audit() -> dict:
    uses = collect_box_uses()
    e8 = PARENT / EXPT8_RESULT
    e8b = PARENT / EXPT8B_RESULT
    fit_cmp = compare_labels(load_csv(e8 / "labels_fit.csv"), load_csv(e8b / "labels_fit.csv"))
    val_cmp = compare_labels(load_csv(e8 / "labels_val.csv"), load_csv(e8b / "labels_val.csv"))
    holdout = []
    for task_id in EIGHT_B_HOLDOUT:
        holdout.append({"task_id": task_id, "prior_uses": uses.get(task_id, []), "fresh": False})
    n_1600_diff = 0
    for row in load_csv(e8b / "labels_fit.csv"):
        raw = row.get("saving_1600")
        if raw not in (None, "", "None") and abs(float(row["remaining_saving"]) - float(raw)) > 1e-9:
            n_1600_diff += 1
    return {
        "n_unique_boxes_in_data": len(uses),
        "expt8b_holdout_status": "development/reused evaluation, not unseen confirmation",
        "expt8b_holdout": holdout,
        "n_holdout_with_prior_use": sum(1 for h in holdout if h["prior_uses"]),
        "label_remaining_budget": LABEL_BUDGET,
        "cache_key": CACHE_KEY,
        "cache_includes_budget": True,
        "disk_label_cache": False,
        "expt8_used_pair_cap_for_remaining_pair": False,
        "expt8_remaining_pair_budget": LABEL_BUDGET,
        "fit_label_comparison": fit_cmp,
        "val_label_comparison": val_cmp,
        "labels_fit_sha256_expt8": file_sha(e8 / "labels_fit.csv") if (e8 / "labels_fit.csv").exists() else None,
        "labels_fit_sha256_expt8b": file_sha(e8b / "labels_fit.csv") if (e8b / "labels_fit.csv").exists() else None,
        "labels_val_sha256_expt8": file_sha(e8 / "labels_val.csv") if (e8 / "labels_val.csv").exists() else None,
        "labels_val_sha256_expt8b": file_sha(e8b / "labels_val.csv") if (e8b / "labels_val.csv").exists() else None,
        "n_fit_rows_where_1600_replay_differs": n_1600_diff,
        "matching_validation_numbers": (
            "Expt-8 and Expt-8B per-seed, frozen Expt-7, and weighted-model validation summaries match because "
            "Expt-8 remaining_pair already used eval_cap − prefix_A for both fit and val. pair_eval_cap was recorded "
            "but not used as the solve budget. File hashes differ because 8B added censoring and 1600-replay columns. "
            "Weighted models were rebuilt from those same y values. Unweighted models are new. Frozen Expt-7 is a "
            "historical comparator trained under pair_eval_cap=1600."
        ),
        "frozen_expt7_historical": True,
        "newly_fitted_need_serialized_identity": True,
        "box_uses": uses,
    }


def write_manifest(audit: dict, path: Path) -> None:
    rows = []
    for task_id, files in sorted((audit.get("box_uses") or {}).items()):
        rows.append({"task_id": task_id, "n_files": len(files), "files": "; ".join(files)})
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "n_files", "files"])
        writer.writeheader()
        writer.writerows(rows)
