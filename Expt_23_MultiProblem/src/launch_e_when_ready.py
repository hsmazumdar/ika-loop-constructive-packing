"""Waits until the baseline parent (run_streams.py) has exited, checks that all expected baseline streams exist, then starts the E1-E4 streams.
Documented command (manual start of the same thing):  set NW=12 & python src\run_e_streams.py   (finished streams are skipped on re-run).
Expected baseline streams = 102 jobs - jobs listed in results/skip_jobs.txt = 91 (amendment A4)."""
import os, sys, time, subprocess, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "launcher_log.txt"
NIGHT = ROOT.parent / "NIGHT_LOG.md"
EXPECT = 91


def log(m):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {m}"
    with open(LOG, "a") as f: f.write(line + "\n")
    return line


def parent_alive():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'run_streams' } | Measure-Object).Count"],
                         capture_output=True, text=True).stdout.strip()
    return int(out or 0) > 0


def n_streams():
    return len(list((ROOT / "results" / "streams").glob("*.json")))


if __name__ == "__main__":
    log(f"watcher started (waiting for run_streams.py to exit; expect {EXPECT} baseline streams)")
    while parent_alive():
        time.sleep(60)
    n = n_streams()
    if n < EXPECT:
        l = log(f"baseline parent exited with only {n}/{EXPECT} streams - NOT starting E-streams (check RESUME.md)")
        with open(NIGHT, "a", encoding="utf-8") as f: f.write("\n- " + l)
        sys.exit(1)
    l = log(f"baselines complete ({n}/{EXPECT}); starting E-streams (F,R,RN,NM x std,hard x 8 seeds, 20k episodes), NW=12")
    with open(NIGHT, "a", encoding="utf-8") as f: f.write("\n- " + l)
    env = dict(os.environ, NW="12")
    with open(ROOT / "results" / "e_streams_stdout.txt", "a") as so, open(ROOT / "results" / "e_streams_stderr.txt", "a") as se:
        rc = subprocess.call([sys.executable, str(ROOT / "src" / "run_e_streams.py")], cwd=str(ROOT), env=env, stdout=so, stderr=se)
    l = log(f"E-streams process exited rc={rc}")
    with open(NIGHT, "a", encoding="utf-8") as f: f.write("\n- " + l)