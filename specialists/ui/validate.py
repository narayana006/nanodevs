"""Prove every task: start state FAILS the hidden checks, start+reference PASSES them.
Usage: python3 validate.py [--only SUBSTR] [--tasks tasks.jsonl]
Exit code 1 if any task is invalid. Containers run one at a time."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_ui import load_tasks, run_checks

ap = argparse.ArgumentParser()
ap.add_argument("--only", default="")
ap.add_argument("--tasks", default=None)
a = ap.parse_args()
bad, n = [], 0
for t in load_tasks(a.tasks):
    if a.only not in t["id"]:
        continue
    n += 1
    s_ok, s_out = run_checks(t["files"], t["checks"])
    r_ok, r_out = run_checks({**t["files"], **t["reference"]["files"]}, t["checks"])
    status = "OK " if (not s_ok and r_ok) else "BAD"
    print(f"{status} {t['id']:<40}{t['kind']:<7}{t['difficulty']:<7} start={'pass' if s_ok else 'fail'} ref={'pass' if r_ok else 'fail'}", flush=True)
    if status == "BAD":
        bad.append(t["id"])
        if s_ok: print("   start state unexpectedly passes")
        if not r_ok: print("   ref output:", r_out.strip().replace("\n", "\n   "))
print(f"\n{n - len(bad)}/{n} tasks valid" + (f"; INVALID: {bad}" if bad else ""))
sys.exit(1 if bad else 0)
