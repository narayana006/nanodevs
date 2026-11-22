"""Sandbox runner, copied from phase0/harness2.py (same flags). Temp dirs live in ./.tmp (docker-shareable)."""
import os
import shutil
import subprocess
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, ".tmp")
IMAGE = "python:3.12-slim"


def run_files(files, entry, timeout=40):
    """Run `python entry` with all files in /w: no network, read-only, no capabilities, 256 MB, 1 CPU."""
    os.makedirs(TMP, exist_ok=True)
    d = tempfile.mkdtemp(dir=TMP)
    name = "tc-" + uuid.uuid4().hex[:10]
    try:
        for fname, code in files.items():
            with open(os.path.join(d, fname), "w", encoding="utf-8") as f:
                f.write(code.strip("\n") + "\n")
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1",
               "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--user", "65534:65534", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTHONHASHSEED=0",
               "-v", f"{d}:/w:ro", "-w", "/w", IMAGE, "python", "/w/" + entry]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return p.returncode == 0, (p.stdout + p.stderr)[-2500:]
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return False, "TIMEOUT"
    finally:
        shutil.rmtree(d, ignore_errors=True)
