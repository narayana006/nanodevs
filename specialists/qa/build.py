"""Build tasks.jsonl from defs/*.py (hand-authored modules, tests, mutant patches), adding auto-mutants.

Each def (a dict in a module-level TASKS list):
  id, diff (easy|medium|hard), spec (str), files {name: src}, tests (reference test file),
  muts [(tag, old, new) | (tag, file, old, new)]   hand-designed mutants as exact-once source patches (3-tuples patch d['main'] or the first file),
  weak int k | [stmt indices]   optional -> also emit an `improve` task whose starting tests = the first k top-level statements of `tests`
  regress [dict(mut=i, report=str, test=str)]   optional (inline or in regress_defs.REGRESS[id]) -> `regression` tasks:
                              hand mutant i (1-based) is the planted bug
Usage: python3 build.py [--only SUBSTR] [--no-auto]    (--only does not write tasks.jsonl)
"""
import hashlib
import importlib
import json
import os
import pkgutil
import random
import sys

import automut
import sandbox
from sandbox import BAD_MUTANT, HERE, run_tests

CACHE_PATH = os.path.join(HERE, ".tmp", "cache.json")
try:
    CACHE = json.load(open(CACHE_PATH))
except Exception:
    CACHE = {}

N_AUTO = 4
TRIES = 14

TESTS_TMPL = ("{spec}\n\nWrite a test file `test_solution.py` that imports from {mods} and uses plain `assert` statements "
              "(no pytest, no unittest). The tests will be run against the correct code, where they must all pass, and "
              "against several subtly broken versions of it, where each must fail. Cover edge cases and error cases, not "
              "only the happy path. Return only `test_solution.py` in one ```python block whose first line is "
              "`# file: test_solution.py`. No explanation.")
REGRESS_TMPL = ("The code shown is the BUGGY version of a small project. Bug report:\n\n{report}\n\nWrite a minimal "
                "regression test file `test_solution.py` (plain `assert` statements, no pytest/unittest, ideally under 10 "
                "lines) that FAILS on the buggy code shown and PASSES once the bug is fixed. Test only the reported bug; "
                "do not rewrite the code. Return only `test_solution.py` in one ```python block whose first line is "
                "`# file: test_solution.py`. No explanation.")
IMPROVE_TMPL = ("{spec}\n\nAn existing test file `test_solution.py` is given. It passes on the correct code, but some "
                "subtly broken versions of the code still pass it (surviving mutants). Improve it: return the complete "
                "updated `test_solution.py` (plain `assert` statements) that still passes on the correct code and now "
                "also fails on every broken version. Keep the useful existing checks. Return only `test_solution.py` in "
                "one ```python block whose first line is `# file: test_solution.py`. No explanation.")


def _key(files, tests):
    return hashlib.sha1(json.dumps([files, tests], sort_keys=True).encode()).hexdigest()


def prefetch(pairs):
    """Run all not-yet-cached (files, tests) pairs in one container."""
    todo, seen = [], set()
    for files, tests in pairs:
        k = _key(files, tests)
        if k not in CACHE and k not in seen:
            seen.add(k)
            todo.append((k, files, tests))
    for i in range(0, len(todo), 60):
        chunk = todo[i:i + 60]
        for (k, _, _), (ok, out) in zip(chunk, sandbox.run_batch([(f, t) for _, f, t in chunk])):
            CACHE[k] = [ok, out[-400:]]
    if todo:
        json.dump(CACHE, open(CACHE_PATH, "w"))


def cached_run(files, tests, timeout=None):
    k = _key(files, tests)
    if k not in CACHE:
        prefetch([(files, tests)])
    return tuple(CACHE[k])


def apply_patch(files, p, main=None):
    if len(p) == 3:
        tag, old, new = p
        fname = main or next(iter(files))
    else:
        tag, fname, old, new = p
    src = files[fname]
    if src.count(old) != 1:
        raise ValueError(f"patch [{tag}] old text occurs {src.count(old)}x: {old[:50]!r}")
    pos = src.index(old)
    if new == "" and old.endswith("\n"):   # line removal: also drop the indentation that precedes the removed text
        while pos > 0 and src[pos - 1] in " \t":
            pos -= 1
            old = src[pos] + old
    res = src[:pos] + new + src[pos + len(old):]
    return tag, fname, res


def split_stmts(src):
    """Top-level statements as source text (decorators included)."""
    import ast as _ast
    lines = src.splitlines()
    out = []
    for n in _ast.parse(src).body:
        start = min([n.lineno] + [x.lineno for x in getattr(n, "decorator_list", [])])
        out.append("\n".join(lines[start - 1:n.end_lineno]))
    return out


def plan(d, auto):
    """Every (files, tests) pair build_def may ask for, so they can be run in one container."""
    files = {k: v.strip("\n") + "\n" for k, v in d["files"].items()}
    pairs = [(files, d["tests"])]
    muts = []
    for p in d["muts"]:
        try:
            _, fname, src = apply_patch(files, p, d.get('main'))
        except Exception:
            continue
        muts.append({**files, fname: src})
    pairs += [(m, d["tests"]) for m in muts]
    if auto:
        pool = [(f, new) for f in files for _, new in automut.candidates(files[f])]
        random.Random(d["id"]).shuffle(pool)
        muts += [{**files, f: new} for f, new in pool[:TRIES]]
        pairs += [(m, d["tests"]) for m in muts[len(d["muts"]):]]
    for rg in d.get("regress", []):
        if rg["mut"] - 1 < len(d["muts"]):
            try:
                _, fname, src = apply_patch(files, d["muts"][rg["mut"] - 1], d.get("main"))
                pairs += [(files, rg["test"]), ({**files, fname: src}, rg["test"])]
            except Exception:
                pass
    if d.get("weak"):
        stmts = split_stmts(d["tests"].strip("\n") + "\n")
        keep = range(d["weak"]) if isinstance(d["weak"], int) else d["weak"]
        start = "\n".join(stmts[i] for i in keep) + "\n"
        pairs += [(files, start)] + [(m, start) for m in muts]
    return pairs


def build_def(d, auto=True):
    probs = []
    files = {k: v.strip("\n") + "\n" for k, v in d["files"].items()}
    ok, out = cached_run(files, d["tests"])
    if not ok:
        return None, [f"reference tests fail on correct code: {out[-300:]}"]
    n_hand = len(d["muts"])
    if not 4 <= n_hand <= 8:
        probs.append(f"{n_hand} hand mutants (need 4-8)")
    mutants = []
    for i, p in enumerate(d["muts"], 1):
        try:
            tag, fname, src = apply_patch(files, p, d.get('main'))
        except Exception as e:
            probs.append(str(e))
            continue
        mok, mout = cached_run({**files, fname: src}, d["tests"])
        if mok:
            probs.append(f"hand mutant h{i} [{tag}] SURVIVES")
        elif any(b in mout for b in BAD_MUTANT):
            probs.append(f"hand mutant h{i} [{tag}] is broken code: {mout[-200:]}")
        mutants.append(dict(id=f"h{i}", origin="hand", tag=tag.split(":")[0].strip(), desc=tag, files={fname: src}))
    if probs:
        return None, probs
    survivors = 0
    if auto:
        pool = [(f, desc, new) for f in files for desc, new in automut.candidates(files[f])]
        random.Random(d["id"]).shuffle(pool)
        kept = 0
        for f, desc, new in pool[:TRIES]:
            if kept >= N_AUTO:
                break
            mok, mout = cached_run({**files, f: new}, d["tests"], 8)
            if mok:
                survivors += 1      # surviving auto-mutant: equivalent or the reference tests are weak -> not included
            elif mout == "TIMEOUT" or any(b in mout for b in BAD_MUTANT) or "NameError" in mout:
                continue
            else:
                kept += 1
                mutants.append(dict(id=f"a{kept}", origin="auto", tag="ast", desc=f"{f} {desc}", files={f: new}))
    return dict(files=files, mutants=mutants, auto_survivors=survivors), []


def main():
    args = sys.argv[1:]
    only = args[args.index("--only") + 1] if "--only" in args else None
    auto = "--no-auto" not in args
    sys.path.insert(0, os.path.join(HERE, "defs"))
    defs = []
    for m in sorted(pkgutil.iter_modules([os.path.join(HERE, "defs")]), key=lambda x: x.name):
        defs += importlib.import_module(m.name).TASKS
    try:
        from regress_defs import REGRESS
        for d in defs:
            d.setdefault("regress", []).extend(REGRESS.get(d["id"], []))
    except ImportError:
        pass
    ids = [d["id"] for d in defs]
    assert len(ids) == len(set(ids)), "duplicate ids"
    out, bad, stats = [], 0, dict(tests=0, regression=0, improve=0, auto=0, hand=0, auto_surv=0)
    for d in defs:
        if only and only not in d["id"]:
            continue
        try:
            prefetch(plan(d, auto))
        except Exception as e:
            print(f"PROBLEM {d['id']}: batch run failed: {e}", flush=True)
            bad += 1
            continue
        r, probs = build_def(d, auto)
        if probs:
            bad += 1
            print(f"PROBLEM {d['id']}: " + " | ".join(probs), flush=True)
            continue
        files, muts = r["files"], r["mutants"]
        mods = ", ".join(f"`{f[:-3]}`" for f in files)
        base = dict(difficulty=d["diff"], files=files, reference_files=files, mutants=muts, reference_tests=d["tests"].strip("\n") + "\n")
        out.append(dict(id=d["id"], kind="tests", **base, instruction=TESTS_TMPL.format(spec=d["spec"], mods=mods)))
        stats["tests"] += 1
        stats["hand"] += sum(m["origin"] == "hand" for m in muts)
        stats["auto"] += sum(m["origin"] == "auto" for m in muts)
        stats["auto_surv"] += r["auto_survivors"]
        for n, rg in enumerate(d.get("regress", []), 1):
            hm = muts[rg["mut"] - 1]
            buggy = {**files, **hm["files"]}
            ok1, o1 = cached_run(files, rg["test"])
            ok2, o2 = cached_run(buggy, rg["test"])
            if not ok1 or ok2:
                bad += 1
                print(f"PROBLEM {d['id']}_regress{n}: fixed passes={ok1} buggy passes={ok2} {o1[-150:]}")
                continue
            out.append(dict(id=f"{d['id']}_regress{n}", kind="regression", difficulty=rg.get("diff", d["diff"]),
                            files=buggy, reference_files=files,
                            mutants=[dict(id="bug", origin="hand", tag=hm["tag"], desc=hm["desc"], files=hm["files"])],
                            reference_tests=rg["test"].strip("\n") + "\n",
                            instruction=REGRESS_TMPL.format(report=rg["report"].strip())))
            stats["regression"] += 1
        if d.get("weak"):
            stmts = split_stmts(d["tests"].strip("\n") + "\n")
            keep = range(d["weak"]) if isinstance(d["weak"], int) else d["weak"]
            start = "\n".join(stmts[i] for i in keep) + "\n"
            ok, o = cached_run(files, start)
            surv = []
            for m in muts:
                mok, _ = cached_run({**files, **m["files"]}, start)
                if mok:
                    surv.append(m["id"])
            if not ok or len(surv) < 2 or len(surv) == len(muts):
                bad += 1
                print(f"PROBLEM {d['id']}_improve: start passes={ok} survivors={surv}/{len(muts)}")
                continue
            out.append(dict(id=f"{d['id']}_improve", kind="improve", **base, starting_tests=start, surviving=surv,
                            instruction=IMPROVE_TMPL.format(spec=d["spec"])))
            stats["improve"] += 1
    print(f"built {len(out)} tasks {stats} problems={bad}")
    if not only and not bad:
        with open(os.path.join(HERE, "tasks.jsonl"), "w") as f:
            for t in out:
                f.write(json.dumps(t) + "\n")
        print("wrote tasks.jsonl")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
