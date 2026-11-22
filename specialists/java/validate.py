#!/usr/bin/env python3
"""Validate tasks.jsonl: for every task the starting files must FAIL the hidden tests and the reference must PASS.

  python3 validate.py                       # host javac (JDK 17+ on PATH), no sandbox, jobs=4
  python3 validate.py --backend docker --image eclipse-temurin:21-jdk   # locked-down container, one at a time
  python3 validate.py --only fix-lru-order --verbose
"""
import argparse, json, sys, time
from concurrent.futures import ThreadPoolExecutor
from runner import run_task, task_files

def check(t, backend, image):
    t0 = time.time()
    ok_ref, out_ref, ph = run_task(task_files(t), t["entry"], backend, image)
    if not ok_ref:
        return t["id"], False, "reference FAILED (%s): %s" % (ph, out_ref[-600:]), time.time() - t0
    ok_start, out_start, ph = run_task({**t["files"], **t["hidden_tests"]}, t["entry"], backend, image)
    if ok_start:
        return t["id"], False, "starting files already PASS the hidden tests (task is vacuous)", time.time() - t0
    return t["id"], True, "ok (start fails in %s phase)" % ph, time.time() - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="tasks.jsonl")
    ap.add_argument("--backend", choices=["host", "docker"], default="host")
    ap.add_argument("--image", default="eclipse-temurin:21-jdk")
    ap.add_argument("--jobs", type=int, default=4, help="host backend only; docker always runs one container at a time")
    ap.add_argument("--only", help="substring filter on task id")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    tasks = [json.loads(l) for l in open(a.tasks)]
    if a.only: tasks = [t for t in tasks if a.only in t["id"]]
    jobs = a.jobs if a.backend == "host" else 1
    bad = 0
    with ThreadPoolExecutor(jobs) as ex:
        for tid, ok, msg, dt in ex.map(lambda t: check(t, a.backend, a.image), tasks):
            bad += not ok
            if not ok or a.verbose: print(("PASS " if ok else "FAIL ") + tid + "  " + msg + "  [%.1fs]" % dt, flush=True)
    print("%d/%d tasks valid" % (len(tasks) - bad, len(tasks)))
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
