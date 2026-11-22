"""Compile + run a Java task. Two backends: 'host' (local javac, timeout only) and 'docker' (locked down)."""
import os, shutil, subprocess, tempfile, uuid

DOCKER_FLAGS = ["--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                "--user", "65534:65534", "--memory", "512m", "--cpus", "1", "--pids-limit", "128",
                "--tmpfs", "/out:exec,size=64m,uid=65534"]

def run_task(files, entry="HiddenTest", backend="host", image=None, timeout=60):
    """files: {name: source} (all .java). Returns (ok, output, phase) where phase in compile|run|timeout."""
    d = tempfile.mkdtemp(prefix="jt-")
    try:
        os.chmod(d, 0o755)
        for n, s in files.items():
            with open(os.path.join(d, n), "w") as f:
                f.write(s)
        srcs = sorted(n for n in files if n.endswith(".java"))
        if backend == "host":
            out = os.path.join(d, "out"); os.mkdir(out)
            c = subprocess.run(["javac", "-nowarn", "--release", "17", "-d", out] + [os.path.join(d, s) for s in srcs],
                               capture_output=True, text=True, timeout=timeout)
            if c.returncode: return False, (c.stdout + c.stderr)[-2000:], "compile"
            try:
                r = subprocess.run(["java", "-Xmx256m", "-cp", out, entry], capture_output=True, text=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                return False, "TIMEOUT", "timeout"
            return r.returncode == 0, (r.stdout + r.stderr)[-2000:], "run"
        name = "jt-" + uuid.uuid4().hex[:10]
        script = "javac -nowarn --release 17 -d /out " + " ".join("/w/" + s for s in srcs) + " && java -Xmx256m -Xshare:auto -cp /out " + entry
        cmd = ["docker", "run", "--rm", "--name", name] + DOCKER_FLAGS + ["-v", f"{d}:/w:ro", "-w", "/w", "--entrypoint", "sh", image, "-c", script]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return False, "TIMEOUT", "timeout"
        txt = r.stdout + r.stderr
        return r.returncode == 0, txt[-2000:], ("compile" if "error:" in txt and "PASS" not in txt and "FAIL" not in txt else "run")
    finally:
        shutil.rmtree(d, ignore_errors=True)

def task_files(task, candidate=None):
    """Starting files overlaid with candidate files (or the reference), plus the hidden tests."""
    return {**task["files"], **(task["reference"] if candidate is None else candidate), **task["hidden_tests"]}

def make_prompt(task, start_output=""):
    """Reference prompt builder (mirrors phase0/harness2.make_prompt)."""
    show = "\n\n".join(f"```java\n// file: {n}\n{c.strip()}\n```" for n, c in task["files"].items())
    fmt = ("Return the complete contents of every file you change or create, each in its own ```java block whose first "
           "line is `// file: <FileName>.java`. Do not return the tests or files you did not change. No explanation.")
    k = task["kind"]
    if k == "fix":
        return (f"Fix the bug(s) in this small Java program. The hidden tests fail.\n\n{show}\n\nSymptom: {task['instruction']}\n\n"
                f"Test output:\n```\n{start_output.strip()}\n```\n\n{fmt}")
    verb = "Implement this" if k == "implement" else "Extend this code"
    vis = f"\n\nExamples that must work:\n```java\n{task['visible']}\n```" if task["visible"] else ""
    return f"{verb}.\n\nCurrent files:\n{show}\n\nTask: {task['instruction']}{vis}\n\n{fmt}"
