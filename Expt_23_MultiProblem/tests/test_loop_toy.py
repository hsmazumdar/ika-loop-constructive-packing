import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import loop as L

class ToyDomain(L.Domain):
    """Task = hidden preference vector over 6 arms (+ noise). Episode = pick 5 arms (with repeats), outcome = sum of payoffs.
    A shared structure (arm 0..2 good in every task) is what the store can learn and transfer to held-out tasks."""
    def sample_task(self, split, rng, index=None):
        w = np.array([1.0, 0.8, 0.6, 0.0, -0.4, -0.8]) + 0.3 * rng.standard_normal(6)
        return w
    def task_id(self, task): return repr(task.round(3).tolist())
    def reference_score(self, task): return 5 * task.max()
    def act(self, task, store, mode, rng, temperature, eps):
        picks = []
        for _ in range(5):
            if mode == "random" or store is None:
                a = int(rng.integers(6))
            else:
                v = store.score()
                z = np.exp((v - v.max()) / max(temperature, 1e-3)); p = z / z.sum(); p = (1 - eps) * p + eps / 6
                a = int(rng.choice(6, p=p))
            picks.append(a)
        return L.Experience("t", picks, float(task[picks].sum()))

class ToyStore(L.KnowledgeStore):
    def __init__(self): self.fast = np.zeros(6); self.slow = np.zeros(6); self.n = np.ones(6); self.buf = []
    def score(self): return self.slow
    def observe(self, e):
        self.buf.append(e)
    def consolidate(self):
        for e in self.buf:
            for a in e.trace:
                self.n[a] += 1; self.fast[a] += (e.outcome / 5 - self.fast[a]) / self.n[a]
        self.slow = 0.7 * self.slow + 0.3 * self.fast; self.buf = []
        return {}
    def freeze(self):
        c = ToyStore(); c.slow = self.slow.copy(); return c

def run(mode, cons, seed):
    cfg = L.LoopConfig(n_experiences=400, sleep_every=20, consolidate=cons, mode=mode, anneal=200,
                       checkpoints=(0, 100, 400), seed=seed)
    return L.run_loop(ToyDomain(), ToyStore(), cfg)

def test_loop_runs_and_is_deterministic():
    a, b = run("guided", True, 0), run("guided", True, 0)
    assert a["curve"] == b["curve"]
    assert set(a["curve"]) == {0, 100, 400}

def test_toy_loop_shows_the_expected_ordering():
    g = np.mean([run("guided", True, s)["curve"][400]["test_iid"] for s in range(6)])
    r = np.mean([run("random", True, s)["curve"][400]["test_iid"] for s in range(6)])
    n = np.mean([run("guided", False, s)["curve"][400]["test_iid"] for s in range(6)])
    g0 = np.mean([run("guided", True, s)["curve"][0]["test_iid"] for s in range(6)])
    assert g > g0 + 0.1          # improves across iterations
    assert n < g                 # without consolidation the store never reaches the evaluation copy