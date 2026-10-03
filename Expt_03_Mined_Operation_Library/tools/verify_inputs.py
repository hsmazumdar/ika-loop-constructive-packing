"""Check upstream inputs, hashes, the Expt-2 cap failure, and this machine."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from mga3.experiment import dataset_hash, source_hash  # noqa: E402
from mga3.hardware import PlacementWorkspace  # noqa: E402
from mga3.pieces import catalogue_hash  # noqa: E402

CATALOGUE = "3f727dd211eccd639da03bb8e724ddfd00a6e556df043c8a71b91da111952e14"
DATASET = "668304e744f0d0ef22b164fb0e6a63a2fb065f835e170e9073a8fe3be7af53ce"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads((ROOT / "data" / "runtime" / "manifest.json").read_text(encoding="utf-8"))
    splits = manifest["splits"]
    assert set(splits) == {"train", "development", "test"}
    assert len(splits["train"]) == 24 and len(splits["development"]) == 8 and len(splits["test"]) == 12
    ids = splits["train"] + splits["development"] + splits["test"]
    assert len(ids) == len(set(ids))
    assert catalogue_hash() == CATALOGUE
    assert dataset_hash() == DATASET
    witness_hits = list(ROOT.rglob("*witness*"))
    assert not witness_hits
    expt2_pieces = REPO / "Expt_02_Autonomous_Abstraction" / "src" / "mga2" / "pieces.py"
    assert _sha(expt2_pieces) == _sha(ROOT / "src" / "mga3" / "pieces.py")
    diagnosis = REPO / "Expt_02_Autonomous_Abstraction" / "results" / "20260929_100457_diagnostic_baseline_policy" / "DIAGNOSIS.md"
    text = diagnosis.read_text(encoding="utf-8")
    profile = {
        "paths": {
            "repo": str(REPO),
            "expt1": str(REPO / "Expt_01_10x10_Packing"),
            "expt2": str(REPO / "Expt_02_Autonomous_Abstraction"),
            "expt3": str(ROOT),
        },
        "catalogue_hash": catalogue_hash(),
        "dataset_hash": dataset_hash(),
        "source_hash": source_hash(),
        "expt2_pieces_hash": _sha(expt2_pieces),
        "expt2_diagnosis_hash": _sha(diagnosis),
        "expt2_failure": "hierarchical boxes spend the 50000 candidate-eval cap inside paired THINK and can place nothing",
        "diagnosis_mentions_50000": "50,000" in text or "50000" in text,
        "witnesses_copied_into_expt3": False,
    }
    workspace = PlacementWorkspace("cuda")
    profile["device"] = workspace.device_name()
    profile["cuda_bytes"] = workspace.memory_bytes()
    out = ROOT / "data" / "input_verification.json"
    out.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(json.dumps({"status": "OK", "device": profile["device"], "catalogue_hash": profile["catalogue_hash"]}))


if __name__ == "__main__":
    main()
