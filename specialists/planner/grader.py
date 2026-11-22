#!/usr/bin/env python3
"""Grader for planner outputs. Stdlib only, pure function, no model calls.

grade(task, output) -> dict(score, passed, gates_ok, components, flags, errors)
  output: the model's raw text (str) or an already-parsed dict.
Usage: python grader.py tasks.jsonl predictions.jsonl   (predictions: {"id":..., "output": "<model text>"} per line)
"""
import json
import os
import re
import sys

SPECIALISTS = {"python", "java", "ui", "data", "devops", "ops", "qa", "debugger", "reviewer"}
STEP_KEYS = {"id", "specialist", "files_to_touch", "goal", "depends_on", "acceptance_check"}
MAX_STEPS_HARD = 12
WEIGHTS = {"recall": 0.20, "precision": 0.10, "specialist": 0.10, "order": 0.20, "parallel": 0.15, "count": 0.10, "acceptance": 0.15}
PASS_SCORE = 0.80

_CMD = re.compile(r"\b(pytest|mvn|gradle|npm|npx|vitest|tsc|eslint|ruff|flake8|mypy|curl|docker|terraform|kubectl|helm|make\s+\w+|sqlfluff|actionlint|psql|sqlite3?|grep|diff|git|python3?|java|promtool|json\.tool|EXPLAIN|PRAGMA|flyway)\b", re.I)
_FILE = re.compile(r"[\w./-]+\.(py|java|ts|tsx|css|sql|ya?ml|json|md|tf|toml|xml|txt|sh)\b|Dockerfile")
_COND = re.compile(r"\b(returns?|exits?|status|HTTP\s*\d{3}|\b[2345]\d\d\b|equals?|contains?|raises?|fails?|passes|exists?|lists?|displays?|shows?|renders?|prints?|rejects?|asserts?|imports?|validates?|unit check|no longer|at most|at least|<=|>=|==)\b", re.I)
_VAGUE = re.compile(r"^\W*(works?( correctly| fine| well| as expected)?|done|it works|looks? good|ok(ay)?|verified|tested|n/?a|none|tbd|complete[d]?|is implemented|everything works)\W*$", re.I)


def concrete_acceptance(s):
    if not isinstance(s, str):
        return False
    t = s.strip()
    if len(t) < 15 or len(t.split()) < 4 or _VAGUE.match(t):
        return False
    return bool(_CMD.search(t) or _FILE.search(t) or _COND.search(t))


def parse_output(output):
    if isinstance(output, dict):
        return output, None
    if not isinstance(output, str):
        return None, "output is not a string"
    try:
        return json.loads(output.strip()), None
    except Exception as e:  # strict: no fences, no prose
        return None, f"invalid JSON: {str(e)[:80]}"


def check_schema(obj):
    errs = []
    if not isinstance(obj, dict) or set(obj) != {"steps"}:
        return ["top level must be an object with exactly one key 'steps'"]
    steps = obj["steps"]
    if not isinstance(steps, list) or not steps:
        return ["'steps' must be a non-empty list"]
    if len(steps) > MAX_STEPS_HARD:
        errs.append(f"more than {MAX_STEPS_HARD} steps")
    for i, s in enumerate(steps):
        if not isinstance(s, dict) or set(s) != STEP_KEYS:
            errs.append(f"step {i}: keys must be exactly {sorted(STEP_KEYS)}")
            continue
        if not isinstance(s["id"], str) or not s["id"].strip():
            errs.append(f"step {i}: id must be a non-empty string")
        if not isinstance(s["specialist"], str):
            errs.append(f"step {i}: specialist must be a string")
        f = s["files_to_touch"]
        if not isinstance(f, list) or not f or not all(isinstance(x, str) and x.strip() for x in f):
            errs.append(f"step {i}: files_to_touch must be a non-empty list of strings")
        if not isinstance(s["goal"], str) or not s["goal"].strip():
            errs.append(f"step {i}: goal must be a non-empty string")
        d = s["depends_on"]
        if not isinstance(d, list) or not all(isinstance(x, str) for x in d):
            errs.append(f"step {i}: depends_on must be a list of strings")
        if not isinstance(s["acceptance_check"], str):
            errs.append(f"step {i}: acceptance_check must be a string")
    ids = [s.get("id") for s in steps if isinstance(s, dict)]
    if len(set(map(str, ids))) != len(ids):
        errs.append("duplicate step ids")
    return errs


def check_specialists(steps):
    return [f"step {s['id']}: unknown specialist {s['specialist']!r}" for s in steps if s["specialist"] not in SPECIALISTS]


def check_dag(steps):
    ids = {s["id"] for s in steps}
    errs = []
    for s in steps:
        for d in s["depends_on"]:
            if d not in ids:
                errs.append(f"step {s['id']}: depends_on {d!r} does not exist")
            if d == s["id"]:
                errs.append(f"step {s['id']}: depends on itself")
    if errs:
        return errs, None
    # Kahn
    indeg = {s["id"]: len(set(s["depends_on"])) for s in steps}
    kids = {i: [] for i in ids}
    for s in steps:
        for d in set(s["depends_on"]):
            kids[d].append(s["id"])
    q = [i for i, n in indeg.items() if n == 0]
    seen = 0
    while q:
        x = q.pop()
        seen += 1
        for k in kids[x]:
            indeg[k] -= 1
            if indeg[k] == 0:
                q.append(k)
    if seen != len(ids):
        return ["dependency cycle"], None
    anc = {}

    def go(i, parents):
        if i in anc:
            return anc[i]
        r = set()
        for d in parents[i]:
            r.add(d)
            r |= go(d, parents)
        anc[i] = r
        return r
    parents = {s["id"]: set(s["depends_on"]) for s in steps}
    for i in ids:
        go(i, parents)
    return [], anc


def norm(p):
    p = p.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def is_outside(p):
    return p.startswith("/") or p.startswith("~") or ".." in p.split("/") or re.match(r"^[A-Za-z]:", p) is not None


def match_items(task, steps):
    """-> (item_id -> set(step ids touching it), set of touched files, matched file set, outside list, extra list)"""
    gt = task["ground_truth"]
    tree = set(task["repo"]["files"])
    touched = {}
    for s in steps:
        for f in s["files_to_touch"]:
            touched.setdefault(norm(f), set()).add(s["id"])
    hits = {it["id"]: set() for it in gt["required"]}
    used = set()
    for it in gt["required"]:
        if "path" in it:
            if it["path"] in touched:
                hits[it["id"]] = set(touched[it["path"]])
                used.add(it["path"])
    for it in gt["required"]:
        if "create" in it:
            cr = it["create"]
            for f, sids in sorted(touched.items()):
                if f not in tree and f not in used and f.startswith(cr["dir"]) and f.endswith(cr["ext"]):
                    hits[it["id"]] = set(sids)
                    used.add(f)
                    break
    optional = set(gt["optional"])
    outside = [f for f in touched if is_outside(f)]
    extra = [f for f in touched if f not in used and f not in optional and f not in outside]
    return hits, touched, outside, extra


def grade(task, output):
    gt = task["ground_truth"]
    res = {"score": 0.0, "passed": False, "gates_ok": False, "components": {}, "flags": [], "errors": []}
    obj, err = parse_output(output)
    if err:
        res["errors"].append(err)
        return res
    errs = check_schema(obj)
    if errs:
        res["errors"] += errs
        return res
    steps = obj["steps"]
    errs = check_specialists(steps)
    if errs:
        res["errors"] += errs
        return res
    errs, anc = check_dag(steps)
    if errs:
        res["errors"] += errs
        return res
    res["gates_ok"] = True
    hits, touched, outside, extra = match_items(task, steps)
    comp = {}
    req = gt["required"]
    comp["recall"] = sum(1 for it in req if hits[it["id"]]) / len(req)
    # precision
    if outside:
        comp["precision"] = 0.0
        res["flags"].append("outside_repo")
    else:
        n = max(0, len(extra) - gt["max_extra_files"])
        comp["precision"] = max(0.0, 1.0 - n / 3.0)
    res["extra_files"] = sorted(extra)
    res["outside_files"] = sorted(outside)
    # specialists
    by_id = {s["id"]: s for s in steps}
    checks = ok = 0
    for it in req:
        if hits[it["id"]]:
            checks += 1
            ok += any(by_id[sid]["specialist"] in it["specialists"] for sid in hits[it["id"]])
        else:
            checks += 1
    present = {s["specialist"] for s in steps}
    for sp in gt["required_specialists"]:
        checks += 1
        ok += sp in present
    comp["specialist"] = ok / checks if checks else 1.0

    def before(a, b):
        sa = by_id_sets(a)
        sb = by_id_sets(b)
        return any(x == y or x in anc[y] for x in sa for y in sb)

    def by_id_sets(ref):
        if ref.startswith("@"):
            return {s["id"] for s in steps if s["specialist"] == ref[1:]}
        return hits.get(ref, set())

    if gt["order"]:
        comp["order"] = sum(before(a, b) for a, b in gt["order"]) / len(gt["order"])
    else:
        comp["order"] = 1.0

    def indep(a, b):
        return any(x != y and x not in anc[y] and y not in anc[x] for x in hits[a] for y in hits[b])
    if gt["parallel"]:
        comp["parallel"] = sum(indep(a, b) for a, b in gt["parallel"]) / len(gt["parallel"])
    else:
        comp["parallel"] = 1.0
    n = len(steps)
    lo, hi = gt["min_steps"], gt["max_steps"]
    comp["count"] = 1.0 if lo <= n <= hi else (0.5 if (n == lo - 1 or n == hi + 1) else 0.0)
    comp["acceptance"] = sum(concrete_acceptance(s["acceptance_check"]) for s in steps) / n
    res["components"] = {k: round(v, 4) for k, v in comp.items()}
    res["score"] = round(sum(WEIGHTS[k] * comp[k] for k in WEIGHTS), 4)
    par_ok = comp["parallel"] >= (1.0 if len(gt["parallel"]) <= 1 else 0.5)
    res["passed"] = bool(
        res["score"] >= PASS_SCORE and comp["recall"] == 1.0 and comp["order"] == 1.0 and par_ok
        and comp["count"] == 1.0 and comp["precision"] == 1.0 and not outside and comp["acceptance"] == 1.0 and comp["specialist"] >= 0.8)
    return res


def load_tasks(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    tasks = {t["id"]: t for t in load_tasks(sys.argv[1])}
    tot = passed = 0
    scores = []
    with open(sys.argv[2]) as f:
        for l in f:
            if not l.strip():
                continue
            p = json.loads(l)
            r = grade(tasks[p["id"]], p["output"])
            tot += 1
            passed += r["passed"]
            scores.append(r["score"])
            print(json.dumps({"id": p["id"], **{k: r[k] for k in ("score", "passed", "errors", "flags")}}))
    if tot:
        print(f"# tasks={tot} passed={passed} ({100 * passed / tot:.1f}%) mean_score={sum(scores) / tot:.3f}")


if __name__ == "__main__":
    main()
