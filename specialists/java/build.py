"""Collects tasks from tasks_*.py, checks schema, writes tasks.jsonl."""
import json, sys, collections
import tasks_fix, tasks_impl, tasks_ext

KEYS = {"id", "kind", "difficulty", "files", "instruction", "visible", "hidden_tests", "reference", "entry", "tags"}
tasks = tasks_fix.T + tasks_impl.T + tasks_ext.T
ids = [t["id"] for t in tasks]
assert len(ids) == len(set(ids)), [i for i, c in collections.Counter(ids).items() if c > 1]
for t in tasks:
    assert set(t) == KEYS, t["id"]
    assert t["kind"] in ("fix", "implement", "extend") and t["difficulty"] in ("easy", "medium", "hard"), t["id"]
    assert t["reference"], t["id"]
with open("tasks.jsonl", "w") as f:
    for t in tasks:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")
c = collections.Counter((t["kind"], t["difficulty"]) for t in tasks)
print(len(tasks), "tasks;", dict(collections.Counter(t["kind"] for t in tasks)), dict(collections.Counter(t["difficulty"] for t in tasks)))
