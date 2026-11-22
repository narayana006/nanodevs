"""Write tasks.jsonl (one JSON object per line) from the task modules. Run after validate.py (which writes start_outputs.json)."""
import json
import os
from collections import Counter

from registry import all_tasks

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    outs = {}
    p = os.path.join(HERE, "start_outputs.json")
    if os.path.exists(p):
        outs = json.load(open(p))
    tasks = all_tasks()
    with open(os.path.join(HERE, "tasks.jsonl"), "w") as f:
        for t in tasks:
            rec = {
                "id": t["id"], "kind": t["kind"], "difficulty": t["difficulty"], "topic": t["topic"],
                "multi_file": len(t["files"]) > 1 or len(t["reference"]) > 1,
                "files": {k: v.strip("\n") + "\n" for k, v in t["files"].items()},
                "instruction": t["instruction"],
                "visible": t["visible"].strip("\n") + "\n",
                "start_output": outs.get(t["id"], "") if t["kind"] == "fix" else "",
                "hidden": t["hidden"].strip("\n") + "\n",
                "reference": {k: v.strip("\n") + "\n" for k, v in t["reference"].items()},
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(len(tasks), "tasks written")
    print("by kind:", dict(Counter(t["kind"] for t in tasks)))
    print("by difficulty:", dict(Counter(t["difficulty"] for t in tasks)))
    for k in ("fix", "write", "feature", "refactor"):
        print(" ", k, dict(Counter(t["difficulty"] for t in tasks if t["kind"] == k)))
    print("multi-file:", sum(1 for t in tasks if len(t["files"]) > 1 or len(t["reference"]) > 1))


if __name__ == "__main__":
    main()
