"""Grading for debugger tasks.

Model response format (see make_prompt):
  * one ```json block with exactly the keys file, function, category, cause
  * one ```python block per changed file, first line `# file: <name>.py` (complete file contents)

score = 0.5 * root_cause + 0.5 * fix   (root_cause and fix are each 0 or 1; `full` = both)
"""
import difflib
import json
import re

from sandbox import run_files

CATEGORIES = ["off-by-one", "wrong type/None handling", "mutated shared state", "wrong default", "stale cache",
              "incorrect ordering", "timezone/rounding", "encoding", "mis-wired config", "wrong unit",
              "incorrect exception handling", "aliasing"]
KEYS = {"file", "function", "category", "cause"}
NAME_OK = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*\.py$")

FORMAT = ("Answer in two parts, nothing else.\n"
          "1. One ```json block with exactly these string keys: \"file\" (the file containing the root cause), "
          "\"function\" (the function, or Class.method, or the constant/class name where the root cause lives), "
          "\"category\" (one of: " + ", ".join(CATEGORIES) + "), \"cause\" (one sentence, max 300 characters). "
          "The root cause is where the code is wrong, which is often not where the traceback points.\n"
          "2. The complete contents of every file you change, each in its own ```python block whose first line is "
          "`# file: <filename>`. Do not return tests or unchanged files. Keep the fix minimal.")


def show(files):
    return "\n\n".join(f"```python\n# file: {n}\n{c.strip()}\n```" for n, c in files.items())


def make_prompt(task):
    return (f"This small Python project has a failing test. Find the root cause and fix it.\n\n{show(task['files'])}\n\n"
            f"Failing test (`{task['failing_test']['name']}`):\n```python\n{task['failing_test']['code'].strip()}\n```\n\n"
            f"Output when it is run:\n```\n{task['traceback'].strip()}\n```\n\n{FORMAT}")


def parse_response(text):
    """-> (root_cause_obj_or_None, {filename: code}, json_error_or_None)"""
    obj, err = None, "no json block"
    for block in re.findall(r"```json[ \t]*\n(.*?)```", text, re.S):
        try:
            obj, err = json.loads(block), None
            break
        except ValueError as e:
            err = f"bad json: {e}"
    files = {}
    for block in re.findall(r"```[A-Za-z]*[ \t]*\n(.*?)```", text, re.S):
        m = re.match(r"\s*#\s*file:\s*(\S+)[ \t]*\n", block)
        if m and NAME_OK.match(m.group(1)):
            files[m.group(1)] = block[m.end():]
    return obj, files, err


def changed_lines(old, new):
    n = 0
    for l in difflib.unified_diff(old.strip().splitlines(), new.strip().splitlines(), lineterm="", n=0):
        if l[:1] in "+-" and not l.startswith(("+++", "---")):
            n += 1
    return n


def grade_root_cause(task, obj):
    gt = task["ground_truth"]
    d = dict(file=False, function=False, category=False, format=False)
    if not isinstance(obj, dict) or set(obj) != KEYS or not all(isinstance(v, str) for v in obj.values()):
        return d
    cause = obj["cause"].strip()
    d["format"] = bool(cause) and len(cause) <= 300 and obj["category"] in CATEGORIES and obj["file"] in task["files"]
    d["file"] = obj["file"] == gt["file"]
    d["function"] = obj["function"].strip().rstrip("()") in gt["function_aliases"]
    d["category"] = obj["category"] == gt["category"]
    return d


def grade(task, text):
    obj, files, jerr = parse_response(text)
    rc = grade_root_cause(task, obj)
    rc_ok = all(rc.values())
    files = {n: c for n, c in files.items() if not n.startswith("test_")}
    detail, fix_ok = "", False
    if not files:
        detail = "no files returned"
    else:
        cap = task.get("max_changed_lines")
        over = None
        if cap is not None:
            total = sum(changed_lines(task["files"].get(n, ""), c) for n, c in files.items())
            if total > cap:
                over = f"diff too large: {total} changed lines > {cap}"
        if over:
            detail = over
        else:
            ok, out = run_files({**task["files"], **files, task["hidden_tests"]["name"]: task["hidden_tests"]["code"]},
                                task["hidden_tests"]["name"])
            fix_ok, detail = ok, ("" if ok else out[-300:])
    return dict(root_cause=rc_ok, root_cause_parts=rc, fix=fix_ok, full=rc_ok and fix_ok,
                score=0.5 * rc_ok + 0.5 * fix_ok, detail=detail)


def reference_response(task):
    rc = {k: task["reference"]["root_cause"][k] for k in ("file", "function", "category", "cause")}
    out = "```json\n" + json.dumps(rc) + "\n```\n\n" + show(task["reference"]["files"])
    return out
