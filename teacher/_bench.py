"""Shared driver for the specialist benchmark runners (run_devops.py, run_ops.py, run_qa.py).
Each runner supplies: tasks, prompt(t), grade(t, text) -> (passed, detail, parsed)."""
import json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "phase0"))
from harness import chat

SEED = 20260101


def sample(tasks, limit):
    """Stratified by (kind, difficulty), fixed seed: shuffle each stratum, then round-robin across strata."""
    if not limit or limit >= len(tasks):
        return list(tasks)
    groups = {}
    for t in tasks:
        groups.setdefault((t["kind"], t["difficulty"]), []).append(t)
    rnd = random.Random(SEED)
    keys = sorted(groups)
    for k in keys:
        groups[k].sort(key=lambda t: t["id"])
        rnd.shuffle(groups[k])
    out, i = [], 0
    while len(out) < limit:
        progressed = False
        for k in keys:
            if i < len(groups[k]) and len(out) < limit:
                out.append(groups[k][i]); progressed = True
        if not progressed:
            break
        i += 1
    return out


def main(spec, tasks, prompt, grade, max_tokens=4000):
    name, port = sys.argv[1], sys.argv[2]
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    W = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    base = f"http://127.0.0.1:{port}"
    chosen = sample(tasks, limit)

    def solve(t):
        p = prompt(t); cands = []; solved = None
        for i in range(1, K + 1):
            t0 = time.time()
            try:
                text, ntok = chat(base, p, 0.0 if i == 1 else 0.8, max_tokens=max_tokens, seed=1000 + 17 * i)
            except Exception as e:
                cands.append(dict(i=i, passed=False, parsed=False, error=str(e)[:100])); continue
            try:
                ok, detail, parsed = grade(t, text)
            except Exception as e:
                ok, detail, parsed = False, "GRADER EXC " + str(e)[:200], True
            cands.append(dict(i=i, passed=bool(ok), parsed=bool(parsed), detail=str(detail)[:400], secs=round(time.time() - t0, 1),
                              tokens=ntok, answer=text[:8000] if ok else text[:1500]))
            if ok:
                solved = i; break
        r = dict(id=t["id"], kind=t["kind"], difficulty=t["difficulty"], solved_at=solved, candidates=cands)
        print(f"[{name}] {t['id']:<40}" + (f"solved at {solved}" if solved else "NOT SOLVED" + ("" if cands[0].get("parsed") else " (unparsed)")), flush=True)
        return r

    with ThreadPoolExecutor(W) as ex:
        results = list(ex.map(solve, chosen))
    first = lambda r: r["solved_at"] == 1
    unp = lambda r: not r["candidates"][0].get("parsed")
    summ = {"model": name, "specialist": spec, "k": K, "limit": limit, "n": len(results),
            "first_try": sum(map(first, results)), "pass_at_k": sum(bool(r["solved_at"]) for r in results),
            "first_try_unparsed": sum(map(unp, results))}
    for key in ("kind", "difficulty"):
        for v in sorted({r[key] for r in results}):
            rs = [r for r in results if r[key] == v]
            summ[f"{key}:{v}"] = f"{sum(map(first, rs))}/{len(rs)} first try, {sum(bool(r['solved_at']) for r in rs)}/{len(rs)} pass@{K}, {sum(map(unp, rs))} unparsed"
    stem = f"{spec}_{name}"
    json.dump({"summary": summ, "task_ids": [t["id"] for t in chosen], "results": results}, open(os.path.join(HERE, stem + ".json"), "w"), indent=1)
    with open(os.path.join(HERE, stem + "_verified.jsonl"), "w") as f:
        for r in results:
            if r["solved_at"]:
                f.write(json.dumps({"id": r["id"], "answer": r["candidates"][r["solved_at"] - 1]["answer"]}) + "\n")
    print(json.dumps(summ, indent=1))
