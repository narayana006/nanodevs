"""Grader for the devops task factory.

API (import from the eval harness):
    load_tasks(path=TASKS)                      -> list[dict]
    make_prompt(task)                           -> str     (what the model sees; hidden checks are NOT included)
    extract_files(model_text)                   -> {path: content}   (blocks whose first line is `# file: <path>`)
    grade(task, candidate_files, sandbox=True)  -> {"passed": bool, "checks": {id: [ok, msg]}}

Sandboxing: all untrusted content is evaluated in ONE container at a time:
  * python:3.12-slim  runs lib/grader_inner.py  (static rule checks + shell behaviour tests against fixtures/stubs)
  * koalaman/shellcheck:stable  runs shellcheck for `shellcheck` checks
both with --network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 65534:65534
--memory 256m --cpus 1 --pids-limit 64 and a small tmpfs /tmp mounted with `exec` (shell tests execute stub commands from it).
sandbox=False evaluates in-process on the host (dev/fast mode only; still stdlib, but behaviour tests then run
unsandboxed and shellcheck checks are skipped).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(HERE, "tasks.jsonl")
TMP = os.path.join(HERE, "tmp")
os.makedirs(TMP, exist_ok=True)
PY_IMAGE = "python:3.12-slim"
SC_IMAGE = "koalaman/shellcheck:stable"
SAFE_NAME = re.compile(r"^(?!/)(?!.*\.\.)[A-Za-z0-9_.\-/]{1,120}$")
LOCKDOWN = ["--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--user", "65534:65534", "--memory", "256m", "--cpus", "1", "--pids-limit", "64"]

sys.path.insert(0, os.path.join(HERE, "lib"))


def load_tasks(path=TASKS):
    return [json.loads(l) for l in open(path) if l.strip()]


def extract_files(text):
    """```lang\n# file: path\n...``` -> {path: content}. The marker line may also use // or ; comment leaders."""
    out = {}
    for block in re.findall(r"```[A-Za-z0-9_+\-]*[ \t]*\n(.*?)```", text, re.S):
        m = re.match(r"\s*(?:#|//|;)\s*file:\s*(\S+)[ \t]*\n", block)
        if m and SAFE_NAME.match(m.group(1)):
            out[m.group(1)] = block[m.end():]
    return out


def _fence(name):
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    return {"yml": "yaml", "yaml": "yaml", "sh": "bash", "tf": "hcl", "json": "json"}.get(ext, "makefile" if name == "Makefile" else "dockerfile" if name.startswith("Dockerfile") else "")


def make_prompt(task):
    parts = [task["instruction"].strip()]
    if task["files"]:
        parts.append("Current files:")
        for n, c in task["files"].items():
            parts.append(f"```{_fence(n)}\n# file: {n}\n{c.strip(chr(10))}\n```")
    parts.append("Return the complete final contents of every file you create or change (" + ", ".join(task["outputs"]) +
                 "), each in its own fenced code block whose first line is `# file: <path>` (use exactly these paths). "
                 "Do not return unchanged files. No explanation.")
    return "\n\n".join(parts)


def _clean(files):
    return {k: v.replace("\r\n", "\n") for k, v in files.items() if SAFE_NAME.match(k)}


def _docker(cmd, timeout):
    name = "dv-" + uuid.uuid4().hex[:10]
    full = ["docker", "run", "--name", name] + LOCKDOWN + cmd
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        return 124, "", "TIMEOUT"


def grade(task, cand, sandbox=True):
    return grade_many(task, [cand], sandbox)[0]


def grade_many(task, cands, sandbox=True):
    """Grade several candidates of one task; all non-shellcheck rules for ALL candidates share one container run."""
    checks = task["checks"]
    d = tempfile.mkdtemp(dir=TMP)
    all_files, results = [], [{} for _ in cands]
    try:
        for n, cand in enumerate(cands):
            files = _clean({**task["files"], **cand})
            all_files.append(files)
            os.makedirs(os.path.join(d, f"files{n}"))
            for k, v in files.items():
                p = os.path.join(d, f"files{n}", k)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w") as f:
                    f.write(v)
            json.dump({"files": files, "checks": checks}, open(os.path.join(d, f"job{n}.json"), "w"))
        os.chmod(d, 0o755)
        for root, ds, fs in os.walk(d):
            for x in ds:
                os.chmod(os.path.join(root, x), 0o755)
            for x in fs:
                os.chmod(os.path.join(root, x), 0o644)
        if sandbox:
            rc, out, err = _docker(["--tmpfs", "/tmp:rw,exec,nosuid,nodev,mode=1777,size=32m", "-v", f"{os.path.join(HERE, 'lib')}:/opt/dolib:ro",
                                    "-v", f"{d}:/job:ro", PY_IMAGE, "python", "-I", "/opt/dolib/grader_inner.py"] + [f"/job/job{n}.json" for n in range(len(cands))], 150 + 60 * len(cands))
            lines = [l for l in out.strip().splitlines() if l.startswith("{")]
            for n in range(len(cands)):
                try:
                    results[n].update(json.loads(lines[n]))
                except Exception:
                    for c in checks:
                        if c["type"] != "shellcheck":
                            results[n][c["id"]] = [False, f"grader failure rc={rc}: {err[-200:]}"]
            for n in range(len(cands)):
                for c in checks:
                    if c["type"] != "shellcheck":
                        continue
                    if c["file"] not in all_files[n]:
                        results[n][c["id"]] = [False, f"{c['file']} missing"]
                        continue
                    cmd = ["-v", f"{os.path.join(d, f'files{n}')}:/mnt:ro", SC_IMAGE, "-f", "gcc"]
                    if c.get("shell"):
                        cmd += ["-s", c["shell"]]
                    for e in c.get("exclude", []):
                        cmd += ["-e", e]
                    cmd += ["/mnt/" + c["file"]]
                    rc, out, err = _docker(cmd, 60)
                    results[n][c["id"]] = [rc == 0, "ok" if rc == 0 else (out + err).strip().replace("/mnt/", "")[:300]]
        else:
            import grader_inner
            for n, files in enumerate(all_files):
                results[n].update(grader_inner.evaluate(files, checks))
                for c in checks:
                    if c["type"] == "shellcheck":
                        results[n][c["id"]] = [True, "skipped (fast mode)"]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return [{"passed": all(v[0] for v in r.values()) and len(r) == len(checks), "checks": r} for r in results]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="grade a model answer: grade.py TASK_ID ANSWER.txt")
    ap.add_argument("task_id")
    ap.add_argument("answer")
    a = ap.parse_args()
    t = next(t for t in load_tasks() if t["id"] == a.task_id)
    r = grade(t, extract_files(open(a.answer).read()))
    print(json.dumps(r, indent=1))
    sys.exit(0 if r["passed"] else 1)
