"""Shared helpers: Docker sandbox runner (same limits as phase0/harness2.py) and task constructors."""
import os
import shutil
import subprocess
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "tmp")
IMAGE = "python:3.12-slim"


def run_files(files, entry, timeout=40):
    """Run `python entry` with all files in /w: no network, read-only, no caps, 256 MB, 1 CPU, 64 pids, uid 65534."""
    os.makedirs(TMP, exist_ok=True)
    d = tempfile.mkdtemp(dir=TMP)
    name = "tc-" + uuid.uuid4().hex[:10]
    try:
        for fname, code in files.items():
            os.makedirs(os.path.dirname(os.path.join(d, fname)), exist_ok=True)
            with open(os.path.join(d, fname), "w") as f:
                f.write(code.strip("\n") + "\n")
        for root, dirs, _ in os.walk(d):
            os.chmod(root, 0o755)
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


def fix(id, difficulty, topic, files, patches, instruction, visible, hidden):
    """Fix-bug task. `files` hold the BUGGY code; the reference is derived by applying (file, old, new) patches."""
    ref = {}
    for fname, old, new in patches:
        src = ref.get(fname, files[fname])
        assert src.count(old) == 1, (id, fname, old)
        ref[fname] = src.replace(old, new)
    return dict(id=id, kind="fix", difficulty=difficulty, topic=topic, files=files, instruction=instruction,
                visible=visible, hidden=hidden, reference=ref)


def task(id, kind, difficulty, topic, files, instruction, visible, hidden, reference):
    return dict(id=id, kind=kind, difficulty=difficulty, topic=topic, files=files, instruction=instruction,
                visible=visible, hidden=hidden, reference=reference)


def feat(id, difficulty, topic, files, instruction, visible, hidden, append=None, patches=None, replace=None, kind="feature"):
    """Extend/refactor task. Reference = files after: patches (file, old, new), then append {file: text}, or whole-file `replace`."""
    ref = {}
    for fname, old, new in (patches or []):
        src = ref.get(fname, files[fname])
        assert src.count(old) == 1, (id, fname, old)
        ref[fname] = src.replace(old, new)
    for fname, text in (append or {}).items():
        ref[fname] = ref.get(fname, files[fname]).rstrip("\n") + "\n" + text
    ref.update(replace or {})
    return dict(id=id, kind=kind, difficulty=difficulty, topic=topic, files=files, instruction=instruction,
                visible=visible, hidden=hidden, reference=ref)
