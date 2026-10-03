import random

from mga.environment import Action, PackingEnv, replay_trace
from mga.pieces import ALL_PLACEMENTS, PIECES, placed_cells


def test_bounds_negative_overlap_atomic():
    env = PackingEnv()
    r = env.step(Action.place("B", 0, -1, 0))
    assert r.invalid and r.consumed_action and env.occupied == 0
    r = env.step(Action.place("B", 0, 0, 9))
    assert r.invalid and env.occupied == 0
    r = env.step(Action.place("B", 0, 0, 0))
    assert r.accepted
    r = env.step(Action.place("B", 0, 0, 0))
    assert r.invalid and env.occupied == 5


def test_corner_and_edge_placements():
    env = PackingEnv()
    # 1-cell offset near far corner with tetromino M vertical
    r = env.step(Action.place("M", 0, 9, 6))
    assert r.accepted
    env.reset_box()
    r = env.step(Action.place("M", 0, 9, 7))
    assert r.invalid


def test_distinct_instance_ids_and_adjacent_same_type():
    env = PackingEnv()
    a = env.step(Action.place("M", 0, 0, 0))
    b = env.step(Action.place("M", 0, 1, 0))
    assert a.instance_id != b.instance_id
    assert env.cells[0][0][1] != env.cells[0][1][1]
    assert env.cells[0][0][0] == env.cells[0][1][0] == "M"


def test_undo_restores_exactly():
    env = PackingEnv()
    env.step(Action.place("P", 0, 0, 0))
    mask = env.mask
    env.step(Action.place("O", 0, 3, 0))
    r = env.step(Action.undo())
    assert r.accepted
    assert env.mask == mask
    assert env.undos == 1


def test_score_blank_consistency_and_undo_reduces_score():
    env = PackingEnv()
    env.step(Action.place("P", 0, 0, 0))
    assert env.score == 7
    assert env.blanks == 93
    env.step(Action.undo())
    assert env.score == 0


def test_action_accounting_and_terminal_protection():
    env = PackingEnv()
    env.step(Action.submit())
    assert env.terminal
    used = env.actions_used
    r = env.step(Action.place("B", 0, 0, 0))
    assert not r.consumed_action
    assert env.actions_used == used
    assert env.occupied == 0


def test_empty_board_submit_and_invalid_empty_undo():
    env = PackingEnv()
    r = env.step(Action.undo())
    assert r.invalid and r.consumed_action
    env.reset_box()
    r = env.step(Action.submit())
    assert r.accepted and env.score == 0 and env.terminal


def test_full_board_auto_finish():
    env = PackingEnv()
    # Fill with vertical B.
    for x in range(10):
        for y in (0, 5):
            r = env.step(Action.place("B", 0, x, y))
            assert r.accepted, r.reason
    assert env.terminal
    assert env.termination_reason == "board_full"
    assert env.score == 100
    assert env.actions_used == 20


def test_action_limit_finish():
    env = PackingEnv(budget=3)
    env.step(Action.place("B", 0, 0, 0))
    env.step(Action.undo())
    env.step(Action.place("B", 0, 1, 0))
    assert env.terminal
    assert env.termination_reason == "action_limit"
    assert env.actions_used == 3
    assert env.score == 5


def test_invariants_random_500():
    rng = random.Random(2026)
    env = PackingEnv()
    for _ in range(500):
        if env.terminal:
            env.reset_box()
        kind = rng.choice(["PLACE", "PLACE", "PLACE", "UNDO", "SUBMIT"])
        if kind == "UNDO":
            env.step(Action.undo())
        elif kind == "SUBMIT" and rng.random() < 0.02:
            env.step(Action.submit())
        else:
            ptype = rng.choice(list(PIECES))
            rot = rng.randint(0, 3)
            x = rng.randint(-1, 10)
            y = rng.randint(-1, 10)
            env.step(Action.place(ptype, rot, x, y))
        env.invariants()
        for inst in env.stack:
            for x, y in inst.cells:
                assert 0 <= x < 10 and 0 <= y < 10
        assert 0 <= env.score <= 100


def test_replay_trace_reproduces_board():
    env = PackingEnv()
    env.step(Action.place("C", 0, 0, 0))
    env.step(Action.place("C", 1, 2, 0))
    env.step(Action.undo())
    env.step(Action.place("M", 0, 5, 0))
    trace = list(env.trace)
    replayed = replay_trace(trace)
    assert replayed.mask == env.mask
    assert replayed.score == env.score
    assert replayed.occupancy_grid() == env.occupancy_grid()
