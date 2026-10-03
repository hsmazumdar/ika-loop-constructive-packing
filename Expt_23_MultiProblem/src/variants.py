"""Variants and conditions for Expt 23 (see DESIGN.md amendment A1)."""
from __future__ import annotations
import generator as G

VARIANTS = {"std": dict(obst_frac=0.06, k_range=(6, 16)), "hard": dict(obst_frac=0.25, k_range=(4, 7))}
CONDS = {"capped_nat": (14, True), "capped_any": (14, False), "unc_nat": (None, True), "unc_any": (None, False)}
TEST_SPLITS = ("test_iid", "test_size", "test_piece", "test_both")


def make(variant: str, split: str, index: int, cond: str = "capped_nat"):
    budget, _ = CONDS[cond]
    if split == "legacy":
        return G.make_problem("legacy", 0, budget)
    return G.make_problem(split, index, budget, **VARIANTS[variant])


def natural_of(cond: str) -> bool:
    return CONDS[cond][1]