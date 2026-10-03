"""One continuous learning stream (one replicate of one variant). Sequential by nature: one box at a time."""

from __future__ import annotations

import time

import numpy as np

import engine as E
from analysis import saturation_test
from config import VARIANTS, Cfg
from learner import Episode, Memory, play_box


def schedule(cfg: Cfg, i: int) -> tuple[float, float]:
    f = min(1.0, i / cfg.anneal_boxes)
    return cfg.tau0 + (cfg.tau_min - cfg.tau0) * f, cfg.eps0 + (cfg.eps_min - cfg.eps0) * f


def evaluate(mem: Memory, cfg: Cfg, n: int | None = None) -> dict:
    """Frozen memory, fixed held-out streams (eval_seed + j), near-greedy softmax, no epsilon, no learning."""
    n = n or cfg.eval_boxes
    s1 = np.zeros(n, dtype=np.int16)
    att = np.zeros(n, dtype=np.int16)
    for j in range(n):
        b = play_box(mem, np.random.default_rng(cfg.eval_seed + j), cfg.tau_eval, 0.0)
        s1[j], att[j] = b.s1, b.n
    return {"S1": s1, "attempts": att}


def run_stream(variant: str, seed: int, max_boxes: int, cfg: Cfg | None = None, log=None, log_every: int = 5000) -> dict:
    cfg = cfg or Cfg()
    learn, sleep, dream, growth = VARIANTS[variant]
    rng = np.random.default_rng(seed * 7919 + 13)
    mem = Memory(cfg)
    if growth == "upfront":
        for g in range(1, len(cfg.stages)):
            mem.grow_to(g)
    s1 = np.zeros(max_boxes, dtype=np.int16)
    att = np.zeros(max_boxes, dtype=np.int16)
    stm: list[Episode] = []
    events: list[dict] = []
    stage_ends: dict[int, float] = {}
    evals: dict[int, dict] = {}
    stage_start, flat, stop_reason, n_done = 0, 0, "max_boxes", 0
    W = cfg.sat_window
    ckpts = set(c for c in cfg.checkpoints if c <= max_boxes)
    t0 = time.time()

    def do_eval(i):
        r = evaluate(mem, cfg)
        r["stage"] = mem.stage
        r["mem"] = mem.stats()["entries"]
        evals[i] = r

    for i in range(max_boxes):
        if i in ckpts:
            do_eval(i)
        tau, eps = schedule(cfg, i)
        box = play_box(mem, rng, tau, eps)
        s1[i], att[i] = box.s1, box.n
        n_done = i + 1
        if learn:
            stm.append(Episode(box.placed, box.s1))
            cap = int(cfg.stm_boxes * mem.stm_mult)
            if len(stm) > cap:
                del stm[: len(stm) - cap]
            if sleep:
                if n_done % cfg.sleep_every == 0:
                    mem.sleep(stm, cfg.sleep_every, rng, tau, dream)
            else:
                mem.learn_online(stm[-1])
        if growth == "sat" and n_done % cfg.check_every == 0:
            n_stage = n_done - stage_start
            if n_done >= cfg.anneal_boxes and n_stage >= 2 * W:
                last, prev = s1[n_done - W:n_done], s1[n_done - 2 * W:n_done - W]
                sat, gain, se = saturation_test(prev, last, cfg.sat_delta, cfg.sat_z)
                forced = n_stage >= cfg.max_stage_boxes
                if sat or forced:
                    if n_done not in evals:
                        do_eval(n_done)  # held-out snapshot at the end of every stage
                    stage_ends[mem.stage] = float(last.mean())
                    stage_gain = stage_ends[mem.stage] - stage_ends[mem.stage - 1] if mem.stage > 0 else None
                    if mem.stage > 0:
                        flat = flat + 1 if stage_gain < cfg.sat_delta else 0
                    ev = {"box": n_done, "stage_done": mem.stage, "reason": "saturated" if sat else "forced_max_stage_boxes",
                          "window_gain": gain, "window_se": se, "mean_at_end_of_stage": stage_ends[mem.stage],
                          "stage_gain_vs_prev_stage": stage_gain, "memory_entries": mem.stats()["entries"],
                          "heldout_S1": float(evals[n_done]["S1"].mean())}
                    if mem.stage + 1 >= len(cfg.stages):
                        ev["to_stage"] = None
                        events.append(ev)
                        if n_done >= cfg.min_boxes:
                            stop_reason = "saturated_at_final_stage"
                            break
                    else:
                        if flat >= cfg.stop_after_flat_stages and n_done >= cfg.min_boxes:
                            ev["to_stage"] = None
                            events.append(ev)
                            stop_reason = f"{flat}_consecutive_growth_stages_without_gain"
                            break
                        new = mem.grow_to(mem.stage + 1)
                        mem.reconsolidate(stm, new)
                        ev["to_stage"] = mem.stage
                        ev["to_name"] = cfg.stages[mem.stage][0]
                        events.append(ev)
                        stage_start = n_done
        if log is not None and n_done % log_every == 0:
            log(f"[{variant} s{seed}] box {n_done} stage {mem.stage} S1(last {log_every}) {s1[n_done-log_every:n_done].mean():.2f} "
                f"entries {mem.stats()['entries']} {time.time()-t0:.0f}s")
    # final evaluation at the actual end (not already a checkpoint)
    if n_done not in evals:
        do_eval(n_done)
    stage_ends.setdefault(mem.stage, float(s1[max(0, n_done - W):n_done].mean()))
    return {"variant": variant, "seed": seed, "n_boxes": n_done, "S1": s1[:n_done], "attempts": att[:n_done],
            "events": events, "stage_ends": stage_ends, "evals": evals, "stop_reason": stop_reason,
            "runtime_s": time.time() - t0, "memory": mem.summary(), "final_stage": mem.stage, "mem_obj": mem}