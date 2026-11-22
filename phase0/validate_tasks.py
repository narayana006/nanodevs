"""Check every task: tests pass on the correct code and fail on the buggy code."""
from tasks import TASKS
from harness import run_in_docker

bad = 0
for t in TASKS:
    good_ok, good_out = run_in_docker(t["correct"].strip() + "\n\n" + t["tests"].strip() + "\n")
    bug_ok, bug_out = run_in_docker(t["buggy"].strip() + "\n\n" + t["tests"].strip() + "\n")
    status = "ok" if (good_ok and not bug_ok) else "PROBLEM"
    if status != "ok":
        bad += 1
        print(t["id"], "correct passes:", good_ok, "| buggy fails:", not bug_ok)
        print("  correct output:", good_out[-200:])
    else:
        print(f"{t['id']:<18} ok")
print(f"\n{len(TASKS) - bad}/{len(TASKS)} tasks valid")
