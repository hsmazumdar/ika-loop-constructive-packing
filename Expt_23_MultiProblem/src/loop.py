"""Domain-agnostic information -> knowledge -> information loop (Expt 23).

Three interfaces, one driver. Nothing here knows about packing, equations or puzzles.

  Domain          information source: samples tasks (train / held-out splits) and executes an action on a task,
                  returning an Experience (observation trace + outcome). Also provides the task-level normaliser.
  KnowledgeStore  compact reusable knowledge: score(task, options) guides action choice; observe(experience) writes
                  fast (short-term) memory; consolidate() turns recent experience into the slow store (replay, dreams,
                  EMA, concept promotion ... whatever the instance implements); freeze() gives the evaluation-time copy.
  Generator       knowledge-guided information generation: given a task and a store, produce Experiences.
                  mode 'guided'  = actions chosen from the store's scores (softmax/eps from a schedule)
                  mode 'random'  = actions chosen uniformly from the domain's action set (store ignored for choosing)

The driver `run_loop` repeats: sample train task -> generate (guided|random) -> observe -> every `sleep_every`
experiences consolidate (or not) -> at checkpoints evaluate the FROZEN store on held-out tasks with the same generator
in greedy-ish mode. Learner updates per experience are identical across arms (a compute-matching requirement).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

import numpy as np


@dataclass
class Experience:
    task_id: str
    trace: Any          # domain-specific record of what was tried (placements, expressions, moves ...)
    outcome: float      # raw outcome (S1, fit error, solved flag ...)
    cost: float = 1.0   # information-gathering cost (episodes, evaluations, node expansions)


class Domain(ABC):
    @abstractmethod
    def sample_task(self, split: str, rng: np.random.Generator, index: int | None = None) -> Any: ...
    @abstractmethod
    def task_id(self, task) -> str: ...
    @abstractmethod
    def reference_score(self, task) -> float:
        """Reference (e.g. beam-search / oracle) outcome used ONLY to normalise reported scores; never given to a learner."""
    @abstractmethod
    def act(self, task, store: "KnowledgeStore | None", mode: str, rng: np.random.Generator, temperature: float,
            eps: float) -> Experience:
        """One unit of information gathering on `task` (an episode, a candidate-expression batch, a search ...)."""


class KnowledgeStore(ABC):
    @abstractmethod
    def observe(self, exp: Experience) -> None: ...
    @abstractmethod
    def consolidate(self) -> dict: ...
    @abstractmethod
    def freeze(self) -> "KnowledgeStore": ...
    def size(self) -> int:
        return 0


@dataclass
class LoopConfig:
    n_experiences: int = 1000
    sleep_every: int = 100
    consolidate: bool = True
    mode: str = "guided"                 # 'guided' | 'random'
    tau0: float = 2.0
    tau_min: float = 0.25
    eps0: float = 0.10
    eps_min: float = 0.01
    anneal: int = 500
    checkpoints: Sequence[int] = (0, 250, 500, 1000)
    eval_tasks: int = 10
    eval_reps: int = 4
    seed: int = 0
    eval_splits: Sequence[str] = ("test_iid",)


def run_loop(domain: Domain, store: KnowledgeStore, cfg: LoopConfig, log: Callable[[str], None] | None = None) -> dict:
    """Returns {'curve': {ckpt: {split: normalised mean}}, 'raw': ..., 'train_outcomes': [...], 'gen_quality': [...]}"""
    rng = np.random.default_rng(cfg.seed * 7919 + 13)
    out = {"curve": {}, "raw": {}, "train_outcomes": [], "cost": 0.0}
    ck = sorted(set(cfg.checkpoints) | {cfg.n_experiences})

    def evaluate(i):
        fz = store.freeze()
        res, raw = {}, {}
        for sp in cfg.eval_splits:
            vals, rv = [], []
            for t in range(cfg.eval_tasks):
                task = domain.sample_task(sp, np.random.default_rng((cfg.seed, 99, t)), t)
                ref = domain.reference_score(task)
                for r in range(cfg.eval_reps):
                    e = domain.act(task, fz, "guided", np.random.default_rng((cfg.seed, 7, t, r)), cfg.tau_min, 0.0)
                    rv.append(e.outcome)
                    vals.append(e.outcome / ref)
            res[sp], raw[sp] = float(np.mean(vals)), float(np.mean(rv))
        out["curve"][i], out["raw"][i] = res, raw

    for i in range(cfg.n_experiences):
        if i in ck:
            evaluate(i)
        f = min(1.0, i / max(cfg.anneal, 1))
        tau, eps = cfg.tau0 + (cfg.tau_min - cfg.tau0) * f, cfg.eps0 + (cfg.eps_min - cfg.eps0) * f
        task = domain.sample_task("train", rng)
        e = domain.act(task, store, cfg.mode, rng, tau, eps)
        out["train_outcomes"].append(e.outcome / domain.reference_score(task))
        out["cost"] += e.cost
        store.observe(e)
        if cfg.consolidate and (i + 1) % cfg.sleep_every == 0:
            store.consolidate()
    if cfg.n_experiences not in out["curve"]:
        evaluate(cfg.n_experiences)
    return out