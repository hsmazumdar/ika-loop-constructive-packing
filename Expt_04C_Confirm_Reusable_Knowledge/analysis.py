"""Per-seed win/tie/loss against primitive. Q and A stay separate."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import FINAL_CONDITIONS, PHILOSOPHY, QUALITY_LOSS_MARGIN


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


def classify(agent: dict, primitive: dict, margin: float) -> str:
    q_ok = float(agent["Q"]) >= float(primitive["Q"]) - margin
    a_agent = float(agent["A"])
    a_prim = float(primitive["A"])
    if not q_ok:
        return "quality_loss"
    if a_agent < a_prim:
        return "win"
    if a_agent == a_prim:
        return "tie"
    return "effort_loss"


def pairwise_rows(test_rows: list[dict], margin: float) -> list[dict]:
    by_key: dict[tuple, dict] = {}
    for row in test_rows:
        if row.get("split") != "test":
            continue
        by_key[(int(row["seed"]), row["task_id"], row["condition"])] = row
    out = []
    seeds = sorted({int(row["seed"]) for row in test_rows})
    tasks = sorted({row["task_id"] for row in test_rows if row.get("split") == "test"})
    for seed in seeds:
        for task_id in tasks:
            prim = by_key.get((seed, task_id, "primitive"))
            if prim is None:
                continue
            for name in FINAL_CONDITIONS:
                if name == "primitive":
                    continue
                agent = by_key.get((seed, task_id, name))
                if agent is None:
                    continue
                label = classify(agent, prim, margin)
                out.append(
                    {
                        "seed": seed,
                        "task_id": task_id,
                        "condition": name,
                        "label": label,
                        "Q_agent": agent["Q"],
                        "Q_primitive": prim["Q"],
                        "A_agent": agent["A"],
                        "A_primitive": prim["A"],
                        "delta_A": float(prim["A"]) - float(agent["A"]),
                        "delta_Q": float(agent["Q"]) - float(prim["Q"]),
                        "acceptable_agent": bool(agent.get("acceptable")),
                        "acceptable_primitive": bool(prim.get("acceptable")),
                        "elapsed_agent": agent.get("elapsed_s"),
                        "internal_agent": agent.get("internal_execution"),
                        "retrievals": agent.get("retrieval_cost"),
                        "applicability_cost": agent.get("applicability_cost"),
                        "rejected_operations": agent.get("rejected_operations"),
                        "memory_bytes": agent.get("memory_bytes"),
                    }
                )
    return out


def seed_summary(pairs: list[dict]) -> list[dict]:
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in pairs:
        grouped[(row["condition"], int(row["seed"]))].append(row)
    rows = []
    for (condition, seed), items in sorted(grouped.items()):
        labels = [item["label"] for item in items]
        savings = [float(item["delta_A"]) for item in items]
        qs = [float(item["Q_agent"]) for item in items]
        gate = [1.0 if item["acceptable_agent"] else 0.0 for item in items]
        rows.append(
            {
                "condition": condition,
                "seed": seed,
                "n": len(items),
                "wins": labels.count("win"),
                "ties": labels.count("tie"),
                "effort_losses": labels.count("effort_loss"),
                "quality_losses": labels.count("quality_loss"),
                "mean_delta_A": _mean(savings),
                "median_delta_A": statistics.median(savings) if savings else None,
                "mean_Q": _mean(qs),
                "pct_Q_ge_75": 100.0 * _mean(gate) if gate else None,
            }
        )
    return rows


def write_plots(run_dir: Path, test_rows: list[dict], pair_rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    conditions = [name for name in FINAL_CONDITIONS]
    means = []
    for name in conditions:
        vals = [float(row["A"]) for row in test_rows if row.get("condition") == name]
        means.append(sum(vals) / len(vals) if vals else 0.0)
    ax.bar(range(len(conditions)), means)
    ax.set_xticks(range(len(conditions)), conditions, rotation=20, ha="right")
    ax.set_ylabel("mean A (candidate evaluations)")
    ax.set_title("Final test deliberation by condition")
    fig.tight_layout()
    fig.savefig(run_dir / "plot_final_A.png", dpi=120)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name in ("selective_hierarchical", "selective_flat", "transfer", "lesion"):
        by_seed = defaultdict(list)
        for row in pair_rows:
            if row["condition"] == name:
                by_seed[int(row["seed"])].append(float(row["delta_A"]))
        if not by_seed:
            continue
        xs = sorted(by_seed)
        ax.plot(xs, [sum(by_seed[x]) / len(by_seed[x]) for x in xs], marker="o", label=name)
    ax.axhline(0.0, color="#888888", lw=0.8)
    ax.set_xlabel("training seed")
    ax.set_ylabel("mean A_primitive - A_agent")
    ax.set_title("Per-seed effort savings vs primitive")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(run_dir / "plot_seed_savings.png", dpi=120)
    plt.close(fig)


def _cond_stats(test_rows, name, field):
    values = [float(row[field]) for row in test_rows if row.get("condition") == name and row.get(field) not in (None, "")]
    return {"n": len(values), "mean": _mean(values), "sd": _sd(values), "median": statistics.median(values) if values else None}


def write_report(run_dir: Path, config: dict, meta: dict, test_rows: list[dict], pair_rows: list[dict], seed_rows: list[dict]) -> None:
    margin = float(config.get("quality_loss_margin", QUALITY_LOSS_MARGIN))
    n_test = len({row["task_id"] for row in test_rows if row.get("split") == "test"})
    lines = [
        "# Expt-4C report",
        "",
        PHILOSOPHY,
        "",
        f"- Directory: `{run_dir}`",
        f"- Preset: `{meta.get('preset')}`",
        f"- Python: {meta.get('python')}",
        f"- Catalogue hash: `{meta.get('catalogue_hash')}`",
        f"- Quality-loss margin (declared before the run): {margin} occupied cells",
        f"- Final test boxes: {n_test}",
        f"- Training seeds: {config.get('seeds')}",
        f"- Training boxes per seed: {config.get('train_boxes')}",
        "",
        "Q/A is not the primary measure. Wins require preserved quality within the predeclared margin and strictly lower A.",
        "",
        "## Final-test means",
        "",
    ]
    for name in FINAL_CONDITIONS:
        q = _cond_stats(test_rows, name, "Q")
        a = _cond_stats(test_rows, name, "A")
        t = _cond_stats(test_rows, name, "elapsed_s")
        gate = [1.0 if row.get("acceptable") else 0.0 for row in test_rows if row.get("condition") == name]
        lines.append(
            f"- {name}: Q mean {_fmt(q['mean'])} sd {_fmt(q['sd'])}; "
            f"A mean {_fmt(a['mean'])} sd {_fmt(a['sd'])}; "
            f"% Q>=75 {_fmt(100.0 * _mean(gate) if gate else None)}; "
            f"wall-clock mean {_fmt(t['mean'])} s"
        )
    lines += ["", "## Per-seed wins / ties / losses versus primitive", ""]
    for row in seed_rows:
        lines.append(
            f"- {row['condition']} seed {row['seed']}: "
            f"wins {row['wins']}, ties {row['ties']}, effort losses {row['effort_losses']}, "
            f"quality losses {row['quality_losses']}; mean ΔA {_fmt(row['mean_delta_A'])}; "
            f"median ΔA {_fmt(row['median_delta_A'])}; mean Q {_fmt(row['mean_Q'])}"
        )

    def _seeds_positive(name: str) -> tuple[int, int]:
        subset = [row for row in seed_rows if row["condition"] == name]
        good = [row for row in subset if (row["median_delta_A"] or 0) > 0 and row["quality_losses"] <= row["n"] * 0.2]
        return len(good), len(subset)

    h_ok, h_n = _seeds_positive("selective_hierarchical")
    t_ok, t_n = _seeds_positive("transfer")
    l_ok, l_n = _seeds_positive("lesion")
    f_ok, f_n = _seeds_positive("selective_flat")
    hier_A = _cond_stats(test_rows, "selective_hierarchical", "A")["mean"]
    flat_A = _cond_stats(test_rows, "selective_flat", "A")["mean"]
    prim_A = _cond_stats(test_rows, "primitive", "A")["mean"]
    lesion_A = _cond_stats(test_rows, "lesion", "A")["mean"]
    transfer_A = _cond_stats(test_rows, "transfer", "A")["mean"]
    lines += [
        "",
        "## Decisive questions",
        "",
        f"1. Combined agent repeatedly saves effort while preserving quality? {h_ok}/{h_n} seeds have median ΔA > 0 with quality losses ≤ 20% of boxes.",
        f"2. Fresh agent inherits savings through transferred knowledge? {t_ok}/{t_n} seeds; transfer mean A {_fmt(transfer_A)} vs hierarchical {_fmt(hier_A)}.",
        f"3. Savings disappear when learned operations are disabled? lesion mean A {_fmt(lesion_A)} vs primitive {_fmt(prim_A)} vs hierarchical {_fmt(hier_A)}.",
        f"4. Hierarchical knowledge outperforms equally selective flat knowledge? hierarchical mean A {_fmt(hier_A)} vs flat {_fmt(flat_A)}.",
        "",
        "These statements describe this run only. They do not claim that intelligence has emerged.",
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "EXPT4C_REPORT.md").write_text(text, encoding="utf-8")
    reports = run_dir.parents[1] / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "EXPT4C_REPORT.md").write_text(text, encoding="utf-8")
