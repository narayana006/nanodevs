"""Compile tasks_src/*.py (each defines TASKS) into tasks.jsonl."""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tasks_src"))
MODULES = ["t_dockerfile", "t_compose", "t_k8s", "t_ci", "t_shell", "t_makefile", "t_terraform"]


def main():
    tasks, ids = [], set()
    for m in MODULES:
        if not os.path.exists(os.path.join(HERE, "tasks_src", m + ".py")):
            continue
        mod = importlib.import_module(m)
        for t in mod.TASKS:
            assert t["id"] not in ids, "duplicate id " + t["id"]
            ids.add(t["id"])
            tasks.append(t)
    with open(os.path.join(HERE, "tasks.jsonl"), "w") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"wrote {len(tasks)} tasks")


if __name__ == "__main__":
    main()
