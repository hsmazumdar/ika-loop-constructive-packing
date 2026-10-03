"""Shared paths/loaders for Expt-22e (read-only on all other experiment folders)."""
import csv
import glob
import os
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]            # .../Assembly_Skill_Learning
E22 = Path(__file__).resolve().parents[1]
RUN = E22 / "results" / "20261001_122457_run"
D22B = ROOT / "Expt_22b_Organic_Value_Learner" / "results" / "20261001_034445_run"
D22C = ROOT / "Expt_22c_Long_Streams" / "results" / "20261001_044425_run"
D22D = ROOT / "Expt_22d_Long_Ablations_Saturation" / "results" / "20261001_060654_main"
D21 = ROOT / "Expt_21_Continuous_Learning_Memory" / "results" / "20260930_233539_run"
SRC22D = ROOT / "Expt_22d_Long_Ablations_Saturation" / "src"
SRC21 = ROOT / "Expt_21_Continuous_Learning_Memory" / "src"
EVAL_SEED = 7_700_000


def ld(p):
    with open(p, "rb") as fh:
        return pickle.load(fh)


def streams(d, variant=None, sub="streams"):
    out = []
    for p in sorted(glob.glob(str(d / sub / (f"{variant}_s*.pkl" if variant else "*.pkl")))):
        r = ld(p)
        r["_file"] = os.path.basename(p)
        out.append(r)
    return out


def ho(rs, k):
    """held-out S1 mean per stream at checkpoint k (streams lacking k skipped)"""
    return np.array([r["evals"][k]["S1"].mean() for r in rs if k in r["evals"]])


def write_csv(path, rows):
    rows = list(rows)
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval="")
        w.writeheader()
        w.writerows(rows)
