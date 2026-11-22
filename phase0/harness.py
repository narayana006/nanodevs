"""Minimal phase 0 harness: ask a local llama-server for fixes, test them in a locked-down Docker container."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "tmp")
os.makedirs(TMP, exist_ok=True)
IMAGE = "python:3.12-slim"


def run_in_docker(code, timeout=30):
    """Run code with no network, read-only filesystem, no capabilities, 256 MB, 1 CPU."""
    d = tempfile.mkdtemp(dir=TMP)
    name = "tc-" + uuid.uuid4().hex[:10]
    try:
        with open(os.path.join(d, "main.py"), "w") as f:
            f.write(code)
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m",
               "--cpus", "1", "--pids-limit", "64", "--read-only", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "--user", "65534:65534",
               "-v", f"{d}:/w:ro", IMAGE, "python", "/w/main.py"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return p.returncode == 0, (p.stdout + p.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return False, "TIMEOUT"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def extract_code(text):
    blocks = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", text, re.S)
    blocks = [b for b in blocks if "def " in b or "class " in b]
    return max(blocks, key=len) if blocks else None


def chat(base, prompt, temperature, max_tokens=2048, seed=1234):
    body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                       "temperature": temperature, "max_tokens": max_tokens, "seed": seed}).encode()
    req = urllib.request.Request(base + "/v1/chat/completions", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    msg = d["choices"][0]["message"]
    return (msg.get("content") or ""), d.get("usage", {}).get("completion_tokens", 0)


PROMPT = """You are fixing a bug in a Python program. The tests below fail.

Code:
```python
{buggy}
```

Tests:
```python
{tests}
```

Test output:
```
{output}
```

Reply with the complete corrected code (everything in the Code block, without the tests) in a single ```python block. No explanation."""


def run_eval(name, base, tasks, k, outfile):
    results = []
    for t in tasks:
        buggy, tests = t["buggy"].strip() + "\n", t["tests"].strip() + "\n"
        ok, fail_out = run_in_docker(buggy + "\n" + tests)
        assert not ok, f"task {t['id']} has no failing test on the buggy code"
        prompt = PROMPT.format(buggy=buggy.strip(), tests=tests.strip(), output=fail_out.strip())
        cands, solved_at = [], None
        for i in range(1, k + 1):
            t0 = time.time()
            text, ntok = chat(base, prompt, 0.0 if i == 1 else 0.8)
            gen_s = time.time() - t0
            code = extract_code(text)
            passed, out = (False, "NO CODE BLOCK") if code is None else run_in_docker(code + "\n\n" + tests)
            cands.append(dict(i=i, passed=passed, gen_seconds=round(gen_s, 1), tokens=ntok,
                              tail=(out[-300:] if not passed else "")))
            if passed:
                solved_at = i
                break
        results.append(dict(id=t["id"], solved_at=solved_at, candidates=cands))
        print(f"[{name}] {t['id']:<18} " + (f"solved at candidate {solved_at}" if solved_at else "NOT SOLVED"), flush=True)
        json.dump(dict(model=name, k=k, results=results), open(outfile, "w"), indent=1)
    return results
