import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "Expt_16_Search_Acquired_Local_Memory" / "src"))
sys.path.insert(0, str(REPO / "Expt_17_Arrangement_Census" / "src"))
sys.path.insert(0, str(ROOT / "src"))
