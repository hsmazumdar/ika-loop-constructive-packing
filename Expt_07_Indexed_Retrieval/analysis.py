"""Expt-7 report from saved rows."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import CONDITIONS, PHILOSOPHY, QUALITY_LOSS_MARGIN


def _mean(values):
    return None if not values else sum(values) / len(values)


def _sd(values):
    return None if len(values) < 2 else statistics.stdev(values)


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _truthy(value) -> bool:
    return str(value).lower() in ("true", "1", "yes")


def _float(row, key, default=0.0) -> float:
    try:
        return float(row.get(key) if row.get(key) not in (None, "") else default)
    except (TypeError, ValueError):
        return float(default)


def write_plots(run_dir: Path, rows: list[dict]) -> None:
    fig_dir = run_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    names = list(CONDITIONS)
    means = [_mean([_float(r, "A") for r in rows if r.get("condition") == name]) or 0 for name in names]
    ax.bar(range(len(names)), means)
    ax.set_xticks(range(len(names)), names, rotation=18, ha="right")
    ax.set_ylabel("mean A")
    ax.set_title("Expt-7 factorial: mean deliberation")
    fig.tight_layout()
    fig.savefig(fig_dir / "plot_condition_A.png", dpi=120)
    plt.close(fig)


def write_report(run_dir: Path, config: dict, meta: dict, rows: list[dict], recall: dict, selection: dict, ledger: dict) -> str:
    margin = float(config.get("quality_loss_margin", QUALITY_LOSS_MARGIN))
    prim = [r for r in rows if r.get("condition") == "primitive"]
    prim_q = _mean([_float(r, "Q") for r in prim])
    lines = [
        "# Expt-7 report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Python: {meta.get('python')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Frozen K={selection.get('k')}; consult budget={selection.get('consult_budget')} (frozen on development before eval)",
        f"- Libraries loaded from Expt-6 snapshots; reconstruction={meta.get('reconstruction')}",
        "- Effort saving = A_primitive − A_agent. Quality-loss rate is separate from mean Q.",
        "- Index lookup is billed. The agent does not see remaining-solve futures.",
        "- consultation_cost = retrieval + applicability + learned site checks + index probes + ranking. "
        "It does not include primitive evaluations. Gate checks are a separate column (zero under indexed conditions).",
        "- Shortlist opportunity recall counts states where some shortlisted *operation* has a beneficial remaining-solve "
        "in the sampled oracle. It is not action-level (orientation/anchor) recall, and it is measured on primitive-trajectory "
        "snapshots, not on the deployed ranked policy's visited states.",
        "",
        "## Frozen selection",
        "",
        f"- Development shortlist recall: {selection.get('dev_recall')}",
        f"- Budget table: {selection.get('budget_table')}",
        f"- Index build: {meta.get('index_build')}",
        "",
        "## Factorial on fresh eval boxes",
        "",
    ]
    for name in CONDITIONS:
        subset = [r for r in rows if r.get("condition") == name]
        q = [_float(r, "Q") for r in subset]
        a = [_float(r, "A") for r in subset]
        s = [_float(r, "effort_saving") for r in subset]
        losses = [1.0 if _truthy(r.get("quality_loss")) else 0.0 for r in subset]
        consult = [_float(r, "consultation_cost") for r in subset]
        idx = [_float(r, "index_cost") for r in subset]
        rankc = [_float(r, "ranking_cost") for r in subset]
        mean_q = _mean(q)
        mean_q_ok = prim_q is None or mean_q is None or mean_q >= prim_q - margin
        lines.append(
            f"- {name}: n={len(subset)}; mean Q {_fmt(mean_q)} (sd {_fmt(_sd(q))}); mean A {_fmt(_mean(a))} "
            f"(sd {_fmt(_sd(a))}); mean effort saving {_fmt(_mean(s))}; "
            f"quality-loss rate {_fmt(100.0 * (_mean(losses) or 0))}% of boxes; "
            f"mean-quality preserved: {'yes' if mean_q_ok else 'no'}; "
            f"mean consultation {_fmt(_mean(consult))}; mean index {_fmt(_mean(idx))}; mean ranking {_fmt(_mean(rankc))}"
        )
    prim_a = _mean([_float(r, "A") for r in prim])
    ranked = [r for r in rows if r.get("condition") == "indexed_ranked"]
    ranked_a = _mean([_float(r, "A") for r in ranked])
    ranked_c = _mean([_float(r, "consultation_cost") for r in ranked])
    ranked_pe = _mean([_float(r, "primitive_evals") for r in ranked])
    if prim_a is not None and ranked_a is not None:
        lines += [
            "",
            "## Cost identity",
            "",
            f"- Mean (A_indexed_ranked − A_primitive) = {_fmt(ranked_a - prim_a)}; mean consultation_cost = {_fmt(ranked_c)}; "
            f"mean ranked primitive_evals = {_fmt(ranked_pe)} vs primitive mean A {_fmt(prim_a)}.",
            "- If those two differences match, remaining extra A is consultation overhead (index + ranking + applicability + site checks), not extra primitive search.",
        ]
    hits = recall.get("n_shortlist_contains_useful")
    useful = recall.get("n_states_with_oracle_useful")
    rec = recall.get("recall")
    lines += [
        "",
        "## Shortlist opportunity recall (diagnosis only)",
        "",
        f"- Among sampled-oracle primitive-trajectory states with a beneficial *operation*, the K-shortlist contained at least one such operation "
        f"in {hits} / {useful} states (operation recall {_fmt(rec)}). This is not placement-level recall and is not measured on the deployed trajectory.",
        "- High recall is insufficient without whole-box effort and quality above.",
        "",
        "## Ledgers",
        "",
        f"- Ranker learning remaining-solves: {ledger.get('learning_A')}",
        f"- Eval diagnostic oracle (recall only): skip {ledger.get('skip_rollouts')}; commit {ledger.get('commit_rollouts')}",
        f"- Historical Expt-5 learning_A {EXPT5_REF} (not billed here)",
        "",
        "## Answers",
        "",
        "- Does indexed access beat current gates on frozen libraries? See mean A and quality-loss above.",
        "- Does learned ranking add anything over the index shortlist alone? Compare indexed_retrieval vs indexed_ranked.",
        "- If free-oracle opportunity existed in Expt-6 and this policy still raises A, the remaining failure is inexpensive selection, not library content.",
        "",
        "The agent cannot see remaining-solve futures. Expt-7 eval boxes cannot later be reused as untouched confirmation tests.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "figures").mkdir(parents=True, exist_ok=True)
    (run_dir / "report.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT7_REPORT.md").write_text(text, encoding="utf-8")
    return text


EXPT5_REF = 486500
