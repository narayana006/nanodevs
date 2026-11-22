"""Validate tasks.jsonl: start state must FAIL, reference must PASS (all checks), in the sandbox.

For kind fix/harden, additionally every check flagged bug=true must fail on the start state and every check
flagged keep=true (regression guards: "do not break what works") must pass on the start state. Unflagged checks are
free on the start state but must pass on the reference. Also lints the schema.

usage: python validate.py [--fast] [--domain D] [--id ID] [--no-build]
  --fast : evaluate in-process on the host (no containers, shellcheck skipped) - for quick iteration only
"""
import argparse
import json
import sys
import time

import build_tasks
import grade as G


def lint(t):
    errs = []
    for k in ("id", "kind", "domain", "difficulty", "instruction", "files", "outputs", "reference", "checks"):
        if k not in t:
            errs.append("missing " + k)
    if not t["checks"]:
        errs.append("no checks")
    if set(t["outputs"]) != set(t["reference"]):
        errs.append("outputs != reference keys")
    if len(t["instruction"]) < 40:
        errs.append("instruction too short")
    if t["kind"] in ("fix", "harden") and not any(c.get("bug") for c in t["checks"]):
        errs.append("fix/harden task without bug-flagged checks")
    if t["kind"] in ("fix", "harden") and not t["files"]:
        errs.append("fix/harden task without start files")
    ids = [c["id"] for c in t["checks"]]
    if len(set(ids)) != len(ids):
        errs.append("duplicate check ids")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--domain")
    ap.add_argument("--id")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()
    if not a.no_build:
        build_tasks.main()
    tasks = G.load_tasks()
    if a.domain:
        tasks = [t for t in tasks if t["domain"] == a.domain]
    if a.id:
        tasks = [t for t in tasks if t["id"] == a.id or t["id"].startswith(a.id)]
    bad, t0 = [], time.time()
    for t in tasks:
        problems = lint(t)
        if not problems:
            s, r = G.grade_many(t, [{}, t["reference"]], sandbox=not a.fast)
            if s["passed"]:
                problems.append("START STATE PASSES (should fail)")
            if t["kind"] in ("fix", "harden"):
                for c in t["checks"]:
                    ok = s["checks"][c["id"]][0]
                    if c.get("bug") and ok and not (a.fast and c["type"] == "shellcheck"):
                        problems.append(f"bug check {c['id']} passes on start state: {c['desc']}")
                    if c.get("keep") and not ok:
                        problems.append(f"keep check {c['id']} fails on start state: {s['checks'][c['id']][1]}")
            for cid, (ok, msg) in r["checks"].items():
                if not ok:
                    problems.append(f"REFERENCE fails {cid}: {msg}")
            if not r["passed"] and not any("REFERENCE" in p for p in problems):
                problems.append("reference did not pass")
        status = "ok  " if not problems else "FAIL"
        print(f"{status} {t['id']:<34}{t['domain']:<11}{t['kind']:<8}{t['difficulty']:<7}checks={len(t['checks'])}", flush=True)
        for p in problems:
            print("     -", p)
        if problems:
            bad.append(t["id"])
    from collections import Counter
    print(f"\n{len(tasks)-len(bad)}/{len(tasks)} tasks valid in {time.time()-t0:.0f}s ({'host fast mode' if a.fast else 'sandboxed'})")
    print("by domain:", dict(Counter(t["domain"] for t in tasks)))
    print("by kind:", dict(Counter(t["kind"] for t in tasks)))
    print("by difficulty:", dict(Counter(t["difficulty"] for t in tasks)))
    if bad:
        print("INVALID:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
