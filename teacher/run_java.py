"""Run a model over the java task set (first try, greedy by default) and keep verified solutions.
Usage: run_java.py NAME PORT [K] [WORKERS] [LIMIT]   (LIMIT: stratified sample by kind/difficulty, fixed seed; 0 = all)"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "phase0"))
sys.path.insert(0, os.path.join(ROOT, "specialists", "java"))
sys.path.insert(0, HERE)
from harness import chat
from runner import run_task, task_files, make_prompt
from benchlib import stratified_sample, write_outputs

name, port = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 0
base = f"http://127.0.0.1:{port}"
IMAGE = "eclipse-temurin:21-jdk"
tasks = stratified_sample([json.loads(l) for l in open(os.path.join(ROOT, "specialists", "java", "tasks.jsonl"))], LIMIT)
FNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.java$")

def extract_java(text):
    """Blocks whose first line is `// file: Name.java`; if a lone block lacks the header, use its public type name."""
    out = {}
    blocks = re.findall(r"```[A-Za-z]*[ \t]*\n(.*?)```", text, re.S)
    for b in blocks:
        m = re.match(r"\s*(?://|/\*)\s*file:\s*(\S+?)\s*(?:\*/)?[ \t]*\n", b)
        if m and FNAME.match(m.group(1)):
            out[m.group(1)] = b[m.end():]
    if not out and len(blocks) == 1:
        m = re.search(r"\bpublic\s+(?:final\s+|abstract\s+)?(?:class|interface|enum|record)\s+(\w+)", blocks[0])
        if m:
            out[m.group(1) + ".java"] = blocks[0]
    return out

def solve(t):
    p = make_prompt(t, start_output="")
    if t["kind"] == "fix":  # reference make_prompt wants the failing test output; give the real one from the starting files
        _, so, _ = run_task({**t["files"], **t["hidden_tests"]}, t["entry"], "docker", IMAGE)
        p = make_prompt(t, start_output=so)
    t0 = time.time(); err = None; ntok = 0; text = ""
    try:
        text, ntok = chat(base, p, 0.0, max_tokens=4000, seed=1017)
    except Exception as e:
        err = str(e)[:200]
    files = extract_java(text)
    ok, out, phase = False, err or "NO FILES PARSED", "unparsed"
    if files:
        ok, out, phase = run_task(task_files(t, files), t["entry"], "docker", IMAGE)
    r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], passed=ok, parsed=bool(files), phase=phase,
             secs=round(time.time() - t0, 1), tokens=ntok, answer=text[:8000] if ok else text[:1500],
             detail="" if ok else out[-500:])
    print(f"[{name}] {t['id']:<40}" + ("PASS" if ok else f"FAIL ({phase})"), flush=True)
    return r

with ThreadPoolExecutor(W) as ex:
    results = list(ex.map(solve, tasks))
write_outputs(HERE, "java", name, results)
