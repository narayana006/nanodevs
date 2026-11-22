"""Validate tasks.jsonl.   python3 validate.py [--only SUBSTR] [--no-docker]

Checks (docker part runs ONE container at a time, python:3.12-slim, locked down, stdlib only):
  schema, unique ids, kind/difficulty mix, stored diff applies to base_files == patched_files, every planted defect
  sits on an added diff line;
  per task in a sandbox:  base passes all hidden tests; corrected code passes all; clean patched passes all;
  buggy patched fails each defect's proof test; each defect applied ALONE (on top of the corrected code) fails its own
  proof test while the other defects' proof tests still pass;
  grader: reference review scores 1.0 and passes everywhere; always-approve fails every buggy task;
  flag-everything fails every task; strict-JSON/tolerance/duplicate behaviour sanity checks.
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import grader  # noqa: E402
from engine import added_lines, apply_diff  # noqa: E402

KEYS = {"id", "kind", "difficulty", "title", "base_files", "diff", "patched_files", "fixed_files", "hidden_tests",
        "defects", "reference_review", "meta"}
errors = []


def err(tid, msg):
    errors.append(f"{tid}: {msg}")


def check_schema(tasks):
    ids = set()
    for t in tasks:
        if set(t) != KEYS:
            err(t.get("id"), f"keys {sorted(set(t) ^ KEYS)}")
            continue
        if t["id"] in ids:
            err(t["id"], "duplicate id")
        ids.add(t["id"])
        if t["kind"] not in ("buggy", "clean") or t["difficulty"] not in ("easy", "medium", "hard"):
            err(t["id"], "bad kind/difficulty")
        if (t["kind"] == "buggy") != bool(t["defects"]) or not 0 <= len(t["defects"]) <= 3:
            err(t["id"], "kind/defects mismatch (buggy needs 1-3 defects, clean 0)")
        if (t["kind"] == "clean") != (t["patched_files"] == t["fixed_files"]):
            err(t["id"], "patched/fixed relation wrong")
        try:
            if apply_diff(t["base_files"], t["diff"]) != t["patched_files"]:
                err(t["id"], "diff does not reproduce patched_files")
        except Exception as e:  # noqa: BLE001
            err(t["id"], f"diff apply error {e}")
        al = added_lines(t["diff"])
        for d in t["defects"]:
            lines = t["patched_files"][d["file"]].split("\n")
            if d["line"] not in al.get(d["file"], ()):
                err(t["id"], f"{d['id']} line {d['line']} is not an added line")
            if d["category"] not in grader.CATEGORIES:
                err(t["id"], f"{d['id']} bad category")
            first = d["buggy_text"].split("\n")[0].strip()
            if not any(first in x for x in lines[max(0, d["line"] - 4): d["line"] + 3]):
                err(t["id"], f"{d['id']} line is not near the buggy text")
            if f"def {d['proof_test']}(" not in t["hidden_tests"]:
                err(t["id"], f"{d['id']} proof test missing")
        if t["reference_review"]["verdict"] != ("request_changes" if t["defects"] else "approve"):
            err(t["id"], "reference verdict")


def docker_checks(tasks):
    from _sandbox import run_states
    for n, t in enumerate(tasks, 1):
        tests = t["hidden_tests"]
        def st(files):
            return {**files, "test_hidden.py": tests}
        states = {"base": st(t["base_files"]), "fixed": st(t["fixed_files"]), "patched": st(t["patched_files"])}
        if len(t["defects"]) > 1:
            for d in t["defects"]:
                f = dict(t["fixed_files"])
                assert f[d["file"]].count(d["correct_text"]) == 1
                f[d["file"]] = f[d["file"]].replace(d["correct_text"], d["buggy_text"])
                states["only_" + d["id"]] = st(f)
        try:
            res = run_states(states)
        except Exception as e:  # noqa: BLE001
            err(t["id"], f"sandbox: {e}")
            continue
        names = set(res["base"])
        for s in ("base", "fixed"):
            bad = [k for k, v in res[s].items() if v != "PASS"]
            if bad:
                err(t["id"], f"{s} fails {bad}")
        if t["kind"] == "clean":
            bad = [k for k, v in res["patched"].items() if v != "PASS"]
            if bad:
                err(t["id"], f"clean patched fails {bad}")
        else:
            for d in t["defects"]:
                if res["patched"].get(d["proof_test"]) != "FAIL":
                    err(t["id"], f"{d['id']} proof test {d['proof_test']} does not fail on diffed code")
                if len(t["defects"]) > 1:
                    r = res["only_" + d["id"]]
                    if r.get(d["proof_test"]) != "FAIL":
                        err(t["id"], f"{d['id']} alone does not fail its proof test")
                    for o in t["defects"]:
                        if o["id"] != d["id"] and o["proof_test"] != d["proof_test"] and r.get(o["proof_test"]) != "PASS":
                            err(t["id"], f"{d['id']} alone also fails {o['id']}'s proof test (not independent)")
        print(f"  [{n}/{len(tasks)}] {t['id']:<34} {t['kind']:<5} {t['difficulty']:<6} " + ("ok" if not any(e.startswith(t['id'] + ":") for e in errors) else "FAIL"), flush=True)


def flag_everything(t):
    fs = []
    for fn, lines in added_lines(t["diff"]).items():
        for ln in sorted(lines):
            for c in grader.CATEGORIES:
                fs.append(dict(file=fn, line=ln, category=c, explanation="x"))
    return dict(verdict="request_changes", findings=fs)


def grader_checks(tasks):
    always = dict(verdict="approve", findings=[])
    stats = Counter()
    for t in tasks:
        r = grader.score(t, json.dumps(t["reference_review"]))
        if not (r["passed"] and r["f1"] == 1.0 and r["fp"] == 0 and r["fn"] == 0):
            err(t["id"], f"reference review does not score full: {r}")
        a = grader.score(t, always)
        if (t["kind"] == "buggy") == a["passed"]:
            err(t["id"], "always-approve outcome wrong")
        stats["approve_pass_" + t["kind"]] += a["passed"]
        f = grader.score(t, flag_everything(t))
        if f["passed"]:
            err(t["id"], "flag-everything passes")
        stats["flag_pass"] += f["passed"]
        # tolerance and strictness sanity
        if t["defects"]:
            d = t["defects"][0]
            near = dict(verdict="request_changes", findings=[dict(file=d["file"], line=d["line"] + grader.LINE_TOLERANCE,
                                                                  category=d["category"], explanation="e")])
            far = dict(verdict="request_changes", findings=[dict(file=d["file"], line=d["line"] + grader.LINE_TOLERANCE + 1,
                                                                 category=d["category"], explanation="e")])
            wrongcat = dict(verdict="request_changes", findings=[dict(
                file=d["file"], line=d["line"], category=[c for c in grader.CATEGORIES if c != d["category"]][0], explanation="e")])
            if len(t["defects"]) == 1:
                if not grader.score(t, near)["passed"]:
                    err(t["id"], "within-tolerance finding should pass")
                if grader.score(t, far)["passed"] or grader.score(t, wrongcat)["passed"]:
                    err(t["id"], "out-of-tolerance / wrong-category finding should fail")
            dup = json.loads(json.dumps(t["reference_review"]))
            dup["findings"].append(dict(dup["findings"][0]))
            if grader.score(t, dup)["fp"] != 1:
                err(t["id"], "duplicate finding should count as a false positive")
            if grader.score(t, "```json\n" + json.dumps(t["reference_review"]) + "\n```")["valid"]:
                err(t["id"], "strict mode must reject fenced JSON")
        else:
            noisy = dict(verdict="approve", findings=[dict(file=sorted(t["base_files"])[0], line=1, category="missing_check", explanation="e")])
            if grader.score(t, noisy)["passed"]:
                err(t["id"], "finding on clean diff must fail")
    return stats


def main():
    argv = sys.argv[1:]
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "tasks.jsonl"))]
    check_schema(tasks)
    stats = grader_checks(tasks)
    full = tasks
    if only:
        tasks = [t for t in tasks if only in t["id"]]
    if "--no-docker" not in argv:
        print("running hidden tests in sandbox (one container at a time)...")
        docker_checks(tasks)
    c = Counter((t["kind"], t["difficulty"]) for t in full)
    nb = sum(t["kind"] == "buggy" for t in full)
    nd = Counter(len(t["defects"]) for t in full if t["kind"] == "buggy")
    cats = Counter(d["category"] for t in full for d in t["defects"])
    print(f"\ntasks: {len(full)} (buggy {nb}, clean {len(full) - nb}); validated in sandbox: {0 if '--no-docker' in argv else len(tasks)}")
    print("by kind/difficulty:", dict(sorted(c.items())))
    print("defects per buggy task:", dict(sorted(nd.items())), "| categories:", dict(sorted(cats.items())))
    print(f"always-approve: passes {stats['approve_pass_clean']}/{len(full) - nb} clean, {stats['approve_pass_buggy']}/{nb} buggy"
          f" | flag-everything passes {stats['flag_pass']}/{len(full)} | reference review: all pass" if not errors else "")
    if errors:
        print(f"\nFAILED: {len(errors)} problem(s)")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
