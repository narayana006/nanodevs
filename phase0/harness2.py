"""Phase 0, round 2: multi-file tasks, four skills (fix, write, feature, tests), mutation grading."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid

from harness import IMAGE, TMP, chat

NAME_OK = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*\.py$")


def run_files(files, entry, timeout=40):
    """Run `python entry` with all files in /w: no network, read-only, no capabilities, 256 MB, 1 CPU."""
    d = tempfile.mkdtemp(dir=TMP)
    name = "tc-" + uuid.uuid4().hex[:10]
    try:
        for fname, code in files.items():
            with open(os.path.join(d, fname), "w") as f:
                f.write(code.strip("\n") + "\n")
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1",
               "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--user", "65534:65534", "-v", f"{d}:/w:ro", "-w", "/w", IMAGE, "python", "/w/" + entry]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return p.returncode == 0, (p.stdout + p.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return False, "TIMEOUT"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def extract_files(text):
    """Blocks whose first line is `# file: name.py` -> {name: code}."""
    out = {}
    for block in re.findall(r"```[A-Za-z]*[ \t]*\n(.*?)```", text, re.S):
        m = re.match(r"\s*#\s*file:\s*(\S+)[ \t]*\n", block)
        if m and NAME_OK.match(m.group(1)):
            out[m.group(1)] = block[m.end():]
    return out


def show(files):
    return "\n\n".join(f"```python\n# file: {n}\n{c.strip()}\n```" for n, c in files.items())


FORMAT = ("Return the complete contents of every file you change or create, each in its own ```python block whose "
          "first line is `# file: <filename>`. Do not return the tests or files you did not change. No explanation.")


def tests_file(task):
    return task["tests"] if task["kind"] == "fix" else task.get("hidden", "")


def make_prompt(task, start_output):
    k = task["kind"]
    if k == "fix":
        return (f"Fix the bug(s) in this small Python project. The tests below fail.\n\n{show(task['files'])}\n\n"
                f"Tests:\n```python\n{task['tests'].strip()}\n```\n\nTest output:\n```\n{start_output.strip()}\n```\n\n{FORMAT}")
    if k in ("write", "feature"):
        verb = "Implement this" if k == "write" else "Extend this code"
        return (f"{verb}.\n\nCurrent files:\n{show(task['files'])}\n\nTask: {task['instruction']}\n\n"
                f"Examples that must work:\n```python\n{task['visible'].strip()}\n```\n\n{FORMAT}")
    return (f"{task['instruction']}\n\nModule under test:\n{show(task['files'])}\n\n"
            f"Write a test file `test_solution.py` that imports from `{task['module']}` and uses plain `assert` "
            f"statements (no pytest, no unittest). The tests will be run against the correct module, where they must all "
            f"pass, and against several subtly broken versions of it, where each must fail. Cover edge cases and error "
            f"cases, not only the happy path.\n\nReturn only the file `test_solution.py` in one ```python block whose first "
            f"line is `# file: test_solution.py`. No explanation.")


def grade(task, cand):
    """Return (passed, detail) for the candidate's files."""
    if task["kind"] == "tests":
        code = cand.get("test_solution.py")
        if code is None:
            return False, "NO test_solution.py"
        ok, out = run_files({**task["files"], "test_solution.py": code}, "test_solution.py")
        if not ok:
            return False, "fails on the correct module: " + out[-250:]
        survived = 0
        for m in task["mutants"]:
            mok, _ = run_files({**task["files"], **m, "test_solution.py": code}, "test_solution.py")
            survived += 1 if mok else 0
        return survived == 0, f"mutants survived: {survived}/{len(task['mutants'])}"
    if not cand:
        return False, "NO FILES"
    files = {**task["files"], **cand, "test_hidden.py": tests_file(task)}
    ok, out = run_files(files, "test_hidden.py")
    return ok, ("" if ok else out[-250:])


def run_eval2(name, base, tasks, k, outfile):
    results = []
    for t in tasks:
        start_out = ""
        if t["kind"] == "fix":
            ok, start_out = run_files({**t["files"], "test_hidden.py": t["tests"]}, "test_hidden.py")
            assert not ok, t["id"]
        prompt = make_prompt(t, start_out)
        cands, solved_at = [], None
        for i in range(1, k + 1):
            t0 = time.time()
            text, ntok = chat(base, prompt, 0.0 if i == 1 else 0.8, max_tokens=3500, seed=1000 + 17 * i)
            gen_s = time.time() - t0
            passed, detail = grade(t, extract_files(text))
            cands.append(dict(i=i, passed=passed, gen_seconds=round(gen_s, 1), tokens=ntok, detail=detail,
                              answer=text[:8000]))
            if passed:
                solved_at = i
                break
        results.append(dict(id=t["id"], kind=t["kind"], solved_at=solved_at, candidates=cands))
        print(f"[{name}] {t['kind']:<8}{t['id']:<26}" + (f"solved at {solved_at}" if solved_at else "NOT SOLVED"), flush=True)
        json.dump(dict(model=name, k=k, results=results), open(outfile, "w"), indent=1)
