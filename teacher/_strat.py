"""Shared helpers for the specialist runners: fixed-seed stratified sampling and summary/output writing."""
import json, os, random, collections


def stratified(tasks, limit, seed=20261122):
    """Up to `limit` tasks, allocated proportionally across (kind, difficulty) strata (largest remainder,
    at least one per stratum when limit allows), sampled with a fixed seed. Returned in original file order."""
    if not limit or limit >= len(tasks):
        return list(tasks)
    rng = random.Random(seed)
    groups = collections.defaultdict(list)
    for t in tasks:
        groups[(t["kind"], t["difficulty"])].append(t)
    keys = sorted(groups)
    n = len(tasks)
    quota = {k: limit * len(groups[k]) / n for k in keys}
    alloc = {k: max(1, int(quota[k])) if limit >= len(keys) else int(quota[k]) for k in keys}
    while sum(alloc.values()) > limit:
        k = max((k for k in keys if alloc[k] > 1), key=lambda k: alloc[k] - quota[k]); alloc[k] -= 1
    while sum(alloc.values()) < limit:
        k = max((k for k in keys if alloc[k] < len(groups[k])), key=lambda k: quota[k] - alloc[k]); alloc[k] += 1
    chosen = set()
    for k in keys:
        chosen.update(t["id"] for t in rng.sample(groups[k], alloc[k]))
    return [t for t in tasks if t["id"] in chosen]


def write_outputs(here, spec, name, summ, results):
    json.dump({"summary": summ, "chosen_ids": [r["id"] for r in results], "results": results},
              open(os.path.join(here, f"{spec}_{name}.json"), "w"), indent=1)
    with open(os.path.join(here, f"{spec}_{name}_verified.jsonl"), "w") as f:
        for r in results:
            if r["passed"]:
                f.write(json.dumps({"id": r["id"], "answer": r["answer"]}) + "\n")


def summarize(name, k, results, extra=None):
    n = len(results)
    summ = {"model": name, "k": k, "n": n, "first_try_pass": sum(r["passed"] for r in results)}
    summ.update(extra or {})
    for key in ("kind", "difficulty"):
        for v in sorted({r[key] for r in results}):
            rs = [r for r in results if r[key] == v]
            summ[f"{key}:{v}"] = f"{sum(r['passed'] for r in rs)}/{len(rs)}"
    return summ
