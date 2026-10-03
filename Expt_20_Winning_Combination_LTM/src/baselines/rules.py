"""Plain packers on the Expt-20 task (unlimited pieces, empty 10x10 box, fill until no legal placement).

A Rule is: candidate pool -> piece filter -> placement choice.
  anchor        True: pool = legal placements covering the first (row-major) empty cell that some legal placement can cover.
                False: pool = all legal placements.
  piece         any | largest | smallest | random_type
                largest/smallest keep only candidates of the maximum/minimum piece area (all orientations and positions).
                random_type picks one piece type uniformly among the types present in the pool.
  place         first            first candidate in catalogue order (type, rotation, y, x): deterministic
                rowmajor_first   candidate whose lowest covered cell is earliest row-major, then catalogue order: deterministic
                random           uniform random candidate
                contact_first    maximum edge contact (wall + occupied neighbours), ties -> catalogue order: deterministic
                contact_random   maximum edge contact, ties -> uniform random
                score_random     maximum (1.0*area + 0.2*contact + 0.05*wall edges), the Expt-16 primitive score without its
                                 random 48-placement window, ties -> uniform random
Rules with no random step are deterministic: every box is the same box, so all 10,000 trials are identical.
Cost units as in stronger/engine.py: mask_ops (bitmask tests made while anchoring) + cand_evals (candidates scored).
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass

from mga.environment import Action, PackingEnv
from mga.pieces import N_CELLS
from stronger.engine import N_ALL, Cost, anchor_pool, contact_score
from trials import trial_seed

AREA_W, CONTACT_W, WALL_W = 1.0, 0.2, 0.05
DETERMINISTIC_PLACES = ("first", "rowmajor_first", "contact_first")


@dataclass(frozen=True)
class Rule:
    name: str
    group: str = "baseline"
    anchor: bool = True
    piece: str = "any"
    place: str = "random"
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def deterministic(self) -> bool:
        return self.piece in ("any", "largest", "smallest") and self.place in DETERMINISTIC_PLACES


def choose(rule: Rule, pool: list, occ: int, rng: random.Random, cost: Cost):
    cands = pool
    if rule.piece in ("largest", "smallest"):
        cost.cand_evals += len(cands)
        areas = [p.area for p in cands]
        target = max(areas) if rule.piece == "largest" else min(areas)
        cands = [p for p in cands if p.area == target]
    elif rule.piece == "random_type":
        types = sorted({p.piece_type for p in cands})
        t = rng.choice(types)
        cands = [p for p in cands if p.piece_type == t]
    elif rule.piece != "any":
        raise ValueError(rule.piece)
    if rule.place == "first":
        return cands[0]
    if rule.place == "random":
        return rng.choice(cands)
    if rule.place == "rowmajor_first":
        cost.cand_evals += len(cands)
        return min(enumerate(cands), key=lambda ip: ((ip[1].mask & -ip[1].mask).bit_length(), ip[0]))[1]
    if rule.place == "contact_first":
        cost.cand_evals += len(cands)
        best, best_c = None, -1
        for p in cands:
            c = contact_score(p, occ)
            if c > best_c:
                best, best_c = p, c
        return best
    if rule.place == "contact_random":
        cost.cand_evals += len(cands)
        # same draw as stronger.policies._choose_placement(select="contact"): key = (contact, rng.random()) per candidate,
        # so anchor + any piece + contact_random reproduces Expt-20's D_anchor_contact_eps0 box for box
        return max(cands, key=lambda p: (contact_score(p, occ), rng.random()))
    if rule.place == "score_random":
        cost.cand_evals += len(cands)
        scores = [round(AREA_W * p.area + CONTACT_W * (p.neighbor_mask & occ).bit_count() + WALL_W * p.boundary_contacts, 9) for p in cands]
        m = max(scores)
        return rng.choice([p for p, s in zip(cands, scores) if s == m])
    raise ValueError(rule.place)


def run_rule_trial(seed: int, trial_id: int, rule: Rule) -> dict:
    rng = random.Random(trial_seed(seed, trial_id))
    env = PackingEnv()
    cost = Cost()
    n_p = 0
    while not env.terminal:
        legal = env.legal_placements()
        cost.enum_ops += N_ALL
        if not legal:
            break
        pool = anchor_pool(env.mask, cost) if rule.anchor else legal
        if not pool:
            pool = legal
        p = choose(rule, pool, env.mask, rng, cost)
        env.step(Action.place_from(p))
        n_p += p.piece_type == "P"
    empty = sum(1 for row in env.cells for cell in row if cell is None)
    s1 = N_CELLS - empty
    assert s1 == env.occupied
    att = env.placements_count
    return {"trial_id": trial_id, "S1": s1, "attempts": att, "S2": s1 / att if att else 0.0, "n_P": n_p,
            "pieces": len(env.stack), "undos": env.undos, "actions": env.actions_used, **cost.as_dict()}


RULES: list[Rule] = [
    Rule("FF_largest_first_legal", anchor=True, piece="largest", place="first", note="first-fit: anchor, largest piece, first legal orientation/position"),
    Rule("FF_largest_random_tie", anchor=True, piece="largest", place="random"),
    Rule("FF_largest_contact_tie", anchor=True, piece="largest", place="contact_random"),
    Rule("FF_smallest_first_legal", anchor=True, piece="smallest", place="first"),
    Rule("FF_smallest_random_tie", anchor=True, piece="smallest", place="random"),
    Rule("FF_random_type_random_orient", anchor=True, piece="random_type", place="random", note="anchor, random piece type, random orientation/position"),
    Rule("FF_first_legal_any_orientation", anchor=True, piece="any", place="first", note="anchor, first legal placement in catalogue order (A rot0 ...)"),
    Rule("FF_contact_first_tie", anchor=True, piece="any", place="contact_first"),
    Rule("G_area_any_random_tie", anchor=False, piece="largest", place="random", note="greedy by area, no anchor"),
    Rule("G_area_any_rowmajor_tie", anchor=False, piece="largest", place="rowmajor_first", note="greedy by area, ties -> first row-major"),
    Rule("G_contact_any_random_tie", anchor=False, piece="any", place="contact_random", note="greedy by contact only, no anchor"),
    Rule("G_contact_any_first_tie", anchor=False, piece="any", place="contact_first"),
    Rule("G_E16score_any_random_tie", anchor=False, piece="any", place="score_random", note="Expt-16 primitive score over all legal placements"),
    Rule("FF_E16score_random_tie", anchor=True, piece="any", place="score_random"),
]