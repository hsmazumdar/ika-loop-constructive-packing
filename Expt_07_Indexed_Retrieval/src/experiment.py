"""Frozen libraries, index, ranker fit, K/budget freeze, eval factorial."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import CONDITIONS, Config, EXPT5_LEARNING_A, EXPT6_DEV
from diagnostic import remaining_pair, solve_gated
from index import LibraryIndex
from library_io import library_hash
from oracle import diagnose_pair
from policy import solve_indexed
from ranker import RANK_NAMES, choose_quality_threshold, fit_quality, fit_regressor, rank_vector
from reconstruct import EXPT5_DIR, file_sha, load_gates, load_snapshot, reconstruct_seed
from retrieval import first_legal_site, state_features
from solver import Ledger, make_rng
from tools.generate_boxes import BLOCKED_PATHS, generate


def load_split(name: str) -> list[dict]:
    return list(json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))["tasks"])


def load_json_tasks(path: Path) -> list[dict]:
    return list(json.loads(path.read_text(encoding="utf-8"))["tasks"])


def _ids(tasks: list[dict]) -> set[str]:
    return {t["task_id"] for t in tasks}


def assert_splits(eval_tasks: list[dict], smoke_tasks: list[dict] | None = None) -> dict:
    eval_ids = _ids(eval_tasks)
    prior = {}
    overlaps = {}
    for rel in BLOCKED_PATHS:
        path = Path(rel)
        if not path.exists():
            prior[str(path)] = 0
            continue
        ids = _ids(json.loads(path.read_text(encoding="utf-8"))["tasks"])
        prior[str(path)] = len(ids)
        hit = ids & eval_ids
        if hit:
            overlaps[str(path)] = sorted(hit)
    if smoke_tasks is not None:
        hit = _ids(smoke_tasks) & eval_ids
        if hit:
            overlaps["smoke_vs_eval"] = sorted(hit)
    if overlaps:
        raise RuntimeError(f"eval boxes overlap prior splits: {overlaps}")
    return {"prior_sources": prior, "n_eval": len(eval_ids)}


def ensure_boxes(name: str, target: int, seed: int, extra_blocked: list[Path] | None = None) -> list[dict]:
    path = ROOT / "data" / f"{name}.json"
    if path.exists():
        tasks = load_split(name)
        if len(tasks) >= target:
            return tasks[:target]
    generate(target=target, seed=seed, out_name=name, extra_blocked=extra_blocked)
    return load_split(name)[:target]


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


def read_csv(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_hashes() -> dict[str, str]:
    hashes = {}
    for path in sorted((ROOT / "src").glob("*.py")):
        hashes[path.name] = file_sha(path)
    for name in ("run_expt7.py", "analysis.py"):
        path = ROOT / name
        if path.exists():
            hashes[name] = file_sha(path)
    return hashes


def freeze_libraries(config: Config, snapshot_dir: Path, seeds: tuple[int, ...]) -> list[dict]:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    bundles = []
    for seed in seeds:
        path = snapshot_dir / f"library_seed{seed}.json"
        if path.exists():
            print(f"load frozen library seed {seed}", flush=True)
            info = load_snapshot(config, int(seed), snapshot_dir)
        else:
            print(f"reconstruct library seed {seed}", flush=True)
            info = reconstruct_seed(config, int(seed), snapshot_dir)
        live = library_hash(info["memory"])
        if live != info["library_hash"]:
            raise RuntimeError(f"library hash drifted seed {seed}")
        consult, commit, gate_sha = load_gates(int(seed))
        info["consult_gate"] = consult
        info["commit_gate"] = commit
        info["gate_file_sha256"] = gate_sha
        info["index"] = LibraryIndex(info["memory"])
        bundles.append(info)
    return bundles


def verify_frozen(bundles: list[dict], snapshot_dir: Path) -> dict:
    checks = []
    for bundle in bundles:
        seed = bundle["seed"]
        path = snapshot_dir / f"library_seed{seed}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        live = library_hash(bundle["memory"])
        ok = live == payload["library_hash"] == bundle["library_hash"]
        gate_now = file_sha(EXPT5_DIR / f"gates_seed{seed}.json")
        checks.append({"seed": seed, "library_hash_ok": ok, "gate_hash_ok": gate_now == bundle["gate_file_sha256"], "library_hash": live})
        if not ok:
            raise RuntimeError(f"library hash changed seed {seed}")
    return {"ok": True, "checks": checks}


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def shortlist_recall_from_oracle_rows(cand_rows: list[dict], k: int) -> dict:
    by_state: dict[tuple, list[dict]] = defaultdict(list)
    for row in cand_rows:
        by_state[(str(row["seed"]), str(row["task_id"]), str(row["state_index"]))].append(row)
    n_useful = 0
    n_hit = 0
    for items in by_state.values():
        beneficial_ops = {(r["op_id"], r["definition_hash"]) for r in items if _truthy(r.get("beneficial_free"))}
        if not beneficial_ops:
            continue
        n_useful += 1
        legal = sorted({(r["definition_hash"], r["op_id"]) for r in items})
        short = {(op_id, h) for h, op_id in legal[: int(k)]}
        if short & {(op, h) for op, h in beneficial_ops}:
            n_hit += 1
    return {
        "k": int(k),
        "n_states_with_oracle_useful": n_useful,
        "n_shortlist_contains_useful": n_hit,
        "recall": None if not n_useful else n_hit / n_useful,
    }


def choose_k(recalls: list[dict]) -> int:
    best = None
    for row in recalls:
        rec = row["recall"]
        if rec is None:
            continue
        key = (0 if rec >= 0.8 else 1, -rec, int(row["k"]))
        if best is None or key < best[0]:
            best = (key, int(row["k"]))
    return int(best[1]) if best else 2


def collect_ranker_labels(config: Config, seed: int, tasks: list[dict], bundle: dict, k: int) -> tuple[list[dict], int]:
    memory = bundle["memory"]
    index = bundle["index"]
    ops = {op.op_id: op for op in memory.active()}
    records = []
    learning_a = 0
    cap = int(config.pair_eval_cap)
    for index_i, task in enumerate(tasks[: config.collect_boxes]):
        from environment import PackingEnv
        from inventory import Inventory
        from diagnostic import primitive_step

        env = PackingEnv(budget=config.physical, inventory=Inventory(dict(task["inventory"])))
        primitive = Ledger()
        tabu: set = set()
        select_rng = make_rng(seed, task["task_id"], "rank-collect", index_i, "select")
        n_states = 0
        while not env.terminal and env.occupied < config.q_min and primitive.A < config.eval_cap and n_states < 4:
            remaining = env.inventory.as_dict()
            posted, _p, _c = index.query(remaining, env.occupied)
            short = posted[: int(k)]
            feats = state_features(env)
            labeled = 0
            for entry in short:
                if labeled >= int(config.unchosen_samples_per_box) + 1:
                    break
                op = ops.get(entry.op_id)
                if op is None:
                    continue
                site_rng = make_rng(seed, task["task_id"], "rank-collect", index_i, f"anchor-{n_states}-{op.op_id}")
                site, examined = first_legal_site(op, env, site_rng, config.anchors)
                if site is None:
                    continue
                skip, commit, ok, _n = remaining_pair(config, env, select_rng, tabu, site, cap)
                if not ok:
                    continue
                learning_a += skip["A"] + commit["A"] + examined
                useful, score = (op.applicability.useful_here(feats) if op.applicability else (True, 0.0))
                remaining_saving = skip["A"] - commit["A"]
                quality_ok = commit["Q"] >= skip["Q"] - config.quality_loss_margin
                records.append(
                    {
                        "vector": rank_vector(
                            env.occupied, remaining, env.actions_used, env.undos, len(op.steps), op.depth, score, op.depth > 1, entry.area
                        ),
                        "remaining_saving": remaining_saving,
                        "quality_ok": quality_ok,
                        "op_id": op.op_id,
                        "seed": seed,
                        "task_id": task["task_id"],
                    }
                )
                labeled += 1
            n_states += 1
            stop, _token = primitive_step(config, env, select_rng, tabu, primitive)
            if stop:
                break
    return records, learning_a


def fit_ranker(config: Config, records: list[dict]) -> tuple[object, object]:
    if not records:
        from ranker import LinearRegressor, QualityModel

        z = [0.0] * len(RANK_NAMES)
        return LinearRegressor(RANK_NAMES, z, 0.0, True), QualityModel(RANK_NAMES, z, 0.0, {}, 1.0, True)
    boxes = sorted({r["task_id"] for r in records})
    cut = max(1, int(0.75 * len(boxes)))
    train_ids = set(boxes[:cut])
    val_ids = set(boxes[cut:]) or train_ids
    train_rows = [r for r in records if r["task_id"] in train_ids]
    val_rows = [r for r in records if r["task_id"] in val_ids]
    benefit = fit_regressor(RANK_NAMES, train_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight)
    quality = fit_quality(RANK_NAMES, train_rows, config.ranker_steps, config.severe_loss_scale, config.quality_fail_weight)
    quality = choose_quality_threshold(quality, val_rows)
    return benefit, quality


def evaluate_condition(config, task, seed, box_index, bundle, name, k, budget, benefit, quality):
    memory = bundle["memory"]
    if name == "primitive":
        return solve_gated(config, task, seed, "expt7", box_index, None, "primitive")
    if name == "both_gates_frozen":
        return solve_gated(config, task, seed, "expt7", box_index, memory, "both_gates", bundle["consult_gate"], bundle["commit_gate"])
    return solve_indexed(
        config,
        task,
        seed,
        "expt7",
        box_index,
        memory,
        bundle["index"],
        ranked=name == "indexed_ranked",
        k=k,
        consult_budget=budget,
        benefit_model=benefit,
        quality_model=quality,
    )


def choose_budget(config: Config, dev_tasks: list[dict], bundles: list[dict], k: int, rankers: dict) -> dict:
    table = []
    for budget in config.budget_candidates:
        rows = []
        for bundle in bundles:
            benefit, quality = rankers[int(bundle["seed"])]
            for index, task in enumerate(dev_tasks[: config.n_dev_boxes]):
                prim = evaluate_condition(config, task, int(bundle["seed"]), index, bundle, "primitive", k, budget, benefit, quality)
                agent = evaluate_condition(config, task, int(bundle["seed"]), index, bundle, "indexed_ranked", k, budget, benefit, quality)
                rows.append(
                    {
                        "saving": prim["A"] - agent["A"],
                        "quality_loss": agent["Q"] < prim["Q"] - config.quality_loss_margin,
                        "A": agent["A"],
                    }
                )
        n = len(rows) or 1
        mean_s = sum(r["saving"] for r in rows) / n
        ql = sum(1.0 for r in rows if r["quality_loss"]) / n
        table.append({"consult_budget": int(budget), "n": len(rows), "mean_saving": mean_s, "quality_loss_rate": ql})
    ranked = sorted(table, key=lambda r: (0 if r["quality_loss_rate"] <= 0.2 else 1, 0 if r["mean_saving"] > 0 else 1, -r["mean_saving"], r["consult_budget"]))
    chosen = ranked[0]["consult_budget"] if ranked else 50
    return {"chosen": chosen, "table": table}


def run_eval(config, tasks, bundles, k, budget, rankers: dict) -> list[dict]:
    rows = []
    for bundle in bundles:
        benefit, quality = rankers[int(bundle["seed"])]
        for index, task in enumerate(tasks):
            by_name = {}
            for name in CONDITIONS:
                out = evaluate_condition(config, task, int(bundle["seed"]), index, bundle, name, k, budget, benefit, quality)
                out.update({"seed": int(bundle["seed"]), "condition": name, "library_hash": bundle["library_hash"], "k_shortlist": k, "consult_budget": budget})
                by_name[name] = out
                rows.append(out)
            prim = by_name["primitive"]
            for name, out in by_name.items():
                out["effort_saving"] = prim["A"] - out["A"]
                out["quality_loss"] = out["Q"] < prim["Q"] - config.quality_loss_margin
                out["A_primitive"] = prim["A"]
                out["Q_primitive"] = prim["Q"]
    return rows


def run_recall_diagnostic(config, tasks, bundles, k, diagnostic_ledger) -> tuple[list[dict], list[dict]]:
    """Sampled-oracle useful actions vs inexpensive shortlist. Diagnosis only."""
    states = []
    boxes = []
    for bundle in bundles:
        for index, task in enumerate(tasks):
            result = diagnose_pair(config, task, int(bundle["seed"]), index, bundle, diagnostic_ledger)
            cand = result["candidates"]
            rec = shortlist_recall_from_oracle_rows(cand, k)
            rec.update({"seed": bundle["seed"], "task_id": task["task_id"], "library_hash": bundle["library_hash"]})
            boxes.append(rec)
            by_state = defaultdict(list)
            for row in cand:
                by_state[int(row["state_index"])].append(row)
            for state_index, items in by_state.items():
                beneficial_ops = {(r["op_id"], r["definition_hash"]) for r in items if _truthy(r.get("beneficial_free"))}
                if not beneficial_ops:
                    continue
                legal = sorted({(r["definition_hash"], r["op_id"]) for r in items})
                short = {(op_id, h) for h, op_id in legal[: int(k)]}
                states.append(
                    {
                        "seed": bundle["seed"],
                        "task_id": task["task_id"],
                        "state_index": state_index,
                        "n_beneficial_ops": len(beneficial_ops),
                        "shortlist_hit": bool(short & beneficial_ops),
                        "diagnosis_only": True,
                    }
                )
    return boxes, states
