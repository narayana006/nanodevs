"""Run a model over the ui task set (first try, greedy) and keep verified solutions.
Usage: run_ui.py NAME PORT [K] [WORKERS] [LIMIT]   (LIMIT: stratified sample by kind/difficulty, fixed seed; 0 = all)"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "phase0"))
sys.path.insert(0, os.path.join(ROOT, "specialists", "ui"))
sys.path.insert(0, HERE)
from harness import chat
from harness_ui import grade, load_tasks, make_prompt, NAME_OK
from benchlib import stratified_sample, write_outputs

name, port = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 0
base = f"http://127.0.0.1:{port}"
tasks = stratified_sample(load_tasks(), LIMIT)

def extract_ui(text):
    """Fenced blocks whose first line is a `file: <name>` comment (// , <!-- -->, /* */) -> {name: code}."""
    out = {}
    for b in re.findall(r"```[A-Za-z]*[ \t]*\n(.*?)```", text, re.S):
        m = re.match(r"\s*(?://|<!--|/\*)\s*file:\s*(\S+?)\s*(?:-->|\*/)?[ \t]*\n", b)
        if m and NAME_OK.match(m.group(1)):
            out[m.group(1)] = b[m.end():]
    return out

def solve(t):
    p = make_prompt(t)
    t0 = time.time(); err = None; ntok = 0; text = ""
    try:
        text, ntok = chat(base, p, 0.0, max_tokens=4000, seed=1017)
    except Exception as e:
        err = str(e)[:200]
    files = extract_ui(text)
    ok, out = False, err or "NO FILES PARSED"
    if files:
        ok, out = grade(t, files)
    r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], lang=t["lang"], passed=ok, parsed=bool(files),
             secs=round(time.time() - t0, 1), tokens=ntok, answer=text[:8000] if ok else text[:1500],
             detail="" if ok else out[-500:])
    print(f"[{name}] {t['id']:<40}" + ("PASS" if ok else "FAIL" if files else "FAIL (unparsed)"), flush=True)
    return r

with ThreadPoolExecutor(W) as ex:
    results = list(ex.map(solve, tasks))
write_outputs(HERE, "ui", name, results)
