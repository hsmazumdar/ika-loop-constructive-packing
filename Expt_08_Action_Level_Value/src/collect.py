"""Collect exact operation–placement remaining-solves. Libraries frozen. Diagnosis only."""

from __future__ import annotations

from action_features import action_vector, context_vector
from diagnostic import remaining_pair
from enumerate_ops import action_key, enumerate_legal
from miner import rotate_steps
from retrieval import first_legal_site, state_features
from snapshot import remaining_cap, restore_rng, run_primitive_snapshots
from solver import make_rng


def _rotation_of_site(op, site) -> int:
    first = tuple(sorted((x - min(c[0] for c in site[0]["cells"]), y - min(c[1] for c in site[0]["cells"])) for x, y in site[0]["cells"]))
    for k in range(4):
        turned = rotate_steps(op.steps, k)
        cells = [tuple(c) for c in turned[0]["cells"]]
        min_x = min(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        norm = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
        if norm == first:
            return k
    return 0


def collect_pair_actions(config, task, seed, box_index, bundle, k: int, placements_per_op: int, ledger: dict, cache: dict, split: str) -> list[dict]:
    prim = run_primitive_snapshots(config, task, seed, "expt8", box_index)
    ops = {op.op_id: op for op in bundle["memory"].active()}
    rows = []
    for snap in prim["snapshots"]:
        remaining = snap["env"].inventory.as_dict()
        posted, probes, checks = bundle["index"].query(remaining, snap["occupied"])
        ledger["index_probes"] = ledger.get("index_probes", 0) + probes
        ledger["compat_checks"] = ledger.get("compat_checks", 0) + checks
        shortlist = posted[: int(k)]
        feats = state_features(snap["env"])
        rng = make_rng(0, "x", "y", 0, "select")
        restore_rng(rng, snap["rng_state"])
        rem_cap = remaining_cap(int(config.eval_cap), snap["prefix_A"])
        pair_cap = min(rem_cap, int(config.pair_eval_cap))
        for entry in shortlist:
            op = ops.get(entry.op_id)
            if op is None:
                continue
            useful, score = (op.applicability.useful_here(feats) if op.applicability else (True, 0.0))
            site_rng = make_rng(seed, task["task_id"], "expt8", box_index, f"anchor-{snap['state_index']}-{op.op_id}")
            first_site, first_examined = first_legal_site(op, snap["env"], site_rng, config.anchors)
            enum = enumerate_legal(op, snap["env"], int(placements_per_op))
            ledger["enum_examined"] = ledger.get("enum_examined", 0) + int(enum["examined"])
            chosen = []
            seen = set()
            if first_site is not None:
                akey = action_key(first_site)
                chosen.append(
                    {
                        "site": first_site,
                        "action_key": akey,
                        "examined": first_examined,
                        "source": "first_legal_site",
                        "rotation": _rotation_of_site(op, first_site),
                    }
                )
                seen.add(akey)
            for rec in enum["placements"]:
                if rec["action_key"] in seen:
                    continue
                if len(chosen) >= int(placements_per_op):
                    break
                chosen.append(
                    {
                        "site": rec["site"],
                        "action_key": rec["action_key"],
                        "examined": 1,
                        "source": "enumerate_legal",
                        "rotation": int(rec["rotation"]),
                    }
                )
                seen.add(rec["action_key"])
            for item in chosen:
                site = item["site"]
                akey = item["action_key"]
                cache_key = (snap["fingerprint"], akey, rem_cap)
                if cache_key in cache:
                    ledger["cache_hits"] = ledger.get("cache_hits", 0) + 1
                    outcome = dict(cache[cache_key])
                    outcome["cache_hit"] = True
                else:
                    skip, commit, ok, n_internal = remaining_pair(config, snap["env"], rng, set(snap["tabu"]), site, rem_cap)
                    ledger["commit_rollouts"] = ledger.get("commit_rollouts", 0) + 1
                    ledger["skip_rollouts"] = ledger.get("skip_rollouts", 0) + 1
                    if ok:
                        ledger["skip_A"] = ledger.get("skip_A", 0) + int(skip["A"])
                        ledger["commit_A"] = ledger.get("commit_A", 0) + int(commit["A"])
                        remaining_saving = skip["A"] - commit["A"]
                        quality_ok = commit["Q"] >= skip["Q"] - config.quality_loss_margin
                        outcome = {
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
                            "pair_cap": pair_cap,
                            "remaining_cap": rem_cap,
                        }
                    else:
                        outcome = {
                            "ok": False,
                            "beneficial_free": False,
                            "quality_ok": False,
                            "remaining_saving": None,
                            "cache_hit": False,
                            "pair_cap": pair_cap,
                            "remaining_cap": rem_cap,
                        }
                    cache[cache_key] = {k: v for k, v in outcome.items() if k != "cache_hit"}
                if not outcome.get("ok"):
                    continue
                ctx = context_vector(snap["occupied"], remaining, snap["actions_used"], snap["undos"], op, score, entry.area)
                avec, feat_checks = action_vector(
                    snap["occupied"], remaining, snap["actions_used"], snap["undos"], op, score, entry.area, site, snap["env"], item["rotation"]
                )
                ledger["feature_checks"] = ledger.get("feature_checks", 0) + feat_checks
                rows.append(
                    {
                        "seed": seed,
                        "task_id": task["task_id"],
                        "split": split,
                        "state_index": snap["state_index"],
                        "occupied": snap["occupied"],
                        "prefix_A": snap["prefix_A"],
                        "op_id": op.op_id,
                        "definition_hash": entry.definition_hash,
                        "action_key": akey,
                        "source": item["source"],
                        "rotation": item["rotation"],
                        "examined": item["examined"],
                        "context_vector": ctx,
                        "action_vector": avec,
                        "feature_checks": feat_checks,
                        "remaining_saving": outcome["remaining_saving"],
                        "quality_ok": outcome["quality_ok"],
                        "beneficial_free": outcome["beneficial_free"],
                        "A_skip": outcome["A_skip"],
                        "A_commit": outcome["A_commit"],
                        "Q_skip": outcome["Q_skip"],
                        "Q_commit": outcome["Q_commit"],
                        "remaining_cap": rem_cap,
                        "pair_cap": pair_cap,
                        "diagnosis_only": True,
                    }
                )
    return rows
