"""Summaries and the automatic report. Numbers are read from the run tables."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev

from config import PHILOSOPHY
from plots import write_genealogy, write_plots


def _float(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _load(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def describe(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "sd": None, "median": None, "ci95_low": None, "ci95_high": None}
    mu = mean(values)
    sd = pstdev(values) if len(values) > 1 else 0.0
    half = 1.96 * sd / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return {
        "n": len(values),
        "mean": mu,
        "sd": sd,
        "median": median(values),
        "ci95_low": mu - half,
        "ci95_high": mu + half,
    }


def _fmt(stats: dict, digits: int = 2) -> str:
    if not stats["n"]:
        return "n=0"
    return (
        f"n={stats['n']}, mean {stats['mean']:.{digits}f}, sd {stats['sd']:.{digits}f}, "
        f"median {stats['median']:.{digits}f}, 95% CI [{stats['ci95_low']:.{digits}f}, {stats['ci95_high']:.{digits}f}]"
    )


def _held(rows: list[dict], agent: str, experience: int) -> list[dict]:
    return [
        row for row in rows
        if row.get("agent") == agent and row.get("split") == "heldout" and int(float(row["experience"])) == experience
    ]


def _vals(rows: list[dict], field: str) -> list[float]:
    out = []
    for row in rows:
        value = _float(row.get(field))
        if value is not None:
            out.append(value)
    return out


def write_knowledge(run_dir: Path, memories: dict) -> None:
    lines = ["Learned operations at the end of this run. Names are neutral.", ""]
    csv_rows = []
    hierarchical = memories.get("hierarchical")
    ops = [] if hierarchical is None else list(hierarchical.operations)
    ops.sort(key=lambda op: (-op.utility, op.op_id))
    for op in ops:
        avg = "" if op.average_q is None else f"{op.average_q:.2f}"
        lines.append(
            f"{op.op_id} depth={op.depth} children={','.join(op.children)} created={op.created_at} "
            f"support_successes={op.successes} failures={op.failures} attempts={op.attempts} "
            f"average_Q={avg or 'NA'} attempts_saved={op.attempts_saved:.1f} bytes={op.nbytes} "
            f"utility={op.utility:.3f}"
        )
        csv_rows.append({
            "op_id": op.op_id,
            "depth": op.depth,
            "children": " ".join(op.children),
            "created_at": op.created_at,
            "successes": op.successes,
            "failures": op.failures,
            "attempts": op.attempts,
            "average_Q": avg,
            "attempts_saved": op.attempts_saved,
            "nbytes": op.nbytes,
            "utility": op.utility,
        })
    if not ops:
        lines.append("No learned operations survived in the hierarchical agent.")
    (run_dir / "knowledge_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (run_dir / "knowledge_report.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["op_id", "depth", "children", "created_at", "successes", "failures", "attempts", "average_Q", "attempts_saved", "nbytes", "utility"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_rows)
    write_genealogy(run_dir / "knowledge_genealogy.png", ops)


def write_report(run_dir: Path, config: dict, meta: dict) -> None:
    train_rows = _load(run_dir / "train_boxes.csv")
    checkpoints = _load(run_dir / "checkpoints.csv")
    specials = _load(run_dir / "special.csv")
    write_plots(run_dir, checkpoints, train_rows)
    held = [row for row in checkpoints if row.get("split") == "heldout"]
    experiences = sorted({int(float(row["experience"])) for row in held})
    agents = sorted({row["agent"] for row in held})
    first = experiences[0] if experiences else None
    last = experiences[-1] if experiences else None
    lines = [
        "# Expt-4 report",
        "",
        PHILOSOPHY,
        "",
        "Packing quality and thinking effort are reported separately. A mean gap on this schedule is not a claim that intelligence emerged.",
        "",
        "## Run",
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Seeds: `{config.get('seeds')}`",
        f"- Training boxes per lifetime: {config.get('train_boxes')}",
        f"- Quality gate Q_min: {config.get('q_min')}",
        f"- Environment change after training box: {config.get('change_at')}",
        f"- Python: {meta.get('python')}",
        f"- Git commit: {meta.get('git')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        "",
        "## Held-out summaries",
        "",
        "A is candidate evaluations. Internal cells of a committed learned operation are recorded separately and are not added to A.",
        "",
    ]
    for experience in experiences:
        lines.append(f"### Experience {experience}")
        lines.append("")
        for agent in agents:
            rows = _held(checkpoints, agent, experience)
            lines.append(f"- {agent} Q: {_fmt(describe(_vals(rows, 'Q')))}")
            lines.append(f"- {agent} A: {_fmt(describe(_vals(rows, 'A')))}")
            lines.append(f"- {agent} Q/A: {_fmt(describe(_vals(rows, 'efficiency')), 4)}")
        lines.append("")
    lines += ["## Answers", ""]
    lines.extend(_answers(config, checkpoints, specials, train_rows, first, last))
    lines += [
        "",
        "These statements describe this run only. They do not claim that intelligence has emerged.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "EXPT4_REPORT.md").write_text(text, encoding="utf-8")
    reports = Path(__file__).resolve().parent / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "EXPT4_REPORT.md").write_text(text, encoding="utf-8")


def _direction(before: float | None, after: float | None, tolerance: float = 0.5) -> str:
    if before is None or after is None:
        return "not measured"
    if after > before + tolerance:
        return "increased"
    if after < before - tolerance:
        return "decreased"
    return "remained approximately stable"


def _answers(config, checkpoints, specials, train_rows, first, last) -> list[str]:
    if first is None or last is None:
        return ["- No held-out checkpoints were written."]
    lines = []
    for agent in ("primitive", "flat", "hierarchical", "hierarchical_unlimited", "control"):
        early = _held(checkpoints, agent, first)
        late = _held(checkpoints, agent, last)
        if not early or not late:
            continue
        q0 = describe(_vals(early, "Q"))["mean"]
        q1 = describe(_vals(late, "Q"))["mean"]
        a0 = describe(_vals(early, "A"))["mean"]
        a1 = describe(_vals(late, "A"))["mean"]
        e0 = describe(_vals(early, "efficiency"))["mean"]
        e1 = describe(_vals(late, "efficiency"))["mean"]
        lines.append(
            f"- {agent}: held-out Q {_direction(q0, q1)} ({q0:.2f} to {q1:.2f}); "
            f"A {_direction(a0, a1, tolerance=1.0)} ({a0:.1f} to {a1:.1f}); "
            f"Q/A {_direction(e0, e1, tolerance=0.0005)} ({e0:.4f} to {e1:.4f})."
        )
    last_means = {}
    for agent in ("primitive", "flat", "hierarchical"):
        rows = _held(checkpoints, agent, last)
        if rows:
            last_means[agent] = describe(_vals(rows, "A"))["mean"]
    if len(last_means) == 3:
        order = sorted(last_means, key=lambda name: last_means[name])
        lines.append(
            "- At the last held-out checkpoint, mean A ordered from smaller to larger is "
            + ", ".join(f"{name} {last_means[name]:.1f}" for name in order)
            + ". The desired order would be hierarchical, then flat, then primitive. "
            + ("That order occurred." if order == ["hierarchical", "flat", "primitive"] else "That order did not occur.")
        )
    hier_ops = [
        int(float(row["library_size"]))
        for row in train_rows
        if row.get("agent") == "hierarchical" and row.get("library_size") not in (None, "")
    ]
    if hier_ops:
        lines.append(
            f"- Hierarchical library size reached {max(hier_ops)} during training. "
            + ("Reusable operations were stored." if max(hier_ops) > 0 else "No reusable operation survived.")
        )
    depths = [
        int(float(row["max_depth"]))
        for row in train_rows
        if row.get("agent") == "hierarchical" and row.get("max_depth") not in (None, "")
    ]
    if depths:
        lines.append(
            f"- Maximum abstraction depth observed for the hierarchical agent: {max(depths)}. "
            + ("A depth above 1 means a learned operation contained another learned operation." if max(depths) > 1 else "Hierarchy above a single chunk did not emerge.")
        )
    if "hierarchical" in last_means and "hierarchical_unlimited" in {
        row.get("agent") for row in _held(checkpoints, "hierarchical_unlimited", last)
    }:
        limited = last_means["hierarchical"]
        unlimited_rows = _held(checkpoints, "hierarchical_unlimited", last)
        unlimited = describe(_vals(unlimited_rows, "A"))["mean"]
        if unlimited < limited - 1:
            lines.append(
                f"- Unlimited memory had lower held-out A ({unlimited:.1f}) than capacity-limited memory ({limited:.1f}). "
                "On this run, scarcity did not reduce thinking below the unlimited library."
            )
        else:
            lines.append(
                f"- Capacity-limited hierarchical A was {limited:.1f}; unlimited-memory A was {unlimited:.1f}."
            )
    transfer = [row for row in specials if row.get("split") == "transfer"]
    primitive_late = _held(checkpoints, "primitive", last)
    if transfer and primitive_late:
        lines.append(
            "- Transfer of learned operations only, with episodes discarded: "
            f"Q {_fmt(describe(_vals(transfer, 'Q')))}; A {_fmt(describe(_vals(transfer, 'A')))}. "
            f"Primitive held-out A at the same experience: {_fmt(describe(_vals(primitive_late, 'A')))}."
        )
    change_at = int(config.get("change_at", 0))
    probe = [row for row in checkpoints if row.get("split") == "probe" and row.get("agent") == "hierarchical"]
    if probe:
        before = [row for row in probe if int(float(row["experience"])) <= change_at]
        after = [row for row in probe if int(float(row["experience"])) > change_at]
        if before and after:
            b = describe(_vals(before, "A"))["mean"]
            a = describe(_vals(after, "A"))["mean"]
            lines.append(
                f"- Hierarchical probe-set A before the change (checkpoints at or before {change_at}) averaged {b:.1f}; "
                f"checkpoints after the change averaged {a:.1f}. "
                + ("Probe thinking rose after the shift." if a > b + 1 else "Probe thinking did not rise after the shift.")
            )
    for mode in ("all", "highest", "frequent", "random"):
        rows = [row for row in specials if row.get("split") == "knockout_" + mode]
        intact = [row for row in specials if False]
        held_late = _held(checkpoints, "hierarchical", last)
        if rows and held_late:
            base_a = describe(_vals(held_late, "A"))["mean"]
            cut_a = describe(_vals(rows, "A"))["mean"]
            base_q = describe(_vals(held_late, "Q"))["mean"]
            cut_q = describe(_vals(rows, "Q"))["mean"]
            lines.append(
                f"- Knockout `{mode}`: Q {cut_q:.2f} versus intact {base_q:.2f}; A {cut_a:.1f} versus intact {base_a:.1f}."
            )
    lines.append("- Strongest negative result: " + _negative(last_means, depths, hier_ops))
    return lines


def _negative(last_means: dict, depths: list[int], hier_ops: list[int]) -> str:
    notes = []
    if "hierarchical" in last_means and "primitive" in last_means and last_means["hierarchical"] >= last_means["primitive"] - 1:
        notes.append("the hierarchical library did not reduce held-out A below the primitive baseline")
    if depths and max(depths) <= 1:
        notes.append("no operation deeper than one chunk survived")
    if hier_ops and max(hier_ops) == 0:
        notes.append("the library stayed empty")
    if not notes:
        notes.append("see the paired means above; a short schedule can move A without establishing the hypothesis")
    return "; ".join(notes) + "."
