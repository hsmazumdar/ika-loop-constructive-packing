"""Meta-controller: the system changes its own learning machinery from measured progress. Every change is logged.

Signals per epoch (1,000 boxes): probe S1 (fixed probe boxes, near-greedy, no learning), its EMA and gain,
training loss drift inside sleeps (instability), replay loss on old vs new episodes (forgetting / surprise).
Rules (multiplicative moves inside bounds):
  stagnation (EMA gain small for 3 epochs) AND probe still below ceiling -> mild re-explore / more dreams / lower lr
  if probe already strong (>=80): cool exploration instead of re-heating (avoid destroying a good policy)
  steady progress                           -> cool exploration (tau, eps down), fewer dreams
  loss rising within sleeps                 -> lr down, lambda up (less bootstrapping)
  loss falling smoothly                     -> lr up a little
  old-episode loss >> new-episode loss      -> larger STM (forgetting);  new >> old -> sleep more often
"""

from __future__ import annotations

import numpy as np

BOUNDS = dict(tau=(0.25, 2.5), eps=(0.005, 0.15), lr=(2e-4, 4e-3), lam=(0.7, 1.0), dream=(0.0, 1.5),
              sleep_every=(100, 400), stm=(300, 4000))

PROBE_GOOD = 80.0  # above this, never re-heat exploration


class Meta:
    def __init__(self, cfg, enabled: bool) -> None:
        self.cfg, self.enabled = cfg, enabled
        self.ema: float | None = None
        self.gains: list[float] = []
        self.events: list[dict] = []
        self.epoch = 0
        self.stag = 0
        self.stats: list[dict] = []

    def _set(self, h: dict, key: str, val: float, reason: str, box: int, probe: float) -> None:
        lo, hi = BOUNDS[key]
        val = float(min(max(val, lo), hi))
        if key in ("sleep_every", "stm"):
            val = int(round(val))
        if val != h[key]:
            self.events.append({"box": box, "epoch": self.epoch, "kind": "hyper", "param": key, "old": h[key], "new": val,
                                "reason": reason, "probe_at_change": probe})
            h[key] = val

    def end_epoch(self, agent, box: int, probe: float, sleeps: list[dict]) -> None:
        self.epoch += 1
        prev = self.ema
        self.ema = probe if prev is None else 0.5 * prev + 0.5 * probe
        gain = 0.0 if prev is None else self.ema - prev
        self.gains.append(gain)
        ls = [s for s in sleeps if s]
        rec = {"box": box, "probe": probe, "ema": self.ema, "gain": gain}
        if ls:
            l1 = np.mean([s["loss_first"] for s in ls]); l2 = np.mean([s["loss_last"] for s in ls])
            ln = np.mean([s["l_new"] for s in ls]); lo = np.mean([s["l_old"] for s in ls])
            rec.update(loss_first=l1, loss_last=l2, l_new=ln, l_old=lo, n_concepts=ls[-1]["n_concepts"])
        self.stats.append(rec)
        if not self.enabled or self.epoch < 2:
            return
        h = agent.h
        g3 = float(np.mean(self.gains[-3:])) if len(self.gains) >= 3 else gain
        stagnating = len(self.gains) >= 3 and g3 < 0.08
        improving = g3 > 0.25
        strong = probe >= PROBE_GOOD
        if stagnating:
            self.stag += 1
        else:
            self.stag = 0
        if stagnating and self.stag % 2 == 1 and not strong:
            # only re-explore when we have NOT already reached a strong probe
            self._set(h, "tau", h["tau"] * 1.12, f"stagnation (3-epoch gain {g3:+.2f}): mild re-explore", box, probe)
            self._set(h, "eps", h["eps"] * 1.2, "stagnation: mild re-explore", box, probe)
            self._set(h, "dream", max(h["dream"], 0.1) * 1.25, "stagnation: more dreaming", box, probe)
            self._set(h, "lr", h["lr"] * 0.85, "stagnation: smaller steps", box, probe)
        elif stagnating and strong:
            # plateau at a good level: cool and consolidate, do not re-heat
            self._set(h, "tau", h["tau"] * 0.92, f"plateau at strong probe {probe:.1f}: cool", box, probe)
            self._set(h, "eps", h["eps"] * 0.9, "plateau at strong probe: cool", box, probe)
            self._set(h, "lr", h["lr"] * 0.9, "plateau: smaller steps", box, probe)
            self._set(h, "lam", min(1.0, h["lam"] + 0.02), "plateau: lean toward MC returns", box, probe)
        elif improving:
            self._set(h, "tau", h["tau"] * 0.88, f"steady progress (3-epoch gain {g3:+.2f}): cool exploration", box, probe)
            self._set(h, "eps", h["eps"] * 0.88, "steady progress: cool exploration", box, probe)
        else:
            self._set(h, "tau", h["tau"] * 0.97, "slow progress: mild cooling", box, probe)
            self._set(h, "eps", h["eps"] * 0.97, "slow progress: mild cooling", box, probe)
        if ls:
            if l2 > 1.3 * l1:
                self._set(h, "lr", h["lr"] * 0.6, f"loss rising inside sleeps ({l1:.3f}->{l2:.3f})", box, probe)
                self._set(h, "lam", h["lam"] + 0.05, "unstable bootstrap: lean on returns", box, probe)
            elif l2 < 0.8 * l1 and not stagnating:
                self._set(h, "lr", h["lr"] * 1.12, f"loss falling smoothly ({l1:.3f}->{l2:.3f})", box, probe)
            if lo > 1.6 * ln:
                self._set(h, "stm", h["stm"] * 1.3, f"old-episode loss {lo:.3f} >> new {ln:.3f}: forgetting", box, probe)
            elif ln > 1.4 * lo:
                self._set(h, "sleep_every", h["sleep_every"] * 0.8, f"new-episode loss {ln:.3f} >> old {lo:.3f}: sleep sooner", box, probe)
            else:
                self._set(h, "sleep_every", h["sleep_every"] * 1.1, "replay balanced: sleep less often", box, probe)
            if improving:
                self._set(h, "dream", h["dream"] * 0.93, "progress without extra dreams: fewer dreams", box, probe)
        if agent.flags.get("growth") and box >= self.cfg.grow_min_box and self.epoch % self.cfg.grow_every_epochs == 0 and g3 < 0.2:
            res = agent.capacity_test()
            if res.get("tested"):
                self.events.append({"box": box, "epoch": self.epoch, "kind": "capacity_test", **res, "probe_at_change": probe,
                                    "reason": "widening beats same-width control on held-out replay" if res["grow"]
                                    else "capacity NOT the bottleneck (widening does not beat control)"})
