"""Check the round 2 tasks with reference solutions: starting code fails, reference passes, mutants die."""
import sys

from harness2 import run_files, tests_file
from tasks_fix import TASKS_FIX
from tasks_write import TASKS_WRITE
from tasks_feature import TASKS_FEATURE
from tasks_tests import TASKS_TESTS

ALL = TASKS_FIX + TASKS_WRITE + TASKS_FEATURE + TASKS_TESTS
bad = 0
for t in ALL:
    problems = []
    if t["kind"] == "tests":
        ok, out = run_files({**t["files"], "test_solution.py": t["reference_tests"]}, "test_solution.py")
        if not ok:
            problems.append("reference tests fail on correct module: " + out[-200:])
        for n, m in enumerate(t["mutants"], 1):
            mok, mout = run_files({**t["files"], **m, "test_solution.py": t["reference_tests"]}, "test_solution.py")
            if mok:
                problems.append(f"mutant {n} survives the reference tests")
            elif "Error" not in mout and "assert" not in mout.lower():
                problems.append(f"mutant {n} failed oddly: {mout[-120:]}")
    else:
        tests = tests_file(t)
        ok0, out0 = run_files({**t["files"], "test_hidden.py": tests}, "test_hidden.py")
        if ok0:
            problems.append("tests already pass before any change")
        ok1, out1 = run_files({**t["files"], **t["reference"], "test_hidden.py": tests}, "test_hidden.py")
        if not ok1:
            problems.append("reference solution fails: " + out1[-300:])
        if t["kind"] != "fix":
            vok, vout = run_files({**t["files"], **t["reference"], "test_hidden.py": t["visible"]}, "test_hidden.py")
            if not vok:
                problems.append("reference fails visible examples: " + vout[-200:])
    if problems:
        bad += 1
        print(f"PROBLEM {t['id']}: " + " | ".join(problems))
    else:
        print(f"ok      {t['id']}")
print(f"\n{len(ALL) - bad}/{len(ALL)} tasks valid")
sys.exit(1 if bad else 0)
