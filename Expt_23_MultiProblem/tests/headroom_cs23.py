import sys, pathlib, time, json
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import cs2_programs as C2, cs3_tiles as C3
out = {}
print("CS2: solved fraction within N candidate programs (enumeration vs random), 40 tasks per split")
for sp in ("train", "test_iid", "test_comp", "test_deep", "test_const"):
    T = [C2.make_task(sp, i) for i in range(40)]
    row = {}
    for B in (500, 2000, 10000):
        t0 = time.time()
        e = np.mean([C2.enumerate_solver(t, B)[0] is not None for t in T])
        r = np.mean([C2.random_solver(t, B, np.random.default_rng((1, i)))[0] is not None for i, t in enumerate(T)])
        row[B] = (round(float(e), 3), round(float(r), 3), round(time.time() - t0, 1))
    out["cs2_" + sp] = row
    print(sp, "depth mean %.1f" % np.mean([t["depth"] for t in T]), {B: "enum %.2f rand %.2f (%.0fs)" % v for B, v in row.items()}, flush=True)
print("CS3: A*(Manhattan) expansions and random-walk success within budget; 30 tasks per split")
for sp in ("train", "test_iid", "test_deep", "test_size"):
    T = [C3.make_task(sp, i) for i in range(30)]
    ex, ln, opt, rw = [], [], [], []
    for i, t in enumerate(T):
        L, e = C3.astar(t["start"], t["R"], t["C"], 100_000, weight=1.0 if t["R"] * t["C"] <= 9 else 2.0)
        ex.append(e); ln.append(L if L else np.nan); o = C3.optimal_length(t); opt.append(o if o else np.nan)
        rw.append(C3.random_walk_solver(t["start"], t["R"], t["C"], 2000, np.random.default_rng((2, i))) is not None)
    print(sp, "A* solved %.2f mean expansions %.0f | random-walk(2000 steps) solved %.2f | mean len/opt %.2f" % (np.mean([l == l for l in ln]), np.mean(ex), np.mean(rw), np.nanmean(np.array(ln) / np.array(opt)) if np.isfinite(np.array(opt)).any() else float('nan')), flush=True)