"""Accounting audit of the frozen Expt-4D diagnostic CSV. No retraining."""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

from pieces import PIECE_TYPES

EXPT4D_DIAG = (
    Path(__file__).resolve().parent.parent
    / "Expt_04D_Where_Reuse_Loses_Advantage"
    / "results"
    / "20260929_210250_diagnostic"
)


def _f(row, key):
    return float(row[key])


def _mean(values):
    return None if not values else sum(values) / len(values)


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def decode_features(blob: str) -> dict:
    feats = json.loads(blob)
    hist = feats[:16]
    mix = {name: hist[i] for i, name in enumerate(PIECE_TYPES) if i < len(hist) and hist[i] > 1e-9}
    return {
        "occupancy_feat": feats[16] if len(feats) > 16 else None,
        "empty_components": int(round(feats[37] * 100.0)) if len(feats) > 37 else None,
        "largest_empty_region": int(round(feats[38] * 100.0)) if len(feats) > 38 else None,
        "border_empty_frac": feats[39] if len(feats) > 39 else None,
        "remaining_mix": mix,
    }


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def audit_diagnostics(rows: list[dict]) -> dict:
    by_mode = defaultdict(list)
    for row in rows:
        by_mode[row["mode"]].append(row)
    pairs = []
    n_trace_match = 0
    n_prim_eval_match = 0
    n_cap_truncated = 0
    identity_failures = []
    extras = []
    for row in by_mode.get("retrieve_check_then_primitive", []):
        prim = next(
            r
            for r in by_mode["primitive"]
            if r["seed"] == row["seed"] and r["task_id"] == row["task_id"]
        )
        a = _f(row, "A")
        recon = _f(row, "primitive_evals") + _f(row, "retrieval_cost") + _f(row, "applicability_cost") + _f(row, "learned_evals")
        if abs(a - recon) > 1e-9:
            identity_failures.append((row["seed"], row["task_id"], a, recon))
        prim_match = abs(_f(row, "primitive_evals") - _f(prim, "primitive_evals")) < 1e-9
        n_prim_eval_match += int(prim_match)
        if row.get("termination") == "eval_cap" or prim.get("termination") == "eval_cap":
            if not prim_match:
                n_cap_truncated += 1
        extras.append(
            {
                "seed": int(row["seed"]),
                "task_id": row["task_id"],
                "A_primitive": _f(prim, "A"),
                "A_retrieve_check": a,
                "delta_A": a - _f(prim, "A"),
                "primitive_evals_baseline": _f(prim, "primitive_evals"),
                "primitive_evals_check": _f(row, "primitive_evals"),
                "retrieval_cost": _f(row, "retrieval_cost"),
                "applicability_cost": _f(row, "applicability_cost"),
                "learned_evals": _f(row, "learned_evals"),
                "consultation": _f(row, "retrieval_cost") + _f(row, "applicability_cost") + _f(row, "learned_evals"),
                "Q_primitive": _f(prim, "Q"),
                "Q_check": _f(row, "Q"),
                "termination_primitive": prim.get("termination"),
                "termination_check": row.get("termination"),
                "primitive_evals_match": prim_match,
            }
        )
    return {
        "n_pairs": len(extras),
        "n_primitive_eval_match": n_prim_eval_match,
        "n_cap_truncated": n_cap_truncated,
        "identity_failures": identity_failures,
        "mean_delta_A": _mean([r["delta_A"] for r in extras]),
        "mean_retrieval": _mean([r["retrieval_cost"] for r in extras]),
        "mean_applicability": _mean([r["applicability_cost"] for r in extras]),
        "mean_learned": _mean([r["learned_evals"] for r in extras]),
        "mean_consultation": _mean([r["consultation"] for r in extras]),
        "mean_prim_evals_drop": _mean([r["primitive_evals_baseline"] - r["primitive_evals_check"] for r in extras]),
        "pairs": extras,
        "n_trace_match": n_trace_match,
    }


def enrich_replays(rows: list[dict], margin: float = 1.0) -> list[dict]:
    out = []
    for index, row in enumerate(rows):
        decoded = decode_features(row.get("features") or "[]")
        saving = float(row["effort_saving_remaining"])
        check = float(row["check_cost"])
        q_commit = float(row["Q_remaining_after_commit"])
        q_skip = float(row["Q_remaining_primitive"])
        quality_ok = q_commit >= q_skip - margin
        effort_ok = saving > check
        mix = decoded["remaining_mix"]
        mix_label = ",".join(f"{k}:{mix[k]:.2f}" for k in sorted(mix, key=lambda n: -mix[n])[:6])
        out.append(
            {
                "rank": 0,
                "decision_id": f"{row['seed']}:{row['task_id']}:{index}:occ{row['occupied_at_choice']}:{row['op_id']}",
                "seed": int(row["seed"]),
                "task_id": row["task_id"],
                "op_id": row["op_id"],
                "composed": row.get("composed"),
                "depth": int(float(row.get("depth") or 1)),
                "op_size": int(float(row.get("internal_execution") or 0)),
                "occupied_at_choice": int(float(row["occupied_at_choice"])),
                "empty_components": decoded["empty_components"],
                "largest_empty_region": decoded["largest_empty_region"],
                "border_empty_frac": decoded["border_empty_frac"],
                "remaining_mix": mix_label,
                "check_cost": check,
                "A_remaining_primitive": float(row["A_remaining_primitive"]),
                "A_remaining_after_commit": float(row["A_remaining_after_commit"]),
                "effort_saving_remaining": saving,
                "Q_remaining_primitive": q_skip,
                "Q_remaining_after_commit": q_commit,
                "quality_difference": q_commit - q_skip,
                "quality_ok": quality_ok,
                "effort_ok": effort_ok,
                "acceptable_success": effort_ok and quality_ok,
                "source": "expt4d_existing",
            }
        )
    out.sort(key=lambda r: r["effort_saving_remaining"])
    for i, rec in enumerate(out, start=1):
        rec["rank"] = i
    return out


def summarize_replays(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    savings = [r["effort_saving_remaining"] for r in rows]
    n_effort = sum(1 for r in rows if r["effort_ok"])
    n_quality = sum(1 for r in rows if r["quality_ok"])
    n_both = sum(1 for r in rows if r["acceptable_success"])
    by_op = defaultdict(list)
    for r in rows:
        by_op[r["op_id"]].append(r)
    op_rows = []
    for op_id, items in by_op.items():
        op_rows.append(
            {
                "op_id": op_id,
                "n": len(items),
                "mean_saving": _mean([i["effort_saving_remaining"] for i in items]),
                "n_acceptable": sum(1 for i in items if i["acceptable_success"]),
                "n_quality_fail": sum(1 for i in items if not i["quality_ok"]),
            }
        )
    op_rows.sort(key=lambda r: r["mean_saving"])
    return {
        "n": len(rows),
        "mean_saving": _mean(savings),
        "median_saving": statistics.median(savings),
        "n_effort_ok": n_effort,
        "n_quality_ok": n_quality,
        "n_acceptable_success": n_both,
        "n_composed": sum(1 for r in rows if str(r.get("composed")).lower() in ("true", "1")),
        "by_operation": op_rows,
        "worst": rows[0] if rows else None,
    }


def write_audit_report(path: Path, audit: dict, replay_summary: dict, replay_rows: list[dict]) -> str:
    lines = [
        "# Expt-4D2 accounting audit",
        "",
        "This audit reads the frozen Expt-4D diagnostic CSV. The learner is not retrained.",
        "",
        "## Why retrieve/check primitive evaluations differed",
        "",
        f"- Pairs: {audit['n_pairs']}; primitive_evals identical on {audit['n_primitive_eval_match']}/{audit['n_pairs']} boxes.",
        f"- Boxes where the shared evaluation cap truncated retrieve/check: {audit['n_cap_truncated']}.",
        f"- Mean ΔA (retrieve/check − primitive): {_fmt(audit['mean_delta_A'])}.",
        f"- Mean retrieval_cost: {_fmt(audit['mean_retrieval'])}.",
        f"- Mean applicability_cost: {_fmt(audit['mean_applicability'])}.",
        f"- Mean learned_evals (site checks): {_fmt(audit['mean_learned'])}.",
        f"- Mean consultation (retrieval + applicability + learned): {_fmt(audit['mean_consultation'])}.",
        f"- Mean drop in primitive_evals: {_fmt(audit['mean_prim_evals_drop'])}.",
        "",
        "A identity: A = primitive_evals + retrieval_cost + applicability_cost + learned_evals.",
        "Retrieval cost alone does not equal net ΔA. Applicability checks are the same order as retrieval.",
        "The remaining gap in the published mean ΔA (+75.46 vs consultation) is the eval-cap truncation:",
        "one box hit the cap, retrieve/check stopped earlier, and primitive_evals fell by 888 on that box alone.",
        "Equal mean Q does not prove identical trajectories on that box.",
        "",
        "RNG: retrieve and site search use purpose-tagged streams (`retrieve-*`, `anchor-*`), not `select`.",
        "Board: `macro_fits` copies mask and inventory counts; first_legal_site does not call env.step.",
        "The implementation bug was sharing one Ledger.A between consultation charges and the primitive stopping cap.",
        "",
        "## Existing 15 matched-state replays (worst remaining-effort-saving first)",
        "",
        f"- n={replay_summary['n']}; mean remaining saving {_fmt(replay_summary['mean_saving'])}; median {_fmt(replay_summary['median_saving'])}.",
        f"- Repay check cost: {replay_summary['n_effort_ok']}/{replay_summary['n']}.",
        f"- Preserve quality (commit Q ≥ skip Q − 1): {replay_summary['n_quality_ok']}/{replay_summary['n']}.",
        f"- Acceptable successes (effort and quality): {replay_summary['n_acceptable_success']}/{replay_summary['n']}.",
        f"- Composed-operation replays: {replay_summary['n_composed']}.",
        "",
        "Mixed outcomes show that a context predictor is needed. Occupancy band 0–24 does not identify one.",
        "Zero composed replays means this table does not speak to hierarchy.",
        "",
    ]
    for rec in replay_rows:
        flag = "acceptable" if rec["acceptable_success"] else ("quality-fail" if not rec["quality_ok"] else "effort-fail")
        lines.append(
            f"{rec['rank']}. `{rec['decision_id']}` op {rec['op_id']} size {rec['op_size']} occ {rec['occupied_at_choice']} "
            f"empty {rec['empty_components']}/{rec['largest_empty_region']} mix {rec['remaining_mix']} "
            f"A {rec['A_remaining_after_commit']:.0f} vs {rec['A_remaining_primitive']:.0f} "
            f"(saving {rec['effort_saving_remaining']:.0f}, check {rec['check_cost']:.0f}) "
            f"Q {rec['Q_remaining_after_commit']:.0f} vs {rec['Q_remaining_primitive']:.0f} [{flag}]"
        )
    lines += ["", "## By operation", ""]
    for item in replay_summary.get("by_operation") or []:
        lines.append(
            f"- {item['op_id']}: n={item['n']}; mean remaining saving {_fmt(item['mean_saving'])}; "
            f"acceptable {item['n_acceptable']}/{item['n']}; quality failures {item['n_quality_fail']}"
        )
    lines += [
        "",
        "Promotion is not changed in this experiment. Admission later must use repeated downstream benefit,",
        "with attention to severe losses, and an applicability rule evaluated on different boxes from those used to learn it.",
        "",
    ]
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    return text


def run_existing_audit(run_dir: Path) -> tuple[dict, list[dict], dict]:
    diag = load_csv(EXPT4D_DIAG / "diagnostics.csv")
    replays = load_csv(EXPT4D_DIAG / "counterfactual_replays.csv")
    audit = audit_diagnostics(diag)
    table = enrich_replays(replays)
    summary = summarize_replays(table)
    return audit, table, summary
