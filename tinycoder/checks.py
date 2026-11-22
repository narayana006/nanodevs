"""Run immutable test cases in disposable candidate subprocesses."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

WORKER = Path(__file__).with_name("worker.py").resolve()


def run_checks(source, function_name, cases, directory, timeout=1.0):
    started = time.monotonic()
    candidate = directory / "candidate.py"
    request = directory / "request.json"
    candidate.write_text(source)
    request.write_text(json.dumps({"candidate": str(candidate), "function": function_name, "cases": cases}))
    env = {"PATH": os.defpath, "PYTHONHASHSEED": "0", "PYTHONNOUSERSITE": "1", "TMPDIR": str(directory)}
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen([sys.executable, "-I", "-B", str(WORKER), str(request)], cwd=directory, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            return {"status": "timeout", "cases": len(cases), "failures": [], "seconds": time.monotonic() - started}
        # Clean up descendants even when the checker itself exited first.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout.seek(0)
        raw = stdout.read(131073)
        if process.returncode != 0:
            stderr.seek(0)
            return {"status": "process_error", "returncode": process.returncode, "failures": [], "detail": stderr.read(2048).decode(errors="replace"), "seconds": time.monotonic() - started}
        try:
            value = json.loads(raw)
            if value.get("status") not in {"passed", "failed"}:
                raise ValueError("Invalid checker status")
        except (ValueError, AttributeError):
            value = {"status": "checker_error", "failures": [], "detail": "Checker did not return its expected JSON protocol"}
    value["seconds"] = time.monotonic() - started
    return value
