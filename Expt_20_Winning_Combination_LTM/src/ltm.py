"""Long-term memory (LTM) of winning combinations. Storage only. Nothing here fills a box."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

from extract import KINDS, KIND_SIZE

LTM_SCHEMA = "expt20_winning_combination_ltm_v1"


def code_hash(root: Path) -> dict:
    files = sorted(list((root / "src").glob("*.py")) + [root / "run_expt20.py"])
    per = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    total = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(per.items())).encode()).hexdigest()
    return {"combined_sha256": total, "files": per}


def _entry(row: dict) -> dict:
    return {
        "key": row["key"], "key_str": row["key_str"], "freq_rank": row["freq_rank"],
        "n_top": row["n_top"], "n_bottom": row["n_bottom"], "n_all": row["n_all"],
        "frac_top": row["frac_top"], "frac_bottom": row["frac_bottom"], "frac_all": row["frac_all"],
        "lift_vs_bottom": row["lift_vs_bottom"], "lift_vs_all": row["lift_vs_all"],
        "z": row["z"], "winning": row["winning"],
    }


def build_ltm(tables: dict, cutoffs: dict, manifest: dict, config) -> dict:
    """tables[ranking][kind] = list of rows. Keeps the top `ltm_pattern_limit` rows by top-group frequency,
    and every row flagged winning among them. Entries are sorted by freq_rank."""
    limit = int(config.ltm_pattern_limit)
    body: dict = {}
    for ranking, per_kind in tables.items():
        body[ranking] = {}
        for kind in KINDS:
            rows = per_kind[kind][:limit]
            body[ranking][kind] = {
                "size": KIND_SIZE[kind],
                "n_rows_total": len(per_kind[kind]),
                "n_rows_kept": len(rows),
                "n_winning_kept": sum(1 for r in rows if r["winning"]),
                "entries": [_entry(r) for r in rows],
            }
    status = {r: ("DEFAULT/PRIMARY" if r == config.default_ranking else "SECONDARY") for r in tables}
    return {"schema": LTM_SCHEMA, "manifest": manifest, "cutoffs": cutoffs, "default_ranking": config.default_ranking,
            "ranking_status": status, "ltm": body}


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    return o


def save_ltm(ltm: dict, folder: Path) -> tuple[Path, Path, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    pkl = folder / "ltm.pkl"
    js = folder / "ltm.json"
    mf = folder / "ltm_manifest.json"
    with pkl.open("wb") as fh:
        pickle.dump(ltm, fh, protocol=4)
    js.write_text(json.dumps(_jsonable(ltm), indent=1), encoding="utf-8")
    man = dict(ltm["manifest"])
    man["ltm_json_sha256"] = hashlib.sha256(js.read_bytes()).hexdigest()
    man["ltm_pickle_sha256"] = hashlib.sha256(pkl.read_bytes()).hexdigest()
    mf.write_text(json.dumps(man, indent=2), encoding="utf-8")
    return js, pkl, mf


def load_ltm(path: Path) -> dict:
    with Path(path).open("rb") as fh:
        return pickle.load(fh)