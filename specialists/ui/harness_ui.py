"""UI specialist harness: run hidden checks against candidate files in a locked-down sandbox.

- runner "node":   host node with the Permission Model (no fs write, no network, no child process, no workers),
                   --max-old-space-size=200, hard timeout, cwd = a throwaway temp dir. No Docker image has node, so this
                   is the sandbox for JS (we never pull images).
- runner "python": python:3.12-slim container: --network none --read-only --cap-drop ALL --user 65534:65534
                   --memory 256m --cpus 1 --pids-limit 64, files mounted read-only at /w. One container at a time.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib")
NODE = os.environ.get("UI_NODE", "/opt/homebrew/bin/node")
IMAGE = "python:3.12-slim"
NAME_OK = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*\.(js|html|css)$")
TMP = os.path.join(HERE, "tmp")


def _write(d, files):
    for name, code in files.items():
        with open(os.path.join(d, name), "w") as f:
            f.write(code.strip("\n") + "\n")


def run_checks(files, checks, timeout=30):
    """files: candidate project files; checks: {"runner","entry","files"}. Returns (passed, output)."""
    os.makedirs(TMP, exist_ok=True)
    d = tempfile.mkdtemp(dir=TMP)
    try:
        _write(d, files)
        _write(d, checks["files"])  # hidden checks overwrite same-named candidate files
        if checks["runner"] == "node":
            shutil.copy(os.path.join(LIB, "tlib.js"), d)
            cmd = [NODE, "--permission", f"--allow-fs-read={d}", "--max-old-space-size=200", os.path.join(d, checks["entry"])]
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=d)
            except subprocess.TimeoutExpired:
                return False, "TIMEOUT"
            return p.returncode == 0, (p.stdout + p.stderr)[-1500:]
        shutil.copy(os.path.join(LIB, "checklib.py"), d)
        os.chmod(d, 0o755)
        for fn in os.listdir(d):
            os.chmod(os.path.join(d, fn), 0o644)
        name = "ui-" + uuid.uuid4().hex[:10]
        cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1",
               "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--user", "65534:65534", "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", f"{d}:/w:ro", "-w", "/w",
               IMAGE, "python", "/w/" + checks["entry"]]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return False, "TIMEOUT"
        return p.returncode == 0, (p.stdout + p.stderr)[-1500:]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def grade(task, candidate):
    """candidate: {filename: content} for files the model returned. Merged over the start files."""
    bad = [n for n in candidate if not NAME_OK.match(n)]
    if bad:
        return False, "bad file names: %s" % bad
    if not candidate:
        return False, "NO FILES"
    return run_checks({**task["files"], **candidate}, task["checks"])


def load_tasks(path=None):
    path = path or os.path.join(HERE, "tasks.jsonl")
    return [json.loads(l) for l in open(path) if l.strip()]


def make_prompt(task, start_output=""):
    """Prompt text for a task (same shape as phase0/harness2.py: files, instruction, examples, output format)."""
    ext = {"js": "javascript", "html": "html", "css": "css"}
    show = "\n\n".join("```%s\n// file: %s\n%s\n```" % (ext[n.rsplit(".", 1)[1]], n, c.strip()) if n.endswith(".js") else
                       "```%s\n<!-- file: %s -->\n%s\n```" % (ext[n.rsplit(".", 1)[1]], n, c.strip()) if n.endswith(".html") else
                       "```css\n/* file: %s */\n%s\n```" % (n, c.strip()) for n, c in task["files"].items())
    out = f"{task['instruction']}\n\nCurrent files:\n{show}\n"
    if task.get("visible"):
        out += f"\nExamples that must work:\n```\n{task['visible'].strip()}\n```\n"
    if start_output:
        out += f"\nCheck output on the current files:\n```\n{start_output.strip()}\n```\n"
    out += ("\nReturn the complete contents of every file you change or create, each in its own fenced block whose first "
            "line is a comment `file: <filename>` (// for js, <!-- --> for html, /* */ for css). Do not return unchanged "
            "files. No explanation.")
    return out
