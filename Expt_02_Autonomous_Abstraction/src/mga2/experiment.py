"""Episode runner, checkpoints, and the demonstration report.

Research logs are written here. The policy never reads them back.
"""

from __future__ import annotations

import csv
import hashlib
import json
import pickle
import platform
import time
from pathlib import Path

from mga2 import __version__
from mga2.environment import Action, ActionKind, PackingEnv
from mga2.inventory import Inventory
from mga2.pieces import catalogue_hash
from mga2.rngutil import derive_seed, make_rng
from mga2.ltm import LongTermMemory
from mga2.selection import LIBRARY_MODES, Agent, make_ledger, new_library

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
RUNTIME = ROOT / "data" / "runtime"


def source_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted((ROOT / "src" / "mga2").glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_config(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def legacy_task(repetition: int) -> dict:
    return {
        "task_id": "legacy",
        "family": "legacy_unlimited",
        "inventory": {},
        "descriptors": {"repetition": repetition},
    }


def load_split(name: str) -> list[dict]:
    path = RUNTIME / f"{name}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload["tasks"])


def build_schedule(task_ids: list[str], n: int, master_seed: int) -> list[str]:
    rng = make_rng(master_seed, "schedule", "schedule", 0, "schedule")
    return [task_ids[rng.randrange(len(task_ids))] for _ in range(n)]


def run_episode(mode: str, task: dict, master_seed: int, phase: str, repetition: int, ltm, config: dict, frozen: bool) -> dict:
    task_id = str(task["task_id"])
    rng_decision = make_rng(master_seed, task_id, phase, repetition, "decision")
    rng_discovery = make_rng(master_seed, task_id, phase, repetition, "discovery")
    rng_eval = make_rng(master_seed, task_id, phase, repetition, "evaluation")
    decision_state = rng_decision.getstate()
    if task.get("family") == "legacy_unlimited":
        inventory = Inventory(None)
    else:
        inventory = Inventory(task.get("inventory") or {})
    budgets = config.get("budgets", {})
    env = PackingEnv(
        budget=int(budgets.get("physical_actions", 100)),
        size=int(config.get("board_size", 10)),
        inventory=inventory,
    )
    agent = Agent(mode, config, ltm=ltm, frozen=frozen)
    agent.begin_box(repetition, task_id)
    ledger = make_ledger(config)
    started = time.perf_counter()
    guard = 0
    limit = env.budget * 4 + 10
    while not env.terminal and guard < limit:
        guard += 1
        agent.decide_and_act(env, ledger, rng_decision, rng_discovery, rng_eval)
    if not env.terminal:
        env.force_terminal("action_limit")
    stm_stats = agent.finish_box()
    elapsed = time.perf_counter() - started
    event_start = 0
    events = list(agent.events)
    return {
        "mode": mode,
        "seed": master_seed,
        "phase": phase,
        "repetition": repetition,
        "task_id": task_id,
        "family": task.get("family", ""),
        "final_score": env.score,
        "best_score": env.best_score,
        "blanks": env.blanks,
        "physical_actions": env.actions_used,
        "primitive_decisions": ledger.primitive_decisions,
        "macro_invocations": ledger.macro_invocations,
        "model_transitions": ledger.model_transitions,
        "candidate_evals": ledger.candidate_evals,
        "planning_peak": ledger.planning_peak,
        "think_batches": ledger.think_batches,
        "stm_entries": stm_stats["entries"],
        "stm_trace_len": stm_stats["trace_len"],
        "stm_peak_bytes": stm_stats["peak_bytes"],
        "stm_avg_bytes": stm_stats["avg_bytes"],
        "ltm_entries": len(ltm.ops),
        "ltm_bytes": ltm.logical_bytes(),
        "ltm_confirmed": len(ltm.confirmed_ops()),
        "termination": env.termination_reason,
        "wall_seconds": elapsed,
        "invalid_attempts": env.invalid_attempts,
        "undos": env.undos,
        "placements": env.placements_count,
        "logging_events": ledger.logging_events,
        "cheap_actions": ledger.cheap_actions,
        "part_think": ledger.part_think,
        "part_paired": ledger.part_paired,
        "part_guard": ledger.part_guard,
        "part_selection": ledger.part_selection,
        "part_other": ledger.part_other,
        "span_think": ledger.span_think,
        "span_paired": ledger.span_paired,
        "trace": env.trace,
        "events": events,
        "decision_rng_state": decision_state,
        "inventory": task.get("inventory") or {},
        "descriptors": task.get("descriptors") or {},
        "decision_trace": list(agent.decision_trace),
    }


def _csv_row(rec: dict) -> dict:
    skip = {"trace", "events", "decision_rng_state", "inventory", "descriptors", "decision_trace"}
    return {k: v for k, v in rec.items() if k not in skip}


CSV_FIELDS = [
    "mode",
    "seed",
    "phase",
    "repetition",
    "task_id",
    "family",
    "final_score",
    "best_score",
    "blanks",
    "physical_actions",
    "primitive_decisions",
    "macro_invocations",
    "model_transitions",
    "candidate_evals",
    "planning_peak",
    "think_batches",
    "stm_entries",
    "stm_trace_len",
    "stm_peak_bytes",
    "stm_avg_bytes",
    "ltm_entries",
    "ltm_bytes",
    "ltm_confirmed",
    "termination",
    "wall_seconds",
    "invalid_attempts",
    "undos",
    "placements",
    "logging_events",
    "cheap_actions",
    "part_think",
    "part_paired",
    "part_guard",
    "part_selection",
    "part_other",
    "span_think",
    "span_paired",
]


def _append_outputs(run_dir: Path, rec: dict) -> None:
    csv_path = run_dir / "episodes.csv"
    new = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if new:
            writer.writeheader()
        writer.writerow(_csv_row(rec))
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        for event in rec["events"]:
            payload = dict(event)
            payload["mode"] = rec["mode"]
            payload["seed"] = rec["seed"]
            payload["phase"] = rec["phase"]
            payload["repetition"] = rec["repetition"]
            payload["task_id"] = rec["task_id"]
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    trace_rec = {
        "mode": rec["mode"],
        "seed": rec["seed"],
        "phase": rec["phase"],
        "repetition": rec["repetition"],
        "task_id": rec["task_id"],
        "family": rec["family"],
        "inventory": rec["inventory"],
        "final_score": rec["final_score"],
        "best_score": rec["best_score"],
        "actions": [step["action"] for step in rec["trace"]],
    }
    with (run_dir / "traces.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(trace_rec, sort_keys=True) + "\n")


def _library_blob(ltm) -> dict:
    return ltm.to_dict()


def evidence_level(libraries: dict[str, dict]) -> int:
    level = 0
    for blob in libraries.values():
        ops = blob.get("ops", {})
        for op in ops.values():
            stats = op.get("stats", {})
            uses = int(stats.get("real_uses", 0))
            successes = int(stats.get("successes", 0))
            if uses >= 1 and successes >= 1:
                level = max(level, 1)
            tasks = stats.get("real_task_ids") or []
            origins = stats.get("origins") or []
            if uses >= 1 and successes >= 1 and (len(tasks) >= 2 or len(origins) >= 2):
                level = max(level, 2)
            parents = op.get("parents") or []
            if len(parents) >= 2 and uses >= 1 and float(stats.get("utility_sum", 0)) > 0:
                child_ok = True
                for pid in parents:
                    child = ops.get(pid)
                    if child is None:
                        child_ok = False
                        break
                    cst = child.get("stats", {})
                    if int(cst.get("real_uses", 0)) < 1 or float(cst.get("utility_sum", 0)) <= 0:
                        child_ok = False
                if child_ok and int(op.get("depth", 0)) >= 1:
                    level = max(level, 3)
    return level


def top_operations(libraries: dict[str, dict], limit: int = 3) -> list[dict]:
    rows = []
    for key, blob in libraries.items():
        for op in blob.get("ops", {}).values():
            stats = op.get("stats", {})
            if int(stats.get("real_uses", 0)) <= 0 and op.get("status") not in {"confirmed", "same_task_reuse", "provisional"}:
                continue
            if int(stats.get("real_uses", 0)) <= 0 and float(stats.get("paired_utility_sum", 0)) <= 0:
                continue
            rows.append(
                {
                    "library": key,
                    "op_id": op.get("op_id"),
                    "status": op.get("status"),
                    "source": op.get("source"),
                    "provenance": op.get("provenance"),
                    "parents": op.get("parents"),
                    "depth": op.get("depth"),
                    "ast": op.get("ast"),
                    "primitive_sequence": op.get("primitive_sequence"),
                    "stats": stats,
                    "confirmation_scope": op.get("confirmation_scope"),
                    "bytes": len(json.dumps(op, sort_keys=True)),
                }
            )
    rows.sort(
        key=lambda r: (
            0 if r["status"] == "confirmed" else 1,
            -int(r["stats"].get("real_uses", 0)),
            -float(r["stats"].get("utility_sum", 0.0)),
            r["op_id"] or "",
        )
    )
    return rows[:limit]


def _mean_std(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    mean = sum(values) / len(values)
    if len(values) == 1:
        return mean, None
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return mean, var ** 0.5


def write_report(run_dir: Path, state: dict, config: dict) -> Path:
    episodes = []
    csv_path = run_dir / "episodes.csv"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as handle:
            episodes = list(csv.DictReader(handle))
    libraries = state.get("libraries", {})
    level = evidence_level(libraries)
    discovered = top_operations(libraries, 3)
    lines = []
    lines.append("# Expt-2 demonstration report")
    lines.append("")
    lines.append("Working title: Autonomous Discovery of Reusable Operations.")
    lines.append("")
    lines.append("## Designer-supplied versus discovered")
    lines.append("")
    lines.append(
        "Supplied by the designer: the 10×10 world, the A–P catalogue, PLACE/UNDO/SUBMIT, "
        "an exact clone of the transition rules, the typed AST constructors "
        "(PLACE_REL, SEQ, CALL, CHOOSE, REPEAT, IF, LOOKAHEAD), bounded search, "
        "STM/LTM, the paired utility formula, and the bandit dispatcher."
    )
    lines.append("")
    lines.append(
        "Discovered only if the logs show it: which operations were proposed, which entered memory, "
        "and which were reused. Nothing in the source preloads a successful macro."
    )
    lines.append("")
    lines.append("## Run status")
    lines.append("")
    lines.append(f"- Run directory: `{run_dir}`")
    lines.append(f"- Preset: `{state.get('preset')}`")
    lines.append(f"- Complete: `{state.get('complete')}`")
    lines.append(f"- Stop reason: `{state.get('stop_reason')}`")
    lines.append(f"- Episodes written: {len(episodes)}")
    lines.append(f"- Planned episodes: {state.get('planned')}")
    lines.append(f"- Catalogue hash: `{catalogue_hash()}`")
    lines.append(f"- Source hash: `{state.get('source_hash')}`")
    lines.append(f"- Config hash: `{state.get('config_hash')}`")
    lines.append("")
    if not state.get("complete"):
        lines.append("This report describes a partial run. Counts below are only the episodes that finished.")
        lines.append("")
    lines.append("## Performance by mode and seed")
    lines.append("")
    lines.append("Differences are means with sample standard deviations. A gap of one occupied cell is not treated as a significance test.")
    lines.append("")
    grouped: dict[tuple, list] = {}
    for row in episodes:
        grouped.setdefault((row["mode"], row["seed"], row["phase"]), []).append(row)
    lines.append("| mode | seed | phase | n | final mean | final sd | best mean | physical mean | macros mean | evals mean |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for key in sorted(grouped):
        rows = grouped[key]
        finals = [float(r["final_score"]) for r in rows]
        bests = [float(r["best_score"]) for r in rows]
        phys = [float(r["physical_actions"]) for r in rows]
        macros = [float(r["macro_invocations"]) for r in rows]
        evals = [float(r["candidate_evals"]) for r in rows]
        fm, fs = _mean_std(finals)
        bm, _bs = _mean_std(bests)
        pm, _ps = _mean_std(phys)
        mm, _ms = _mean_std(macros)
        em, _es = _mean_std(evals)
        lines.append(
            f"| {key[0]} | {key[1]} | {key[2]} | {len(rows)} | {fm:.2f} | {'' if fs is None else f'{fs:.2f}'} | {bm:.2f} | {pm:.2f} | {mm:.2f} | {em:.1f} |"
        )
    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    lines.append(f"Observed evidence level: **{level}**.")
    lines.append("")
    lines.append("- 0: engine ran, no validated useful discovery.")
    lines.append("- 1: a repeated action sequence was stored and reused.")
    lines.append("- 2: a stored operation was used at another location or task.")
    lines.append("- 3: a parent combines independently used children and itself has positive real utility.")
    lines.append("- 4: not claimed. Causal lesion checks were not part of this bounded run.")
    lines.append("")
    if not discovered or all(int(op["stats"].get("real_uses", 0)) <= 0 for op in discovered):
        lines.append("Discovered operations that qualify: **NONE**.")
    else:
        lines.append("Up to three operations with recorded real use or provisional paired support:")
        lines.append("")
        for op in discovered:
            if int(op["stats"].get("real_uses", 0)) <= 0 and float(op["stats"].get("paired_utility_sum", 0)) <= 0:
                continue
            lines.append(f"### `{op['op_id']}`")
            lines.append("")
            lines.append(f"- Library `{op['library']}`, status `{op['status']}`, source `{op['source']}`, provenance `{op['provenance']}`.")
            lines.append(f"- Parents: `{op['parents']}`. Effective depth: {op['depth']}.")
            lines.append(f"- Confirmation scope: `{op['confirmation_scope'] or 'not confirmed'}`.")
            lines.append(f"- Real uses: {op['stats'].get('real_uses')}. Tasks: `{op['stats'].get('real_task_ids')}`. Origins: `{op['stats'].get('origins')}`.")
            lines.append(f"- Utility sum (real only): {op['stats'].get('utility_sum')}. Paired utility sum: {op['stats'].get('paired_utility_sum')}. Failures: {op['stats'].get('failures')}.")
            lines.append(f"- AST: `{json.dumps(op['ast'], sort_keys=True)}`")
            lines.append(f"- Primitive expansion: `{json.dumps(op['primitive_sequence'], sort_keys=True)}`")
            lines.append("")
        if not any(int(op["stats"].get("real_uses", 0)) > 0 for op in discovered):
            lines.append("No operation had a real reuse. Qualifying discovered operations: **NONE**.")
    lines.append("")
    lines.append("## Flat versus hierarchical")
    lines.append("")
    flat_macros = [float(r["macro_invocations"]) for r in episodes if r["mode"] == "flat_library"]
    hier_macros = [float(r["macro_invocations"]) for r in episodes if r["mode"] == "hierarchical_library"]
    lines.append(f"- Flat macro invocations per logged box: mean {_fmt(_mean_std(flat_macros)[0])}.")
    lines.append(f"- Hierarchical macro invocations per logged box: mean {_fmt(_mean_std(hier_macros)[0])}.")
    deep = [
        op
        for blob in libraries.values()
        for op in blob.get("ops", {}).values()
        if int(op.get("depth", 0)) > 1 and int(op.get("stats", {}).get("real_uses", 0)) > 0 and float(op.get("stats", {}).get("utility_sum", 0)) > 0
    ]
    if deep:
        lines.append(f"- Operations with effective depth above 1 and positive real utility: {len(deep)}.")
    else:
        lines.append("- No operation with effective depth above 1 had positive real utility in this run.")
    lines.append("")
    lines.append("## Discovery cost")
    lines.append("")
    think_model = sum(float(r["model_transitions"]) for r in episodes)
    lines.append(f"- Sum of charged model transitions over logged boxes: {think_model:.0f}.")
    lines.append("- Both branches of each paired check are included in that total.")
    lines.append("- No extrapolated savings are reported. Amortization is claimed only if the tables show later boxes costing less computation after a library exists; this bounded run does not fit a crossover curve.")
    lines.append("")
    if state.get("dry_run"):
        lines.append("## Dry-run estimate")
        lines.append("")
        dry = state["dry_run"]
        lines.append(f"- Probe boxes: {dry.get('boxes')}. Elapsed seconds: {dry.get('seconds')}.")
        lines.append(f"- Linear estimate for the planned episode count: {dry.get('estimated_seconds')} seconds.")
        lines.append("- The probe is not included in the episode table.")
        lines.append("")
    if episodes and "part_think" in episodes[0]:
        lines.extend(_accounting_lines(episodes, config))
    lines.append("## Limitations")
    lines.append("")
    lines.append("- Utility weights are the published engineering defaults, not a tuned objective.")
    lines.append("- Paired rollouts are short local comparisons.")
    lines.append("- The primitive controller examines legal placements until the evaluation cap, so many boxes end on `compute_budget` rather than a full board.")
    lines.append("- Lesion checks for evidence level 4 were not executed.")
    lines.append("- A next debugging step, if proposal counts are nonzero but promotions are not, is to log how often paired utility is negative because both branches pay the full scan cost inside an 8-step horizon.")
    lines.append("")
    lines.append(f"Package version {__version__}. Python {platform.python_version()} on {platform.platform()}.")
    lines.append("")
    text = "\n".join(lines)
    path = run_dir / "EXPT02_DEMONSTRATION_REPORT.md"
    path.write_text(text, encoding="utf-8")
    return path


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def _accounting_lines(episodes: list[dict], config: dict) -> list[str]:
    """Innermost partition versus inclusive THINK and paired spans."""
    reserve = make_ledger(config).cheap_reserve
    lines = [
        "## Evaluation accounting",
        "",
        f"- Cheap-scan reserve: {reserve} candidate evaluations. Deliberation stops at this distance before the cap. A cheap legal primitive may then use the remainder.",
        "- `part_think`, `part_paired`, `part_guard`, `part_selection`, and `part_other` are an innermost partition of `candidate_evals`. Each charged evaluation is counted once, under the tally that was open on top.",
        "- `span_think` counts every evaluation taken while a THINK tally was open, including paired validation and the guard scans inside it.",
        "- `span_paired` counts every evaluation taken while a paired tally was open, including guard scans inside that check.",
        "- The spans overlap the partition. They are not additional evaluations.",
        "- These figures locate where the budget went. They do not show improved packing, a useful hierarchy, or amortized discovery cost.",
        "",
        "| mode | n | evals mean | part think | part paired | part guard | part selection | span think | span paired | cheap mean | macros mean | physical mean | final mean |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    grouped: dict[str, list] = {}
    for row in episodes:
        grouped.setdefault(row["mode"], []).append(row)
    keys = (
        "candidate_evals",
        "part_think",
        "part_paired",
        "part_guard",
        "part_selection",
        "span_think",
        "span_paired",
        "cheap_actions",
        "macro_invocations",
        "physical_actions",
        "final_score",
    )
    for mode in sorted(grouped):
        rows = grouped[mode]
        means = []
        for key in keys:
            values = [float(r[key]) for r in rows]
            means.append(f"{sum(values) / len(values):.2f}")
        lines.append(f"| {mode} | {len(rows)} | " + " | ".join(means) + " |")
    mismatches = 0
    for row in episodes:
        parts = sum(float(row[name]) for name in ("part_think", "part_paired", "part_guard", "part_selection", "part_other"))
        if abs(parts - float(row["candidate_evals"])) > 0.5:
            mismatches += 1
    lines.append("")
    lines.append(f"- Boxes whose innermost parts do not sum to candidate evaluations: {mismatches}.")
    lines.append("")
    return lines


def _write_accounting(run_dir: Path, config: dict) -> None:
    csv_path = run_dir / "episodes.csv"
    if not csv_path.exists():
        return
    with csv_path.open(encoding="utf-8") as handle:
        episodes = list(csv.DictReader(handle))
    if not episodes or "part_think" not in episodes[0]:
        return
    by_mode: dict[str, dict] = {}
    part_names = ("part_think", "part_paired", "part_guard", "part_selection", "part_other", "span_think", "span_paired", "candidate_evals", "cheap_actions", "macro_invocations", "physical_actions", "final_score")
    for row in episodes:
        bucket = by_mode.setdefault(row["mode"], {"boxes": 0, **{name: 0.0 for name in part_names}})
        bucket["boxes"] += 1
        for name in part_names:
            bucket[name] += float(row[name])
    for bucket in by_mode.values():
        n = bucket["boxes"]
        bucket["means"] = {name: bucket[name] / n for name in part_names}
    arms: dict[str, dict[str, int]] = {}
    think_evals: list[float] = []
    arm_events = 0
    events_path = run_dir / "events.jsonl"
    if events_path.exists():
        with events_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                kind = event.get("type")
                if kind == "arm_choice":
                    arm_events += 1
                    mode = str(event.get("mode", ""))
                    arm = str(event.get("arm", ""))
                    arms.setdefault(mode, {})
                    arms[mode][arm] = arms[mode].get(arm, 0) + 1
                elif kind == "think_batch":
                    think_evals.append(float(event.get("evals", 0)))
    payload = {
        "cheap_scan_reserve": make_ledger(config).cheap_reserve,
        "note": "part_* is an innermost partition of candidate_evals. span_think and span_paired are inclusive and overlap that partition.",
        "by_mode": by_mode,
        "arm_choices": arms,
        "arm_choice_events": arm_events,
        "think_batches": {
            "count": len(think_evals),
            "evals_sum": sum(think_evals),
            "evals_mean": (sum(think_evals) / len(think_evals)) if think_evals else None,
            "evals_max": max(think_evals) if think_evals else None,
        },
    }
    (run_dir / "DIAGNOSTIC_ACCOUNTING.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _save_checkpoint(run_dir: Path, state: dict) -> None:
    payload = dict(state)
    payload.pop("config", None)
    (run_dir / "checkpoint.pkl").write_bytes(pickle.dumps(payload))
    (run_dir / "checkpoint_meta.json").write_text(
        json.dumps(
            {
                "complete": state.get("complete"),
                "stop_reason": state.get("stop_reason"),
                "completed": len(state.get("completed", [])),
                "planned": state.get("planned"),
                "preset": state.get("preset"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _episodes_for_preset(preset: str, config: dict) -> list[dict]:
    if preset == "tiny":
        seed = int(config.get("tiny_seed", 1))
        modes = list(config.get("modes", ["primitive", "search_only", "flat_library", "hierarchical_library"]))
        jobs = []
        for mode in modes:
            for rep in range(int(config.get("tiny_boxes", 3))):
                jobs.append(
                    {
                        "mode": mode,
                        "seed": seed,
                        "phase": "train",
                        "repetition": rep,
                        "task": legacy_task(rep),
                    }
                )
        return jobs
    if preset == "discovery_smoke":
        seeds = list(config.get("seeds", [11, 22]))
        modes = list(config.get("modes", ["primitive", "search_only", "flat_library", "hierarchical_library"]))
        train = load_split("train")
        test = load_split("test")
        jobs = []
        for seed in seeds:
            schedule = build_schedule([t["task_id"] for t in train], int(config.get("train_boxes", 40)), int(seed))
            by_id = {t["task_id"]: t for t in train}
            for mode in modes:
                for rep, task_id in enumerate(schedule):
                    jobs.append(
                        {
                            "mode": mode,
                            "seed": int(seed),
                            "phase": "train",
                            "repetition": rep,
                            "task": by_id[task_id],
                        }
                    )
                for rep, task in enumerate(test):
                    jobs.append(
                        {
                            "mode": mode,
                            "seed": int(seed),
                            "phase": "eval",
                            "repetition": rep,
                            "task": task,
                        }
                    )
        return jobs
    if preset == "memory_sweep":
        raise RuntimeError("memory_sweep is implemented as a config preset and is not launched by the first delivery")
    raise ValueError(f"unknown preset {preset}")


def dry_run_estimate(config: dict, planned: int) -> dict:
    """Time two training boxes and extrapolate. Results are not scored."""
    train = load_split("train")
    task = train[0]
    started = time.perf_counter()
    for mode in ("flat_library", "hierarchical_library"):
        ltm = new_library(config)
        run_episode(mode, task, int(config.get("seeds", [11])[0]), "dry_run", 0, ltm, config, frozen=False)
    seconds = time.perf_counter() - started
    per = seconds / 2.0
    return {
        "boxes": 2,
        "seconds": seconds,
        "seconds_per_box": per,
        "estimated_seconds": per * planned,
        "planned": planned,
        "note": "Probe boxes are excluded from episodes.csv.",
    }


def execute_run(preset: str, config: dict, wall_minutes: float | None, resume: Path | None = None) -> dict:
    deadline = None if wall_minutes is None else time.monotonic() + float(wall_minutes) * 60.0
    if resume is not None:
        run_dir = Path(resume)
        state = pickle.loads((run_dir / "checkpoint.pkl").read_bytes())
        config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
        preset = state["preset"]
    else:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        label = str(config.get("run_label") or preset)
        run_dir = RESULTS / f"{stamp}_{label}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
        jobs = _episodes_for_preset(preset, config)
        state = {
            "preset": preset,
            "planned": len(jobs),
            "jobs": jobs,
            "completed": [],
            "libraries": {},
            "complete": False,
            "stop_reason": "",
            "source_hash": source_hash(),
            "config_hash": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
            "catalogue_hash": catalogue_hash(),
            "python": platform.python_version(),
            "dry_run": None,
            "version": __version__,
            "run_label": config.get("run_label") or preset,
            "cheap_scan_reserve": make_ledger(config).cheap_reserve,
        }
        if preset == "discovery_smoke":
            state["dry_run"] = dry_run_estimate(config, len(jobs))
            (run_dir / "DRY_RUN_ESTIMATE.json").write_text(json.dumps(state["dry_run"], indent=2), encoding="utf-8")
        _save_checkpoint(run_dir, state)
    jobs = state["jobs"]
    libraries = {key: LongTermMemory.from_dict(blob) for key, blob in state.get("libraries", {}).items()}
    completed = set(state.get("completed", []))
    stop_reason = "finished"
    for job in jobs:
        ep_key = f"{job['mode']}|{job['seed']}|{job['phase']}|{job['repetition']}|{job['task']['task_id']}"
        if ep_key in completed:
            continue
        if deadline is not None and time.monotonic() >= deadline:
            stop_reason = "wall_cap"
            break
        lib_key = f"{job['mode']}|{job['seed']}"
        if lib_key not in libraries:
            libraries[lib_key] = new_library(config)
        ltm = libraries[lib_key]
        frozen = job["phase"] == "eval"
        before = json.dumps(ltm.to_dict()["ops"], sort_keys=True)
        rec = run_episode(
            job["mode"],
            job["task"],
            int(job["seed"]),
            job["phase"],
            int(job["repetition"]),
            ltm,
            config,
            frozen=frozen,
        )
        if frozen:
            after = json.dumps(ltm.to_dict()["ops"], sort_keys=True)
            if before != after:
                raise RuntimeError("frozen evaluation mutated LTM")
            ltm.frozen = False
        _append_outputs(run_dir, rec)
        state["libraries"][lib_key] = ltm.to_dict()
        completed.add(ep_key)
        state["completed"] = sorted(completed)
        state["stop_reason"] = "in_progress"
        _save_checkpoint(run_dir, state)
        # Readable library snapshot after each library-mode episode.
        if job["mode"] in LIBRARY_MODES:
            (run_dir / f"library_{lib_key.replace('|', '_')}.json").write_text(
                json.dumps(ltm.to_dict(), indent=2), encoding="utf-8"
            )
    state["complete"] = stop_reason == "finished" and len(completed) == len(jobs)
    state["stop_reason"] = stop_reason if state["complete"] else stop_reason
    if state["complete"]:
        state["stop_reason"] = "finished"
    _save_checkpoint(run_dir, state)
    from mga2.render import plot_run

    if (run_dir / "episodes.csv").exists():
        plot_run(run_dir / "episodes.csv", run_dir)
        _write_accounting(run_dir, config)
    report = write_report(run_dir, state, config)
    state["report"] = str(report)
    state["run_dir"] = str(run_dir)
    return state


EXPT2A_POLICIES = ("primitive_only", "library_lookup", "fixed_think", "adaptive_think")
_BUCKET_KEYS = ("candidate", "paired", "library_scan", "lookahead", "placement", "think", "other")


def _policy_config(config: dict, policy: str) -> tuple[str, dict]:
    """Frozen-eval controller for one Expt-2A policy. The library is unchanged."""
    cfg = json.loads(json.dumps(config))
    cfg["record_decisions"] = False
    cfg.pop("think_eval_allowance", None)
    allowance = int(config.get("think_eval_allowance", 3636))
    if policy == "primitive_only":
        cfg["budgets"]["allow_think"] = False
        return "primitive", cfg
    if policy == "library_lookup":
        cfg["budgets"]["allow_think"] = False
        return "flat_library", cfg
    if policy == "fixed_think":
        cfg["budgets"]["allow_think"] = True
        cfg["think_eval_allowance"] = allowance
        return "flat_library", cfg
    if policy == "adaptive_think":
        cfg["budgets"]["allow_think"] = True
        return "flat_library", cfg
    raise ValueError(f"unknown Expt-2A policy {policy}")


def _load_saved_library(config: dict, seed: int) -> LongTermMemory:
    run = ROOT / str(config["library_run"])
    mode = str(config.get("library_mode", "flat_library"))
    path = run / f"library_{mode}_{int(seed)}.json"
    if not path.exists():
        raise FileNotFoundError(f"learned library not found: {path}")
    return LongTermMemory.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _diagnose_box(config: dict, test_tasks: list[dict], run_dir: Path) -> dict:
    spec = config.get("diagnostic_box") or {}
    seed = int(spec.get("seed", config.get("seeds", [11])[0]))
    rep = int(spec.get("repetition", 0))
    policy = str(spec.get("policy", "adaptive_think"))
    task = test_tasks[rep]
    mode, cfg = _policy_config(config, policy)
    cfg["record_decisions"] = True
    library = new_library(cfg) if policy == "primitive_only" else _load_saved_library(config, seed)
    library.frozen = True
    rec = run_episode(mode, task, seed, "eval", rep, library, cfg, frozen=True)
    trace = rec["decision_trace"]
    totals = {key: sum(int(row.get(key, 0)) for row in trace) for key in _BUCKET_KEYS}
    totals["think_span"] = sum(int(row.get("think_span", 0)) for row in trace)
    payload = {
        "policy": policy,
        "mode": mode,
        "seed": seed,
        "phase": "eval",
        "repetition": rep,
        "task_id": task["task_id"],
        "final_score": rec["final_score"],
        "candidate_evals": rec["candidate_evals"],
        "physical_actions": rec["physical_actions"],
        "macro_invocations": rec["macro_invocations"],
        "think_batches": rec["think_batches"],
        "termination": rec["termination"],
        "totals": totals,
        "decisions": [
            {k: v for k, v in row.items() if k != "action"}
            for row in trace
        ],
    }
    (run_dir / "BOX_TRACE.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    from mga2.render import plot_box_trace

    plot_box_trace(
        trace,
        run_dir / "BOX_TRACE.png",
        f"Occupied cells vs evaluations — {policy}, seed {seed}, {task['task_id']}",
        "Pink marks a decision whose evaluations were mostly paired tests. Green marks a library scan. Blue marks a placement.",
    )
    return payload


def _rows_for(episodes: list[dict], policy: str, seed: int) -> list[dict]:
    return [row for row in episodes if row["policy"] == policy and int(row["seed"]) == int(seed)]


def _mean_key(rows: list[dict], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def _compare_policy(episodes: list[dict], policy: str, seeds: list[int]) -> dict:
    """Held-out success: higher occupied cells at the shared cap, or the same cells with fewer evaluations, on every seed."""
    per_seed = []
    for seed in seeds:
        lib = _rows_for(episodes, policy, seed)
        base = _rows_for(episodes, "primitive_only", seed)
        score = _mean_key(lib, "final_score")
        base_score = _mean_key(base, "final_score")
        evals = _mean_key(lib, "candidate_evals")
        base_evals = _mean_key(base, "candidate_evals")
        higher = score > base_score
        fewer = evals < base_evals and score >= base_score
        per_seed.append(
            {
                "seed": seed,
                "score": score,
                "primitive_score": base_score,
                "evals": evals,
                "primitive_evals": base_evals,
                "macros": _mean_key(lib, "macro_invocations"),
                "physical": _mean_key(lib, "physical_actions"),
                "think_batches": _mean_key(lib, "think_batches"),
                "higher_score": higher,
                "fewer_evals_at_same_or_better_score": fewer,
                "meets_seed": higher or fewer,
            }
        )
    return {"policy": policy, "meets": all(item["meets_seed"] for item in per_seed), "seeds": per_seed}


def _write_expt2a_report(run_dir: Path, config: dict, diagnosis: dict, episodes: list[dict], comparisons: list[dict]) -> Path:
    seeds = [int(s) for s in config.get("seeds", [])]
    lines = [
        "# Expt-2A — Cost-aware use of discovered operations",
        "",
        "Held-out inventories only. The library is the flat library saved by the baseline discovery smoke. It is frozen: this run does not discover a new operation into long-term memory and does not change that file.",
        "",
        f"- Library run: `{config.get('library_run')}`",
        f"- Seeds: {seeds}",
        f"- Eval boxes per policy per seed: {len(episodes) // max(1, len(seeds) * len(EXPT2A_POLICIES))}",
        f"- Candidate-eval cap: {config.get('budgets', {}).get('candidate_evals')}",
        f"- Cheap-scan reserve: {config.get('budgets', {}).get('cheap_scan_reserve')}",
        f"- Fixed THINK allowance: {config.get('think_eval_allowance')} evaluations, one catalogue pass, chosen before this comparison.",
        "",
        "The four policies share that cap. `primitive_only` ignores the library. `library_lookup` may execute stored operations and does not THINK. `fixed_think` may THINK until the allowance is spent, then acts. `adaptive_think` is the current flat interval of one THINK batch every 5 decisions, with no extra stop.",
        "",
        "Training cost that created the library is not charged again here. The question is whether the stored operations are worth using inside a held-out box.",
        "",
        "## One box",
        "",
        f"- Policy `{diagnosis['policy']}`, seed {diagnosis['seed']}, task `{diagnosis['task_id']}`.",
        f"- Occupied cells {diagnosis['final_score']}. Evaluations {diagnosis['candidate_evals']}. Physical actions {diagnosis['physical_actions']}. Macros {diagnosis['macro_invocations']}. THINK batches {diagnosis['think_batches']}. Termination `{diagnosis['termination']}`.",
        "- Plot: `BOX_TRACE.png`. Per-decision counts: `BOX_TRACE.json`.",
        "",
        "Evaluations in that box, as a partition of candidate evaluations:",
        "",
    ]
    totals = diagnosis["totals"]
    for key in list(_BUCKET_KEYS) + ["think_span"]:
        lines.append(f"- {key}: {totals.get(key, 0)}")
    lines.append("")
    lines.append("`think_span` includes paired tests that ran inside THINK. `candidate` is proposal generation; it does not examine placements. `paired` includes the guard scans inside paired tests. `library_scan` is an origin check for a stored operation on the real board.")
    lines.append("")
    lines.append("## Held-out means")
    lines.append("")
    lines.append("| policy | seed | n | final mean | evals mean | physical mean | macros mean | think batches |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for policy in EXPT2A_POLICIES:
        for seed in seeds:
            rows = _rows_for(episodes, policy, seed)
            lines.append(
                f"| {policy} | {seed} | {len(rows)} | {_mean_key(rows, 'final_score'):.2f} | {_mean_key(rows, 'candidate_evals'):.1f} | {_mean_key(rows, 'physical_actions'):.2f} | {_mean_key(rows, 'macro_invocations'):.3f} | {_mean_key(rows, 'think_batches'):.2f} |"
            )
    lines.append("")
    lines.append("## Success criterion")
    lines.append("")
    lines.append("A frozen library policy meets the criterion only when, on every seed, its mean occupied cells are higher than `primitive_only` at this same cap, or its mean occupied cells are at least as high and its mean evaluations are lower.")
    lines.append("")
    any_met = False
    for item in comparisons:
        if item["policy"] == "primitive_only":
            continue
        any_met = any_met or bool(item["meets"])
        lines.append(f"- `{item['policy']}`: {'meets the criterion on every seed' if item['meets'] else 'does not meet the criterion on every seed'}.")
        for seed_row in item["seeds"]:
            lines.append(
                f"  - seed {seed_row['seed']}: score {seed_row['score']:.2f} vs primitive {seed_row['primitive_score']:.2f}; evals {seed_row['evals']:.1f} vs {seed_row['primitive_evals']:.1f}."
            )
    lines.append("")
    if any_met:
        lines.append("At least one frozen library policy meets the stated criterion. This is not a claim that hierarchy is useful, that discovery cost is amortized, or that a learned stopping rule exists.")
    else:
        lines.append("No frozen library policy meets the criterion on every seed. The one-box breakdown is the evidence for what to change. A learned stopping rule and a hierarchy comparison were not run.")
    lines.append("")
    lines.append("Postponed: teaching the dispatcher to stop THINK from an expected-gain estimate, testing a parent against its flattened children, and any memory or harder-task sweep.")
    lines.append("")
    text = "\n".join(lines)
    path = run_dir / "EXPT2A_REPORT.md"
    path.write_text(text, encoding="utf-8")
    return path


def execute_expt2a(config: dict) -> dict:
    """Diagnose one held-out box, then compare four frozen policies. Does not train."""
    test_tasks = load_split("test")
    seeds = [int(s) for s in config.get("seeds", [11, 22])]
    policies = list(config.get("policies") or EXPT2A_POLICIES)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = RESULTS / f"{stamp}_expt2a"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
    diagnosis = _diagnose_box(config, test_tasks, run_dir)
    episodes = []
    for seed in seeds:
        saved = _load_saved_library(config, seed)
        for policy in policies:
            mode, cfg = _policy_config(config, policy)
            for rep, task in enumerate(test_tasks):
                library = new_library(cfg) if policy == "primitive_only" else saved.copy()
                library.frozen = True
                before = json.dumps(library.to_dict()["ops"], sort_keys=True)
                rec = run_episode(mode, task, seed, "eval", rep, library, cfg, frozen=True)
                after = json.dumps(library.to_dict()["ops"], sort_keys=True)
                if before != after:
                    raise RuntimeError(f"frozen library changed under {policy} seed {seed}")
                episodes.append(
                    {
                        "policy": policy,
                        "mode": mode,
                        "seed": seed,
                        "repetition": rep,
                        "task_id": task["task_id"],
                        "final_score": rec["final_score"],
                        "candidate_evals": rec["candidate_evals"],
                        "physical_actions": rec["physical_actions"],
                        "macro_invocations": rec["macro_invocations"],
                        "think_batches": rec["think_batches"],
                        "model_transitions": rec["model_transitions"],
                        "termination": rec["termination"],
                        "span_think": rec["span_think"],
                        "span_paired": rec["span_paired"],
                    }
                )
    matched = [
        row
        for row in episodes
        if row["policy"] == diagnosis["policy"]
        and int(row["seed"]) == int(diagnosis["seed"])
        and int(row["repetition"]) == int(diagnosis["repetition"])
    ]
    if matched and int(matched[0]["final_score"]) != int(diagnosis["final_score"]):
        raise RuntimeError("diagnostic box score diverged from the same comparison episode")
    fieldnames = list(episodes[0].keys())
    with (run_dir / "episodes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(episodes)
    comparisons = [_compare_policy(episodes, policy, seeds) for policy in policies if policy != "primitive_only"]
    report = _write_expt2a_report(run_dir, config, diagnosis, episodes, comparisons)
    (run_dir / "COMPARISON.json").write_text(json.dumps(comparisons, indent=2), encoding="utf-8")
    return {
        "run_dir": str(run_dir),
        "complete": True,
        "stop_reason": "finished",
        "report": str(report),
        "planned": len(seeds) * len(policies) * len(test_tasks),
        "completed": episodes,
        "diagnosis": diagnosis,
        "comparisons": comparisons,
    }


def assert_replay(trace_record: dict, budget: int) -> None:
    inventory = Inventory(None if trace_record["family"] == "legacy_unlimited" else trace_record["inventory"])
    env = PackingEnv(budget=budget, inventory=inventory)
    for action in trace_record["actions"]:
        kind = ActionKind(action["kind"])
        if kind is ActionKind.PLACE:
            env.step(Action.place(action["piece_type"], action["rotation"], action["x"], action["y"]))
        elif kind is ActionKind.UNDO:
            env.step(Action.undo())
        else:
            if action.get("kind") == "SUBMIT" and env.terminal:
                continue
            env.step(Action.submit())
    if env.score != int(trace_record["final_score"]):
        raise AssertionError("replay score mismatch")
