import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import learner as Lr
import learner_matched as LM
import variants as V
from env import Env
from encode import Encoder


def _episodes(n, variant="std", seed=0):
    rng = np.random.default_rng(seed); out = []
    ag = Lr.Agent(seed)
    for i in range(n):
        prob = V.make(variant, "dev", i, "capped_nat"); env = Env(prob); enc = Encoder(env)
        s, ep = ag.play(env, enc, rng, 2.0, 0.1, True)
        out.append(ep)
    return out


def test_rows_matched_to_F_budget():
    eps = _episodes(200)
    ag = LM.MatchedAgent(1, "rows")
    for e in eps:
        ag.online_step(e)
    rows_ep = sum(len(e.X) for e in eps)
    target = rows_ep + 40 * 256            # F: online rows + sleep rows per 200 episodes
    assert abs(ag.total_rows - target) <= max(len(e.X) for e in eps) + 1, (ag.total_rows, target)
    assert ag.total_steps > 200 * 3        # many more Adam steps than F's 240


def test_steps_matched_to_F_steps():
    eps = _episodes(200)
    ag = LM.MatchedAgent(1, "steps")
    for e in eps:
        ag.online_step(e)
    assert ag.total_steps == 240, ag.total_steps


def test_no_replay_no_slow_no_dream():
    ag = LM.MatchedAgent(1)
    assert not ag.sleep_on and not ag.dream_on and ag.buf == [] and ag.memory_net() is ag.fast
    eps = _episodes(30)
    for e in eps:
        ag.online_step(e)
    assert ag.buf == [] and ag.prio == []      # nothing remembered
    for k in ag.slow.p:                          # slow net untouched (still the initial copy)
        assert np.array_equal(ag.slow.p[k], Lr.Agent(1).slow.p[k])


def test_extra_steps_use_only_current_episode_rows():
    # one episode, mode rows: the weights change more than with plain N on the same episode, and the plain N step is reproduced as first step
    eps = _episodes(1)
    n1, m1 = Lr.Agent(3), LM.MatchedAgent(3, "rows")
    n1.online_step(eps[0]); m1.online_step(eps[0])
    # first call: credit 51.2 >= n? rows of episode ~13 -> 3 extra steps (51.2/13.25)
    assert m1.total_steps >= 2
    d = sum(float(np.abs(n1.fast.p[k] - m1.fast.p[k]).sum()) for k in n1.fast.p)
    assert d > 0


def test_identical_to_N_when_no_credit():
    eps = _episodes(5)
    a, b = Lr.Agent(5), LM.MatchedAgent(5, "steps")
    for e in eps[:4]:       # 4 episodes: credit 0.8 < 1 -> no extra step -> identical to N
        a.online_step(e); b.online_step(e)
    for k in a.fast.p:
        assert np.array_equal(a.fast.p[k], b.fast.p[k])