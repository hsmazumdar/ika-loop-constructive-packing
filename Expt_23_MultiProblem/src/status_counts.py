"""Exact job counts: baseline streams (done / started-not-done / not started / dropped (A4) / total) and E-streams. Writes results/status_counts.md and prints it."""
import sys, re, pathlib, datetime, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ROOT = pathlib.Path(__file__).resolve().parents[1]
import run_streams as R
import run_e_streams as E

def started(logf, ext=r"ep 0 "):
    st = set()
    if logf.exists():
        for l in open(logf, encoding="utf-8", errors="ignore"):
            m = re.match(r"\[(\w+) (\w+) (\w+) s(\d+)\] ep 0 ", l)
            if m: st.add((m[1], m[2], m[3], int(m[4])))
    return st

def table(jobs, folder, logf, skip):
    done = {p.stem for p in (ROOT / "results" / folder).glob("*.json")} if (ROOT / "results" / folder).exists() else set()
    st = started(ROOT / "results" / logf)
    rows = collections.OrderedDict()
    for arm, v, c, s, n in jobs:
        k = (arm, v, c); r = rows.setdefault(k, dict(done=0, running=0, notstarted=0, dropped=0, total=0))
        r["total"] += 1
        name = f"{arm}_{v}_{c}_s{s}"
        if name in done: r["done"] += 1
        elif (arm, v, c, s) in st: r["running"] += 1
        elif f"{arm} {v} {c} {s}" in skip: r["dropped"] += 1
        else: r["notstarted"] += 1
    return rows

def fmt(title, rows):
    out = [f"\n### {title}\n", "| arm | variant | condition | done | running | not started | dropped (A4) | total |", "|---|---|---|---|---|---|---|---|"]
    tot = collections.Counter()
    for (a, v, c), r in rows.items():
        out.append(f"| {a} | {v} | {c} | {r['done']} | {r['running']} | {r['notstarted']} | {r['dropped']} | {r['total']} |")
        tot.update(r)
    out.append(f"| **all** | | | **{tot['done']}** | {tot['running']} | {tot['notstarted']} | {tot['dropped']} | **{tot['total']}** |")
    return "\n".join(out), tot

if __name__ == "__main__":
    skipf = ROOT / "results" / "skip_jobs.txt"
    skip = {x.strip() for x in skipf.read_text().split("\n")} if skipf.exists() else set()
    t1 = table(R.job_list(), "streams", "streams_log.txt", skip)
    t2 = table(E.job_list(), "e_streams", "e_streams_log.txt", set())
    a, ta = fmt("Baseline streams (N, DQN, PPO)", t1); b, tb = fmt("E-streams (F, R, RN, NM)", t2)
    txt = f"## Stream counts at {datetime.datetime.now():%Y-%m-%d %H:%M} IST\nBaseline: {ta['done']} done / {ta['total'] - ta['dropped']} planned after A4 ({ta['total']} listed, {ta['dropped']} dropped).{a}\n{b}\n"
    (ROOT / "results" / "status_counts.md").write_text(txt, encoding="utf-8")
    print(txt)