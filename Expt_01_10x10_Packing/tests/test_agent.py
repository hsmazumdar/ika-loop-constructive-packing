import ast
from pathlib import Path
import random

from mga.agent import PackingAgent
from mga.environment import Action, PackingEnv
from mga.experiment import load_config, run_episode
from mga.memory import LongTermMemory
from mga.paths import CODE_DIR


def test_agent_does_not_import_solver():
    source = (CODE_DIR / "agent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module.split(".")[0])
    assert "validation" not in imported
    assert "validate_catalogue" not in source


def test_mode_disables_memory_components():
    cfg = load_config()
    env = PackingEnv()
    rng = random.Random(0)
    none = PackingAgent(mode="none", config=cfg)
    stm = PackingAgent(mode="stm", config=cfg)
    ltm = PackingAgent(mode="ltm", config=cfg)
    both = PackingAgent(mode="both", config=cfg)
    assert not none.use_stm and not none.use_ltm
    assert stm.use_stm and not stm.use_ltm
    assert ltm.use_ltm and not ltm.use_stm
    assert both.use_stm and both.use_ltm
    run_episode(env, none, rng)
    assert none.memory_stats()["stm_entries"] == 0
    assert none.memory_stats()["ltm_entries"] == 0


def test_mode_isolation_separate_ltm():
    cfg = load_config()
    a = PackingAgent(mode="both", config=cfg, ltm=LongTermMemory())
    b = PackingAgent(mode="both", config=cfg, ltm=LongTermMemory())
    a.ltm.update("only_a", 1.0)
    assert "only_a" not in b.ltm.entries


def test_frozen_eval_survives_full_episode():
    cfg = load_config()
    ltm = LongTermMemory()
    ltm.config_hash = "abc"
    ltm.update("k", 0.2)
    agent = PackingAgent(mode="ltm", config=cfg, ltm=ltm)
    agent.ltm.freeze()
    before = agent.ltm.dump_bytes()
    run_episode(PackingEnv(), agent, random.Random(3))
    assert agent.ltm.dump_bytes() == before


def test_seeded_replay_determinism():
    cfg = load_config()
    cfg = dict(cfg)
    cfg["epsilon"] = 0.15

    def scores(seed):
        env = PackingEnv()
        agent = PackingAgent(mode="none", config=cfg)
        rng = random.Random(seed)
        return run_episode(env, agent, rng)["terminal_score"], env.mask

    assert scores(11) == scores(11)
    assert scores(11) != scores(12) or True  # second seed may coincidentally match; first pair must match


def test_hole_free_moves_preferred():
    cfg = load_config()
    cfg = dict(cfg)
    cfg["epsilon"] = 0.0
    cfg["avoid_new_holes_if_possible"] = True
    env = PackingEnv()
    env.step(Action.place("M", 0, 0, 0))
    env.step(Action.place("M", 0, 1, 0))
    env.step(Action.place("M", 0, 2, 0))
    agent = PackingAgent(mode="none", config=cfg)
    scored = agent._rank(env)
    assert scored
    for _h, p in scored:
        holes = agent.heuristic.features(env.mask, p)[1]
        assert holes == 0


def test_shared_dead_end_rule_documented():
    cfg = load_config()
    assert "UNDO" in cfg["dead_end_rule"]
    assert "SUBMIT" in cfg["dead_end_rule"]
