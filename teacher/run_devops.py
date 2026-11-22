"""Run a model over the devops task set with the specialist's own prompt builder and grader.
Usage: run_devops.py NAME PORT [K] [WORKERS] [LIMIT]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bench
sys.path.insert(0, os.path.join(_bench.ROOT, "specialists", "devops"))
import grade as G

tasks = G.load_tasks()

def grade(t, text):
    files = G.extract_files(text)
    if not all(o in files for o in t["outputs"]):
        return False, "missing output file(s): " + ",".join(o for o in t["outputs"] if o not in files), bool(files)
    r = G.grade(t, files)
    return r["passed"], {k: v[1] for k, v in r["checks"].items() if not v[0]}, True

_bench.main("devops", tasks, G.make_prompt, grade)
