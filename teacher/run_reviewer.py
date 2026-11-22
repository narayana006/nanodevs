"""Benchmark a model on the reviewer task set (first try, greedy). Prompt and scoring are the specialist's own
(specialists/reviewer/grader.py: render_prompt, score). PASS (README): buggy diff = verdict request_changes AND
F1 >= 0.75; clean diff = verdict approve AND zero findings. The system prompt is prepended to the user message
(the shared chat helper sends one user turn). The grader is strict (bare JSON); a single ```json fence is
stripped before grading (strict=False) and the answer counts as unparsed only if it is still invalid.
Usage: run_reviewer.py NAME PORT K WORKERS LIMIT"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "phase0")); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "specialists", "reviewer"))
from harness import chat
import grader as G
from _strat import stratified, write_outputs, summarize

name, port = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else 0
base = f"http://127.0.0.1:{port}"
tasks = stratified([json.loads(l) for l in open(os.path.join(ROOT, "specialists", "reviewer", "tasks.jsonl"))], LIMIT)

def solve(t):
    system, user = G.render_prompt(t); p = system + "\n\n" + user; cands = []; first = None
    for i in range(1, K + 1):
        t0 = time.time()
        try:
            text, ntok = chat(base, p, 0.0 if i == 1 else 0.8, max_tokens=3000, seed=1000 + 17 * i)
        except Exception as e:
            cands.append(dict(i=i, passed=False, unparsed=True, error=str(e)[:100])); continue
        sc = G.score(t, text, strict=False)
        strict_ok = G.score(t, text, strict=True)["passed"]
        cands.append(dict(i=i, passed=sc["passed"], strict_passed=strict_ok, unparsed=not sc["valid"], score=sc,
                          secs=round(time.time() - t0, 1), tokens=ntok, answer=text[:8000] if sc["passed"] else text[:1500]))
        if first is None: first = cands[-1]
        if sc["passed"]: break
    c = first or dict(passed=False, strict_passed=False, unparsed=True, score={}, answer="")
    r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], passed=c["passed"], strict_passed=c["strict_passed"],
             unparsed=c["unparsed"], f1=c["score"].get("f1"), tp=c["score"].get("tp"), fp=c["score"].get("fp"),
             fn=c["score"].get("fn"), verdict_ok=c["score"].get("verdict_ok"), error=c["score"].get("error"),
             answer=c["answer"] if c["passed"] else None, first_try_text=None if c["passed"] else c["answer"], candidates=cands)
    print(f"[{name}] {t['id']:<44}" + ("PASS" if c["passed"] else f"fail f1={r['f1']} fp={r['fp']} unparsed={c['unparsed']}"), flush=True)
    return r

with ThreadPoolExecutor(W) as ex:
    results = list(ex.map(solve, tasks))
buggy = [r for r in results if r["kind"] == "buggy"]
summ = summarize(name, K, results, {
    "pass_definition": "buggy: verdict=request_changes and F1>=0.75; clean: verdict=approve and no findings",
    "unparsed": sum(r["unparsed"] for r in results), "strict_json_pass": sum(r["strict_passed"] for r in results),
    "mean_f1_buggy": round(sum((r["f1"] or 0) for r in buggy) / max(1, len(buggy)), 4),
    "false_positive_findings_clean": sum((r["fp"] or 0) for r in results if r["kind"] == "clean")})
write_outputs(HERE, "reviewer", name, summ, results)
print(json.dumps(summ, indent=1))
