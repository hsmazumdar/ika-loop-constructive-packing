"""Project folder layout for Expt_01_10x10_Packing."""

from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
CONFIGS_DIR = ROOT / "configs"
TESTS_DIR = ROOT / "tests"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

for _folder in (DATA_DIR, RESULTS_DIR, CONFIGS_DIR, SNAPSHOTS_DIR):
    _folder.mkdir(parents=True, exist_ok=True)
