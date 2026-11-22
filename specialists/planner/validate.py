#!/usr/bin/env python3
"""Validate the task set and the grader. Stdlib only, deterministic, no model calls.

  python validate.py            run all checks locally
  python validate.py --docker   re-run the same checks inside the python:3.12-slim sandbox
                                (--network none --read-only --cap-drop ALL --user 65534:65534
                                 --memory 256m --cpus 1 --pids-limit 64); image must already exist locally.
Exit code 0 only if every check passes.
"""
import copy
import json
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grader  # noqa: E402

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
        print("FAIL:", msg)


def plan_json(p):
    return json.dumps(p)


def mut_empty(t, p):
    return '{"steps": []}'


def mut_blank(t, p):
    return ""


def mut_prose(t, p):
    return "Here is my plan: first edit the model, then the API."


def mut_fenced(t, p):
    return "```json\n" + plan_json(p) + "\n```"


def mut_cyclic(t, p):
    q = copy.deepcopy(p)
    st = q["steps"]
    if len(st) == 1:
        st[0]["depends_on"] = [st[0]["id"]]
    else:
        edge = next(((d, s) for s in st for d in s["depends_on"]), None)
        if edge:
            a = next(s for s in st if s["id"] == edge[0])
            a["depends_on"] = a["depends_on"] + [edge[1]["id"]]
        else:
            st[0]["depends_on"] = [st[1]["id"]]
            st[1]["depends_on"] = [st[0]["id"]]
    return plan_json(q)


def mut_halluc_spec(t, p):
    q = copy.deepcopy(p)
    q["steps"][0]["specialist"] = "wizard"
    return plan_json(q)


def mut_missing_dep(t, p):
    q = copy.deepcopy(p)
    q["steps"][-1]["depends_on"] = q["steps"][-1]["depends_on"] + ["s99"]
    return plan_json(q)


def mut_serial(t, p):
    q = copy.deepcopy(p)
    for i, s in enumerate(q["steps"]):
        s["depends_on"] = [q["steps"][i - 1]["id"]] if i else []
    return plan_json(q)


def mut_one_step(t, p):
    q = copy.deepcopy(p)
    files = []
    for s in q["steps"]:
        for f in s["files_to_touch"]:
            if f not in files:
                files.append(f)
    s0 = q["steps"][0]
    q["steps"] = [{"id": "s1", "specialist": s0["specialist"], "files_to_touch": files, "goal": "do everything",
                   "depends_on": [], "acceptance_check": s0["acceptance_check"]}]
    return plan_json(q)


def mut_outside(t, p):
    q = copy.deepcopy(p)
    q["steps"][0]["files_to_touch"] = q["steps"][0]["files_to_touch"] + ["/etc/passwd"]
    return plan_json(q)


def mut_drop_required(t, p):
    q = copy.deepcopy(p)
    it = t["ground_truth"]["required"][0]
    target = it.get("path") or it.get("example")
    for s in q["steps"]:
        s["files_to_touch"] = [f for f in s["files_to_touch"] if f != target] or ["README.md"]
    return plan_json(q)


def mut_halluc_file(t, p):
    q = copy.deepcopy(p)
    it = t["ground_truth"]["required"][0]
    target = it.get("path") or it.get("example")
    for s in q["steps"]:
        s["files_to_touch"] = [("lib/imaginary/Thing.py" if f == target else f) for f in s["files_to_touch"]]
    return plan_json(q)


def mut_vague_acc(t, p):
    q = copy.deepcopy(p)
    for s in q["steps"]:
        s["acceptance_check"] = "works correctly"
    return plan_json(q)


def mut_no_order(t, p):
    q = copy.deepcopy(p)
    for s in q["steps"]:
        s["depends_on"] = []
    return plan_json(q)


def mut_reverse(t, p):
    """reverse every dependency edge (consumer before producer)."""
    q = copy.deepcopy(p)
    rev = {s["id"]: [] for s in q["steps"]}
    for s in q["steps"]:
        for d in s["depends_on"]:
            rev[d].append(s["id"])
    for s in q["steps"]:
        s["depends_on"] = rev[s["id"]]
    return plan_json(q)


def mut_shotgun(t, p):
    q = copy.deepcopy(p)
    extra = [f for f in t["repo"]["files"] if f not in sum((s["files_to_touch"] for s in q["steps"]), [])][:8]
    q["steps"][0]["files_to_touch"] = q["steps"][0]["files_to_touch"] + extra
    return plan_json(q)


def mut_extra_step(t, p):
    q = copy.deepcopy(p)
    n = len(q["steps"]) + 1
    q["steps"] += [{"id": f"s{n + i}", "specialist": "reviewer", "files_to_touch": [q["steps"][0]["files_to_touch"][0]],
                    "goal": "extra review", "depends_on": [], "acceptance_check": "review lists issues or states none were found"} for i in range(6)]
    return plan_json(q)


# name -> (mutator, applies(task) predicate, must_fail)
NEGATIVES = {
    "empty_steps": (mut_empty, lambda t: True),
    "blank_output": (mut_blank, lambda t: True),
    "prose_output": (mut_prose, lambda t: True),
    "fenced_json": (mut_fenced, lambda t: True),
    "cyclic": (mut_cyclic, lambda t: True),
    "hallucinated_specialist": (mut_halluc_spec, lambda t: True),
    "missing_dependency_id": (mut_missing_dep, lambda t: True),
    "everything_serial": (mut_serial, lambda t: len(t["ground_truth"]["parallel"]) > 0),
    "one_giant_step": (mut_one_step, lambda t: len(t["reference_plan"]["steps"]) >= 3),
    "file_outside_repo": (mut_outside, lambda t: True),
    "missing_required_file": (mut_drop_required, lambda t: True),
    "hallucinated_file": (mut_halluc_file, lambda t: True),
    "vague_acceptance": (mut_vague_acc, lambda t: True),
    "no_dependencies": (mut_no_order, lambda t: len(t["ground_truth"]["order"]) > 0),
    "reversed_dependencies": (mut_reverse, lambda t: len(t["ground_truth"]["order"]) > 0),
    "shotgun_files": (mut_shotgun, lambda t: True),
    "too_many_steps": (mut_extra_step, lambda t: True),
}


def run(tasks_path):
    tasks = grader.load_tasks(tasks_path)
    n = len(tasks)
    print(f"tasks: {n}")
    check(n >= 150, f"need >=150 tasks, have {n}")
    check(len({t["id"] for t in tasks}) == n, "duplicate task ids")
    diff = Counter(t["difficulty"] for t in tasks)
    single = sum(t["ground_truth"]["single_step"] for t in tasks)
    print("difficulty:", dict(diff), "| single-step tasks:", single, "| families:", len({t["family"] for t in tasks}))
    check(all(diff[d] >= 20 for d in ("easy", "medium", "hard")), "each difficulty needs >=20 tasks")
    check(single >= 20, "need >=20 single-step tasks")
    sizes = Counter(len(t["reference_plan"]["steps"]) for t in tasks)
    print("steps histogram:", dict(sorted(sizes.items())))
    check(min(sizes) == 1 and max(sizes) <= 10, "step counts must span 1..10")
    hard = [t for t in tasks if t["difficulty"] == "hard"]
    check(all(7 <= len(t["reference_plan"]["steps"]) <= 10 for t in hard), "hard tasks must have 7-10 steps")
    check(sum(len(t["ground_truth"]["languages"]) >= 3 for t in hard) >= 10, "need >=10 hard tasks with >=3 languages")
    check(sum(any(s["specialist"] in ("devops", "ops") for s in t["reference_plan"]["steps"]) for t in hard) >= 10, "need >=10 hard tasks with devops/ops work")
    spec_seen = Counter(s["specialist"] for t in tasks for s in t["reference_plan"]["steps"])
    print("specialist usage in reference plans:", dict(spec_seen))
    check(set(spec_seen) == grader.SPECIALISTS, "every specialist must appear in some reference plan")

    # reference plans
    ref_bad = 0
    for t in tasks:
        tree = set(t["repo"]["files"])
        for it in t["ground_truth"]["required"]:
            if "path" in it:
                check(it["path"] in tree, f"{t['id']}: required path not in repo tree: {it['path']}")
            else:
                check(it["example"] not in tree and it["example"].startswith(it["create"]["dir"]), f"{t['id']}: bad create example")
        r = grader.grade(t, json.dumps(t["reference_plan"]))
        if r["score"] != 1.0 or not r["passed"]:
            ref_bad += 1
            print("FAIL: reference plan not full score:", t["id"], r)
        check(1 <= len(t["reference_plan"]["steps"]) and t["ground_truth"]["min_steps"] <= len(t["reference_plan"]["steps"]) <= t["ground_truth"]["max_steps"], f"{t['id']}: ref outside range")
        check(t["prompt"].count(t["request"]) == 1, f"{t['id']}: prompt must embed the request")
    check(ref_bad == 0, f"{ref_bad} reference plans do not score 1.0 and pass")
    print(f"reference plans scoring 1.0 and passing: {n - ref_bad}/{n}")

    # negatives
    print("negative controls (plans that must FAIL):")
    for name, (mut, applies) in NEGATIVES.items():
        tot = fail = 0
        zero = 0
        mx = 0.0
        for t in tasks:
            if not applies(t):
                continue
            out = mut(t, t["reference_plan"])
            r = grader.grade(t, out)
            tot += 1
            fail += (not r["passed"])
            zero += (r["score"] == 0.0)
            mx = max(mx, r["score"])
            if r["passed"]:
                print(f"FAIL: negative '{name}' PASSED on {t['id']} score={r['score']}")
        check(fail == tot and tot > 0, f"negative '{name}': {tot - fail} of {tot} passed")
        print(f"  {name:26s} applied={tot:3d} rejected={fail:3d} gated_to_zero={zero:3d} max_score={mx:.2f}")

    # determinism
    import generator
    a = generator.generate(generator.DEFAULT_SEED)
    with open(tasks_path) as f:
        on_disk = [json.loads(l) for l in f if l.strip()]
    if os.path.abspath(tasks_path) == os.path.join(HERE, "tasks.jsonl"):
        check(a == on_disk, "tasks.jsonl differs from generate(default seed); regenerate it")
    check(generator.generate(generator.DEFAULT_SEED) == a, "generator is not deterministic")
    b = generator.generate(7)
    check(len(b) >= 150 and b != a, "other seeds must also work and differ")
    bad_other = sum(1 for t in b if grader.grade(t, json.dumps(t["reference_plan"]))["score"] != 1.0)
    check(bad_other == 0, f"seed 7: {bad_other} reference plans below 1.0")
    print(f"determinism ok; seed 7 also yields {len(b)} valid tasks")


def main():
    if "--docker" in sys.argv:
        cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "256m", "--cpus", "1", "--pids-limit", "64",
               "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
               "-v", f"{HERE}:/w:ro", "-w", "/w", "python:3.12-slim", "python", "-B", "/w/validate.py"]
        sys.exit(subprocess.run(cmd).returncode)
    path = os.path.join(HERE, "tasks.jsonl")
    for a in sys.argv[1:]:
        if not a.startswith("--"):
            path = a
    run(path)
    if FAILS:
        print(f"\nVALIDATION FAILED ({len(FAILS)} problems)")
        sys.exit(1)
    print("\nVALIDATION OK")


if __name__ == "__main__":
    main()
