"""Collect exact operation–placement remaining-solves under one remaining-budget definition."""

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


def _cap_hit(result: dict, cap: int) -> bool:
    return str(result.get("termination") or "") == "eval_cap" or int(result.get("A") or 0) >= int(cap)


def _solve_pair(config, env, rng, tabu, site, cap, ledger, cache, fingerprint, akey) -> dict:
    cache_key = (fingerprint, akey, int(cap))
    if cache_key in cache:
        ledger["cache_hits"] = ledger.get("cache_hits", 0) + 1
        copied = dict(cache[cache_key])
        copied["cache_hit"] = True
        return copied
    skip, commit, ok, n_internal = remaining_pair(config, env, rng, tabu, site, cap)
    ledger["commit_rollouts"] = ledger.get("commit_rollouts", 0) + 1
    ledger["skip_rollouts"] = ledger.get("skip_rollouts", 0) + 1
    if not ok:
        payload = {"ok": False, "cache_hit": False}
        cache[cache_key] = {"ok": False}
        return payload
    ledger["skip_A"] = ledger.get("skip_A", 0) + int(skip["A"])
    ledger["commit_A"] = ledger.get("commit_A", 0) + int(commit["A"])
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
        "skip_termination": skip["termination"],
        "commit_termination": commit["termination"],
        "skip_cap_hit": _cap_hit(skip, cap),
        "commit_cap_hit": _cap_hit(commit, cap),
        "cache_hit": False,
        "cap": int(cap),
    }
    cache[cache_key] = {k: v for k, v in payload.items() if k != "cache_hit"}
    return payload


def collect_pair_actions(config, task, seed, box_index, bundle, k: int, placements_per_op: int, ledger: dict, cache: dict, split: str, phase: str = "expt8") -> list[dict]:
    """Labels use remaining_cap = eval_cap - prefix_A. Optional 1600-cap replay is diagnosis of the Expt-8 mismatch."""
    prim = run_primitive_snapshots(config, task, seed, phase, box_index)
    ops = {op.op_id: op for op in bundle["memory"].active()}
    rows = []
    replay = bool(getattr(config, "replay_pair_cap", True))
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
            _useful, score = (op.applicability.useful_here(feats) if op.applicability else (True, 0.0))
            site_rng = make_rng(seed, task["task_id"], phase, box_index, f"anchor-{snap['state_index']}-{op.op_id}")
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
                full = _solve_pair(config, snap["env"], rng, set(snap["tabu"]), site, rem_cap, ledger, cache, snap["fingerprint"], akey)
                if not full.get("ok"):
                    continue
                truncated = None
                if replay and pair_cap != rem_cap:
                    truncated = _solve_pair(config, snap["env"], rng, set(snap["tabu"]), site, pair_cap, ledger, cache, snap["fingerprint"], akey)
                ctx = context_vector(snap["occupied"], remaining, snap["actions_used"], snap["undos"], op, score, entry.area)
                avec, feat_checks = action_vector(
                    snap["occupied"], remaining, snap["actions_used"], snap["undos"], op, score, entry.area, site, snap["env"], item["rotation"]
                )
                ledger["feature_checks"] = ledger.get("feature_checks", 0) + feat_checks
                saving_1600 = truncated.get("remaining_saving") if truncated and truncated.get("ok") else None
                row = {
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
                    "admission_bound": max(1, int(config.anchors)),
                    "context_vector": ctx,
                    "action_vector": avec,
                    "feature_checks": feat_checks,
                    "remaining_saving": full["remaining_saving"],
                    "quality_ok": full["quality_ok"],
                    "beneficial_free": full["beneficial_free"],
                    "severe_loss": float(full["remaining_saving"]) < -200,
                    "A_skip": full["A_skip"],
                    "A_commit": full["A_commit"],
                    "Q_skip": full["Q_skip"],
                    "Q_commit": full["Q_commit"],
                    "skip_termination": full["skip_termination"],
                    "commit_termination": full["commit_termination"],
                    "skip_cap_hit": full["skip_cap_hit"],
                    "commit_cap_hit": full["commit_cap_hit"],
                    "remaining_cap": rem_cap,
                    "pair_cap": pair_cap,
                    "saving_1600": saving_1600,
                    "skip_cap_hit_1600": truncated.get("skip_cap_hit") if truncated and truncated.get("ok") else None,
                    "commit_cap_hit_1600": truncated.get("commit_cap_hit") if truncated and truncated.get("ok") else None,
                    "skip_termination_1600": truncated.get("skip_termination") if truncated and truncated.get("ok") else None,
                    "commit_termination_1600": truncated.get("commit_termination") if truncated and truncated.get("ok") else None,
                    "cap_delta": None if saving_1600 is None else float(full["remaining_saving"]) - float(saving_1600),
                    "label_excludes_site_checks": True,
                    "net_after_check": float(full["remaining_saving"]) - float(item["examined"]),
                    "diagnosis_only": True,
                }
                rows.append(row)
    return rows


def cap_distortion_summary(rows: list[dict]) -> dict:
    paired = [r for r in rows if r.get("saving_1600") not in (None, "", "None")]
    if not paired:
        return {"n_paired": 0}
    deltas = [float(r["cap_delta"]) for r in paired]
    full = [float(r["remaining_saving"]) for r in paired]
    trunc = [float(r["saving_1600"]) for r in paired]
    n_skip = sum(1 for r in paired if str(r.get("skip_cap_hit_1600")).lower() in ("true", "1"))
    n_commit = sum(1 for r in paired if str(r.get("commit_cap_hit_1600")).lower() in ("true", "1"))
    n_either = sum(
        1
        for r in paired
        if str(r.get("skip_cap_hit_1600")).lower() in ("true", "1") or str(r.get("commit_cap_hit_1600")).lower() in ("true", "1")
    )
    n_full_gt = sum(1 for d in deltas if d > 1e-9)
    n_full_lt = sum(1 for d in deltas if d < -1e-9)
    n_eq = sum(1 for d in deltas if abs(d) <= 1e-9)
    return {
        "n_paired": len(paired),
        "n_skip_capped_1600": n_skip,
        "n_commit_capped_1600": n_commit,
        "n_either_capped_1600": n_either,
        "mean_saving_full": sum(full) / len(full),
        "mean_saving_1600": sum(trunc) / len(trunc),
        "mean_delta_full_minus_1600": sum(deltas) / len(deltas),
        "n_full_greater": n_full_gt,
        "n_full_smaller": n_full_lt,
        "n_equal": n_eq,
        "note": "A positive delta means the full remaining budget records a larger saving than the 1600 cap on that same state–action. Both directions occur.",
    }
