"""One continuous stream for one (variant, replicate)."""

from __future__ import annotations

import time

import numpy as np

import engine as E
from agent import Agent
from config import VARIANTS, Cfg
from meta import Meta


def evaluate(agent: Agent, cfg: Cfg, n: int, budget: int, net=None, seed0: int | None = None) -> dict:
    """Frozen memory (slow = consolidated LTM net + concept library), fixed fresh boxes, near-greedy softmax, no learning."""
    net = net or agent.memory_net()
    s1 = np.zeros(n, np.int16)
    att = np.zeros(n, np.int16)
    sd = cfg.eval_seed if seed0 is None else seed0
    for j in range(n):
        b, _ = agent.play(np.random.default_rng(sd + j), cfg.tau_eval, 0.0, budget, net=net, record=False)
        s1[j], att[j] = b.s1, b.n
    return {"S1": s1, "attempts": att}


def sched(cfg: Cfg, i: int):
    f = min(1.0, i / cfg.anneal_boxes)
    return cfg.tau0 + (cfg.tau_min - cfg.tau0) * f, cfg.eps0 + (cfg.eps_min - cfg.eps0) * f


def run_stream(variant: str, seed: int, cfg: Cfg, n_boxes: int | None = None, log=None, extra_ckpts=()) -> dict:
    flags = VARIANTS[variant]
    n_boxes = n_boxes or cfg.n_boxes
    ag = Agent(cfg, flags, seed)
    meta = Meta(cfg, flags["meta"])
    rng = np.random.default_rng(seed * 7919 + 13)
    s1 = np.zeros(n_boxes, np.int16)
    att = np.zeros(n_boxes, np.int16)
    ck = sorted(set(c for c in list(cfg.checkpoints) + list(extra_ckpts) if c <= n_boxes) | {n_boxes})
    evals: dict[int, dict] = {}
    hyper_log: list[dict] = []
    probe_ids = cfg.eval_seed + 500_000
    sleeps_epoch: list[dict] = []
    t0 = time.time()
    last_hid = ag.hidden

    def do_eval(i):
        r = evaluate(ag, cfg, cfg.eval_boxes, cfg.budget)
        r.update(hidden=ag.hidden, concepts=int(ag.lib.keys.size), hyper=dict(ag.h), sleeps=ag.sleeps)
        evals[i] = r

    for i in range(n_boxes):
        if i in ck:
            do_eval(i)
        if flags["sched"]:
            ag.h["tau"], ag.h["eps"] = sched(cfg, i)
        box, ep = ag.play(rng, ag.h["tau"], ag.h["eps"], cfg.budget)
        s1[i], att[i] = box.s1, box.n
        n = i + 1
        if flags["learn"] and ep is not None:
            ag.remember(ep)
            if flags["online"]:
                ag.online_step(ep)
            if flags["sleep"] and ag.new_since_sleep >= ag.h["sleep_every"]:
                sleeps_epoch.append(ag.sleep(flags["dream"], cfg.budget))
        if flags["learn"] and n % cfg.epoch == 0:
            probe = evaluate(ag, cfg, cfg.probe_boxes, cfg.budget, seed0=probe_ids)["S1"].mean()
            meta.end_epoch(ag, n, float(probe), sleeps_epoch)
            sleeps_epoch = []
            hyper_log.append({"box": n, "probe": float(probe), **{k: float(v) for k, v in ag.h.items()}, "hidden": ag.hidden,
                              "concepts": int(ag.lib.keys.size)})
        if log and n % 2000 == 0:
            log(f"[{variant} s{seed}] box {n} train S1 {s1[n-2000:n].mean():.2f} hidden {ag.hidden} concepts {ag.lib.keys.size} "
                f"tau {ag.h['tau']:.2f} eps {ag.h['eps']:.3f} lr {ag.h['lr']:.4f} {time.time()-t0:.0f}s")
    if n_boxes not in evals:
        do_eval(n_boxes)
    return {"variant": variant, "seed": seed, "n_boxes": n_boxes, "S1": s1, "attempts": att, "evals": evals,
            "hyper_log": hyper_log, "events": meta.events, "meta_stats": meta.stats, "runtime_s": time.time() - t0,
            "final_h": dict(ag.h), "agent": ag}