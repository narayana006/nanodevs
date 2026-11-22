"""Run a model over the python task set: first-try pass rate (greedy), pass@k with fresh seeds, and keep verified solutions.
Usage: run_python.py NAME PORT [K] [WORKERS] [LIMIT]"""
import json, os, re, sys, time, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "phase0"))
sys.path.insert(0, os.path.join(ROOT, "specialists", "python"))
from harness import chat
from harness2 import extract_files, show, FORMAT
from common import run_files

name, port = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 4
W = int(sys.argv[4]) if len(sys.argv) > 4 else 2
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 0
base = f"http://127.0.0.1:{port}"
tasks = [json.loads(l) for l in open(os.path.join(ROOT, "specialists", "python", "tasks.jsonl"))]
if LIMIT:
    import random
    tasks = random.Random(7).sample(tasks, min(LIMIT, len(tasks)))  # fixed seed: same tasks every run

def prompt(t):
    k = t["kind"]
    if k == "fix":
        return (f"Fix the bug(s) in this small Python project. The tests below fail.\n\n{show(t['files'])}\n\nSymptom: {t['instruction']}\n\n"
                f"Tests:\n```python\n{t['visible'].strip()}\n```\n\nTest output:\n```\n{t.get('start_output','').strip()}\n```\n\n{FORMAT}")
    verb = {"write": "Implement this", "feature": "Extend this code", "refactor": "Refactor this code, keeping its behaviour"}[k]
    return (f"{verb}.\n\nCurrent files:\n{show(t['files'])}\n\nTask: {t['instruction']}\n\n"
            f"Examples that must work:\n```python\n{t['visible'].strip()}\n```\n\n{FORMAT}")

def solve(t):
    p = prompt(t); cands = []; solved = None
    for i in range(1, K + 1):
        t0 = time.time()
        try:
            text, ntok = chat(base, p, 0.0 if i == 1 else 0.8, max_tokens=3500, seed=1000 + 17 * i)
        except Exception as e:
            cands.append(dict(i=i, passed=False, error=str(e)[:100])); continue
        files = extract_files(text)
        ok = False
        if files:
            ok, out = run_files({**t["files"], **files, "test_hidden.py": t["hidden"]}, "test_hidden.py")
        cands.append(dict(i=i, passed=ok, secs=round(time.time() - t0, 1), tokens=ntok, answer=text[:8000] if ok else text[:1500]))
        if ok:
            solved = i; break
    r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], solved_at=solved, candidates=cands)
    print(f"[{name}] {t['id']:<40}" + (f"solved at {solved}" if solved else "NOT SOLVED"), flush=True)
    return r

with ThreadPoolExecutor(W) as ex:
    results = list(ex.map(solve, tasks))
os.makedirs(os.path.join(ROOT, "benchmarks"), exist_ok=True)
summ = {"model": name, "k": K, "n": len(results),
        "first_try": sum(r["solved_at"] == 1 for r in results), "pass_at_k": sum(bool(r["solved_at"]) for r in results)}
for key in ("kind", "difficulty"):
    for v in sorted({r[key] for r in results}):
        rs = [r for r in results if r[key] == v]
        summ[f"{key}:{v}"] = f"{sum(r['solved_at'] == 1 for r in rs)}/{len(rs)} first try, {sum(bool(r['solved_at']) for r in rs)}/{len(rs)} pass@{K}"
json.dump({"summary": summ, "results": results}, open(os.path.join(HERE, f"python_{name}.json"), "w"), indent=1)
with open(os.path.join(HERE, f"python_{name}_verified.jsonl"), "w") as f:
    for r in results:
        if r["solved_at"]:
            f.write(json.dumps({"id": r["id"], "answer": r["candidates"][r["solved_at"] - 1]["answer"]}) + "\n")
print(json.dumps(summ, indent=1))
