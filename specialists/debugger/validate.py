"""Validate tasks.jsonl against the sandbox. For every task:
  1. starting code fails the visible failing test AND the hidden tests
  2. the reference fix passes the visible test (and, via grade(), the hidden tests)
  3. the reference response (root-cause JSON + fixed files) scores full (1.0)
  4. a wrong-category JSON loses the root-cause half, an empty fix loses the fix half
  5. no_collateral tasks: the negative reference (passes the failing test, breaks unrelated behavior) fails hidden tests
  6. minimal_diff tasks: an oversized rewrite of the reference is rejected by the diff cap
  7. flaky_looking tasks: start fails and reference passes on a second run too
Usage: python validate.py [tasks.jsonl] [--only SUBSTRING]
"""
import json
import sys

from grade import CATEGORIES, grade, reference_response
from sandbox import run_files

argv = sys.argv[1:]
only = None
if "--only" in argv:
    i = argv.index("--only")
    only = argv[i + 1]
    del argv[i:i + 2]
path = argv[0] if argv else "tasks.jsonl"
tasks = [json.loads(l) for l in open(path, encoding="utf-8")]
if only:
    tasks = [t for t in tasks if only in t["id"]]

REQUIRED = {"id", "kind", "difficulty", "category", "tags", "files", "failing_test", "traceback", "ground_truth",
            "hidden_tests", "reference"}
bad = 0
for t in tasks:
    p = []
    miss = REQUIRED - set(t)
    if miss:
        p.append(f"missing fields {miss}")
    gt = t["ground_truth"]
    if gt["category"] not in CATEGORIES or gt["file"] not in t["files"]:
        p.append("bad ground truth")
    if not 3 <= len(t["files"]) <= 6:
        p.append(f"{len(t['files'])} files")
    hid = t["hidden_tests"]
    if t["failing_test"]["code"].strip() not in hid["code"]:
        p.append("hidden tests do not include the failing test")
    ok, _ = run_files({**t["files"], "test_failing.py": t["failing_test"]["code"]}, "test_failing.py")
    if ok:
        p.append("start passes visible test")
    ok, _ = run_files({**t["files"], hid["name"]: hid["code"]}, hid["name"])
    if ok:
        p.append("start passes hidden tests")
    ok, out = run_files({**t["files"], **t["reference"]["files"], "test_failing.py": t["failing_test"]["code"]}, "test_failing.py")
    if not ok:
        p.append("reference fails visible test: " + out[-200:])
    g = grade(t, reference_response(t))
    if g["score"] != 1.0:
        p.append(f"reference response scores {g['score']}: {g['detail']} {g['root_cause_parts']}")
    wrong = dict(t["reference"]["root_cause"], category=[c for c in CATEGORIES if c != gt["category"]][0])
    g2 = grade(t, "```json\n" + json.dumps(wrong) + "\n```\n")
    if g2["score"] != 0.0:
        p.append("wrong category + no files should score 0")
    for neg in t.get("negative_references", []):
        ok, _ = run_files({**t["files"], **neg["files"], "test_failing.py": t["failing_test"]["code"]}, "test_failing.py")
        if not ok:
            p.append("negative reference should pass the visible test")
        gn = grade(t, reference_response({**t, "reference": {**t["reference"], "files": neg["files"]}}))
        if gn["fix"]:
            p.append("negative reference passes hidden tests (collateral damage not detected)")
    if "no_collateral" in t["tags"] and not t.get("negative_references"):
        p.append("no_collateral task without negative reference")
    if "max_changed_lines" in t:
        fat = {n: c + "\n".join(f"# pad {i}" for i in range(t["max_changed_lines"] + 1)) + "\n" for n, c in t["reference"]["files"].items()}
        gf = grade(t, reference_response({**t, "reference": {**t["reference"], "files": fat}}))
        if gf["fix"] or "too large" not in gf["detail"]:
            p.append("diff cap not enforced")
    if "flaky_looking" in t["tags"]:
        ok, _ = run_files({**t["files"], hid["name"]: hid["code"]}, hid["name"])
        ok2, out = run_files({**t["files"], **t["reference"]["files"], hid["name"]: hid["code"]}, hid["name"])
        if ok or not ok2:
            p.append("not deterministic across runs")
    if p:
        bad += 1
        print(f"PROBLEM {t['id']}: " + " | ".join(p), flush=True)
    else:
        print(f"ok      {t['id']:<34}{t['difficulty']:<8}{t['category']}", flush=True)
print(f"\n{len(tasks) - bad}/{len(tasks)} tasks valid")
sys.exit(1 if bad else 0)
