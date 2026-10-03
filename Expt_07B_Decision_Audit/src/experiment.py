"""Load frozen Expt-7 artifacts and run the decision audit. No ranker/library updates."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from audit import solve_primitive_traced, solve_ranked_audit
from config import Config, EXPT7_RESULT
from diagnostic import remaining_pair
from enumerate_ops import action_key
from index import LibraryIndex
from library_io import library_hash, memory_from_json
from ranker import LinearRegressor, QualityModel
from reconstruct import file_sha, load_gates
from retrieval import first_legal_site
from snapshot import remaining_cap, restore_rng, run_primitive_snapshots
from solver import make_rng


def expt7_dir() -> Path:
    return ROOT.parent / Path(EXPT7_RESULT)


def load_split_eval() -> list[dict]:
    path = ROOT / "data" / "eval.json"
    if not path.exists():
        path = ROOT.parent / "Expt_07_Indexed_Retrieval" / "data" / "eval.json"
    return list(json.loads(path.read_text(encoding="utf-8"))["tasks"])


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    serialised = []
    for row in rows:
        copied = dict(row)
        for key, value in list(copied.items()):
            if isinstance(value, (list, dict)):
                copied[key] = json.dumps(value)
        serialised.append(copied)
    fields = []
    for row in serialised:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in serialised:
            writer.writerow({key: row.get(key) for key in fields})


def load_artifacts(config: Config, seeds: tuple[int, ...]) -> list[dict]:
    run = expt7_dir()
    bundles = []
    for seed in seeds:
        lib_path = run / f"library_seed{seed}.json"
        payload = json.loads(lib_path.read_text(encoding="utf-8"))
        memory = memory_from_json(payload, config)
        consult, commit, gate_sha = load_gates(int(seed))
        ranker = json.loads((run / f"ranker_seed{seed}.json").read_text(encoding="utf-8"))
        benefit = LinearRegressor.from_dict(ranker["benefit"])
        quality = QualityModel.from_dict(ranker["quality"])
        index = LibraryIndex(memory)
        bundles.append(
            {
                "seed": int(seed),
                "memory": memory,
                "index": index,
                "consult_gate": consult,
                "commit_gate": commit,
                "benefit": benefit,
                "quality": quality,
                "library_hash": payload["library_hash"],
                "library_file_sha256": file_sha(lib_path),
                "ranker_file_sha256": file_sha(run / f"ranker_seed{seed}.json"),
                "gate_file_sha256": gate_sha,
                "n_active": len(memory.active()),
            }
        )
        if library_hash(memory) != payload["library_hash"]:
            raise RuntimeError(f"library hash drifted seed {seed}")
        if not benefit.frozen or not quality.frozen:
            raise RuntimeError(f"ranker was not frozen seed {seed}")
    return bundles


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def load_expt7_eval() -> dict[tuple, dict]:
    path = expt7_dir() / "eval.csv"
    keyed = {}
    if not path.exists():
        return keyed
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            keyed[(int(row["seed"]), row["task_id"], row["condition"])] = row
    return keyed


def load_expt7_recall_states() -> list[dict]:
    path = expt7_dir() / "recall_states.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def op_and_action_recall_from_rows(op_state_rows: list[dict], action_rows: list[dict]) -> dict:
    """op_state_rows: frozen Expt-7 recall_states. action_rows: first_legal remaining-solves."""
    n_op = len(op_state_rows)
    n_op_hit = sum(1 for r in op_state_rows if _truthy(r.get("shortlist_hit")))
    by_state = defaultdict(list)
    for row in action_rows:
        by_state[(str(row["seed"]), str(row["task_id"]), str(row["state_index"]))].append(row)
    n_action_hit = 0
    n_with_site = 0
    for rec in op_state_rows:
        key = (str(rec["seed"]), str(rec["task_id"]), str(rec["state_index"]))
        items = by_state.get(key, [])
        if any(r.get("placement_found") for r in items):
            n_with_site += 1
        if any(_truthy(r.get("beneficial_free")) for r in items):
            n_action_hit += 1
    return {
        "n_oracle_useful_states": n_op,
        "op_recall_hits": n_op_hit,
        "action_recall_hits": n_action_hit,
        "n_states_with_first_legal_site": n_with_site,
    }


def oracle_first_legal_action_recall(config, task, seed, box_index, bundle, k: int, useful_states: set[int], diagnostic_ledger: dict, replay_cache: dict) -> list[dict]:
    """Diagnosis only. first_legal_site remaining-solves on the same occupancy-schedule snapshots as Expt-7 recall (phase expt6)."""
    if not useful_states or not config.collect_counterfactuals:
        return []
    prim = run_primitive_snapshots(config, task, seed, "expt6", box_index)
    ops = {op.op_id: op for op in bundle["memory"].active()}
    rows = []
    for snap in prim["snapshots"]:
        if int(snap["state_index"]) not in useful_states:
            continue
        remaining = snap["env"].inventory.as_dict()
        posted, _probes, _checks = bundle["index"].query(remaining, snap["occupied"])
        shortlist = posted[: int(k)]
        rng = make_rng(0, "x", "y", 0, "select")
        restore_rng(rng, snap["rng_state"])
        rem_cap = remaining_cap(int(config.eval_cap), snap["prefix_A"])
        for entry in shortlist:
            op = ops.get(entry.op_id)
            if op is None:
                continue
            site_rng = make_rng(seed, task["task_id"], "expt6", box_index, f"audit-first-legal-{snap['state_index']}-{op.op_id}")
            site, examined = first_legal_site(op, snap["env"], site_rng, config.anchors)
            akey = action_key(site) if site is not None else None
            rec = {
                "seed": seed,
                "task_id": task["task_id"],
                "state_index": snap["state_index"],
                "occupied": snap["occupied"],
                "op_id": op.op_id,
                "definition_hash": entry.definition_hash,
                "action_key": akey,
                "placement_found": site is not None,
                "placement_examined": examined,
                "diagnosis_only": True,
                "note": "oracle-snapshot first_legal_site; not the deployed expt7 RNG",
            }
            if site is None:
                rec.update({"ok": False, "beneficial_free": False, "quality_ok": False, "remaining_saving": None})
            else:
                cache_key = (snap["fingerprint"], akey, rem_cap)
                if cache_key in replay_cache:
                    diagnostic_ledger["cache_hits"] = diagnostic_ledger.get("cache_hits", 0) + 1
                    rec.update(replay_cache[cache_key])
                    rec["cache_hit"] = True
                else:
                    skip, commit, ok, n_internal = remaining_pair(config, snap["env"], rng, set(snap["tabu"]), site, rem_cap)
                    diagnostic_ledger["commit_rollouts"] = diagnostic_ledger.get("commit_rollouts", 0) + 1
                    diagnostic_ledger["skip_rollouts"] = diagnostic_ledger.get("skip_rollouts", 0) + 1
                    if ok:
                        diagnostic_ledger["skip_A"] = diagnostic_ledger.get("skip_A", 0) + int(skip["A"])
                        diagnostic_ledger["commit_A"] = diagnostic_ledger.get("commit_A", 0) + int(commit["A"])
                        remaining_saving = skip["A"] - commit["A"]
                        quality_ok = commit["Q"] >= skip["Q"] - config.quality_loss_margin
                        payload = {
                            "ok": True,
                            "A_skip": skip["A"],
                            "A_commit": commit["A"],
                            "remaining_saving": remaining_saving,
                            "Q_skip": skip["Q"],
                            "Q_commit": commit["Q"],
                            "quality_ok": quality_ok,
                            "beneficial_free": quality_ok and remaining_saving > 0,
                            "internal_execution": n_internal,
                            "cache_hit": False,
                        }
                    else:
                        payload = {"ok": False, "beneficial_free": False, "quality_ok": False, "remaining_saving": None, "cache_hit": False}
                    replay_cache[cache_key] = payload
                    rec.update(payload)
            rows.append(rec)
    return rows


def run_audit(config: Config, tasks: list[dict], bundles: list[dict]) -> dict:
    box_rows = []
    decision_rows = []
    ranker_rows = []
    cf_rows = []
    recall_rows = []
    oracle_action_rows = []
    ledger = {"skip_A": 0, "commit_A": 0, "skip_rollouts": 0, "commit_rollouts": 0, "cache_hits": 0}
    cache: dict = {}
    oracle_cache: dict = {}
    k = int(config.k_shortlist)
    budget = int(config.consult_budget)
    frozen_eval = load_expt7_eval()
    frozen_recall = load_expt7_recall_states()
    recall_by_pair = defaultdict(list)
    for row in frozen_recall:
        recall_by_pair[(int(row["seed"]), row["task_id"])].append(row)
    collect_cf = bool(config.collect_counterfactuals)
    for bundle in bundles:
        for index, task in enumerate(tasks):
            print(f"audit seed={bundle['seed']} box={index + 1}/{len(tasks)} {task['task_id']}", flush=True)
            prim = solve_primitive_traced(config, task, int(bundle["seed"]), "expt7", index)
            ranked = solve_ranked_audit(
                config,
                task,
                int(bundle["seed"]),
                "expt7",
                index,
                bundle["memory"],
                bundle["index"],
                bundle["benefit"],
                bundle["quality"],
                k,
                budget,
                ledger,
                cache,
                collect_counterfactuals=collect_cf,
            )
            zero = solve_ranked_audit(
                config,
                task,
                int(bundle["seed"]),
                "expt7",
                index,
                bundle["memory"],
                bundle["index"],
                bundle["benefit"],
                bundle["quality"],
                k,
                0,
                {"skip_A": 0, "commit_A": 0, "skip_rollouts": 0, "commit_rollouts": 0, "cache_hits": 0},
                {},
                collect_counterfactuals=False,
            )
            n_admit = sum(1 for r in ranked["ranker_rows"] if r["ranker_admit"])
            n_reject = sum(1 for r in ranked["ranker_rows"] if not r["ranker_admit"])
            n_commit = ranked["n_commitments"]
            trace_match = ranked["primitive_trace"] == prim["primitive_trace"]
            frozen_ranked = frozen_eval.get((int(bundle["seed"]), task["task_id"], "indexed_ranked"), {})
            frozen_prim = frozen_eval.get((int(bundle["seed"]), task["task_id"], "primitive"), {})
            pair_recall = recall_by_pair.get((int(bundle["seed"]), task["task_id"]), [])
            useful_states = {int(r["state_index"]) for r in pair_recall if _truthy(r.get("shortlist_hit")) or int(float(r.get("n_beneficial_ops") or 0)) > 0}
            oracle_actions = oracle_first_legal_action_recall(
                config, task, int(bundle["seed"]), index, bundle, k, useful_states, ledger, oracle_cache
            )
            oracle_action_rows.extend(oracle_actions)
            summary = op_and_action_recall_from_rows(pair_recall, oracle_actions)
            recall_rows.append(
                {
                    "seed": bundle["seed"],
                    "task_id": task["task_id"],
                    "n_oracle_useful_states": summary["n_oracle_useful_states"],
                    "op_recall_hits": summary["op_recall_hits"],
                    "action_recall_hits": summary["action_recall_hits"],
                    "n_states_with_first_legal_site": summary["n_states_with_first_legal_site"],
                    "diagnosis_only": True,
                    "note": "170/170 in Expt-7 was operation recall on primitive snapshots, not action recall and not the deployed trajectory.",
                }
            )
            box_rows.append(
                {
                    "seed": bundle["seed"],
                    "task_id": task["task_id"],
                    "library_hash": bundle["library_hash"],
                    "Q_primitive": prim["Q"],
                    "A_primitive": prim["A"],
                    "Q_ranked": ranked["Q"],
                    "A_ranked": ranked["A"],
                    "consultation_ranked": ranked["consultation_cost"],
                    "index_cost": ranked["index_cost"],
                    "ranking_cost": ranked["ranking_cost"],
                    "applicability_cost": ranked["applicability_cost"],
                    "learned_evals": ranked["learned_evals"],
                    "primitive_evals_ranked": ranked["primitive_evals"],
                    "A_minus_primitive": ranked["A"] - prim["A"],
                    "consultation_equals_gap": abs((ranked["A"] - prim["A"]) - ranked["consultation_cost"]) < 1e-9
                    if ranked["primitive_evals"] == prim["A"]
                    else False,
                    "primitive_evals_match": ranked["primitive_evals"] == prim["A"],
                    "Q_match": ranked["Q"] == prim["Q"],
                    "trace_match": trace_match,
                    "consult_attempts": ranked["consult_attempts"],
                    "n_commitments": n_commit,
                    "n_ranker_admit": n_admit,
                    "n_ranker_reject": n_reject,
                    "first_budget_exhaustion_step": ranked["first_budget_exhaustion_step"],
                    "A_budget0": zero["A"],
                    "Q_budget0": zero["Q"],
                    "budget0_trace_match": zero["primitive_trace"] == prim["primitive_trace"],
                    "A_identity_ok": ranked["A_identity_ok"],
                    "termination_primitive": prim["termination"],
                    "termination_ranked": ranked["termination"],
                    "A_expt7_ranked": float(frozen_ranked["A"]) if frozen_ranked else None,
                    "A_matches_expt7_ranked": abs(ranked["A"] - float(frozen_ranked["A"])) < 1e-9 if frozen_ranked else None,
                    "A_expt7_primitive": float(frozen_prim["A"]) if frozen_prim else None,
                }
            )
            for rec in ranked["decisions"]:
                decision_rows.append(
                    {
                        "seed": bundle["seed"],
                        "task_id": task["task_id"],
                        "step": rec["step"],
                        "occupied": rec["occupied"],
                        "consulted": rec["consulted"],
                        "budget_exhausted": rec["budget_exhausted"],
                        "budget_remaining": rec["budget_remaining"],
                        "consult_A_before": rec["consult_A_before"],
                        "committed": rec["committed"],
                        "shortlist": rec.get("shortlist") or [],
                        "committed_op_id": rec.get("committed_op_id"),
                        "primitive_token": rec.get("primitive_token"),
                        "fingerprint": rec.get("fingerprint"),
                    }
                )
            ranker_rows.extend(ranked["ranker_rows"])
            cf_rows.extend(ranked["counterfactuals"])
    return {
        "box_rows": box_rows,
        "decision_rows": decision_rows,
        "ranker_rows": ranker_rows,
        "counterfactuals": cf_rows,
        "recall_rows": recall_rows,
        "oracle_action_rows": oracle_action_rows,
        "ledger": ledger,
    }
