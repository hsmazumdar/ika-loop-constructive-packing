"""Why did Test 2 store no local entries? Replay store trajectories and describe bounded regions.

For every bounded free region (size within the configured range) that appears during a store
trajectory, report how much of it is later covered by pieces lying entirely inside it, and what
the final state of those cells is. Diagnostic only; not part of the billed experiment.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from config import diagnostic_config  # noqa: E402
from experiment import load_json_tasks  # noqa: E402
from local_memory import all_regions  # noqa: E402
from pieces import bit_for, placed_cells  # noqa: E402
from policy_exact import solve_primitive  # noqa: E402


def probe(stack, lo, hi):
    masks, cell_sets = [], []
    for piece, rotation, x, y in stack:
        cells = placed_cells(piece, rotation, x, y)
        cell_sets.append(set(cells))
        m = 0
        for c in cells:
            m |= bit_for(*c)
        masks.append(m)
    final_occ = set().union(*cell_sets) if cell_sets else set()
    seen = set()
    out = []
    occupied = 0
    for t in range(len(stack) + 1):
        if t > 0:
            occupied |= masks[t - 1]
        regions, _ = all_regions(occupied, lo, hi)
        for comp in regions:
            key = tuple(sorted(comp))
            if key in seen:
                continue
            seen.add(key)
            region = set(comp)
            inside = set()
            n_inside = 0
            for j in range(t, len(stack)):
                if cell_sets[j] <= region:
                    inside |= cell_sets[j]
                    n_inside += 1
            out.append({
                "t": t,
                "n_placed": len(stack),
                "size": len(region),
                "covered_inside": len(inside),
                "final_filled": len(region & final_occ),
                "n_inside": n_inside,
            })
    return out


def main():
    config = diagnostic_config()
    lo, hi = int(config.region_min_cells), int(config.region_max_cells)
    tasks = load_json_tasks(ROOT / "data" / "store.json")[: int(config.n_store_independent)]
    tasks += json.loads((ROOT / "data" / "family_store.json").read_text(encoding="utf-8"))["tasks"]
    recs = []
    for seed in config.store_seeds:
        for index, task in enumerate(tasks):
            prim = solve_primitive(config, task, seed, "expt15-t2-store", index)
            if prim["acceptable"]:
                recs += probe(prim["stack"], lo, hi)
    n = len(recs)
    print(json.dumps({
        "n_trajectories": len(tasks) * len(config.store_seeds),
        "n_regions": n,
        "regions_per_trajectory": n / max(1, len(tasks) * len(config.store_seeds)),
        "size_hist": dict(sorted(Counter(r["size"] for r in recs).items())),
        "appear_at_placements_left": dict(sorted(Counter(r["n_placed"] - r["t"] for r in recs).items())),
        "exactly_filled_by_inside": sum(r["covered_inside"] == r["size"] for r in recs),
        "final_empty_cells_hist": dict(sorted(Counter(r["size"] - r["final_filled"] for r in recs).items())),
        "any_inside_piece": sum(r["n_inside"] > 0 for r in recs),
        "mean_covered_fraction": sum(r["covered_inside"] / r["size"] for r in recs) / max(1, n),
    }, indent=2))


if __name__ == "__main__":
    main()
