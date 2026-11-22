"""Run a model over the ops task set with the specialist's own prompts and grader.
Usage: run_ops.py NAME PORT [K] [WORKERS] [LIMIT]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bench
sys.path.insert(0, os.path.join(_bench.ROOT, "specialists", "ops"))
import graders

tasks = [json.loads(l) for l in open(os.path.join(_bench.ROOT, "specialists", "ops", "tasks.jsonl")) if l.strip()]

def grade(t, text):
    r = graders.grade(t, text, "docker")
    err = str(r["detail"].get("error", ""))
    parsed = not (err.startswith("no JSON") or err.startswith("no code block"))
    return r["pass"], r["detail"], parsed

_bench.main("ops", tasks, lambda t: t["inputs"]["prompt"], grade)
