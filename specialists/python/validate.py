"""Prove every task: starting code fails the hidden tests, reference passes them (and the visible examples).
Usage: python3 validate.py [id-substring ...]   (runs Docker containers one at a time)"""
import json
import sys

from common import run_files
from registry import all_tasks

OUT = {}  # task id -> output of the visible examples on the starting code (used as the failing-test output in fix prompts)
KINDS = {"fix", "write", "feature", "refactor"}
DIFFS = {"easy", "medium", "hard"}


RUNNER = r'''
import json, subprocess, sys
res = {}
for name in ("start_hidden", "ref_hidden", "start_visible", "ref_visible"):
    try:
        p = subprocess.run([sys.executable, "test_hidden.py"], cwd="/w/" + name, capture_output=True, text=True, timeout=30)
        res[name] = [p.returncode == 0, (p.stdout + p.stderr)[-350:]]
    except subprocess.TimeoutExpired:
        res[name] = [False, "TIMEOUT"]
print(json.dumps(res))
'''


def check(t):
    """All four runs (start/reference x hidden/visible) happen in ONE container, in four separate sub-processes."""
    p = []
    if t["kind"] not in KINDS or t["difficulty"] not in DIFFS:
        p.append("bad kind/difficulty")
    if not t["reference"]:
        p.append("empty reference")
    files = {"runner.py": RUNNER}
    for name, base, tests in (("start_hidden", t["files"], t["hidden"]), ("ref_hidden", {**t["files"], **t["reference"]}, t["hidden"]),
                              ("start_visible", t["files"], t["visible"]), ("ref_visible", {**t["files"], **t["reference"]}, t["visible"])):
        for fname, code in {**base, "test_hidden.py": tests}.items():
            files[name + "/" + fname] = code
    ok, out = run_files(files, "runner.py", timeout=90)
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except Exception:
        return p + ["sandbox run failed: " + out[-300:]]
    OUT[t["id"]] = res["start_visible"][1]
    if res["start_hidden"][0]:
        p.append("hidden tests already pass on starting code")
    if not res["ref_hidden"][0]:
        p.append("reference fails hidden tests: " + res["ref_hidden"][1][-400:])
    if t["kind"] == "fix" and res["start_visible"][0]:
        p.append("visible example passes on buggy code")
    if not res["ref_visible"][0]:
        p.append("reference fails visible examples: " + res["ref_visible"][1][-300:])
    return p


if __name__ == "__main__":
    flt = sys.argv[1:]
    tasks = all_tasks()
    ids = [t["id"] for t in tasks]
    assert len(ids) == len(set(ids)), "duplicate ids"
    bad = n = 0
    for t in tasks:
        if flt and not any(f in t["id"] for f in flt):
            continue
        n += 1
        pr = check(t)
        if pr:
            bad += 1
            print(f"PROBLEM {t['id']}: " + " | ".join(pr), flush=True)
        else:
            print(f"ok      {t['id']:<40}{t['kind']:<9}{t['difficulty']}", flush=True)
    if not flt:
        import json, os
        json.dump(OUT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "start_outputs.json"), "w"), indent=1)
    print(f"\n{n - bad}/{n} tasks valid")
    sys.exit(1 if bad else 0)
