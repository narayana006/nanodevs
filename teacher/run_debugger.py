"""Benchmark a model on the debugger task set (first try, greedy). Prompt, parser and grader are the specialist's own
(specialists/debugger/grade.py). A task passes iff `full`: root-cause JSON matches ground truth AND the fix passes
the hidden tests (score = 0.5*root_cause + 0.5*fix is also recorded).
Usage: run_debugger.py NAME PORT K WORKERS LIMIT"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "phase0")); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "specialists", "debugger"))
from harness import chat
import grade as G
from _strat import stratified, write_outputs, summarize

name, port = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 0
base = f"http://127.0.0.1:{port}"
alltasks = [json.loads(l) for l in open(os.path.join(ROOT, "specialists", "debugger", "tasks.jsonl"))]
for t in alltasks:
    t.setdefault("kind", "debug")
tasks = stratified(alltasks, LIMIT)

def solve(t):
    p = G.make_prompt(t); cands = []; first = None
    for i in range(1, K + 1):
        t0 = time.time()
        try:
            text, ntok = chat(base, p, 0.0 if i == 1 else 0.8, max_tokens=3500, seed=1000 + 17 * i)
        except Exception as e:
            cands.append(dict(i=i, passed=False, error=str(e)[:100])); continue
        obj, files, jerr = G.parse_response(text)
        g = G.grade(t, text)
        unparsed = (obj is None) or not any(not n.startswith("test_") for n in files)
        cands.append(dict(i=i, passed=g["full"], root_cause=g["root_cause"], fix=g["fix"], score=g["score"],
                          unparsed=unparsed, json_error=jerr, parts=g["root_cause_parts"], detail=g["detail"][:200],
                          secs=round(time.time() - t0, 1), tokens=ntok, answer=text[:8000] if g["full"] else text[:1500]))
        if first is None: first = cands[-1]
        if g["full"]: break
    c = first or dict(passed=False, root_cause=False, fix=False, score=0.0, unparsed=True, answer="")
    r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], category=t.get("category"), passed=c["passed"],
             root_cause=c["root_cause"], fix=c["fix"], score=c["score"], unparsed=c["unparsed"],
             answer=c["answer"] if c["passed"] else None, first_try_text=None if c["passed"] else c["answer"],
             candidates=cands)
    print(f"[{name}] {t['id']:<40}" + ("PASS" if c["passed"] else f"fail rc={c['root_cause']} fix={c['fix']} unparsed={c['unparsed']}"), flush=True)
    return r

with ThreadPoolExecutor(W) as ex:
    results = list(ex.map(solve, tasks))
n = len(results)
summ = summarize(name, K, results, {
    "pass_definition": "root_cause AND fix (grade.full)",
    "root_cause_correct": sum(r["root_cause"] for r in results), "fix_correct": sum(r["fix"] for r in results),
    "mean_score": round(sum(r["score"] for r in results) / n, 4), "unparsed": sum(r["unparsed"] for r in results)})
write_outputs(HERE, "debugger", name, summ, results)
print(json.dumps(summ, indent=1))
