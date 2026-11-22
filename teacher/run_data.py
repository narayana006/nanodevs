"""Run a model over the data task set (first try, greedy) and keep verified solutions.
Usage: run_data.py NAME PORT [K] [WORKERS] [LIMIT]   (LIMIT: stratified sample by kind/difficulty, fixed seed; 0 = all)
Uses the task's own rendered `prompt` and the specialist's grader.py inside its locked-down container."""
import json, os, re, subprocess, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GDIR = os.path.join(ROOT, "specialists", "data")
sys.path.insert(0, os.path.join(ROOT, "phase0"))
sys.path.insert(0, HERE)
from harness import chat
from benchlib import stratified_sample, write_outputs

name, port = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 0
base = f"http://127.0.0.1:{port}"
tasks = stratified_sample([json.loads(l) for l in open(os.path.join(GDIR, "tasks.jsonl")) if l.strip()], LIMIT)

def grade(t, answer):
    cname = "tc-data-" + uuid.uuid4().hex[:10]
    # same hardening flags as specialists/data/validate.py
    cmd = ["docker", "run", "--rm", "-i", "--name", cname, "--network", "none", "--memory", "256m", "--cpus", "1",
           "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
           "--user", "65534:65534", "-v", f"{GDIR}:/g:ro", "-w", "/g", "python:3.12-slim", "python", "-c",
           "import sys;sys.path.insert(0,'/g');sys.dont_write_bytecode=True;import grader;grader.main()"]
    job = json.dumps({"job_id": t["id"], "task": t, "answer": answer}) + "\n"
    try:
        p = subprocess.run(cmd, input=job, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", cname], capture_output=True)
        return False, "TIMEOUT"
    try:
        r = json.loads(p.stdout.strip().splitlines()[-1])
        return r["pass"], r["detail"]
    except Exception:
        return False, "grader error: " + (p.stderr or p.stdout)[-300:]

def solve(t):
    t0 = time.time(); err = None; ntok = 0; text = ""
    try:
        text, ntok = chat(base, t["prompt"], 0.0, max_tokens=4000, seed=1017)
    except Exception as e:
        err = str(e)[:200]
    # the grader takes the first fenced block, else the raw text; "parsed" = answer non-empty and has a fenced block
    parsed = bool(re.search(r"```[A-Za-z0-9_+-]*[ \t]*\n.*?```", text, re.S))
    ok, detail = (False, err or "empty answer") if not text.strip() else grade(t, text)
    r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], passed=ok, parsed=parsed,
             secs=round(time.time() - t0, 1), tokens=ntok, answer=text[:8000] if ok else text[:1500],
             detail="" if ok else detail[-500:])
    print(f"[{name}] {t['id']:<44}" + ("PASS" if ok else "FAIL" if parsed else "FAIL (no fenced block)"), flush=True)
    return r

with ThreadPoolExecutor(W) as ex:
    results = list(ex.map(solve, tasks))
write_outputs(HERE, "data", name, results)
