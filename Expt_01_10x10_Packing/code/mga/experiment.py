"""Training / evaluation loops, logging and smoke-experiment orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import sys
import time
from typing import Any

import pandas as pd

from mga.agent import MODES, PackingAgent
from mga.environment import Action, PackingEnv, replay_trace
from mga.memory import LongTermMemory, config_hash
from mga.paths import ROOT, RESULTS_DIR
from mga.pieces import catalogue_hash
from mga.render import save_populated_canvas


EPISODE_FIELDS = [
    "mode",
    "seed",
    "phase",
    "episode",
    "terminal_score",
    "blanks",
    "actions",
    "placements",
    "invalid_attempts",
    "undos",
    "perfect",
    "termination_reason",
    "stm_entries",
    "ltm_entries",
    "ltm_hits",
    "ltm_lookups",
    "ltm_evictions",
    "memory_serialized_bytes",
    "candidate_evaluations",
    "elapsed_seconds",
]


def load_config(path: Path | None = None) -> dict[str, Any]:
    from mga.paths import CONFIGS_DIR

    cfg_path = path or (CONFIGS_DIR / "default.json")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def source_hash() -> str:
    code_dir = ROOT / "code" / "mga"
    h = hashlib.sha256()
    for path in sorted(code_dir.glob("*.py")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def environment_versions() -> dict[str, Any]:
    import matplotlib
    import numpy
    import pandas
    import pytest

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "matplotlib": matplotlib.__version__,
        "pytest": pytest.__version__,
        "catalogue_hash": catalogue_hash(),
        "source_hash": source_hash(),
    }


def run_episode(env: PackingEnv, agent: PackingAgent, rng: random.Random) -> dict[str, Any]:
    env.reset_box()
    agent.begin_box()
    t0 = time.perf_counter()
    while not env.terminal:
        occupied_before = env.occupied
        mask_before = env.mask
        action = agent.select(env, rng)
        result = env.step(action)
        if result.accepted and action.kind.value == "PLACE":
            agent.after_step(env, action, occupied_before, mask_before)
    agent.end_box(env)
    stats = agent.memory_stats()
    elapsed = time.perf_counter() - t0
    return {
        "terminal_score": env.score,
        "blanks": env.blanks,
        "actions": env.actions_used,
        "placements": env.placements_count,
        "invalid_attempts": env.invalid_attempts,
        "undos": env.undos,
        "perfect": int(env.score == 100),
        "termination_reason": env.termination_reason,
        "elapsed_seconds": elapsed,
        "trace": [rec for rec in env.trace],
        **stats,
    }


def new_run_dir(preset: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{stamp}_{preset}"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class ExperimentRunner:
    config: dict[str, Any]
    out_dir: Path
    preset: str = "smoke"

    def __post_init__(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.cfg_hash = config_hash(self.config)
        spec = self.config["presets"][self.preset]
        self.seeds = list(spec["seeds"])
        self.train_boxes = int(spec["train_boxes"])
        self.eval_boxes = int(spec["eval_boxes"])
        self.modes = list(spec["modes"])
        self.rows: list[dict[str, Any]] = []
        self.traces_saved = 0
        self.started = time.perf_counter()
        self.partial = False
        (self.out_dir / "config.json").write_text(
            json.dumps(self.config, indent=2), encoding="utf-8"
        )
        (self.out_dir / "versions.json").write_text(
            json.dumps(environment_versions(), indent=2), encoding="utf-8"
        )
        self.trace_path = self.out_dir / "action_trace.jsonl"
        self.ckpt_dir = self.out_dir / "checkpoints"
        self.ckpt_dir.mkdir(exist_ok=True)

    def _agent_for(self, mode: str, ltm: LongTermMemory | None) -> PackingAgent:
        agent = PackingAgent(mode=mode, config=self.config, ltm=ltm)
        agent.ltm.config_hash = self.cfg_hash
        agent.ltm.catalogue_hash = catalogue_hash()
        return agent

    def _write_trace(self, mode: str, seed: int, phase: str, episode: int, trace: list) -> None:
        rec = {
            "mode": mode,
            "seed": seed,
            "phase": phase,
            "episode": episode,
            "trace": trace,
        }
        with self.trace_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        # Verify replay of this episode.
        env = replay_trace(trace, budget=self.config["action_budget"])
        last = trace[-1]
        if env.score != last["score"] or env.mask != last["mask"]:
            raise RuntimeError("action-trace replay mismatch")

    def run(self, time_budget_seconds: float | None = None) -> pd.DataFrame:
        populated_saved = False
        traces_needed = {mode: True for mode in self.modes}

        for seed in self.seeds:
            train_rng = random.Random(seed)
            eval_rng = random.Random(seed + int(self.config["eval_seed_offset"]))
            viz_rng = random.Random(seed + int(self.config["viz_seed_offset"]))
            del viz_rng  # reserved visualisation stream; not used for training

            for mode in self.modes:
                if time_budget_seconds is not None:
                    if time.perf_counter() - self.started > time_budget_seconds:
                        self.partial = True
                        break
                ltm = LongTermMemory(
                    capacity=int(self.config["ltm_capacity"]),
                    coefficient=float(self.config["ltm_coefficient"]),
                    shrinkage_k=int(self.config["ltm_shrinkage_k"]),
                )
                ltm.config_hash = self.cfg_hash
                ltm.catalogue_hash = catalogue_hash()
                agent = self._agent_for(mode, ltm)
                env = PackingEnv(budget=int(self.config["action_budget"]))

                for ep in range(1, self.train_boxes + 1):
                    metrics = run_episode(env, agent, train_rng)
                    self.rows.append(
                        self._row(mode, seed, "train", ep, metrics)
                    )
                    if ep % 10 == 0:
                        pd.DataFrame(self.rows, columns=EPISODE_FIELDS).to_csv(
                            self.out_dir / "episodes.csv", index=False
                        )
                        print(
                            f"[train] mode={mode} seed={seed} ep={ep}/{self.train_boxes} "
                            f"score={metrics['terminal_score']} undos={metrics['undos']} "
                            f"ltm={metrics['ltm_entries']}",
                            flush=True,
                        )
                    if traces_needed.get(mode) and ep == 1:
                        self._write_trace(mode, seed, "train", ep, metrics["trace"])
                        traces_needed[mode] = False
                    if not populated_saved and env.occupied >= 20:
                        save_populated_canvas(
                            env,
                            self.out_dir / "populated_canvas.png",
                            extra="Recorded training state (not a learned result).",
                        )
                        env.snapshot_path = str(self.out_dir / "board_snapshot.json")
                        (self.out_dir / "board_snapshot.json").write_text(
                            json.dumps(env.snapshot(), indent=2), encoding="utf-8"
                        )
                        populated_saved = True
                    if time_budget_seconds is not None:
                        if time.perf_counter() - self.started > time_budget_seconds:
                            self.partial = True
                            break
                if self.partial:
                    break

                ckpt = self.ckpt_dir / f"ltm_{mode}_seed{seed}.json"
                if mode in ("ltm", "both"):
                    agent.ltm.save(ckpt)

                if self.eval_boxes:
                    if mode in ("ltm", "both"):
                        eval_ltm = LongTermMemory.from_payload(
                            json.loads(agent.ltm.dump_bytes()),
                            expected_catalogue_hash=catalogue_hash(),
                            expected_config_hash=self.cfg_hash,
                        )
                    else:
                        eval_ltm = LongTermMemory()
                    eval_agent = self._agent_for(mode, eval_ltm)
                    eval_agent.ltm.freeze()
                    frozen_bytes = (
                        eval_agent.ltm.dump_bytes() if mode in ("ltm", "both") else None
                    )
                    for ep in range(1, self.eval_boxes + 1):
                        metrics = run_episode(env, eval_agent, eval_rng)
                        self.rows.append(self._row(mode, seed, "eval", ep, metrics))
                        if ep % 10 == 0:
                            print(
                                f"[eval ] mode={mode} seed={seed} ep={ep}/{self.eval_boxes} "
                                f"score={metrics['terminal_score']}",
                                flush=True,
                            )
                    if frozen_bytes is not None and eval_agent.ltm.dump_bytes() != frozen_bytes:
                        raise RuntimeError("frozen evaluation mutated LTM")
            if self.partial:
                break

        df = pd.DataFrame(self.rows, columns=EPISODE_FIELDS)
        df.to_csv(self.out_dir / "episodes.csv", index=False)
        self._write_summaries(df)
        self._write_plots(df)
        if not populated_saved:
            env = PackingEnv()
            rng = random.Random(11)
            agent = PackingAgent(mode="none", config=self.config)
            run_episode(env, agent, rng)
            save_populated_canvas(env, self.out_dir / "populated_canvas.png")
        self.write_report(df)
        return df

    def write_report(self, df: pd.DataFrame) -> None:
        wall = time.perf_counter() - self.started
        lines = [
            "# SMOKE_TEST_REPORT — MGA Expt-1",
            "",
            f"- Run directory: `{self.out_dir}`",
            f"- Preset: `{self.preset}`",
            f"- Partial: `{self.partial}`",
            f"- Wall time (s): `{wall:.1f}`",
            f"- Catalogue hash: `{catalogue_hash()}`",
            f"- Config hash: `{self.cfg_hash}`",
            f"- Source hash: `{source_hash()}`",
            "",
            "## Commands",
            "",
            "```powershell",
            r".\.venv\Scripts\python -m pytest -q --junitxml=results/tests.xml",
            r".\.venv\Scripts\python validate_catalogue.py --output results/catalogue_validation.json",
            rf".\.venv\Scripts\python run_experiment.py --config configs/default.json --preset {self.preset}",
            r".\.venv\Scripts\python run_gui.py",
            "```",
            "",
            "## Episode counts",
            "",
        ]
        if df.empty:
            lines.append("No episodes were written.")
        else:
            lines.append(
                f"- Rows: {len(df)}; modes={sorted(df['mode'].unique())}; "
                f"seeds={sorted(df['seed'].unique())}; phases={sorted(df['phase'].unique())}"
            )
            lines += ["", "## Summary (seed-level means, then averaged)", ""]
            summary_path = self.out_dir / "summary.csv"
            if summary_path.exists():
                lines.append(summary_path.read_text(encoding="utf-8"))
            lines += ["", "## Did memory help?", ""]
            ev = df[df["phase"] == "eval"] if "phase" in df.columns else df.iloc[0:0]
            use = ev if not ev.empty else df[df["phase"] == "train"]
            if not use.empty:
                means = use.groupby("mode")["terminal_score"].mean().sort_values(ascending=False)
                lines.append("Mean terminal score by mode:")
                for mode, val in means.items():
                    lines.append(f"- `{mode}`: {val:.3f}")
                lookups = float(use["ltm_lookups"].sum())
                hits = float(use["ltm_hits"].sum())
                hit_frac = hits / lookups if lookups else 0.0
                lines.append("")
                lines.append(
                    f"LTM lookups={int(lookups)}, hits={int(hits)}, hit fraction={hit_frac:.4f}."
                )
                lines.append(
                    "Nonempty memory with ~zero useful retrieval is not evidence that memory helped."
                )
                if len(means) >= 2:
                    best, worst = means.index[0], means.index[-1]
                    gap = means.iloc[0] - means.iloc[-1]
                    if gap < 1.0:
                        verdict = (
                            "No detectable improvement: mode means differ by less than 1 occupied cell. "
                            "Three seeds are a smoke check, not statistical significance."
                        )
                    elif best in ("stm", "ltm", "both") and "none" in means.index and means[best] > means["none"] + 1.0:
                        verdict = (
                            f"Measured scores are higher for `{best}` than `none` in this run "
                            f"(gap {gap:.2f}). This is a smoke check, not a significance claim."
                        )
                    else:
                        verdict = (
                            f"Highest mean is `{best}` ({means.iloc[0]:.2f}); `none` is "
                            f"{means.get('none', float('nan')):.2f}. Do not claim that BOTH must win. "
                            "Negative or tied results are retained."
                        )
                    lines += ["", "## Verdict", "", verdict]
            lines += [
                "",
                "## Limitations",
                "",
                "- Repeated empty 10×10 boxes test practice on the same task, not transfer.",
                "- The heuristic is engineered; hole-avoidance is a shared filter, not learned intelligence.",
                "- GUI mouse-click verification is separate from this batch run.",
                "",
            ]
        path = self.out_dir / "SMOKE_TEST_REPORT.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        root_report = RESULTS_DIR / "SMOKE_TEST_REPORT.md"
        root_report.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    def _row(self, mode, seed, phase, ep, metrics) -> dict[str, Any]:
        return {
            "mode": mode,
            "seed": seed,
            "phase": phase,
            "episode": ep,
            "terminal_score": metrics["terminal_score"],
            "blanks": metrics["blanks"],
            "actions": metrics["actions"],
            "placements": metrics["placements"],
            "invalid_attempts": metrics["invalid_attempts"],
            "undos": metrics["undos"],
            "perfect": metrics["perfect"],
            "termination_reason": metrics["termination_reason"],
            "stm_entries": metrics["stm_entries"],
            "ltm_entries": metrics["ltm_entries"],
            "ltm_hits": metrics["ltm_hits"],
            "ltm_lookups": metrics["ltm_lookups"],
            "ltm_evictions": metrics["ltm_evictions"],
            "memory_serialized_bytes": metrics["memory_serialized_bytes"],
            "candidate_evaluations": metrics["candidate_evaluations"],
            "elapsed_seconds": metrics["elapsed_seconds"],
        }

    def _write_summaries(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        seed_rows = []
        for (mode, seed, phase), g in df.groupby(["mode", "seed", "phase"], sort=True):
            seed_rows.append(
                {
                    "mode": mode,
                    "seed": seed,
                    "phase": phase,
                    "n_boxes": len(g),
                    "mean_terminal_score": g["terminal_score"].mean(),
                    "perfect_fraction": g["perfect"].mean(),
                    "mean_actions": g["actions"].mean(),
                    "mean_undos": g["undos"].mean(),
                    "ltm_hit_fraction": (
                        (g["ltm_hits"].sum() / g["ltm_lookups"].sum())
                        if g["ltm_lookups"].sum()
                        else 0.0
                    ),
                    "mean_serialized_bytes": g["memory_serialized_bytes"].mean(),
                    "perfect_per_1000_actions": (
                        1000.0 * g["perfect"].sum() / g["actions"].sum()
                        if g["actions"].sum()
                        else 0.0
                    ),
                    "wall_seconds": g["elapsed_seconds"].sum(),
                }
            )
        seed_df = pd.DataFrame(seed_rows)
        seed_df.to_csv(self.out_dir / "per_seed_summaries.csv", index=False)
        for seed, g in seed_df.groupby("seed"):
            g.to_csv(self.out_dir / f"seed_{seed}_summary.csv", index=False)

        agg_rows = []
        for (mode, phase), g in seed_df.groupby(["mode", "phase"], sort=True):
            agg_rows.append(
                {
                    "mode": mode,
                    "phase": phase,
                    "seeds_completed": g["seed"].nunique(),
                    "train_or_eval_boxes": int(g["n_boxes"].sum()),
                    "mean_terminal_score": g["mean_terminal_score"].mean(),
                    "seed_score_std": g["mean_terminal_score"].std(ddof=0),
                    "perfect_box_fraction": g["perfect_fraction"].mean(),
                    "mean_actions": g["mean_actions"].mean(),
                    "mean_undos": g["mean_undos"].mean(),
                    "ltm_hit_fraction": g["ltm_hit_fraction"].mean(),
                    "mean_serialized_memory_bytes": g["mean_serialized_bytes"].mean(),
                    "perfect_per_1000_actions": g["perfect_per_1000_actions"].mean(),
                    "wall_time_seconds": g["wall_seconds"].sum(),
                }
            )
        pd.DataFrame(agg_rows).to_csv(self.out_dir / "summary.csv", index=False)

    def _write_plots(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        window = int(self.config.get("smoothing_window", 10))
        train = df[df["phase"] == "train"]
        if not train.empty:
            fig, ax = plt.subplots(figsize=(9.5, 5.2))
            for (mode, seed), g in train.groupby(["mode", "seed"]):
                g = g.sort_values("episode")
                ax.plot(
                    g["episode"],
                    g["terminal_score"],
                    alpha=0.25,
                    lw=0.8,
                    label=None,
                )
                smooth = g["terminal_score"].rolling(window, min_periods=1).mean()
                ax.plot(
                    g["episode"],
                    smooth,
                    lw=2.0,
                    label=f"{mode} seed {seed} (rolling mean W={window})",
                )
            ax.set_xlabel("Training box")
            ax.set_ylabel("Terminal score")
            ax.set_ylim(0, 100)
            ax.set_title(f"Learning curves (smoothing window = {window} boxes)")
            ax.legend(fontsize=7, ncol=2)
            fig.tight_layout()
            fig.savefig(self.out_dir / "learning_curves.png", dpi=140)
            plt.close(fig)

        ev = df[df["phase"] == "eval"]
        if not ev.empty:
            fig, ax = plt.subplots(figsize=(8.5, 4.8))
            modes = list(ev["mode"].unique())
            seeds = sorted(ev["seed"].unique())
            width = 0.8 / max(len(seeds), 1)
            for i, seed in enumerate(seeds):
                means = [
                    ev[(ev["mode"] == m) & (ev["seed"] == seed)]["terminal_score"].mean()
                    for m in modes
                ]
                xs = [j + (i - (len(seeds) - 1) / 2) * width for j in range(len(modes))]
                ax.bar(xs, means, width=width, label=f"seed {seed}")
            ax.set_xticks(range(len(modes)))
            ax.set_xticklabels(modes)
            ax.set_ylabel("Mean evaluation terminal score")
            ax.set_ylim(0, 100)
            ax.set_title("Evaluation scores by seed (not pooled)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(self.out_dir / "evaluation_scores.png", dpi=140)
            plt.close(fig)


def run_preset(config_path: Path | None, preset: str, time_budget_seconds: float | None = None) -> Path:
    config = load_config(config_path)
    out = new_run_dir(preset)
    runner = ExperimentRunner(config=config, out_dir=out, preset=preset)
    runner.run(time_budget_seconds=time_budget_seconds)
    marker = RESULTS_DIR / "LATEST_RUN.txt"
    marker.write_text(str(out), encoding="utf-8")
    return out
