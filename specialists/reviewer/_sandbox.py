"""Runs states inside ONE locked-down container: python:3.12-slim, no network, read-only, no caps, uid 65534."""
import json
import os
import shutil
import subprocess
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGE = "python:3.12-slim"
DRIVER = r'''
import json, os, subprocess, sys
res = {}
for st in sorted(os.listdir("/w/states")):
    try:
        p = subprocess.run([sys.executable, "-B", "/w/_run.py", "/w/states/" + st], capture_output=True, text=True,
                           timeout=15, cwd="/w/states/" + st)
        out = {}
        for ln in p.stdout.splitlines():
            parts = ln.split(" ", 2)
            if parts[0] in ("PASS", "FAIL") and len(parts) >= 2:
                out[parts[1]] = parts[0]
        if not out:
            out = {"__crash__": "FAIL " + (p.stderr or "no output")[-300:]}
        res[st] = out
    except subprocess.TimeoutExpired:
        res[st] = {"__timeout__": "FAIL"}
print(json.dumps(res))
'''


def run_states(states, timeout=180):
    """states: {name: {filename: text}} (each must include test_hidden.py). -> {name: {test: PASS|FAIL}}"""
    d = tempfile.mkdtemp(dir=HERE)
    cname = "rv-" + uuid.uuid4().hex[:10]
    try:
        os.makedirs(os.path.join(d, "states"))
        for st, files in states.items():
            sd = os.path.join(d, "states", st)
            os.makedirs(sd)
            for fn, txt in files.items():
                with open(os.path.join(sd, fn), "w") as f:
                    f.write(txt)
        for fn in ("_rt.py", "_run.py"):
            shutil.copy(os.path.join(HERE, fn), os.path.join(d, fn))
        with open(os.path.join(d, "_driver.py"), "w") as f:
            f.write(DRIVER)
        os.chmod(d, 0o755)
        for root, ds, fs in os.walk(d):
            for x in ds:
                os.chmod(os.path.join(root, x), 0o755)
            for x in fs:
                os.chmod(os.path.join(root, x), 0o644)
        cmd = ["docker", "run", "--rm", "--name", cname, "--network", "none", "--memory", "256m", "--cpus", "1",
               "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--user", "65534:65534", "-v", f"{d}:/w:ro", "-w", "/w", IMAGE, "python", "-B", "/w/_driver.py"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", cname], capture_output=True)
            raise RuntimeError("container timeout")
        if p.returncode != 0:
            raise RuntimeError("container failed: " + p.stderr[-500:])
        return json.loads(p.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(d, ignore_errors=True)
