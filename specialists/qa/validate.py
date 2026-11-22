"""Validate tasks.jsonl.

For every task:
  * schema: required fields, kind/difficulty values, unique ids, 4-8 hand mutants (tests/improve), `id` unique;
  * the reference tests PASS on reference_files and KILL (non-zero exit) every mutant; a mutant that fails only with
    SyntaxError/ImportError is rejected as broken; no mutant may already die on a bare import of the modules;
  * trivial candidates (empty file, `pass`, `assert True`, import-only) FAIL the grade (they pass on the correct code but
    leave every mutant alive);
  * regression: `files` (buggy) == reference_files overlaid with the single 'bug' mutant, test passes on the fixed code,
    fails on the buggy code, and is minimal (<= 12 non-blank lines);
  * improve: starting_tests passes on the correct code, `surviving` lists exactly the mutants that survive it (>= 2, not
    all), and the reference tests kill all.
Usage: python3 validate.py [--ids SUBSTR] [--exact]
  default: all variants of a task run in ONE container (sandbox.run_batch: same limits + a 64 MB /tmp tmpfs);
  --exact: one container per run, identical to harness2.run_files (slow).
"""
import json
import os
import sys
from collections import Counter

import sandbox
from sandbox import BAD_MUTANT, HERE

KINDS = ("tests", "regression", "improve")
DIFFS = ("easy", "medium", "hard")
REQ = ("id", "kind", "difficulty", "files", "reference_files", "instruction", "mutants", "reference_tests")


def run_all(pairs, exact, hashseed=None):
    if exact:
        return [sandbox.run_tests(f, t) for f, t in pairs]
    return sandbox.run_batch(pairs, hashseed=hashseed)


def validate(t, exact):
    probs = []
    for k in REQ:
        if k not in t:
            return [f"missing field {k}"]
    if t["kind"] not in KINDS or t["difficulty"] not in DIFFS:
        return ["bad kind/difficulty"]
    ref = t["reference_files"]
    muts = t["mutants"]
    hand = [m for m in muts if m["origin"] == "hand"]
    if t["kind"] == "regression":
        if len(muts) != 1 or muts[0]["id"] != "bug":
            probs.append("regression needs exactly one mutant 'bug'")
        elif {**ref, **muts[0]["files"]} != t["files"]:
            probs.append("files != reference_files + bug")
        if len([l for l in t["reference_tests"].splitlines() if l.strip()]) > 12:
            probs.append("regression test not minimal (> 12 lines)")
    else:
        if not 4 <= len(hand) <= 8:
            probs.append(f"{len(hand)} hand mutants")
        if t["files"] != ref:
            probs.append("files != reference_files")
    if t["kind"] == "improve" and "starting_tests" not in t:
        return ["improve without starting_tests"]
    mods = " ".join(f[:-3] for f in ref)
    bare = "import " + ", ".join(f[:-3] for f in ref) + "\n"
    variants = [ref] + [{**ref, **m["files"]} for m in muts]
    pairs = [(v, t["reference_tests"]) for v in variants]
    triv = ["", "pass", "assert True", bare]
    pairs += [(v, tt) for tt in triv for v in variants]
    if t["kind"] == "improve":
        pairs += [(v, t["starting_tests"]) for v in variants]
    res = run_all(pairs, exact, 1)
    n = len(variants)
    if not exact:   # flakiness guard: kill/pass vector must not depend on the string-hash seed
        again = run_all(pairs[:n], exact, 2)
        if [ok for ok, _ in again] != [ok for ok, _ in res[:n]]:
            probs.append('results depend on PYTHONHASHSEED (flaky ordering)')
    r = res[:n]
    if not r[0][0]:
        probs.append("reference tests fail on correct code: " + r[0][1][-200:])
    for m, (ok, out) in zip(muts, r[1:]):
        if ok:
            probs.append(f"mutant {m['id']} SURVIVES the reference tests")
        elif any(b in out for b in BAD_MUTANT):
            probs.append(f"mutant {m['id']} is broken code")
    off = n
    for tt in triv:
        rr = res[off:off + n]
        off += n
        if not rr[0][0]:
            if tt == bare:
                probs.append("bare import fails on the correct code")
            continue
        if all(not ok for ok, _ in rr[1:]):
            probs.append(f"trivial test {tt!r} kills every mutant")
        elif any(not ok for ok, _ in rr[1:]) and tt == bare:
            probs.append("a mutant dies on a bare import")
        grade_ok = all(not ok for ok, _ in rr[1:])
        if grade_ok:
            probs.append(f"trivial test {tt!r} would pass the grade")
    if t["kind"] == "improve":
        rr = res[off:off + n]
        if not rr[0][0]:
            probs.append("starting tests fail on the correct code")
        surv = [m["id"] for m, (ok, _) in zip(muts, rr[1:]) if ok]
        if surv != t.get("surviving"):
            probs.append(f"surviving mismatch: file {t.get('surviving')} actual {surv}")
        if len(surv) < 2 or len(surv) == len(muts):
            probs.append(f"starting tests not meaningfully weak ({len(surv)}/{len(muts)} survive)")
    return probs


def main():
    args = sys.argv[1:]
    only = args[args.index("--ids") + 1] if "--ids" in args else None
    exact = "--exact" in args
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "tasks.jsonl"))]
    ids = [t["id"] for t in tasks]
    bad = 0
    if len(ids) != len(set(ids)):
        print("PROBLEM duplicate ids")
        bad += 1
    n_run = 0
    for t in tasks:
        if only and only not in t["id"]:
            continue
        n_run += 1
        probs = validate(t, exact)
        if probs:
            bad += 1
            print(f"PROBLEM {t['id']}: " + " | ".join(probs), flush=True)
        else:
            print(f"ok      {t['id']:<34}{t['kind']:<11}{t['difficulty']:<7}mutants={len(t['mutants'])}", flush=True)
    c = Counter(t["kind"] for t in tasks)
    print(f"\n{n_run - bad}/{n_run} tasks valid   total={len(tasks)} {dict(c)}"
          f"   mutants={sum(len(t['mutants']) for t in tasks)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
