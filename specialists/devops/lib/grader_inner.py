"""Runs INSIDE the sandbox container (python:3.12-slim, stdlib only): evaluates all non-shellcheck checks of one job.

usage: python -I /lib/grader_inner.py /job/job.json  -> prints JSON {check_id: [ok, message]}
job.json = {"files": {relpath: text}, "checks": [{"id":..., "type":..., ...args}]}
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402


def _shebang_interp(text):
    first = text.split("\n", 1)[0]
    if first.startswith("#!") and re.search(r"\bsh\b", first) and "bash" not in first:
        return "sh"
    return "bash"


def run_behavior(files, script, cases, shell=None):
    problems = []
    if script not in files:
        return False, f"{script} missing"
    interp = shell or _shebang_interp(files[script])
    for n, case in enumerate(cases):
        name = case.get("name", f"case{n}")
        d = tempfile.mkdtemp(prefix="case", dir="/tmp")
        try:
            def w(rel, content, mode=None):
                p = os.path.join(d, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w") as f:
                    f.write(content)
                os.chmod(p, int(mode, 8) if mode else 0o644)
            w(script, files[script], "755")
            for rel, content in (case.get("files") or {}).items():
                w(rel, content, (case.get("modes") or {}).get(rel))
            stubdir = os.path.join(d, ".stubs")
            os.makedirs(stubdir)
            log = os.path.join(d, ".calls.log")
            open(log, "w").close()
            for cmd, body in (case.get("stubs") or {}).items():
                w(".stubs/" + cmd, '#!/bin/bash\necho "' + cmd + ' $*" >> "$STUB_LOG"\n' + body + "\n", "755")
            env = {"PATH": f"{stubdir}:/usr/local/bin:/usr/bin:/bin", "HOME": d, "LC_ALL": "C", "STUB_LOG": log, "TMPDIR": d}
            env.update(case.get("env") or {})
            try:
                p = subprocess.run([interp, script] + list(case.get("args") or []), cwd=d, env=env, input=case.get("stdin", ""),
                                   capture_output=True, text=True, timeout=case.get("timeout", 10))
            except subprocess.TimeoutExpired:
                problems.append(f"[{name}] timeout")
                continue
            out, err = p.stdout, p.stderr
            rc = case.get("rc", 0)
            if rc == "nonzero":
                if p.returncode == 0:
                    problems.append(f"[{name}] expected non-zero exit, got 0")
            elif p.returncode != rc:
                problems.append(f"[{name}] exit {p.returncode}, want {rc}; stderr={err.strip()[-120:]!r}")
            if "stdout" in case and out.strip() != case["stdout"].strip():
                problems.append(f"[{name}] stdout {out.strip()[:160]!r} != {case['stdout'].strip()[:160]!r}")
            for s in case.get("stdout_has", []):
                if s not in out:
                    problems.append(f"[{name}] stdout lacks {s!r}; got {out.strip()[:120]!r}")
            for s in case.get("stdout_not", []):
                if s in out:
                    problems.append(f"[{name}] stdout must not contain {s!r}")
            for s in case.get("stdout_re", []):
                if not re.search(s, out, re.M):
                    problems.append(f"[{name}] stdout !~ {s!r}; got {out.strip()[:120]!r}")
            for s in case.get("stderr_re", []):
                if not re.search(s, err, re.M):
                    problems.append(f"[{name}] stderr !~ {s!r}; got {err.strip()[:120]!r}")
            for s_ in case.get("stderr_not", []):
                if s_ in err:
                    problems.append(f"[{name}] stderr must not contain {s_!r}")
            for rel in case.get("dirs_exist", []):
                if not os.path.isdir(os.path.join(d, rel)):
                    problems.append(f"[{name}] directory {rel} must exist")
            if case.get("no_leftover_re"):
                left = [e for e in os.listdir(d) if e not in (".stubs", ".calls.log", script)]
                bad = [e for e in left if re.search(case["no_leftover_re"], e)]
                if bad:
                    problems.append(f"[{name}] leftover temp entries: {bad[:3]}")
            for rel, want in (case.get("out_files") or {}).items():
                fp = os.path.join(d, rel)
                if not os.path.exists(fp):
                    problems.append(f"[{name}] expected file {rel} not created")
                elif open(fp).read().strip() != want.strip():
                    problems.append(f"[{name}] {rel} = {open(fp).read().strip()[:120]!r}, want {want.strip()[:120]!r}")
            for rel, rx in (case.get("out_files_re") or {}).items():
                fp = os.path.join(d, rel)
                if not os.path.exists(fp) or not re.search(rx, open(fp).read(), re.M):
                    problems.append(f"[{name}] file {rel} missing or !~ {rx!r}")
            for rel in case.get("no_files", []):
                if os.path.exists(os.path.join(d, rel)):
                    problems.append(f"[{name}] file {rel} must not exist")
            calls = open(log).read()
            pos = 0
            for rx in case.get("calls_re", []):
                m = re.compile(rx, re.M).search(calls, pos)
                if not m:
                    problems.append(f"[{name}] expected call !~ {rx!r} (in order); calls={calls.strip()[:200]!r}")
                    break
                pos = m.end()
            for rx in case.get("calls_not", []):
                if re.search(rx, calls, re.M):
                    problems.append(f"[{name}] forbidden call {rx!r}; calls={calls.strip()[:200]!r}")
            if "calls_count" in case:
                cnt = len([l for l in calls.splitlines() if l.strip()])
                if cnt != case["calls_count"]:
                    problems.append(f"[{name}] {cnt} stub calls, want {case['calls_count']}")
            for rel, mode in (case.get("modes_after") or {}).items():
                fp = os.path.join(d, rel)
                if not os.path.exists(fp) or oct(stat.S_IMODE(os.stat(fp).st_mode))[2:] != mode:
                    problems.append(f"[{name}] mode of {rel} != {mode}")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    return (not problems), ("ok" if not problems else "; ".join(problems[:4]))


def evaluate(files, checks):
    ctx = rules.Ctx(files)
    res = {}
    for ch in checks:
        cid, typ = ch["id"], ch["type"]
        if typ == "shellcheck":
            continue
        args = {k: v for k, v in ch.items() if k not in ("id", "type", "desc", "bug", "keep")}
        try:
            if typ == "sh_behavior":
                ok, msg = run_behavior(files, **args)
            else:
                ok, msg = rules.RULES[typ](ctx, **args)
        except Exception as e:  # unparsable candidate etc. => fail the check
            ok, msg = False, f"{type(e).__name__}: {str(e)[:160]}"
        res[cid] = [bool(ok), msg]
    return res


if __name__ == "__main__":
    for path in sys.argv[1:]:  # one JSON result line per job file
        job = json.load(open(path))
        print(json.dumps(evaluate(job["files"], job["checks"])))
