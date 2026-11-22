"""Benchmark a model on the planner task set (first try, greedy). The prompt is the task's own `prompt` field and
grading is the specialist's own grader.grade. PASS = grader's `passed` (README: score >= 0.80 AND recall, order,
precision, step count, acceptance all perfect, specialist >= 0.8, parallel ok, no outside files). The mean score is
also recorded. The grader is strict (bare JSON); if the reply is wrapped in a ```json fence the fence is stripped
before grading and `fenced` is recorded; an answer is `unparsed` only if it is not valid JSON after that.
Usage: run_planner.py NAME PORT K WORKERS LIMIT"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "phase0")); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "specialists", "planner"))
from harness import chat
import grader as G
from _strat import stratified, write_outputs, summarize

name, port = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 0
base = f"http://127.0.0.1:{port}"
tasks = stratified([json.loads(l) for l in open(os.path.join(ROOT, "specialists", "planner", "tasks.jsonl"))], LIMIT)

if os.environ.get("IDS_FILE"):  # restrict to a fixed held-out id list
    _ids = set(json.load(open(os.environ["IDS_FILE"]))["test_ids"]); tasks = [json.loads(l) for l in open(os.path.join(ROOT, "specialists", "planner", "tasks.jsonl"))]; tasks = [t for t in tasks if t["id"] in _ids]

def unfence(text):
    m = re.match(r"^\s*```(?:json)?\s*\n(.*?)\n?```\s*$", text, re.S)
    return (m.group(1).strip(), True) if m else (text.strip(), False)

def solve(t):
    cands = []; first = None
    for i in range(1, K + 1):
        t0 = time.time()
        try:
            text, ntok = chat(base, t["prompt"], 0.0 if i == 1 else 0.8, max_tokens=3500, seed=1000 + 17 * i)
        except Exception as e:
            cands.append(dict(i=i, passed=False, unparsed=True, error=str(e)[:100])); continue
        body, fenced = unfence(text)
        g = G.grade(t, body)
        unparsed = any(e.startswith("invalid JSON") for e in g["errors"])
        cands.append(dict(i=i, passed=g["passed"], score=g["score"], gates_ok=g["gates_ok"], fenced=fenced, unparsed=unparsed,
                          components=g["components"], errors=g["errors"], flags=g["flags"], secs=round(time.time() - t0, 1),
                          tokens=ntok, answer=text[:8000] if g["passed"] else text[:1500]))
        if first is None: first = cands[-1]
        if g["passed"]: break
    c = first or dict(passed=False, score=0.0, gates_ok=False, fenced=False, unparsed=True, components={}, errors=[], answer="")
    r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], family=t["family"], passed=c["passed"], score=c["score"],
             gates_ok=c["gates_ok"], fenced=c["fenced"], unparsed=c["unparsed"], components=c["components"], errors=c["errors"],
             answer=c["answer"] if c["passed"] else None, first_try_text=None if c["passed"] else c["answer"], candidates=cands)
    print(f"[{name}] {t['id']:<14}" + ("PASS" if c["passed"] else f"fail score={c['score']} gates={c['gates_ok']} unparsed={c['unparsed']}"), flush=True)
    return r

with ThreadPoolExecutor(W) as ex:
    results = list(ex.map(solve, tasks))
n = len(results)
summ = summarize(name, K, results, {
    "pass_definition": "grader.passed (score>=0.80 and recall/order/precision/count/acceptance all perfect, specialist>=0.8, parallel ok)",
    "mean_score": round(sum(r["score"] for r in results) / n, 4), "unparsed": sum(r["unparsed"] for r in results),
    "gates_failed": sum(not r["gates_ok"] for r in results), "fenced_replies": sum(r["fenced"] for r in results)})
write_outputs(HERE, "planner", name, summ, results)
print(json.dumps(summ, indent=1))
