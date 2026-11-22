"""Sandbox runner + grading for the qa task factory (same container limits as phase0/harness2.py)."""
import os
import shutil
import subprocess
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, ".tmp")
os.makedirs(TMP, exist_ok=True)
IMAGE = "python:3.12-slim"
BAD_MUTANT = ("SyntaxError", "IndentationError", "ImportError", "ModuleNotFoundError")


def run_files(files, entry="test_solution.py", timeout=20):
    """Run `python entry` with all files in /w: no network, read-only, no caps, 256 MB, 1 CPU. One container."""
    d = tempfile.mkdtemp(dir=TMP)
    name = "tcqa-" + uuid.uuid4().hex[:10]
    try:
        for fname, code in files.items():
            with open(os.path.join(d, fname), "w") as f:
                f.write(code.strip("\n") + "\n")
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1",
               "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--user", "65534:65534", "-v", f"{d}:/w:ro", "-w", "/w", "-e", "PYTHONDONTWRITEBYTECODE=1",
               IMAGE, "python", "/w/" + entry]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return p.returncode == 0, (p.stdout + p.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return False, "TIMEOUT"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def run_tests(files, tests, timeout=20):
    return run_files({**files, "test_solution.py": tests}, "test_solution.py", timeout)


def grade(task, tests):
    """Candidate test file -> (passed, detail). Must pass on reference_files and fail on every mutant."""
    ok, out = run_tests(task["reference_files"], tests)
    if not ok:
        return False, "fails on the correct module: " + out[-250:]
    for m in task["mutants"]:
        mok, _ = run_tests({**task["reference_files"], **m["files"]}, tests)
        if mok:
            return False, f"mutant {m['id']} survives"
    return True, "all mutants killed"


DRIVER = r'''
import json, os, subprocess, sys, tempfile
jobs = json.load(open("/w/_job.json"))
res = []
for j in jobs["variants"]:
    d = tempfile.mkdtemp(dir="/tmp")
    for name, code in {**j["files"], "test_solution.py": j["tests"]}.items():
        with open(os.path.join(d, name), "w") as f:
            f.write(code.strip("\n") + "\n")
    try:
        p = subprocess.run([sys.executable, "test_solution.py"], cwd=d, capture_output=True, text=True,
                           timeout=jobs["per_timeout"], env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": str(jobs.get("hashseed", "random"))})
        res.append([p.returncode == 0, (p.stdout + p.stderr)[-1500:]])
    except subprocess.TimeoutExpired:
        res.append([False, "TIMEOUT"])
print("@@RESULT@@" + json.dumps(res))
'''


def run_batch(variants, per_timeout=8, hashseed=None):
    """variants: list of (files, tests). Runs them all inside ONE container (same limits as run_files, plus a small
    tmpfs so the driver can lay out each variant), one fresh `python test_solution.py` subprocess per variant.
    Returns a list of (ok, output) in order."""
    import json
    if not variants:
        return []
    d = tempfile.mkdtemp(dir=TMP)
    name = "tcqa-" + uuid.uuid4().hex[:10]
    try:
        with open(os.path.join(d, "_driver.py"), "w") as f:
            f.write(DRIVER)
        with open(os.path.join(d, "_job.json"), "w") as f:
            json.dump({"per_timeout": per_timeout, "hashseed": hashseed if hashseed is not None else "random",
                       "variants": [{"files": fl, "tests": t} for fl, t in variants]}, f)
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1",
               "--pids-limit", "64", "--read-only", "--tmpfs", "/tmp:rw,size=64m", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "--user", "65534:65534", "-v", f"{d}:/w:ro", "-w", "/w",
               IMAGE, "python", "/w/_driver.py"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=len(variants) * (per_timeout + 2) + 60)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return [(False, "TIMEOUT")] * len(variants)
        for line in p.stdout.splitlines():
            if line.startswith("@@RESULT@@"):
                return [tuple(r) for r in json.loads(line[len("@@RESULT@@"):])]
        raise RuntimeError("batch failed: " + (p.stdout + p.stderr)[-500:])
    finally:
        shutil.rmtree(d, ignore_errors=True)
