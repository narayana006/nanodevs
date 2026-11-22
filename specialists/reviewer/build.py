"""Build tasks.jsonl from templates_*.py.  Usage: python3 build.py"""
import glob
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import build  # noqa: E402


def all_tasks():
    tasks = []
    for path in sorted(glob.glob(os.path.join(HERE, "templates_*.py"))):
        mod = importlib.import_module(os.path.basename(path)[:-3])
        for name, (tpl, params) in mod.TEMPLATES.items():
            for vi, P in enumerate(params, 1):
                tasks.extend(build(tpl, P, name, f"v{vi}"))
    return tasks


if __name__ == "__main__":
    tasks = all_tasks()
    ids = [t["id"] for t in tasks]
    assert len(ids) == len(set(ids)), "duplicate ids"
    # stable, interleaved order: sort by id
    tasks.sort(key=lambda t: t["id"])
    with open(os.path.join(HERE, "tasks.jsonl"), "w") as f:
        for t in tasks:
            f.write(json.dumps(t, sort_keys=True) + "\n")
    nb = sum(t["kind"] == "buggy" for t in tasks)
    print(f"wrote {len(tasks)} tasks ({nb} buggy, {len(tasks) - nb} clean)")
