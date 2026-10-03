"""Freeze Expt-16 problem sets once. Runs load these manifests; nothing is regenerated per run.

- acquisition_store: the Expt-15 store set that produced the 128-region census (8 independent +
  8 family boxes, copied from Expt-15 data with source hashes).
- applicability_{fresh,family}: fresh ordinary inventories for read-only matching.
- validation_{fresh,family}: a further fresh set, reserved for a deployed policy only.

Generation is time-budgeted, which is why its output is saved here rather than reproduced.
Refuses to overwrite existing manifests.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from family_gen import sample_family_stream  # noqa: E402
from tools.generate_boxes import generate  # noqa: E402

MANIFESTS = ROOT / "manifests"
EXPT15_DATA = ROOT.parent / "Expt_15_Local_Subproblem_Memory" / "data"
N_STORE_INDEPENDENT = 8
N_STREAMS = 4
N_PER_STREAM = 15
SEED = 2026093022


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(name: str, payload: dict) -> Path:
    path = MANIFESTS / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _fresh(label: str, seed_offset: int) -> list[dict]:
    tasks = []
    for sid in range(N_STREAMS):
        out_name = f"expt16_{label}_fresh_s{sid}"
        generate(target=N_PER_STREAM, timeout=600.0, seed=SEED + seed_offset + sid, out_name=out_name)
        data = json.loads((ROOT / "data" / f"{out_name}.json").read_text(encoding="utf-8"))["tasks"][:N_PER_STREAM]
        if len(data) < N_PER_STREAM:
            raise RuntimeError(f"{out_name}: {len(data)} boxes")
        for t in data:
            t["workload"] = "independent_fresh"
            t["stream_id"] = sid
            t["constructed_prefix"] = None
        tasks += data
    return tasks


def _family(specs: list[dict], seed_offset: int) -> list[dict]:
    tasks = []
    for sid in range(N_STREAMS):
        fam = sample_family_stream(specs, N_PER_STREAM, SEED + seed_offset + sid)
        for t in fam:
            t["stream_id"] = sid
        tasks += fam
    return tasks


def main() -> None:
    MANIFESTS.mkdir(exist_ok=True)
    if any(MANIFESTS.glob("*.json")):
        raise SystemExit("manifests already frozen; refusing to overwrite")
    (ROOT / "data").mkdir(exist_ok=True)
    src_store = EXPT15_DATA / "store.json"
    src_family = EXPT15_DATA / "family_store.json"
    independent = json.loads(src_store.read_text(encoding="utf-8"))["tasks"][:N_STORE_INDEPENDENT]
    for t in independent:
        t["workload"] = "store_independent"
        t["constructed_prefix"] = None
    fam_payload = json.loads(src_family.read_text(encoding="utf-8"))
    specs = fam_payload["specs"]
    paths = [
        _write("acquisition_store", {
            "tasks": independent + fam_payload["tasks"],
            "specs": specs,
            "source": {
                "store": "Expt_15_Local_Subproblem_Memory/data/store.json",
                "store_sha256": sha256(src_store),
                "family_store": "Expt_15_Local_Subproblem_Memory/data/family_store.json",
                "family_store_sha256": sha256(src_family),
                "n_store_independent": N_STORE_INDEPENDENT,
            },
        })
    ]
    paths.append(_write("applicability_fresh", {"tasks": _fresh("applicability", 100)}))
    paths.append(_write("applicability_family", {"tasks": _family(specs, 200), "specs": specs}))
    paths.append(_write("validation_fresh", {"tasks": _fresh("validation", 300)}))
    paths.append(_write("validation_family", {"tasks": _family(specs, 400), "specs": specs}))
    hashes = {p.name: sha256(p) for p in paths}
    (MANIFESTS / "MANIFEST_HASHES.txt").write_text("\n".join(f"{h}  {n}" for n, h in hashes.items()) + "\n", encoding="utf-8")
    print(json.dumps(hashes, indent=2))


if __name__ == "__main__":
    main()
