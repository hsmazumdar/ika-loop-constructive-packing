"""Held-out report. Numbers are read from the run directory, never filled in by hand."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


def _bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _float(value):
    if value is None or value == "":
        return None
    return float(value)


def _int(value) -> int:
    return int(float(value))


def _group(rows, phase: str):
    kept = [row for row in rows if row["phase"] == phase]
    return kept


def _mean(values) -> float | None:
    if not values:
        return None
    return float(mean(values))


def _sd(values) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    return float(pstdev(values))


def write_report(run_dir: Path, config: dict, summary: dict, rows: list[dict], solutions: list[dict], mined_by_size: dict) -> None:
    held = _group(rows, "heldout")
    dev = _group(rows, "development")
    target = int(config["quality_target"])
    lines = [
        "# Expt-3 report",
        "",
        "Mining reusable operations from teacher packings of the Expt-2 training inventories.",
        "Rectangularity is a designer-supplied filter. A negative result is a valid result.",
        "",
        "## Run",
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{config.get('preset')}`",
        f"- Complete: `{summary['complete']}`",
        f"- Stop reason: `{summary['stop_reason']}`",
        f"- Episodes written: {summary['episodes']} of {summary['planned']}",
        f"- Device: `{summary['device']}`",
        f"- CUDA bytes allocated at the end: {summary['cuda_bytes']}",
        f"- Catalogue hash: `{summary['catalogue_hash']}`",
        f"- Dataset hash: `{summary['dataset_hash']}`",
        f"- Source hash: `{summary['source_hash']}`",
        f"- Corpus solutions: {summary['corpus_solutions']}",
        f"- Teacher cost: `{json.dumps(summary.get('teacher_cost', {}))}`",
        f"- Mining seconds (library construction, separate from agent evaluation): {summary['mine_seconds']:.3f}",
        f"- Wall seconds for this process: {summary['wall_seconds']:.3f}",
        f"- Snapshot plan notes: `{json.dumps(summary['snapshot_notes'])}`",
        "",
        "## What was supplied and what was measured",
        "",
        "Supplied by the designer: the A–P catalogue, the Expt-2 inventory split, the rectangle filter, the shared placement score, the retrieval rule, and the teacher exact-cover solver.",
        "Measured: which training groups met the support and within-training validation rule, which of those were rectangles, and what the frozen libraries did on held-out inventories.",
        "The teacher solutions are labeled teacher experience. The agent did not discover them.",
        "Expt-1 action traces are unlimited-piece boxes. They are not in this comparison.",
        "",
        "## Corpus",
        "",
    ]
    if solutions:
        scores = [int(s["Q"]) for s in solutions]
        lines.append(f"- Solutions: {len(solutions)}. Q min {min(scores)}, max {max(scores)}, mean {mean(scores):.2f}.")
        by_solver = defaultdict(int)
        for solution in solutions:
            by_solver[solution["solver"]] += 1
        lines.append(f"- By solver: `{dict(by_solver)}`.")
        lines.append(f"- Distinct training tasks represented: {len({s['task_id'] for s in solutions})}.")
    else:
        lines.append("- No solutions were retained.")
    lines += ["", "## Development lock", ""]
    if dev:
        q_dev = [_int(row["Q"]) for row in dev]
        zero_place = sum(1 for row in dev if _int(row["P"]) == 0)
        lines.append(
            f"- Development episodes: {len(dev)}. Mean final Q {mean(q_dev):.2f}. Boxes with P=0: {zero_place}."
        )
        lines.append(
            "- The budget in `configs/default.json` was predeclared from the Expt-2 cap failure. Development did not choose an arm and did not change the cap."
        )
    else:
        lines.append("- No development episodes were written.")
    lines += ["", "## Held-out tables", ""]
    lines.append("Means are descriptive. The held-out set has 12 inventories at full size. A mean gap is not a claim of statistical superiority.")
    lines.append("")
    lines.append("| snapshot | arm | seed | n | Q mean | Q sd | P mean | attainment | conditional E | censored | evals mean | macros mean |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    buckets = defaultdict(list)
    for row in held:
        buckets[(row["snapshot"], row["arm"], str(row["seed"]))].append(row)
    for key in sorted(buckets, key=lambda item: (int(item[0]), str(item[1]), int(item[2]))):
        group = buckets[key]
        qs = [_int(row["Q"]) for row in group]
        ps = [_int(row["P"]) for row in group]
        evals = [_int(row["candidate_evals"]) for row in group]
        macros = [_int(row["macros_invoked"]) for row in group]
        attained = [row for row in group if _bool(row["target_met"])]
        conditional = [_float(row["E"]) for row in attained if _float(row["E"]) is not None]
        censored = sum(1 for row in group if _bool(row["censored"]))
        cond = f"{mean(conditional):.3f}" if conditional else "NA"
        lines.append(
            f"| {key[0]} | {key[1]} | {key[2]} | {len(group)} | {mean(qs):.2f} | {_sd(qs):.2f} | {mean(ps):.2f} | {len(attained)}/{len(group)} | {cond} | {censored} | {mean(evals):.1f} | {mean(macros):.2f} |"
        )
    lines += ["", "## Paired differences at the largest snapshot", ""]
    if held:
        largest = max(int(row["snapshot"]) for row in held)
        paired = defaultdict(dict)
        for row in held:
            if int(row["snapshot"]) != largest:
                continue
            paired[(str(row["seed"]), row["task_id"])][row["arm"]] = row
        deltas = defaultdict(list)
        for arms in paired.values():
            if "rect_mined" in arms and "neutral_mined" in arms:
                deltas["rect_minus_neutral_Q"].append(_int(arms["rect_mined"]["Q"]) - _int(arms["neutral_mined"]["Q"]))
            if "rect_mined" in arms and "primitive" in arms:
                deltas["rect_minus_primitive_Q"].append(_int(arms["rect_mined"]["Q"]) - _int(arms["primitive"]["Q"]))
            if "neutral_mined" in arms and "primitive" in arms:
                deltas["neutral_minus_primitive_Q"].append(_int(arms["neutral_mined"]["Q"]) - _int(arms["primitive"]["Q"]))
            if "rect_mined" in arms and "matched_control" in arms:
                deltas["rect_minus_matched_Q"].append(_int(arms["rect_mined"]["Q"]) - _int(arms["matched_control"]["Q"]))
        lines.append(f"Largest held-out snapshot in this file: {largest}. Target Q>={target}.")
        for name, values in deltas.items():
            lines.append(f"- {name}: n={len(values)}, mean {mean(values):.2f}, sd {_sd(values):.2f}.")
        if not deltas:
            lines.append("- Paired arms were not all present.")
        by_arm: dict[str, list] = defaultdict(list)
        for arms in paired.values():
            for arm, row in arms.items():
                by_arm[arm].append(row)
        for arm, group in sorted(by_arm.items()):
            no_legal = sum(1 for row in group if row.get("termination") == "no_legal")
            undos = [_int(row.get("undos", 0)) for row in group]
            ps = [_int(row["P"]) for row in group]
            lines.append(
                f"- {arm}: no_legal {no_legal}/{len(group)}, mean undos {mean(undos):.2f}, mean placements {mean(ps):.2f}."
            )
    lines += ["", "## Libraries", ""]
    for size, mined in sorted(mined_by_size.items()):
        lines.append(
            f"- Snapshot {size}: pool {mined['pool_ops']}, admitted {mined['admitted_candidates']}, "
            f"rectangle candidates {mined['rectangle_candidates']}, rectangles inside the neutral library {mined['neutral_rectangles']}, "
            f"bytes {mined['bytes']}, mismatches {len(mined['mismatches'])}."
        )
    lines += ["", "## Conditional efficiency and sensitivity", ""]
    for threshold in [target, 70, 90]:
        met = [row for row in held if _int(row["Q"]) >= threshold]
        lines.append(f"- Held-out rows with Q>={threshold}: {len(met)} of {len(held)}.")
    lines.append(
        "Efficiency is reported in the table only for rows that met the preregistered target of 80. "
        "Thresholds 70 and 90 are descriptive counts. They were not used to pick a winner."
    )
    lines += ["", "## Amortization", ""]
    teacher = summary.get("teacher_cost") or {}
    teacher_seconds = float(teacher.get("exact_seconds", 0.0)) + float(teacher.get("gpu_seconds", 0.0))
    lines.append(
        f"- Offline teacher search plus GPU beam: {teacher_seconds:.3f}s. Mining: {summary['mine_seconds']:.3f}s. "
        "These costs are not inside the per-box evaluation cap."
    )
    lines.append(
        "- No amortization crossover is fitted. End-to-end savings would require the measured evaluation work, "
        "plus teacher and mining work, to fall below the primitive arm inside this run. See the evals column. "
        "Teacher effort is included in any such claim, and this report does not make that claim unless the table shows it."
    )
    # A direct arithmetic check, not a fitted curve.
    if held:
        largest = max(int(row["snapshot"]) for row in held)
        prim = [_int(r["candidate_evals"]) for r in held if int(r["snapshot"]) == largest and r["arm"] == "primitive"]
        rect = [_int(r["candidate_evals"]) for r in held if int(r["snapshot"]) == largest and r["arm"] == "rect_mined"]
        if prim and rect:
            lines.append(
                f"- At snapshot {largest}, mean candidate evaluations were {mean(prim):.1f} (primitive) and {mean(rect):.1f} (rect_mined). "
                "Offline teacher and mining seconds are additional."
            )
    lines += [
        "",
        "## Plain answers",
        "",
    ]
    answers = _answers(held, mined_by_size)
    lines.extend(answers)
    lines += [
        "",
        "A favourable ratio, or a single transferred macro, is not general intelligence.",
    ]
    lines.extend(pilot_paragraph())
    text = "\n".join(lines)
    (run_dir / "EXPT03_REPORT.md").write_text(text, encoding="utf-8")
    (EXPT03_ROOT()).write_text(text, encoding="utf-8")


def EXPT03_ROOT() -> Path:
    return Path(__file__).resolve().parents[2] / "EXPT03_REPORT.md"


def _answers(held, mined_by_size) -> list[str]:
    if not held:
        return ["- The held-out table is empty, so no arm comparison is available."]
    largest = max(int(row["snapshot"]) for row in held)
    def arm_mean(arm: str) -> float | None:
        vals = [_int(row["Q"]) for row in held if int(row["snapshot"]) == largest and row["arm"] == arm]
        return mean(vals) if vals else None
    rect = arm_mean("rect_mined")
    neutral = arm_mean("neutral_mined")
    primitive = arm_mean("primitive")
    lines = []
    if rect is None or neutral is None:
        lines.append("- Rectangular extraction and shape-neutral extraction were not both measured at the largest snapshot.")
    elif abs(rect - neutral) < 1e-9:
        lines.append(
            f"- At snapshot {largest}, rectangular extraction and shape-neutral extraction have the same mean final Q ({rect:.2f})."
        )
    elif rect > neutral:
        lines.append(
            f"- At snapshot {largest}, mean final Q is higher for rectangular extraction ({rect:.2f}) than for shape-neutral extraction ({neutral:.2f}). "
            "That is a paired descriptive gap on this small schedule, not a general claim."
        )
    else:
        lines.append(
            f"- At snapshot {largest}, mean final Q is higher for shape-neutral extraction ({neutral:.2f}) than for rectangular extraction ({rect:.2f}). "
            "Rectangular extraction did not beat shape-neutral extraction on this schedule."
        )
    if primitive is not None and rect is not None:
        lines.append(f"- Primitive mean final Q at that snapshot: {primitive:.2f}.")
    last = mined_by_size.get(largest) or mined_by_size.get(max(mined_by_size)) if mined_by_size else None
    if last:
        lines.append(
            f"- Neutral library rectangles: {last['neutral_rectangles']} of the admitted neutral operations. "
            "Those rectangles were selected by frequency, not by the rectangle filter."
        )
    lines.append("- Learned behaviour, if any, is which stored operations the retrieval rule fired. The rectangle test itself was supplied.")
    return lines


def pilot_paragraph() -> list[str]:
    path = Path(__file__).resolve().parents[2] / "data" / "expt1_pilot.json"
    if not path.exists():
        return []
    pilot = json.loads(path.read_text(encoding="utf-8"))
    groups = int(pilot["connected_groups"])
    fitted = int(pilot["groups_whose_multiset_fits_some_training_inventory"])
    rate = fitted / groups if groups else 0.0
    return [
        "",
        "## Expt-1 exploratory pilot",
        "",
        (
            f"Four unlimited-piece boards from `{pilot['source']}` finished at Q>=80. "
            f"They produced {groups} connected groups. {fitted} of those groups ({rate:.2f}) have a piece multiset "
            "that at least one Expt-2 training inventory can supply. That is not transfer to inventory-constrained packing, "
            "and those groups were not loaded into the libraries above."
        ),
        "",
    ]
