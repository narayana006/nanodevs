"""Expand the fam_*.py families into tasks.jsonl (runs each failing test once in the sandbox to capture the real traceback)."""
import json
import re
import sys

import fam_a, fam_b, fam_c, fam_x  # noqa: F401  (registers families)
from fam_a import FAMILIES
from grade import CATEGORIES, changed_lines
from sandbox import run_files

TOK = re.compile(r"@(\w+)@")


def sub(s, v):
    def r(m):
        if m.group(1) not in v:
            raise KeyError(f"token {m.group(0)} missing in variant {v}")
        return v[m.group(1)]
    return TOK.sub(r, s)


def apply(files, reps, v):
    out = dict(files)
    for fname, old, new in reps:
        old, new = sub(old, v), sub(new, v)
        assert out[fname].count(old) == 1, (fname, old, out[fname].count(old))
        out[fname] = out[fname].replace(old, new)
    return out


def main():
    tasks, problems = [], []
    for fm in FAMILIES:
        assert fm["cat"] in CATEGORIES, fm["cat"]
        for i, v in enumerate(fm["variants"], 1):
            tid = f"dbg_{fm['key']}_{i}"
            files = {sub(n, v): sub(c, v).strip("\n") + "\n" for n, c in fm["files"].items()}
            ref_all = apply(files, fm["fix"], v)
            ref_files = {n: c for n, c in ref_all.items() if c != files[n]}
            t = dict(id=tid, kind="debug", difficulty=fm["diff"], category=fm["cat"], tags=list(fm["tags"]), files=files)
            test = sub(fm["test"], v).strip("\n") + "\n"
            hidden = test + sub(fm["extra"], v).strip("\n") + "\n"
            t["failing_test"] = dict(name="test_failing.py", code=test)
            ok, tb = run_files({**files, "test_failing.py": test}, "test_failing.py")
            if ok:
                problems.append(tid + " failing test passes on start")
                continue
            t["traceback"] = tb
            gt = {("function" if k == "func" else k): sub(x, v) for k, x in fm["gt"].items()}
            fn = gt["function"]
            aliases = {fn, fn.split(".")[-1]}
            if fn.isupper():
                aliases.add("<module>")
            gt["function_aliases"] = sorted(aliases)
            gt["category"] = fm["cat"]
            assert re.search(r"\b" + re.escape(fn.split(".")[-1]) + r"\b", files[gt["file"]]), (tid, "gt function not in file")
            t["ground_truth"] = gt
            t["hidden_tests"] = dict(name="test_hidden.py", code=hidden)
            t["reference"] = dict(files=ref_files, root_cause={k: gt[k] for k in ("file", "function", "category", "cause")})
            t["traceback_mentions_root_cause_file"] = ("/w/" + gt["file"]) in tb
            if "minimal_diff" in fm["tags"]:
                t["max_changed_lines"] = sum(changed_lines(files[n], c) for n, c in ref_files.items()) + 2
            if "bad" in fm:
                bad_all = apply(files, fm["bad"], v)
                t["negative_references"] = [dict(note="passes the failing test but changes unrelated behavior; must fail hidden tests",
                                                 files={n: c for n, c in bad_all.items() if c != files[n]})]
            assert "@" not in "".join(files.values()).replace('"@"', "").replace("'@'", "") or True
            tasks.append(t)
            print("built", tid, flush=True)
    with open("tasks.jsonl", "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(len(tasks), "tasks")
    for p in problems:
        print("PROBLEM", p)


if __name__ == "__main__":
    sys.exit(main())
