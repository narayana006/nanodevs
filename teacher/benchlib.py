"""Shared helpers for the teacher benchmark runners: stratified sampling and summary/verified output."""
import json, os, random, collections

SEED = 20240611

def stratified_sample(tasks, limit, seed=SEED):
    """Up to `limit` tasks, proportional to (kind, difficulty) strata, fixed seed. Returns tasks in original order."""
    if not limit or limit >= len(tasks):
        return list(tasks)
    strata = collections.defaultdict(list)
    for t in tasks:
        strata[(t["kind"], t["difficulty"])].append(t)
    keys = sorted(strata)
    rng = random.Random(seed)
    for k in keys:
        rng.shuffle(strata[k])
    total = len(tasks)
    quota = {k: limit * len(strata[k]) / total for k in keys}
    take = {k: min(len(strata[k]), int(quota[k])) for k in keys}
    for k in keys:  # at least one per stratum while there is room
        if take[k] == 0 and sum(take.values()) < limit:
            take[k] = 1
    while sum(take.values()) < limit:
        k = max((k for k in keys if take[k] < len(strata[k])), key=lambda k: quota[k] - take[k])
        take[k] += 1
    while sum(take.values()) > limit:
        k = max((k for k in keys if take[k] > 1), key=lambda k: take[k] - quota[k])
        take[k] -= 1
    ids = {t["id"] for k in keys for t in strata[k][:take[k]]}
    return [t for t in tasks if t["id"] in ids]

def write_outputs(here, spec, name, results, extra=None):
    """results: dicts with id, kind, difficulty, passed, parsed, answer. Writes <spec>_<name>.json and _verified.jsonl."""
    n = len(results)
    summ = {"model": name, "specialist": spec, "k": 1, "n": n,
            "first_try": sum(r["passed"] for r in results),
            "unparsed": sum(not r["parsed"] for r in results)}
    summ["first_try_rate"] = round(summ["first_try"] / n, 3) if n else 0
    for key in ("kind", "difficulty"):
        for v in sorted({r[key] for r in results}):
            rs = [r for r in results if r[key] == v]
            summ[f"{key}:{v}"] = f"{sum(r['passed'] for r in rs)}/{len(rs)} first try, {sum(not r['parsed'] for r in rs)} unparsed"
    if extra:
        summ.update(extra)
    out = {"summary": summ, "task_ids": [r["id"] for r in results], "results": results}
    json.dump(out, open(os.path.join(here, f"{spec}_{name}.json"), "w"), indent=1)
    with open(os.path.join(here, f"{spec}_{name}_verified.jsonl"), "w") as f:
        for r in results:
            if r["passed"]:
                f.write(json.dumps({"id": r["id"], "answer": r["answer"]}) + "\n")
    print(json.dumps(summ, indent=1))
